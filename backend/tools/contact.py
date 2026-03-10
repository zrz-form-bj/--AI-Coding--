"""
联系人查询工具 - LangChain 1.0+
从数据库查询联系人的电话、地址等信息
"""
from typing import Optional, List
from langchain_core.tools import tool
from sqlalchemy import select
from models.database import async_session, Contact, ElderlyInfo


class ContactService:
    """联系人服务"""
    
    async def get_contacts(self, elderly_id: int) -> List[dict]:
        """获取老人的所有联系人"""
        async with async_session() as session:
            result = await session.execute(
                select(Contact).where(Contact.elderly_id == elderly_id)
            )
            contacts = result.scalars().all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "relationship": c.contact_relationship,
                    "phone": c.phone,
                    "email": c.email,
                    "address": c.address,
                    "lat": c.lat,
                    "lng": c.lng,
                    "is_emergency": c.is_emergency
                }
                for c in contacts
            ]
    
    async def get_emergency_contacts(self, elderly_id: int) -> List[dict]:
        """获取紧急联系人"""
        async with async_session() as session:
            result = await session.execute(
                select(Contact).where(
                    Contact.elderly_id == elderly_id,
                    Contact.is_emergency == True
                )
            )
            contacts = result.scalars().all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "relationship": c.contact_relationship,
                    "phone": c.phone,
                    "email": c.email,
                    "address": c.address
                }
                for c in contacts
            ]
    
    async def get_contact_by_name(self, elderly_id: int, name: str) -> Optional[dict]:
        """根据姓名查询联系人"""
        async with async_session() as session:
            result = await session.execute(
                select(Contact).where(
                    Contact.elderly_id == elderly_id,
                    Contact.name.contains(name)
                )
            )
            contact = result.scalar_one_or_none()
            if contact:
                return {
                    "id": contact.id,
                    "name": contact.name,
                    "relationship": contact.contact_relationship,
                    "phone": contact.phone,
                    "email": contact.email,
                    "address": contact.address,
                    "lat": contact.lat,
                    "lng": contact.lng
                }
            return None
    
    async def get_contact_by_relationship(
        self, elderly_id: int, relationship: str
    ) -> Optional[dict]:
        """根据关系查询联系人（如：女儿、儿子）"""
        async with async_session() as session:
            result = await session.execute(
                select(Contact).where(
                    Contact.elderly_id == elderly_id,
                    Contact.contact_relationship.contains(relationship)
                )
            )
            contact = result.scalar_one_or_none()
            if contact:
                return {
                    "id": contact.id,
                    "name": contact.name,
                    "relationship": contact.contact_relationship,
                    "phone": contact.phone,
                    "email": contact.email,
                    "address": contact.address,
                    "lat": contact.lat,
                    "lng": contact.lng
                }
            return None
    
    async def get_elderly_info(self, elderly_id: int) -> Optional[dict]:
        """获取老人信息"""
        async with async_session() as session:
            result = await session.execute(
                select(ElderlyInfo).where(ElderlyInfo.id == elderly_id)
            )
            elderly = result.scalar_one_or_none()
            if elderly:
                return {
                    "id": elderly.id,
                    "name": elderly.name,
                    "phone": elderly.phone,
                    "home_address": elderly.home_address,
                    "home_lat": elderly.home_lat,
                    "home_lng": elderly.home_lng,
                    "health_info": elderly.health_info
                }
            return None


# 创建服务实例
contact_service = ContactService()


# ========== LangChain Tools ==========

@tool
async def query_contact_phone(
    name: str,
    elderly_id: int = 1
) -> str:
    """
    查询联系人电话工具。
    根据联系人姓名或关系查询电话号码。
    
    参数:
        name: 联系人姓名或关系，如"女儿"、"儿子"、"张三"
        elderly_id: 老人ID（默认1）
    
    返回:
        联系人电话信息
    """
    # 先尝试按关系查询
    contact = await contact_service.get_contact_by_relationship(elderly_id, name)
    
    # 如果没找到，再按姓名查询
    if not contact:
        contact = await contact_service.get_contact_by_name(elderly_id, name)
    
    if contact:
        result = f"找到联系人信息：\n"
        result += f"姓名：{contact['name']}\n"
        result += f"关系：{contact['relationship']}\n"
        result += f"电话：{contact['phone']}"
        if contact['address']:
            result += f"\n地址：{contact['address']}"
        return result
    
    return f"抱歉，没有找到关于「{name}」的联系人信息。"


@tool
async def query_contact_address(
    name: str,
    elderly_id: int = 1
) -> str:
    """
    查询联系人地址工具。
    根据联系人姓名或关系查询地址。
    
    参数:
        name: 联系人姓名或关系
        elderly_id: 老人ID（默认1）
    
    返回:
        联系人地址信息
    """
    # 先尝试按关系查询
    contact = await contact_service.get_contact_by_relationship(elderly_id, name)
    
    # 如果没找到，再按姓名查询
    if not contact:
        contact = await contact_service.get_contact_by_name(elderly_id, name)
    
    if contact:
        result = f"找到「{contact['name']}」的地址信息：\n"
        result += f"地址：{contact['address']}"
        if contact['lat'] and contact['lng']:
            result += f"\n坐标：纬度{contact['lat']}，经度{contact['lng']}"
        return result
    
    return f"抱歉，没有找到关于「{name}」的地址信息。"


@tool
async def list_all_contacts(elderly_id: int = 1) -> str:
    """
    列出所有联系人工具。
    列出老人保存的所有联系人信息。
    
    参数:
        elderly_id: 老人ID（默认1）
    
    返回:
        所有联系人列表
    """
    contacts = await contact_service.get_contacts(elderly_id)
    
    if not contacts:
        return "您还没有保存任何联系人信息。"
    
    result = f"您共有 {len(contacts)} 位联系人：\n\n"
    for i, c in enumerate(contacts, 1):
        result += f"{i}. {c['name']}（{c['relationship']}）\n"
        result += f"   电话：{c['phone']}\n"
        if c['address']:
            result += f"   地址：{c['address']}\n"
        if c['is_emergency']:
            result += "   ⭐ 紧急联系人\n"
        result += "\n"
    
    return result


@tool
async def query_home_address(elderly_id: int = 1) -> str:
    """
    查询家庭住址工具。
    查询老人的家庭住址信息。
    
    参数:
        elderly_id: 老人ID（默认1）
    
    返回:
        家庭住址信息
    """
    elderly = await contact_service.get_elderly_info(elderly_id)
    
    if elderly and elderly.get('home_address'):
        result = f"您的家庭住址是：{elderly['home_address']}"
        if elderly.get('home_lat') and elderly.get('home_lng'):
            result += f"\n坐标：纬度{elderly['home_lat']}，经度{elderly['home_lng']}"
        return result
    
    return "您还没有设置家庭住址。"


@tool
async def make_call(phone: str) -> str:
    """
    拨打电话工具。
    返回拨打电话的链接（需要用户点击）。
    
    参数:
        phone: 电话号码
    
    返回:
        拨打电话的指令
    """
    return f"请点击拨打按钮：tel:{phone}"
