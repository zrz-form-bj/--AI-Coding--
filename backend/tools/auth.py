"""
用户认证服务
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import secrets

from models import User, ElderlyInfo, UserRegister, UserResponse


class AuthService:
    """用户认证服务"""
    
    def _hash_password(self, password: str) -> str:
        """密码哈希（使用SHA256 + salt）"""
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
    
    async def register(
        self, 
        data: UserRegister, 
        session: AsyncSession
    ) -> Tuple[bool, str, Optional[User]]:
        """
        用户注册
        
        Returns:
            Tuple[成功标志, 消息, 用户对象]
        """
        # 检查用户名是否存在
        result = await session.execute(
            select(User).where(User.username == data.username)
        )
        if result.scalar_one_or_none():
            return False, "用户名已存在", None
        
        # 检查手机号是否存在
        result = await session.execute(
            select(User).where(User.phone == data.phone)
        )
        if result.scalar_one_or_none():
            return False, "手机号已注册", None
        
        # 创建用户
        user = User(
            username=data.username,
            password_hash=self._hash_password(data.password),
            phone=data.phone
        )
        session.add(user)
        await session.flush()  # 获取user.id
        
        # 创建老人信息
        elderly = ElderlyInfo(
            user_id=user.id,
            name=data.name,
            phone=data.phone,
            email=data.email
        )
        session.add(elderly)
        await session.commit()
        await session.refresh(user)
        
        return True, "注册成功", user
    
    async def login(
        self, 
        username: str, 
        password: str, 
        session: AsyncSession
    ) -> Tuple[bool, str, Optional[User], Optional[int]]:
        """
        用户登录
        
        Returns:
            Tuple[成功标志, 消息, 用户对象, 老人ID]
        """
        # 查找用户
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "用户名不存在", None, None
        
        # 验证密码
        if not self._verify_password(password, user.password_hash):
            return False, "密码错误", None, None
        
        # 获取老人信息
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.user_id == user.id)
        )
        elderly = result.scalar_one_or_none()
        elderly_id = elderly.id if elderly else None
        
        return True, "登录成功", user, elderly_id


# 全局实例
auth_service = AuthService()
