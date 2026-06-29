"""
问候生成节点
示例节点：根据用户名称生成问候消息
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import GreetingNodeInput, GreetingNodeOutput


def greeting_node(
    state: GreetingNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> GreetingNodeOutput:
    """
    title: 问候生成
    desc: 根据用户名称生成个性化的问候消息
    integrations: 
    """
    # 获取运行时上下文
    ctx = runtime.context
    
    # 生成问候消息
    user_name = state.user_name
    greeting = f"你好，{user_name}！欢迎使用工作流模板。"
    
    # 返回节点输出
    return GreetingNodeOutput(greeting_message=greeting)