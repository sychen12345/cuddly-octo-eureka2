"""
在线提示词编辑节点。

通过 GraphInput.prompt_overrides 覆盖默认提示词，让用户可以在 Coze 运行时
直接修改 OpenAI 文案、Grok 生图和最终审核提示词。
"""
from __future__ import annotations

from typing import Any, Dict

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
    from graphs.state import EditablePrompt, PromptNodeInput, PromptNodeOutput
except ImportError:
    from .state import EditablePrompt, PromptNodeInput, PromptNodeOutput


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


def _selected_title(state: Any) -> str:
    selected = _get(state, "selected_topic", {})
    return str(_dump(selected).get("title", "")).strip()


def prompt_node(
    state: PromptNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> PromptNodeOutput:
    """
    title: 在线提示词编辑
    desc: 输出可在线修改的提示词块，并应用用户 prompt_overrides
    integrations:
    """
    niche = str(_get(state, "niche", "")).strip()
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    brand_voice = str(_get(state, "brand_voice", "清醒、实操、少废话")).strip()
    selected_title = _selected_title(state)
    overrides = _get(state, "prompt_overrides", {}) or {}
    if not isinstance(overrides, dict):
        overrides = {}

    defaults = {
        "topic_selection": (
            f"围绕「{niche}」为「{audience}」选择小红书高浏览潜力选题。"
            "优先看真实浏览量、收藏、评论、搜索热词和用户指定选题。"
        ),
        "openai_text_description": (
            f"你是 GPT5.5 超高推理模式。请为选题「{selected_title}」生成小红书图文文字描述，"
            f"语气为「{brand_voice}」。输出：封面标题、每页脚本、正文、CTA、给生图模型的视觉 brief。"
            "不要承诺收益，不虚构数据。"
        ),
        "grok_expert_image_set": (
            f"你是 Grok Expert 生图模式。请基于 OpenAI 文案为「{selected_title}」生成一组 3:4 竖版卡通图。"
            "要求：套图风格统一、每张只表达一个信息、文字极少、角色和色板一致、适合小红书。"
        ),
        "final_review": (
            "检查最终图文包：选题是否有需求和热度依据，文案是否清楚，图片提示是否 3:4 卡通套图，"
            "是否泄露 API Key，是否有收益/涨粉/阅读量承诺。"
        ),
    }

    prompts = [
        EditablePrompt(
            key=key,
            title={
                "topic_selection": "选题判断提示词",
                "openai_text_description": "OpenAI GPT5.5 文案提示词",
                "grok_expert_image_set": "Grok Expert 套图提示词",
                "final_review": "最终审核提示词",
            }[key],
            target_model={
                "topic_selection": "规则评分",
                "openai_text_description": str(_get(state, "openai_text_model", "gpt-5.5")),
                "grok_expert_image_set": str(_get(state, "grok_image_model", "grok-expert")),
                "final_review": "workflow packager",
            }[key],
            default_prompt=default_prompt,
            final_prompt=str(overrides.get(key, default_prompt)).strip() or default_prompt,
        )
        for key, default_prompt in defaults.items()
    ]
    return PromptNodeOutput(editable_prompts=prompts)
