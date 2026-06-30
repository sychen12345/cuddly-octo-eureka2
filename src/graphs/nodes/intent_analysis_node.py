import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.llm import LLMClient
from graphs.state import IntentAnalysisInput, IntentAnalysisOutput


def intent_analysis_node(
    state: IntentAnalysisInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> IntentAnalysisOutput:
    """
    title: AI理解运营目标
    desc: 分析运营的自然语言需求，判断本次要做竞品调研、爆款选题、文案生成、图片制作、完整流程还是数据复盘
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 如果没有需求文本，默认完整流程
    if not state.user_request and not state.xiaohongshu_url:
        return IntentAnalysisOutput(
            intent="完整流程",
            intent_reason="无自然语言需求，默认执行完整内容生产流程",
            niche=state.niche,
            audience=state.audience,
        )

    # 读取 LLM 配置
    cfg_file = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", ""),
        config["metadata"]["llm_cfg"],
    )
    with open(cfg_file, "r", encoding="utf-8") as fd:
        _cfg: dict = json.load(fd)

    llm_config: dict = _cfg.get("config", {})
    sp: str = _cfg.get("sp", "")
    up_raw: str = _cfg.get("up", "")

    model: str = llm_config.get("model", "deepseek-v3-2-251201")

    # 渲染用户提示词
    up_tpl = Template(up_raw)
    user_prompt: str = up_tpl.render(
        user_request=state.user_request or "（无）",
        xiaohongshu_url=state.xiaohongshu_url or "（无）",
        niche=state.niche or "（未指定）",
        audience=state.audience or "（未指定）",
    )

    try:
        client = LLMClient(ctx=ctx)
        messages: list = [
            {"role": "system", "content": sp},
            {"role": "user", "content": user_prompt},
        ]
        resp = client.invoke(
            messages=messages,
            model=model,
            temperature=llm_config.get("temperature", 0.0),
            max_tokens=llm_config.get("max_completion_tokens", 500),
        )

        # 提取响应内容
        raw_content: str = ""
        if isinstance(resp, list) and len(resp) > 0:
            first_msg: dict = resp[0] if isinstance(resp[0], dict) else {}
            raw_content = str(first_msg.get("content", ""))
        elif isinstance(resp, str):
            raw_content = resp
        else:
            raw_content = str(resp)

        # 解析 JSON 输出
        content_clean: str = raw_content.strip()
        if content_clean.startswith("```"):
            lines: list = content_clean.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content_clean = "\n".join(lines).strip()

        result: dict = json.loads(content_clean)
        intent: str = str(result.get("intent", "完整流程"))
        intent_reason: str = str(result.get("reason", ""))
        extracted_niche: str = str(result.get("niche", state.niche or ""))
        extracted_audience: str = str(result.get("audience", state.audience or ""))

        return IntentAnalysisOutput(
            intent=intent,
            intent_reason=intent_reason,
            niche=extracted_niche,
            audience=extracted_audience,
        )

    except Exception:
        # 兜底：完整流程
        return IntentAnalysisOutput(
            intent="完整流程",
            intent_reason="意图识别调用失败，默认执行完整流程",
            niche=state.niche,
            audience=state.audience,
        )
