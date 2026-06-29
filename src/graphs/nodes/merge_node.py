"""
合并分析结果节点
Agent节点：调用大模型将 Grok 和 OpenAI 两个并行分支的分析结果智能合并
"""
import os
import json
from jinja2 import Template
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient

from graphs.state import MergeNodeInput, MergeNodeOutput


def merge_node(
    state: MergeNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> MergeNodeOutput:
    """
    title: 结果合并
    desc: 调用大模型将 Grok 和 OpenAI 两个模型的分析结果进行对比和智能合并
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 读取配置文件
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
    up = Template(up_template).render(
        grok_result=state.grok_result,
        openai_result=state.openai_result
    )

    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=up)
    ]
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-lite-260215"),
        temperature=float(llm_config.get("temperature", 0.5)),
        top_p=float(llm_config.get("top_p", 0.9)),
        max_completion_tokens=int(llm_config.get("max_completion_tokens", 300)),
        thinking=llm_config.get("thinking", "disabled")
    )

    # 安全提取文本
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

    return MergeNodeOutput(merged_analysis=content)