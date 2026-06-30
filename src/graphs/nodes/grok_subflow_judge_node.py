import os
import json
from typing import List, Dict, Any
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.llm import LLMClient
from graphs.state import GrokSubflowJudgeInput, GrokSubflowJudgeOutput


def grok_subflow_judge_node(
    state: GrokSubflowJudgeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> GrokSubflowJudgeOutput:
    """
    title: 子流程变更智能判断
    desc: 使用大模型智能判断运营对子流程的修改是"内容调整"还是"规则修改"，仅规则修改才同步回skill配置
    integrations: 大语言模型
    """
    ctx = runtime.context

    cfg_file = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", ""),
        config["metadata"]["llm_cfg"]
    )
    with open(cfg_file, "r") as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")

    # 构建变更摘要
    changed_items = state.subflows_changed_items
    if not changed_items:
        return GrokSubflowJudgeOutput(
            subflows_judge_decision="skip",
            subflows_judge_reason="无子流程变更，无需同步"
        )

    # 渲染用户提示词
    up_tpl = Template(up)
    user_prompt = up_tpl.render({
        "niche": state.niche,
        "audience": state.audience,
        "changed_items": json.dumps(changed_items, ensure_ascii=False, indent=2)
    })

    # 调用大模型
    client = LLMClient()
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    resp = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-lite-260215"),
        temperature=llm_config.get("temperature", 0.0),
        max_completion_tokens=llm_config.get("max_completion_tokens", 500),
        thinking=llm_config.get("thinking", "disabled")
    )

    # 解析响应 - invoke 返回 AIMessage, content 可能是 str 或 list
    raw_content = resp.content if hasattr(resp, "content") else str(resp)
    if isinstance(raw_content, list):
        # 多模态响应，取第一个文本元素
        text_parts: List[str] = [str(item) for item in raw_content if isinstance(item, str)]
        resp_text = " ".join(text_parts) if text_parts else str(raw_content)
    else:
        resp_text = str(raw_content)

    # 从响应中提取判断结果
    decision = "skip"
    reason = ""
    resp_lower = resp_text.lower().strip()

    # 尝试 JSON 解析
    try:
        parsed = json.loads(resp_text)
        if isinstance(parsed, dict):
            decision = str(parsed.get("decision", "skip")).lower()
            reason = str(parsed.get("reason", ""))
    except (json.JSONDecodeError, ValueError):
        if '"sync"' in resp_lower or "'sync'" in resp_lower:
            decision = "sync"
        elif '"skip"' in resp_lower or "'skip'" in resp_lower:
            decision = "skip"
        else:
            # 默认：有变更项就同步
            if changed_items:
                decision = "sync"
                reason = "检测到子流程规则变更，默认同步"

    if not reason:
        reason = resp_text[:200] if resp_text else "无详细理由"

    return GrokSubflowJudgeOutput(
        subflows_judge_decision=decision,
        subflows_judge_reason=reason
    )
