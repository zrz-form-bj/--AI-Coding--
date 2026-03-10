"""
数据库模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from config import config

Base = declarative_base()


class User(Base):
    """用户表 - 用于登录认证"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    phone = Column(String(20), unique=True, nullable=False, comment="手机号")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联老人信息（一对一）
    elderly_info = relationship("ElderlyInfo", back_populates="user", uselist=False, cascade="all, delete-orphan")


class ElderlyInfo(Base):
    """老人信息表"""
    __tablename__ = "elderly_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, comment="关联用户ID")
    name = Column(String(50), nullable=False, comment="姓名")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱地址（用于接收提醒）")
    home_address = Column(String(200), comment="家庭住址")
    home_lat = Column(String(20), comment="家庭住址纬度")
    home_lng = Column(String(20), comment="家庭住址经度")
    health_info = Column(Text, comment="健康信息")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联用户
    user = relationship("User", back_populates="elderly_info")
    # 关联联系人
    contacts = relationship("Contact", back_populates="elderly", cascade="all, delete-orphan")


class Contact(Base):
    """联系人表"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    elderly_id = Column(Integer, ForeignKey("elderly_info.id"), nullable=False, comment="关联的老人ID")
    name = Column(String(50), nullable=False, comment="姓名")
    contact_relationship = Column("relationship", String(20), comment="关系：女儿/儿子/配偶/朋友等")
    phone = Column(String(20), comment="电话")
    email = Column(String(100), comment="邮箱")
    address = Column(String(200), comment="住址")
    lat = Column(String(20), comment="住址纬度")
    lng = Column(String(20), comment="住址经度")
    is_emergency = Column(Boolean, default=False, comment="是否紧急联系人")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联老人
    elderly = relationship("ElderlyInfo", back_populates="contacts")


class Memo(Base):
    """记事表"""
    __tablename__ = "memos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    elderly_id = Column(Integer, ForeignKey("elderly_info.id"), nullable=False, comment="关联的老人ID")
    content = Column(Text, nullable=False, comment="记事内容")
    memo_type = Column(String(20), default="once", comment="记事类型: once(一次性) | periodic(周期性)")
    reminder_time = Column(DateTime, comment="提醒时间(一次性)或提醒时间点(周期性)")
    repeat_type = Column(String(20), comment="重复类型: daily(每天) | weekly(每周) | monthly(每月)")
    repeat_days = Column(String(50), comment="重复日期: 周几提醒，如'1,3,5'表示周一三五")
    end_date = Column(DateTime, comment="结束日期(周期性记事可选)")
    is_completed = Column(Boolean, default=False, comment="是否已完成/停用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")


class ConversationHistory(Base):
    """对话历史表"""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    elderly_id = Column(Integer, ForeignKey("elderly_info.id"), nullable=False, comment="关联的老人ID")
    role = Column(String(20), nullable=False, comment="角色: user/assistant")
    content = Column(Text, nullable=False, comment="对话内容")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")


class AdminUser(Base):
    """管理员表"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    name = Column(String(50), comment="管理员姓名")
    role = Column(String(20), default="admin", comment="角色: admin/super_admin")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_login = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")


# 异步数据库引擎
engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] 数据库初始化完成")


async def get_session():
    """获取数据库会话"""
    async with async_session() as session:
        yield session
