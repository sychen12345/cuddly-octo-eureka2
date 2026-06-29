"""
问候生成节点
示例节点：根据用户名称和风格生成问候消息
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
    desc: 根据用户名称和推荐的问候风格，生成个性化的问候消息
    integrations: 
    """
    ctx = runtime.context

    user_name = state.user_name
    style = state.greeting_style

    # 根据风格生成不同的问候语
    style_map = {
        "热情": f"🎉 嗨！{user_name}，欢迎欢迎！今天也要元气满满哦！",
        "简洁": f"你好，{user_name}，欢迎。",
        "正式": f"尊敬的{user_name}，您好！很荣幸为您服务。",
        "幽默": f"哟～{user_name}来了！今天又有什么有趣的事？😄",
    }
    greeting = style_map.get(style, f"你好，{user_name}！欢迎使用工作流模板。")

    return GreetingNodeOutput(greeting_message=greeting)