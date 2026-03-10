"""
LangChain 回调处理器 - 用于打印详细的执行日志
"""
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
import time


class LoggingCallbackHandler(BaseCallbackHandler):
    """日志回调处理器 - 打印Agent执行过程的详细日志"""
    
    def __init__(self):
        self.start_time = None
        
    def _print(self, message: str, emoji: str = "📝"):
        """打印带时间戳的日志"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {message}")
    
    # ========== Agent 生命周期 ==========
    
    def on_chain_start(
        self, 
        serialized: Dict[str, Any], 
        inputs: Dict[str, Any], 
        **kwargs: Any
    ) -> None:
        """Agent 开始执行"""
        self.start_time = time.time()
        self._print("=" * 60, "🚀")
        self._print("Agent 开始执行", "🚀")
        self._print(f"输入: {inputs.get('input', 'N/A')[:50]}...", "📥")
    
    def on_chain_end(
        self, 
        outputs: Dict[str, Any], 
        **kwargs: Any
    ) -> None:
        """Agent 执行结束"""
        duration = time.time() - self.start_time if self.start_time else 0
        output_text = outputs.get('output', str(outputs))[:100]
        self._print(f"Agent 执行完成 (耗时: {duration:.2f}s)", "✅")
        self._print(f"输出: {output_text}...", "📤")
        self._print("=" * 60, "🚀")
    
    def on_chain_error(
        self, 
        error: BaseException, 
        **kwargs: Any
    ) -> None:
        """Agent 执行出错"""
        self._print(f"Agent 执行出错: {str(error)}", "❌")
    
    # ========== LLM 调用 ==========
    
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """开始调用大模型"""
        model_name = serialized.get("name", "Unknown")
        prompt_preview = prompts[0][:80] if prompts else "N/A"
        self._print(f"[LLM] 开始调用模型: {model_name}", "🤖")
        self._print(f"[LLM] Prompt预览: {prompt_preview}...", "💬")
    
    def on_llm_end(
        self, 
        response: LLMResult, 
        **kwargs: Any
    ) -> None:
        """大模型调用完成"""
        generations = response.generations
        if generations and generations[0]:
            output = generations[0][0].text[:80]
            self._print(f"[LLM] 模型响应: {output}...", "💭")
        self._print("[LLM] 模型调用完成", "✅")
    
    def on_llm_error(
        self, 
        error: BaseException, 
        **kwargs: Any
    ) -> None:
        """大模型调用出错"""
        self._print(f"[LLM] 模型调用出错: {str(error)}", "❌")
    
    # ========== 工具调用 ==========
    
    def on_tool_start(
        self, 
        serialized: Optional[Dict[str, Any]], 
        input_str: str, 
        **kwargs: Any
    ) -> None:
        """开始调用工具"""
        tool_name = serialized.get("name", "Unknown") if serialized else "Unknown"
        self._print("-" * 40, "🔧")
        self._print(f"[Tool] 开始调用工具: {tool_name}", "🔧")
        self._print(f"[Tool] 输入参数: {input_str[:100]}...", "📋")
    
    def on_tool_end(
        self, 
        output: str, 
        **kwargs: Any
    ) -> None:
        """工具调用完成"""
        output_preview = output[:100] if output else "N/A"
        self._print(f"[Tool] 工具返回: {output_preview}...", "📦")
        self._print("[Tool] 工具调用完成", "✅")
        self._print("-" * 40, "🔧")
    
    def on_tool_error(
        self, 
        error: BaseException, 
        **kwargs: Any
    ) -> None:
        """工具调用出错"""
        self._print(f"[Tool] 工具调用出错: {str(error)}", "❌")
    
    # ========== 思考/观察 ==========
    
    def on_agent_action(
        self, 
        action: Any, 
        **kwargs: Any
    ) -> None:
        """Agent 采取行动"""
        tool = getattr(action, 'tool', 'Unknown')
        tool_input = getattr(action, 'tool_input', 'N/A')
        self._print(f"[Action] Agent决定调用工具: {tool}", "🎯")
        self._print(f"[Action] 工具输入: {str(tool_input)[:100]}...", "📋")
    
    def on_agent_finish(
        self, 
        finish: Any, 
        **kwargs: Any
    ) -> None:
        """Agent 完成"""
        output = getattr(finish, 'return_values', {}).get('output', 'N/A')
        self._print(f"[Finish] Agent完成，最终输出: {str(output)[:100]}...", "🏁")


class ToolTimingCallbackHandler(BaseCallbackHandler):
    """工具计时回调 - 统计每个工具的执行时间"""
    
    def __init__(self):
        self.tool_start_times = {}
        self.tool_stats = {}
    
    def _print(self, message: str, emoji: str = "⏱️"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {message}")
    
    def on_tool_start(
        self, 
        serialized: Optional[Dict[str, Any]], 
        input_str: str, 
        **kwargs: Any
    ) -> None:
        """记录工具开始时间"""
        import time
        tool_name = serialized.get("name", "Unknown") if serialized else "Unknown"
        self.tool_start_times[tool_name] = time.time()
        self._print(f"[Timer] 工具 {tool_name} 开始计时", "⏱️")
    
    def on_tool_end(
        self, 
        output: str, 
        **kwargs: Any
    ) -> None:
        """记录工具结束时间"""
        import time
        # 从 kwargs 中获取 tool_name
        tool_name = "Unknown"
        for key in ['name', 'tool_name']:
            if key in kwargs:
                tool_name = kwargs[key]
                break
        
        if tool_name in self.tool_start_times:
            duration = time.time() - self.tool_start_times[tool_name]
            self._print(f"[Timer] 工具 {tool_name} 执行耗时: {duration:.2f}s", "⏱️")
            
            # 统计
            if tool_name not in self.tool_stats:
                self.tool_stats[tool_name] = []
            self.tool_stats[tool_name].append(duration)
