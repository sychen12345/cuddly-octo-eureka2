"""
结果审核打包节点。

把选题、OpenAI 文案、Grok 套图计划和审核规则打包成最终小红书交付物。
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
    from graphs.state import CardPackage, CardPage, FinalizeNodeInput, FinalizeNodeOutput
except ImportError:
    from .state import CardPackage, CardPage, FinalizeNodeInput, FinalizeNodeOutput


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


def _clean_hashtag(text: str) -> str:
    cleaned = "".join(ch for ch in text if ch.isalnum() or ch in ["_", "-"])
    return f"#{cleaned}" if cleaned else "#小红书运营"


def _image_by_page(state: Any) -> Dict[int, Dict[str, Any]]:
    image_set = _dump(_get(state, "grok_image_set", {}))
    out: Dict[int, Dict[str, Any]] = {}
    for item in image_set.get("images", []) or []:
        data = _dump(item)
        out[int(data.get("page", 0) or 0)] = data
    return out


def _cards(state: Any) -> List[CardPage]:
    text_package = _dump(_get(state, "openai_text_package", {}))
    by_page = _image_by_page(state)
    scripts = list(text_package.get("card_script", []) or [])
    cards: List[CardPage] = []
    for index, script in enumerate(scripts, start=1):
        if "：" in script:
            headline, body = script.split("：", 1)
        else:
            headline, body = f"第 {index} 页", script
        image_prompt = str(by_page.get(index, {}).get("prompt", "")).strip()
        cards.append(
            CardPage(
                page=index,
                headline=headline,
                body=body,
                visual_prompt=image_prompt,
            )
        )
    return cards


def finalize_node(
    state: FinalizeNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> FinalizeNodeOutput:
    """
    title: 结果审核打包
    desc: 汇总 OpenAI 文案、Grok 套图和审核清单，形成最终输出
    integrations:
    """
    niche = str(_get(state, "niche", "")).strip()
    selected_topic = _dump(_get(state, "selected_topic", {}))
    text_package = _dump(_get(state, "openai_text_package", {}))
    image_set = _dump(_get(state, "grok_image_set", {}))
    prompts = _get(state, "editable_prompts", []) or []
    workflow_steps = _get(state, "workflow_steps", []) or []
    cards = _cards(state)

    topic_title = str(selected_topic.get("title", "")).strip()
    card_package = CardPackage(
        topic_title=topic_title,
        cover_options=list(text_package.get("title_options", []) or []),
        cards=cards,
        caption=str(text_package.get("post_description", "")).strip(),
        hashtags=[
            _clean_hashtag(niche),
            "#小红书选题",
            "#高浏览选题",
            "#卡通图文",
            "#AI工作流",
            "#Grok生图",
        ],
        cta="把你的参考图、对标标题和评论原话继续补进来，我会按同一套规则迭代下一版套图。",
        review_checklist=[
            "API Key 没有出现在任何输出字段",
            "选题有用户指定或浏览量/热词/评论依据",
            "OpenAI 文案没有承诺收益、涨粉、阅读量",
            "Grok 图片提示词明确 3:4 竖版和卡通风格",
            "套图保持角色、色板、线条、版式一致",
            "每页只表达一个核心信息，文字不压画面",
            "提示词可通过 prompt_overrides 在线修改",
        ],
    )

    workflow_summary = (
        f"已完成完整工作流：{len(workflow_steps)} 个流程节点、"
        f"{len(prompts)} 个可在线修改提示词、"
        f"{len(_get(state, 'topic_bank', []) or [])} 个选题、"
        f"{len(cards)} 页 OpenAI 文案卡片、"
        f"{len(image_set.get('images', []) or [])} 张 Grok Expert 3:4 卡通套图计划。"
    )
    next_commands = [
        "在 prompt_overrides.openai_text_description 中改写文案提示词后重跑。",
        "在 prompt_overrides.grok_expert_image_set 中加入你的参考图风格要求后重跑。",
        "补充 topic_research_notes 的浏览量、收藏、评论数据，重新选择高浏览选题。",
        "填写 user_selected_topic，强制使用你指定的小红书选题。",
    ]
    return FinalizeNodeOutput(
        card_package=card_package,
        workflow_summary=workflow_summary,
        next_commands=next_commands,
    )
