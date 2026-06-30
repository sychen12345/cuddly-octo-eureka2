"""
节点5: 在线提示词编辑 (prompt_node)
─────────────────────────────────────
输入: niche, audience, brand_voice, selected_topic, prompt_overrides,
      skill_subflows, openai_text_model, grok_image_model
输出: editable_prompts
"""
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    PromptNodeInput,
    PromptNodeOutput,
    EditablePrompt,
    SkillSubflow,
    TopicRecord,
)


# ── 通用辅助 ──────────────────────────────────────────────
def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _dump(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_dump(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _dump(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: _dump(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


# ── 提示词生成 ────────────────────────────────────────────
def _build_prompts(
    niche: str,
    audience: str,
    brand_voice: str,
    topic: TopicRecord,
    overrides: Dict[str, str],
    subflows: List[SkillSubflow],
    openai_model: str,
    grok_model: str,
) -> List[EditablePrompt]:
    prompts: List[EditablePrompt] = []

    # OpenAI 文案提示词
    default_openai: str = (
        f"你是小红书内容创作专家，擅长按「{brand_voice}」语气写作。\n"
        f"领域：{niche}\n目标人群：{audience}\n"
        f"选题：{topic.title}\n"
        f"请生成图文卡片的标题选项、正文、每页脚本和视觉说明。"
    )
    prompts.append(EditablePrompt(
        key="openai_text_prompt",
        title="OpenAI 文案提示词",
        target_model=openai_model,
        default_prompt=default_openai,
        final_prompt=overrides.get("openai_text_prompt", default_openai),
    ))

    # Grok 生图提示词
    default_grok: str = (
        f"生成小红书 3:4 卡通风格图文卡片套图。\n"
        f"选题：{topic.title}\n"
        f"风格：卡通、短句、层级清楚、留白充足。\n"
        f"每页一个核心信息，配色统一。"
    )
    prompts.append(EditablePrompt(
        key="grok_image_prompt",
        title="Grok 生图提示词",
        target_model=grok_model,
        default_prompt=default_grok,
        final_prompt=overrides.get("grok_image_prompt", default_grok),
    ))

    # 从子流程步骤中提取提示词
    for sf in subflows:
        for step in sf.steps:
            if step.prompt_key and step.prompt_key not in {p.key for p in prompts}:
                prompts.append(EditablePrompt(
                    key=step.prompt_key,
                    title=step.title,
                    target_model=step.model_or_tool,
                    default_prompt=step.default_prompt,
                    final_prompt=overrides.get(step.prompt_key, step.final_prompt),
                ))

    return prompts


# ── 节点函数 ──────────────────────────────────────────────
def prompt_node(
    state: PromptNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> PromptNodeOutput:
    """
    title: 在线提示词编辑
    desc: 汇总所有可编辑提示词，应用用户覆盖后生成最终提示词列表
    integrations:
    """
    niche: str = _get(state, "niche", "")
    audience: str = _get(state, "audience", "小红书新手用户")
    brand_voice: str = _get(state, "brand_voice", "清醒、实操、少废话")
    selected_topic: TopicRecord = _get(state, "selected_topic", TopicRecord(title="", audience="", hook="", demand_source="", differentiation=""))
    prompt_overrides: Dict[str, str] = _get(state, "prompt_overrides", {})
    skill_subflows: List[SkillSubflow] = _get(state, "skill_subflows", [])
    openai_model: str = _get(state, "openai_text_model", "gpt-5.5")
    grok_model: str = _get(state, "grok_image_model", "grok-imagine-image-quality")

    editable_prompts: List[EditablePrompt] = _build_prompts(
        niche, audience, brand_voice, selected_topic,
        prompt_overrides, skill_subflows,
        openai_model, grok_model,
    )

    return PromptNodeOutput(editable_prompts=editable_prompts)
