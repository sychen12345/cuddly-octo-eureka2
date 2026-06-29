"""
结果处理节点
示例节点：对问候消息进行进一步处理
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import ProcessNodeInput, ProcessNodeOutput


def process_node(
    state: ProcessNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ProcessNodeOutput:
    """
    title: 结果处理
    desc: 对问候消息进行格式化处理，生成最终结果
    integrations: 
    """
    # 获取运行时上下文
    ctx = runtime.context
    
    # 处理问候消息
    greeting = state.greeting_message
    processed_result = f"[工作流结果] {greeting}"
    
    # 返回节点输出
    return ProcessNodeOutput(processed_result=processed_result)