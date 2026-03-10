"""
对话历史存储服务
使用数据库持久化存储，支持按时间范围读取
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from models import ConversationHistory


class ConversationHistoryService:
    """对话历史存储服务"""
    
    # 最大加载消息数量（防止上下文过长）
    MAX_HISTORY_MESSAGES = 20
    
    async def save_message(
        self,
        elderly_id: int,
        role: str,
        content: str,
        session: AsyncSession
    ) -> ConversationHistory:
        """
        保存一条消息到数据库
        
        Args:
            elderly_id: 老人ID
            role: 角色 (user/assistant)
            content: 消息内容
            session: 数据库会话
        """
        history = ConversationHistory(
            elderly_id=elderly_id,
            role=role,
            content=content
        )
        session.add(history)
        await session.commit()
        await session.refresh(history)
        print(f"[History] 已保存消息: [{role}] {content[:50]}...")
        return history
    
    async def get_recent_history(
        self,
        elderly_id: int,
        days: int,
        session: AsyncSession,
        max_messages: int = None
    ) -> List[BaseMessage]:
        """
        获取近N天的对话历史，转换为LangChain消息格式
        
        Args:
            elderly_id: 老人ID
            days: 天数
            session: 数据库会话
            max_messages: 最大消息数量（默认使用MAX_HISTORY_MESSAGES）
        
        Returns:
            LangChain消息列表
        """
        if max_messages is None:
            max_messages = self.MAX_HISTORY_MESSAGES
        
        # 计算时间范围
        start_time = datetime.now() - timedelta(days=days)
        
        # 查询数据库
        result = await session.execute(
            select(ConversationHistory)
            .where(
                and_(
                    ConversationHistory.elderly_id == elderly_id,
                    ConversationHistory.created_at >= start_time
                )
            )
            .order_by(ConversationHistory.created_at.desc())
            .limit(max_messages)
        )
        records = result.scalars().all()
        
        # 反转顺序（从旧到新）
        records = list(reversed(records))
        
        # 转换为LangChain消息格式
        messages: List[BaseMessage] = []
        for record in records:
            if record.role == "user":
                messages.append(HumanMessage(content=record.content))
            else:
                messages.append(AIMessage(content=record.content))
        
        print(f"[History] 已加载 {len(messages)} 条近{days}天的对话历史")
        return messages
    
    async def get_history_count(
        self,
        elderly_id: int,
        days: int,
        session: AsyncSession
    ) -> int:
        """
        获取近N天的对话历史数量
        """
        start_time = datetime.now() - timedelta(days=days)
        result = await session.execute(
            select(ConversationHistory)
            .where(
                and_(
                    ConversationHistory.elderly_id == elderly_id,
                    ConversationHistory.created_at >= start_time
                )
            )
        )
        return len(result.scalars().all())
    
    async def clear_history(
        self,
        elderly_id: int,
        session: AsyncSession
    ):
        """
        清空指定用户的所有对话历史
        """
        result = await session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.elderly_id == elderly_id)
        )
        records = result.scalars().all()
        for record in records:
            await session.delete(record)
        await session.commit()
        print(f"[History] 已清空用户 {elderly_id} 的对话历史")


# 全局实例
conversation_history_service = ConversationHistoryService()
