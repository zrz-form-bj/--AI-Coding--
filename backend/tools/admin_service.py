"""
管理员服务
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import secrets

from models import User, ElderlyInfo, Contact, Memo, ConversationHistory, AdminUser


class AdminService:
    """管理员服务"""
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(8)
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = password_hash.split(":")
            computed_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            return computed_hash == stored_hash
        except:
            return False
    
    # ========== 管理员认证 ==========
    async def login(
        self, 
        username: str, 
        password: str, 
        session: AsyncSession
    ) -> Tuple[bool, str, Optional[AdminUser]]:
        """管理员登录"""
        result = await session.execute(
            select(AdminUser).where(
                and_(AdminUser.username == username, AdminUser.is_active == True)
            )
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            return False, "用户名不存在或账户已禁用", None
        
        if not self._verify_password(password, admin.password_hash):
            return False, "密码错误", None
        
        # 更新最后登录时间
        admin.last_login = datetime.now()
        await session.commit()
        
        return True, "登录成功", admin
    
    async def create_admin(
        self,
        username: str,
        password: str,
        name: str,
        session: AsyncSession,
        role: str = "admin"
    ) -> Tuple[bool, str, Optional[AdminUser]]:
        """创建管理员（用于初始化）"""
        # 检查是否已存在
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        if result.scalar_one_or_none():
            return False, "用户名已存在", None
        
        admin = AdminUser(
            username=username,
            password_hash=self._hash_password(password),
            name=name,
            role=role
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        
        return True, "创建成功", admin
    
    # ========== 用户管理 ==========
    async def get_user_list(
        self,
        session: AsyncSession,
        search: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取用户列表（带统计）"""
        # 构建查询
        query = select(User, ElderlyInfo).join(ElderlyInfo, User.id == ElderlyInfo.user_id)
        
        if search:
            query = query.where(
                or_(
                    User.username.contains(search),
                    User.phone.contains(search),
                    ElderlyInfo.name.contains(search)
                )
            )
        
        # 获取总数
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # 分页查询
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        rows = result.all()
        
        # 组装数据
        users = []
        for user, elderly in rows:
            # 统计联系人数量
            contact_count = await session.execute(
                select(func.count()).where(Contact.elderly_id == elderly.id)
            )
            # 统计记事数量
            memo_count = await session.execute(
                select(func.count()).where(Memo.elderly_id == elderly.id)
            )
            
            users.append({
                "id": elderly.id,
                "user_id": user.id,
                "username": user.username,
                "phone": user.phone,
                "email": elderly.email,
                "name": elderly.name,
                "home_address": elderly.home_address,
                "created_at": user.created_at,
                "contact_count": contact_count.scalar(),
                "memo_count": memo_count.scalar()
            })
        
        return users, total
    
    async def get_user_detail(
        self,
        elderly_id: int,
        session: AsyncSession
    ) -> Optional[dict]:
        """获取用户详情"""
        result = await session.execute(
            select(ElderlyInfo, User)
            .join(User, ElderlyInfo.user_id == User.id)
            .where(ElderlyInfo.id == elderly_id)
        )
        row = result.first()
        
        if not row:
            return None
        
        elderly, user = row
        
        # 获取联系人
        contacts_result = await session.execute(
            select(Contact).where(Contact.elderly_id == elderly_id)
        )
        contacts = contacts_result.scalars().all()
        
        # 获取记事
        memos_result = await session.execute(
            select(Memo).where(Memo.elderly_id == elderly_id)
        )
        memos = memos_result.scalars().all()
        
        return {
            "elderly": elderly,
            "user": user,
            "contacts": contacts,
            "memos": memos
        }
    
    async def create_user(
        self,
        data: dict,
        session: AsyncSession
    ) -> Tuple[bool, str, Optional[ElderlyInfo]]:
        """创建用户"""
        # 检查用户名
        result = await session.execute(
            select(User).where(User.username == data["username"])
        )
        if result.scalar_one_or_none():
            return False, "用户名已存在", None
        
        # 检查手机号
        result = await session.execute(
            select(User).where(User.phone == data["phone"])
        )
        if result.scalar_one_or_none():
            return False, "手机号已注册", None
        
        # 创建用户
        user = User(
            username=data["username"],
            password_hash=self._hash_password(data["password"]),
            phone=data["phone"]
        )
        session.add(user)
        await session.flush()
        
        # 创建老人信息
        elderly = ElderlyInfo(
            user_id=user.id,
            name=data["name"],
            phone=data["phone"],
            email=data.get("email"),
            home_address=data.get("home_address"),
            health_info=data.get("health_info")
        )
        session.add(elderly)
        await session.commit()
        await session.refresh(elderly)
        
        return True, "创建成功", elderly
    
    async def update_user(
        self,
        elderly_id: int,
        data: dict,
        session: AsyncSession
    ) -> Tuple[bool, str]:
        """更新用户"""
        result = await session.execute(
            select(ElderlyInfo, User)
            .join(User, ElderlyInfo.user_id == User.id)
            .where(ElderlyInfo.id == elderly_id)
        )
        row = result.first()
        
        if not row:
            return False, "用户不存在"
        
        elderly, user = row
        
        # 更新老人信息
        if "name" in data and data["name"]:
            elderly.name = data["name"]
        if "phone" in data and data["phone"]:
            elderly.phone = data["phone"]
            user.phone = data["phone"]
        if "email" in data:
            elderly.email = data["email"]
        if "home_address" in data:
            elderly.home_address = data["home_address"]
        if "health_info" in data:
            elderly.health_info = data["health_info"]
        
        # 更新密码
        if "password" in data and data["password"]:
            user.password_hash = self._hash_password(data["password"])
        
        await session.commit()
        return True, "更新成功"
    
    async def delete_user(
        self,
        elderly_id: int,
        session: AsyncSession
    ) -> Tuple[bool, str]:
        """删除用户"""
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.id == elderly_id)
        )
        elderly = result.scalar_one_or_none()
        
        if not elderly:
            return False, "用户不存在"
        
        # 获取关联的用户
        result = await session.execute(
            select(User).where(User.id == elderly.user_id)
        )
        user = result.scalar_one_or_none()
        
        # 删除老人信息（级联删除联系人、记事）
        await session.delete(elderly)
        
        # 删除用户
        if user:
            await session.delete(user)
        
        await session.commit()
        return True, "删除成功"
    
    # ========== 联系人管理 ==========
    async def create_contact(
        self,
        data: dict,
        session: AsyncSession
    ) -> Tuple[bool, str, Optional[Contact]]:
        """创建联系人"""
        # 检查老人是否存在
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.id == data["elderly_id"])
        )
        if not result.scalar_one_or_none():
            return False, "老人不存在", None
        
        # 字段名映射: relationship -> contact_relationship
        contact_data = data.copy()
        if "relationship" in contact_data:
            contact_data["contact_relationship"] = contact_data.pop("relationship")
        
        contact = Contact(**contact_data)
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        
        return True, "创建成功", contact
    
    async def update_contact(
        self,
        contact_id: int,
        data: dict,
        session: AsyncSession
    ) -> Tuple[bool, str]:
        """更新联系人"""
        result = await session.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            return False, "联系人不存在"
        
        # 字段名映射: relationship -> contact_relationship
        for key, value in data.items():
            if value is not None:
                attr_name = "contact_relationship" if key == "relationship" else key
                setattr(contact, attr_name, value)
        
        await session.commit()
        return True, "更新成功"
    
    async def delete_contact(
        self,
        contact_id: int,
        session: AsyncSession
    ) -> Tuple[bool, str]:
        """删除联系人"""
        result = await session.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            return False, "联系人不存在"
        
        await session.delete(contact)
        await session.commit()
        return True, "删除成功"
    
    # ========== 记事管理 ==========
    async def create_memo(
        self,
        data: dict,
        session: AsyncSession
    ) -> Tuple[bool, str, Optional[Memo]]:
        """创建记事"""
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.id == data["elderly_id"])
        )
        if not result.scalar_one_or_none():
            return False, "老人不存在", None
        
        memo = Memo(**data)
        session.add(memo)
        await session.commit()
        await session.refresh(memo)
        
        return True, "创建成功", memo
    
    async def update_memo(
        self,
        memo_id: int,
        data: dict,
        session: AsyncSession
    ) -> Tuple[bool, str]:
        """更新记事"""
        result = await session.execute(
            select(Memo).where(Memo.id == memo_id)
        )
        memo = result.scalar_one_or_none()
        
        if not memo:
            return False, "记事不存在"
        
        for key, value in data.items():
            if value is not None:
                setattr(memo, key, value)
        
        await session.commit()
        return True, "更新成功"
    
    async def delete_memo(
        self,
        memo_id: int,
        session: AsyncSession
    ) -> Tuple[bool, str]:
        """删除记事"""
        result = await session.execute(
            select(Memo).where(Memo.id == memo_id)
        )
        memo = result.scalar_one_or_none()
        
        if not memo:
            return False, "记事不存在"
        
        await session.delete(memo)
        await session.commit()
        return True, "删除成功"
    
    # ========== 对话历史 ==========
    async def get_conversations(
        self,
        session: AsyncSession,
        elderly_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ConversationHistory], int]:
        """获取对话历史"""
        query = select(ConversationHistory)
        
        if elderly_id:
            query = query.where(ConversationHistory.elderly_id == elderly_id)
        if start_date:
            query = query.where(ConversationHistory.created_at >= start_date)
        if end_date:
            query = query.where(ConversationHistory.created_at <= end_date)
        
        # 总数
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # 分页
        query = query.order_by(ConversationHistory.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        return result.scalars().all(), total
    
    # ========== 统计数据 ==========
    async def get_dashboard_stats(
        self,
        session: AsyncSession
    ) -> dict:
        """获取仪表盘统计数据"""
        # 总用户数
        user_count = await session.execute(select(func.count()).select_from(User))
        
        # 总联系人数
        contact_count = await session.execute(select(func.count()).select_from(Contact))
        
        # 总记事数
        memo_count = await session.execute(select(func.count()).select_from(Memo))
        
        # 总对话数
        conv_count = await session.execute(select(func.count()).select_from(ConversationHistory))
        
        # 今日对话数
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_conv = await session.execute(
            select(func.count())
            .where(ConversationHistory.created_at >= today)
        )
        
        # 紧急联系人数
        emergency_count = await session.execute(
            select(func.count()).where(Contact.is_emergency == True)
        )
        
        return {
            "total_users": user_count.scalar(),
            "total_contacts": contact_count.scalar(),
            "total_memos": memo_count.scalar(),
            "total_conversations": conv_count.scalar(),
            "today_conversations": today_conv.scalar(),
            "emergency_contacts": emergency_count.scalar()
        }


# 全局实例
admin_service = AdminService()
