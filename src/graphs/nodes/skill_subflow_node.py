"""
节点4: OpenAI/Grok Skill 子流程 (skill_subflow_node)
────────────────────────────────────────────────────
输入: selected_topic, audience, brand_voice, openai/grok model/mode,
      image_aspect_ratio, image_style, skill_flow_overrides, prompt_overrides
输出: skill_subflows
"""
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    SkillSubflowNodeInput,
    SkillSubflowNodeOutput,
    SkillSubflow,
    SkillSubflowStep,
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


# ── 子流程构建 ────────────────────────────────────────────
def _build_openai_subflow(
    topic: TopicRecord,
    audience: str,
    brand_voice: str,
    model: str,
    reasoning_mode: str,
    aspect_ratio: str,
    style: str,
    overrides: Dict[str, Any],
    prompt_overrides: Dict[str, str],
) -> SkillSubflow:
    steps: List[SkillSubflowStep] = [
        SkillSubflowStep(
            step_key="openai_analyze",
            title="分析选题与需求",
            node_type="model",
            model_or_tool=model,
            prompt_key="openai_text_prompt",
            default_prompt=f"分析选题「{topic.title}」的核心需求，生成图文卡片文案。",
            final_prompt=prompt_overrides.get("openai_text_prompt", f"分析选题「{topic.title}」的核心需求，生成图文卡片文案。"),
            input_keys=["selected_topic", "audience", "niche"],
            output_keys=["title_options", "card_script", "image_brief"],
            notes="可修改提示词来调整文案风格",
        ),
        SkillSubflowStep(
            step_key="openai_generate",
            title="生成正文与卡片脚本",
            node_type="prompt",
            model_or_tool=model,
            prompt_key="openai_generate_prompt",
            default_prompt=f"根据分析结果，按「{brand_voice}」语气生成{audience}的图文卡片正文和每页脚本。",
            final_prompt=prompt_overrides.get("openai_generate_prompt", f"根据分析结果，按「{brand_voice}」语气生成{audience}的图文卡片正文和每页脚本。"),
            input_keys=["openai_text_prompt_output"],
            output_keys=["post_description", "card_script"],
            notes="可调整每页卡片的内容密度",
        ),
    ]
    return SkillSubflow(
        skill_key="openai_text_skill",
        title="OpenAI GPT5.5 文案子流程",
        provider="openai",
        model=model,
        mode=reasoning_mode,
        endpoint="https://api.openai.com/v1/chat/completions",
        description="生成小红书图文卡片文案：标题、正文、每页脚本、视觉说明",
        steps=steps,
    )


def _build_grok_subflow(
    topic: TopicRecord,
    model: str,
    mode: str,
    aspect_ratio: str,
    style: str,
    overrides: Dict[str, Any],
    prompt_overrides: Dict[str, str],
) -> SkillSubflow:
    steps: List[SkillSubflowStep] = [
        SkillSubflowStep(
            step_key="grok_plan",
            title="规划套图视觉方向",
            node_type="rule",
            model_or_tool=model,
            prompt_key="grok_plan_prompt",
            default_prompt=f"为选题「{topic.title}」规划 {aspect_ratio} {style} 风格套图。",
            final_prompt=prompt_overrides.get("grok_plan_prompt", f"为选题「{topic.title}」规划 {aspect_ratio} {style} 风格套图。"),
            input_keys=["image_style_rules", "openai_text_package"],
            output_keys=["grok_image_plan"],
            notes="可修改视觉方向",
        ),
        SkillSubflowStep(
            step_key="grok_generate",
            title="生成套图",
            node_type="model",
            model_or_tool=model,
            prompt_key="grok_image_prompt",
            default_prompt=f"按规划生成{aspect_ratio} {style}风格的小红书图文卡片。",
            final_prompt=prompt_overrides.get("grok_image_prompt", f"按规划生成{aspect_ratio} {style}风格的小红书图文卡片。"),
            input_keys=["grok_image_plan"],
            output_keys=["grok_image_set"],
            notes="可修改生图提示词",
        ),
    ]
    return SkillSubflow(
        skill_key="grok_image_skill",
        title="Grok Expert 套图子流程",
        provider="grok",
        model=model,
        mode=mode,
        endpoint="https://api.x.ai/v1/images/generations",
        description=f"生成 {aspect_ratio} {style} 风格的小红书图文套图",
        steps=steps,
    )


# ── 节点函数 ──────────────────────────────────────────────
def skill_subflow_node(
    state: SkillSubflowNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SkillSubflowNodeOutput:
    """
    title: OpenAI/Grok Skill 子流程
    desc: 构建可视化可编辑的 OpenAI 文案和 Grok 套图子流程
    integrations:
    """
    selected_topic: TopicRecord = _get(state, "selected_topic", TopicRecord(title="", audience="", hook="", demand_source="", differentiation=""))
    audience: str = _get(state, "audience", "小红书新手用户")
    brand_voice: str = _get(state, "brand_voice", "清醒、实操、少废话")
    openai_model: str = _get(state, "openai_text_model", "gpt-5.5")
    openai_mode: str = _get(state, "openai_reasoning_mode", "ultra_high")
    grok_model: str = _get(state, "grok_image_model", "grok-imagine-image-quality")
    grok_mode: str = _get(state, "grok_image_mode", "Expert")
    aspect_ratio: str = _get(state, "image_aspect_ratio", "3:4")
    style: str = _get(state, "image_style", "cartoon")
    flow_overrides: Dict[str, Any] = _get(state, "skill_flow_overrides", {})
    prompt_overrides: Dict[str, str] = _get(state, "prompt_overrides", {})

    openai_sf: SkillSubflow = _build_openai_subflow(
        selected_topic, audience, brand_voice, openai_model, openai_mode,
        aspect_ratio, style, flow_overrides, prompt_overrides,
    )
    grok_sf: SkillSubflow = _build_grok_subflow(
        selected_topic, grok_model, grok_mode,
        aspect_ratio, style, flow_overrides, prompt_overrides,
    )

    return SkillSubflowNodeOutput(skill_subflows=[openai_sf, grok_sf])
