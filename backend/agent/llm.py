"""
LLM配置 - 通义千问 (LangChain 1.0+ 兼容)
"""
from langchain_openai import ChatOpenAI
from config import config


def get_llm() -> ChatOpenAI:
    """
    获取通义千问LLM实例
    
    通义千问通过OpenAI兼容接口调用
    LangChain 1.0+ 使用 langchain_openai 包
    """
    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        openai_api_key=config.DASHSCOPE_API_KEY,
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    return llm
