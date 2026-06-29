"""
OpenAI GPT5.5 超高推理文案节点。

默认生成可审阅的请求计划与 dry-run 文案包，避免本地测试消耗真实 API；
在 Coze 线上可把 request.payload 接入真实 OpenAI 节点或代码节点。
"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    from langchain_core.runnables import RunnableConfig
except ImportError:  # pragma: no cover
    RunnableConfig = Dict[str, Any]  # type: ignore

try:
    from langgraph.runtime import Runtime
except ImportError:  # pragma: no cover
    Runtime = Any  # type: ignore

try:
    from coze_coding_utils.runtime_ctx.context import Context
except ImportError:  # pragma: no cover
    Context = Any  # type: ignore

try:
    from graphs.state import ModelRequest, OpenAITextNodeInput, OpenAITextNodeOutput, TextDescriptionPackage
except ImportError:
    from .state import ModelRequest, OpenAITextNodeInput, OpenAITextNodeOutput, TextDescriptionPackage


def _get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _dump(model: Any) -> Dict[str, Any]:
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return {}


def _prompt(state: Any, key: str) -> str:
    for prompt in _get(state, "editable_prompts", []) or []:
        data = _dump(prompt)
        if data.get("key") == key:
            return str(data.get("final_prompt", "")).strip()
    return ""


def _selected_topic(state: Any) -> Dict[str, Any]:
    return _dump(_get(state, "selected_topic", {}))


def _card_script(title: str, audience: str, count: int) -> List[str]:
    count = max(3, min(count or 6, 8))
    pages = [
        f"封面：{title}",
        f"痛点：{audience}最容易卡在第一步，不是不会努力，而是没看清需求。",
        "证据：先看评论区反复出现的问题，再看对标内容为什么被收藏。",
        "方法：找对标结构、挖评论需求、只做一个可验证的小选题。",
        "行动：今天先整理 5 条评论和 3 个对标标题，别急着做大项目。",
        "收口：收藏这套流程，下次直接用评论原话反推选题。",
        "复盘：发布后看收藏、评论追问和私信关键词，再决定下一篇。",
        "沉淀：把标题、需求来源、证据、差异化写回选题库。",
    ]
    return pages[:count]


def openai_text_node(
    state: OpenAITextNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> OpenAITextNodeOutput:
    """
    title: OpenAI GPT5.5 超高推理文案
    desc: 调用/规划 OpenAI 生成小红书文字描述和给 Grok 的视觉 brief
    integrations:
    """
    topic = _selected_topic(state)
    title = str(topic.get("title", "")).strip()
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    niche = str(_get(state, "niche", "")).strip()
    model = str(_get(state, "openai_text_model", "gpt-5.5")).strip() or "gpt-5.5"
    reasoning_mode = str(_get(state, "openai_reasoning_mode", "ultra_high")).strip() or "ultra_high"
    card_count = int(_get(state, "card_count", 6) or 6)
    prompt = _prompt(state, "openai_text_description")

    title_options = [
        title,
        f"{audience}做「{niche}」，先别急着发笔记",
        f"评论区问爆的「{niche}」问题，我拆成 3 步",
        f"想做「{niche}」，先存这份验证清单",
    ]
    card_script = _card_script(title, audience, card_count)
    post_description = (
        f"这组选题来自「{topic.get('demand_source', '用户需求')}」。"
        f"先用评论和对标内容确认需求，再让 OpenAI 生成文字描述，最后交给 Grok 生成 3:4 卡通套图。"
        "发布前补齐真实截图或案例，避免把猜测写成结论。"
    )
    image_brief = (
        f"为小红书选题「{title}」生成统一卡通套图。主角面向{audience}，"
        "画面要有清晰层级、少量中文标签、统一色板和 3:4 竖版构图。"
    )

    request = ModelRequest(
        provider="openai",
        model=model,
        mode=f"reasoning={reasoning_mode}",
        endpoint="https://api.openai.com/v1/responses",
        prompt_key="openai_text_description",
        payload={
            "model": model,
            "reasoning": {"effort": reasoning_mode},
            "input": prompt,
            "output_requirements": ["title_options", "card_script", "post_description", "image_brief"],
        },
        dry_run=not bool(_get(state, "execute_model_calls", False)),
        status="dry_run",
    )
    package = TextDescriptionPackage(
        provider="openai",
        model=model,
        reasoning_mode=reasoning_mode,
        request=request,
        title_options=title_options,
        post_description=post_description,
        card_script=card_script,
        image_brief=image_brief,
        status="dry_run",
    )
    return OpenAITextNodeOutput(openai_text_package=package)
