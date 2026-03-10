"""
LangChain Agent 配置 - LangChain 1.0+ 版本
"""
from typing import List, Dict, Any
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from tenacity import retry, stop_after_attempt, wait_exponential

from agent.llm import get_llm
from agent.callbacks import LoggingCallbackHandler, ToolTimingCallbackHandler
from config import config


# 系统提示词
SYSTEM_PROMPT = """你是一位专业的老年人智能助手，名字叫"小助"。你的主要任务是帮助老年人解决日常生活中的问题。

## 你的特点：
1. 说话简洁明了，语速适中，让老年人容易理解
2. 有耐心，理解老年人可能表达不够清晰
3. 在涉及安全问题时，优先考虑安全因素
4. 主动提供实用建议，但不过度干预

## 你可以帮助老人的事情：
1. 路线导航：查询去某个地点的路线（如"我要去女儿家怎么走"）
2. 天气查询：查询天气情况
3. 联系人查询：查询亲友的电话、地址等信息
4. 紧急求助：在紧急情况下帮助联系亲人
5. 生活咨询：回答日常生活问题
6. 记事提醒：帮助老人记录重要事项

## 重要规则：
1. 当用户询问路线时，使用百度地图工具查询
2. 当用户询问天气时，使用天气查询工具
3. 当用户需要联系某人时，先从数据库查询联系人信息
4. 如果需要发送短信或邮件，使用相应的工具
5. 回复要简洁，适合老年人理解

## 当前老人信息：
姓名：{elderly_name}
家庭住址：{home_address}

请根据用户的需求，选择合适的工具来帮助他们。回复时要友善、耐心、简洁。
"""


class ElderlyAssistantAgent:
    """老年人智能助手Agent - LangChain 1.0+ 实现"""
    
    def __init__(self, tools: List, elderly_info: Dict[str, Any] = None, history_messages: List[BaseMessage] = None):
        self.llm = get_llm()
        self.tools = tools
        self.elderly_info = elderly_info or {}
        self.chat_history = InMemoryChatMessageHistory()
        
        # 如果有历史消息，加载到内存
        if history_messages:
            for msg in history_messages:
                self.chat_history.add_message(msg)
            print(f"[Agent] 已加载 {len(history_messages)} 条历史消息到上下文")
        
        self.agent_executor = self._create_agent()
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """创建提示词模板 - LangChain 1.0+ 方式"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        return prompt
    
    def _create_agent(self):
        """创建Agent - LangChain 1.0+ 方式"""
        prompt = self._create_prompt()
        
        # 创建回调处理器
        callbacks = [
            LoggingCallbackHandler(),
            ToolTimingCallbackHandler()
        ]
        
        # 使用 create_tool_calling_agent (LangChain 1.0+ 推荐)
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 创建 AgentExecutor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=False,
            callbacks=callbacks  # 添加回调处理器
        )
        
        # 包装为带历史记录的 Runnable (LangChain 1.0+ 方式)
        agent_with_history = RunnableWithMessageHistory(
            agent_executor,
            get_session_history=lambda session_id: self.chat_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        return agent_with_history
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def invoke(self, user_input: str) -> str:
        """调用Agent处理用户输入"""
        try:
            result = await self.agent_executor.ainvoke(
                {
                    "input": user_input,
                    "elderly_name": self.elderly_info.get("name", "老人家"),
                    "home_address": self.elderly_info.get("home_address", "未设置"),
                },
                config={"configurable": {"session_id": "default"}}
            )
            return result.get("output", "抱歉，我没有理解您的意思，请再说一次。")
        except Exception as e:
            print(f"Agent调用失败: {e}")
            return f"处理请求时遇到问题：{str(e)}，请稍后再试。"
    
    def clear_history(self):
        """清空对话历史"""
        self.chat_history = InMemoryChatMessageHistory()


class SimpleAgent:
    """简化版Agent，用于快速响应 - LangChain 1.0+ 实现"""
    
    def __init__(self):
        self.llm = get_llm()
        self.chat_history = InMemoryChatMessageHistory()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def invoke(self, user_input: str, context: str = "") -> str:
        """简单调用LLM"""
        try:
            # 构建消息列表 (LangChain 1.0+ 方式)
            messages = [
                SystemMessage(content="你是老年人智能助手'小助'，请用简洁、易懂、友善的语言回答问题。回复控制在100字以内。"),
            ]
            
            # 添加历史消息
            for msg in self.chat_history.messages:
                messages.append(msg)
            
            # 添加当前用户输入
            user_content = f"{context}\n\n用户说：{user_input}" if context else user_input
            messages.append(HumanMessage(content=user_content))
            
            # 调用LLM (LangChain 1.0+ 异步方式)
            response = await self.llm.ainvoke(messages)
            
            # 保存到历史
            self.chat_history.add_message(HumanMessage(content=user_content))
            self.chat_history.add_message(AIMessage(content=response.content))
            
            return response.content
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return "抱歉，我现在有点忙，请稍后再试。"
    
    def clear_history(self):
        """清空对话历史"""
        self.chat_history = InMemoryChatMessageHistory()
