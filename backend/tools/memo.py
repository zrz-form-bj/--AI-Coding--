"""
记事提醒工具 - 支持一次性提醒和周期性提醒
"""
from datetime import datetime
from typing import Optional, List
from langchain.tools import tool
from sqlalchemy import select
from models.database import async_session, Memo


class MemoService:
    """记事服务"""
    
    async def add_memo(
        self,
        elderly_id: int,
        content: str,
        memo_type: str = "once",
        reminder_time: datetime = None,
        repeat_type: str = None,
        repeat_days: str = None,
        end_date: datetime = None
    ) -> dict:
        """添加记事
        
        Args:
            elderly_id: 老人ID
            content: 记事内容
            memo_type: 记事类型 (once=一次性, periodic=周期性)
            reminder_time: 提醒时间
            repeat_type: 重复类型 (daily=每天, weekly=每周, monthly=每月)
            repeat_days: 重复日期，周几提醒，如"1,3,5"表示周一三五
            end_date: 结束日期
        """
        async with async_session() as session:
            memo = Memo(
                elderly_id=elderly_id,
                content=content,
                memo_type=memo_type,
                reminder_time=reminder_time,
                repeat_type=repeat_type if memo_type == "periodic" else None,
                repeat_days=repeat_days if memo_type == "periodic" else None,
                end_date=end_date if memo_type == "periodic" else None
            )
            session.add(memo)
            await session.commit()
            return {
                "success": True,
                "id": memo.id,
                "message": "记事添加成功"
            }
    
    async def get_memos(
        self,
        elderly_id: int,
        include_completed: bool = False
    ) -> list:
        """获取记事列表"""
        async with async_session() as session:
            query = select(Memo).where(Memo.elderly_id == elderly_id)
            if not include_completed:
                query = query.where(Memo.is_completed == False)
            query = query.order_by(Memo.created_at.desc())
            
            result = await session.execute(query)
            memos = result.scalars().all()
            
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "memo_type": m.memo_type or "once",
                    "reminder_time": m.reminder_time,
                    "repeat_type": m.repeat_type,
                    "repeat_days": m.repeat_days,
                    "is_completed": m.is_completed,
                    "created_at": m.created_at
                }
                for m in memos
            ]
    
    async def complete_memo(self, memo_id: int) -> dict:
        """完成记事"""
        async with async_session() as session:
            result = await session.execute(
                select(Memo).where(Memo.id == memo_id)
            )
            memo = result.scalar_one_or_none()
            if memo:
                memo.is_completed = True
                await session.commit()
                return {"success": True, "message": "记事已标记完成"}
            return {"success": False, "message": "记事不存在"}


# 创建服务实例
memo_service = MemoService()


# ========== LangChain Tools ==========

@tool
async def add_memo(
    content: str, 
    reminder_time: str = None,
    memo_type: str = "once",
    repeat_type: str = None,
    repeat_days: str = None,
    elderly_id: int = 1
) -> str:
    """
    添加记事工具。
    帮助老人记录重要事项，支持一次性提醒和周期性提醒。
    
    参数:
        content: 记事内容
        reminder_time: 提醒时间，格式如 "2024-01-15 10:00" 或 "10:00"（周期性记事）
        memo_type: 记事类型，"once"(一次性) 或 "periodic"(周期性)，默认"once"
        repeat_type: 重复类型，仅周期性记事需要，"daily"(每天)、"weekly"(每周)、"monthly"(每月)
        repeat_days: 重复日期，仅周重复需要，如"1,3,5"表示周一三五（0=周日,1=周一...6=周六）
        elderly_id: 老人ID（默认1）
    
    返回:
        添加结果
    """
    # 解析提醒时间
    parsed_time = None
    if reminder_time:
        try:
            if len(reminder_time) <= 5:  # 只有时间 "10:00"
                parsed_time = datetime.strptime(f"2000-01-01 {reminder_time}", "%Y-%m-%d %H:%M")
            else:  # 完整日期时间
                parsed_time = datetime.strptime(reminder_time, "%Y-%m-%d %H:%M")
        except:
            pass
    
    result = await memo_service.add_memo(
        elderly_id=elderly_id,
        content=content,
        memo_type=memo_type,
        reminder_time=parsed_time,
        repeat_type=repeat_type,
        repeat_days=repeat_days
    )
    
    if result["success"]:
        if memo_type == "periodic":
            type_desc = {"daily": "每天", "weekly": "每周", "monthly": "每月"}.get(repeat_type, "")
            return f"好的，已为您设置周期性提醒：{content}，{type_desc}会通过邮件提醒您。"
        return f"好的，已为您记录：{content}"
    return "抱歉，记事添加失败，请稍后再试。"


@tool
async def list_memos(elderly_id: int = 1) -> str:
    """
    查看记事工具。
    查看老人记录的所有事项。
    
    参数:
        elderly_id: 老人ID（默认1）
    
    返回:
        记事列表
    """
    memos = await memo_service.get_memos(elderly_id)
    
    if not memos:
        return "您还没有记录任何事项。"
    
    weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
    result = f"您共有 {len(memos)} 条记事：\n\n"
    
    for i, m in enumerate(memos, 1):
        status = "✅" if m['is_completed'] else "⬜"
        memo_type = m.get('memo_type', 'once')
        
        if memo_type == 'periodic':
            type_desc = {"daily": "每天", "weekly": "每周", "monthly": "每月"}.get(m.get('repeat_type'), "")
            result += f"{i}. {status} 🔄 {m['content']}（{type_desc}提醒）\n"
        else:
            result += f"{i}. {status} 📍 {m['content']}\n"
            if m['reminder_time']:
                result += f"   提醒时间：{m['reminder_time'].strftime('%Y-%m-%d %H:%M')}\n"
    
    return result


@tool
async def query_time() -> str:
    """
    查询时间工具。
    查询当前时间和日期。
    
    返回:
        当前时间信息
    """
    now = datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[now.weekday()]
    
    return f"现在是 {now.strftime('%Y年%m月%d日')} {weekday} {now.strftime('%H点%M分')}"
