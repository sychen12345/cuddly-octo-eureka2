"""
模型选取节点
Agent节点：调用大模型根据用户名称推荐问候风格
"""
import os
import json
from jinja2 import Template
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient

from graphs.state import ModelSelectNodeInput, ModelSelectNodeOutput


def model_select_node(
    state: ModelSelectNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ModelSelectNodeOutput:
    """
    title: 模型选取
    desc: 根据用户名称，由大模型推荐合适的问候风格（热情/简洁/正式/幽默）
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 读取大模型配置文件
    cfg_path = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH"),
        config['metadata']['llm_cfg']
    )
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)

    llm_config: dict = cfg.get("config", {})
    sp: str = cfg.get("sp", "")
    up_template: str = cfg.get("up", "")

    # 渲染用户提示词
    up = Template(up_template).render(user_name=state.user_name)

    # 初始化大模型客户端
    client = LLMClient(ctx=ctx)

    # 组装消息
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=up)
    ]

    # 调用大模型
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-lite-260215"),
        temperature=float(llm_config.get("temperature", 0.7)),
        top_p=float(llm_config.get("top_p", 0.9)),
        max_completion_tokens=int(llm_config.get("max_completion_tokens", 200)),
        thinking=llm_config.get("thinking", "disabled")
    )

    # 安全提取文本内容
    content: str = ""
    if isinstance(response.content, str):
        content = response.content.strip()
    elif isinstance(response.content, list):
        parts: list[str] = []
        for item in response.content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                text_val = item.get("text", "")
                if isinstance(text_val, str):
                    parts.append(text_val)
        content = "".join(parts).strip()

    # 兜底：如果模型返回不是预期的风格词，默认使用"热情"
    valid_styles = {"热情", "简洁", "正式", "幽默"}
    if content not in valid_styles:
        content = "热情"

    return ModelSelectNodeOutput(greeting_style=content)