"""
Pydantic 数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ========== 用户认证 ==========
class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    email: Optional[str] = Field(None, description="邮箱地址")
    name: str = Field(..., min_length=2, max_length=50, description="老人姓名")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    phone: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    message: str
    user: Optional[UserResponse] = None
    elderly_id: Optional[int] = None


# ========== 管理员认证 ==========
class AdminLogin(BaseModel):
    """管理员登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class AdminResponse(BaseModel):
    """管理员信息响应"""
    id: int
    username: str
    name: Optional[str] = None
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLoginResponse(BaseModel):
    """管理员登录响应"""
    success: bool
    message: str
    admin: Optional[AdminResponse] = None


# ========== 老人信息 ==========
class ElderlyInfoBase(BaseModel):
    name: str = Field(..., description="姓名")
    phone: Optional[str] = Field(None, description="手机号")
    email: Optional[str] = Field(None, description="邮箱地址")
    home_address: Optional[str] = Field(None, description="家庭住址")
    home_lat: Optional[str] = Field(None, description="家庭住址纬度")
    home_lng: Optional[str] = Field(None, description="家庭住址经度")
    health_info: Optional[str] = Field(None, description="健康信息")


class ElderlyInfoCreate(ElderlyInfoBase):
    pass


class ElderlyInfoResponse(ElderlyInfoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 联系人 ==========
class ContactBase(BaseModel):
    name: str = Field(..., description="姓名")
    relationship: Optional[str] = Field(None, description="关系")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="住址")
    lat: Optional[str] = Field(None, description="纬度")
    lng: Optional[str] = Field(None, description="经度")
    is_emergency: bool = Field(False, description="是否紧急联系人")


class ContactCreate(ContactBase):
    elderly_id: int = Field(..., description="关联的老人ID")


class ContactResponse(ContactBase):
    id: int
    elderly_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 记事 ==========
class MemoBase(BaseModel):
    content: str = Field(..., description="记事内容")
    memo_type: str = Field("once", description="记事类型: once(一次性) | periodic(周期性)")
    reminder_time: Optional[datetime] = Field(None, description="提醒时间")
    repeat_type: Optional[str] = Field(None, description="重复类型: daily(每天) | weekly(每周) | monthly(每月)")
    repeat_days: Optional[str] = Field(None, description="重复日期，如'1,3,5'表示周一三五")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class MemoCreate(MemoBase):
    elderly_id: int = Field(..., description="关联的老人ID")


class MemoResponse(MemoBase):
    id: int
    elderly_id: int
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ========== API请求/响应 ==========
class AssistantRequest(BaseModel):
    """智能助手请求"""
    text: str = Field(..., description="语音转文字后的内容")
    elderly_id: int = Field(..., description="老人ID")
    lat: Optional[str] = Field(None, description="当前位置纬度")
    lng: Optional[str] = Field(None, description="当前位置经度")


class AssistantResponse(BaseModel):
    """智能助手响应"""
    success: bool = Field(..., description="是否成功")
    reply: str = Field(..., description="AI回复内容")
    action_taken: Optional[str] = Field(None, description="执行的动作")


class SOSRequest(BaseModel):
    """SOS紧急求助请求"""
    lat: str = Field(..., description="纬度")
    lng: str = Field(..., description="经度")
    elderly_id: int = Field(..., description="老人ID")


class SOSResponse(BaseModel):
    """SOS紧急求助响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    contacts_notified: int = Field(0, description="已通知的联系人数")
    location_text: Optional[str] = Field(None, description="位置文本")


class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[dict] = None


# ========== 管理员用户管理 ==========
class AdminUserCreate(BaseModel):
    """管理员创建用户请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    name: str = Field(..., min_length=2, max_length=50, description="老人姓名")
    home_address: Optional[str] = Field(None, description="家庭住址")
    health_info: Optional[str] = Field(None, description="健康信息")


class AdminUserUpdate(BaseModel):
    """管理员更新用户请求"""
    name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="手机号")
    home_address: Optional[str] = Field(None, description="家庭住址")
    health_info: Optional[str] = Field(None, description="健康信息")
    password: Optional[str] = Field(None, min_length=6, description="新密码（不填则不修改）")


class AdminUserListResponse(BaseModel):
    """用户列表响应"""
    id: int
    username: str
    phone: str
    name: str
    home_address: Optional[str] = None
    created_at: datetime
    contact_count: int = Field(0, description="联系人数量")
    memo_count: int = Field(0, description="记事数量")

    class Config:
        from_attributes = True


class UserImportResult(BaseModel):
    """批量导入结果"""
    success: bool
    message: str
    total: int
    success_count: int
    fail_count: int
    errors: List[str] = []


# ========== 管理员联系人管理 ==========
class AdminContactCreate(BaseModel):
    """管理员创建联系人"""
    elderly_id: int = Field(..., description="老人ID")
    name: str = Field(..., description="姓名")
    relationship: Optional[str] = Field(None, description="关系")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="住址")
    is_emergency: bool = Field(False, description="是否紧急联系人")


class AdminContactUpdate(BaseModel):
    """管理员更新联系人"""
    name: Optional[str] = Field(None, description="姓名")
    relationship: Optional[str] = Field(None, description="关系")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="住址")
    is_emergency: Optional[bool] = Field(None, description="是否紧急联系人")


# ========== 管理员记事管理 ==========
class AdminMemoCreate(BaseModel):
    """管理员创建记事"""
    elderly_id: int = Field(..., description="老人ID")
    content: str = Field(..., description="记事内容")
    memo_type: str = Field("once", description="记事类型: once(一次性) | periodic(周期性)")
    reminder_time: Optional[datetime] = Field(None, description="提醒时间")
    repeat_type: Optional[str] = Field(None, description="重复类型: daily(每天) | weekly(每周) | monthly(每月)")
    repeat_days: Optional[str] = Field(None, description="重复日期，如'1,3,5'表示周一三五")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class AdminMemoUpdate(BaseModel):
    """管理员更新记事"""
    content: Optional[str] = Field(None, description="记事内容")
    memo_type: Optional[str] = Field(None, description="记事类型")
    reminder_time: Optional[datetime] = Field(None, description="提醒时间")
    repeat_type: Optional[str] = Field(None, description="重复类型")
    repeat_days: Optional[str] = Field(None, description="重复日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    is_completed: Optional[bool] = Field(None, description="是否完成")


# ========== 统计数据 ==========
class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_users: int
    total_contacts: int
    total_memos: int
    total_conversations: int
    today_conversations: int
    emergency_contacts: int
