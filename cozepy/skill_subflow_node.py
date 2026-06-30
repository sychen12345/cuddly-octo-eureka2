"""
OpenAI/Grok 可编辑 skill 子流程节点。

这个节点把两个模型调用拆成可视化子流程，便于运营在低代码工作流中
修改每一步 prompt、模型模式和启用状态。
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
    from graphs.state import SkillSubflow, SkillSubflowNodeInput, SkillSubflowNodeOutput, SkillSubflowStep
except ImportError:
    from .state import SkillSubflow, SkillSubflowNodeInput, SkillSubflowNodeOutput, SkillSubflowStep


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
    selected = _dump(_get(state, "selected_topic", {}))
    return str(selected.get("title", "")).strip()


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on", "enable", "enabled"}:
            return True
        if lowered in {"false", "0", "no", "off", "disable", "disabled"}:
            return False
    return bool(value)


def _step_overrides(skill_override: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw_steps = skill_override.get("steps", {})
    if isinstance(raw_steps, dict):
        return {str(key): value for key, value in raw_steps.items() if isinstance(value, dict)}
    if isinstance(raw_steps, list):
        out: Dict[str, Dict[str, Any]] = {}
        for item in raw_steps:
            if isinstance(item, dict) and item.get("step_key"):
                out[str(item["step_key"])] = item
        return out
    return {}


def _apply_overrides(
    subflow: SkillSubflow,
    skill_overrides: Dict[str, Any],
    prompt_overrides: Dict[str, str],
) -> SkillSubflow:
    skill_override = skill_overrides.get(subflow.skill_key, {})
    if not isinstance(skill_override, dict):
        skill_override = {}

    subflow.title = str(skill_override.get("title", subflow.title)).strip() or subflow.title
    subflow.description = str(skill_override.get("description", subflow.description)).strip() or subflow.description
    subflow.model = str(skill_override.get("model", subflow.model)).strip() or subflow.model
    subflow.mode = str(skill_override.get("mode", subflow.mode)).strip() or subflow.mode
    subflow.endpoint = str(skill_override.get("endpoint", subflow.endpoint)).strip() or subflow.endpoint
    subflow.editable = _as_bool(skill_override.get("editable"), subflow.editable)

    step_overrides = _step_overrides(skill_override)
    patched_steps: List[SkillSubflowStep] = []
    for step in subflow.steps:
        step_override = step_overrides.get(step.step_key, {})
        if step_override:
            step.title = str(step_override.get("title", step.title)).strip() or step.title
            step.node_type = str(step_override.get("node_type", step.node_type)).strip() or step.node_type
            step.model_or_tool = str(step_override.get("model_or_tool", step.model_or_tool)).strip() or step.model_or_tool
            step.notes = str(step_override.get("notes", step.notes)).strip() or step.notes
            step.editable = _as_bool(step_override.get("editable"), step.editable)
            step.enabled = _as_bool(step_override.get("enabled"), step.enabled)
            if isinstance(step_override.get("input_keys"), list):
                step.input_keys = [str(item) for item in step_override["input_keys"]]
            if isinstance(step_override.get("output_keys"), list):
                step.output_keys = [str(item) for item in step_override["output_keys"]]

        final_prompt = (
            step_override.get("final_prompt")
            or step_override.get("prompt")
            or prompt_overrides.get(step.prompt_key)
            or prompt_overrides.get(step.step_key)
            or step.default_prompt
        )
        step.final_prompt = str(final_prompt).strip() or step.default_prompt
        patched_steps.append(step)

    subflow.steps = patched_steps
    return subflow


def _openai_subflow(state: Any) -> SkillSubflow:
    title = _selected_title(state)
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    brand_voice = str(_get(state, "brand_voice", "清醒、实操、少废话")).strip()
    model = str(_get(state, "openai_text_model", "gpt-5.5")).strip() or "gpt-5.5"
    mode = str(_get(state, "openai_reasoning_mode", "ultra_high")).strip() or "ultra_high"
    return SkillSubflow(
        skill_key="openai_text_skill",
        title="OpenAI 图文文案 Skill 子流程",
        provider="openai",
        model=model,
        mode=mode,
        endpoint="https://api.openai.com/v1/responses",
        description="把选题、对标和评论需求转成小红书标题、卡片脚本、正文和视觉 brief。",
        steps=[
            SkillSubflowStep(
                step_key="collect_topic_context",
                title="整理选题和需求上下文",
                node_type="rule",
                model_or_tool="xhs-content-workflow",
                prompt_key="openai_text_skill.collect_topic_context",
                default_prompt=(
                    f"围绕选题「{title}」整理目标人群、评论痛点、浏览量证据、限制条件和账号语气。"
                    "只使用已提供证据，缺口标为待补充。"
                ),
                final_prompt=(
                    f"围绕选题「{title}」整理目标人群、评论痛点、浏览量证据、限制条件和账号语气。"
                    "只使用已提供证据，缺口标为待补充。"
                ),
                input_keys=["selected_topic", "demand_insights", "topic_research_notes", "constraints"],
                output_keys=["text_context"],
                notes="运营可在这里改变文案取材重点，例如更重评论原话或更重对标结构。",
            ),
            SkillSubflowStep(
                step_key="generate_xhs_text",
                title="GPT5.5 超高推理生成图文文字",
                node_type="model",
                model_or_tool=model,
                prompt_key="openai_text_skill.generate_xhs_text",
                default_prompt=(
                    f"你是 GPT5.5 超高推理模式。请为「{audience}」生成小红书图文文案，"
                    f"账号语气是「{brand_voice}」。输出封面标题、每页脚本、正文、CTA 和给图片模型的视觉 brief。"
                    "不要承诺收益，不虚构平台数据。"
                ),
                final_prompt=(
                    f"你是 GPT5.5 超高推理模式。请为「{audience}」生成小红书图文文案，"
                    f"账号语气是「{brand_voice}」。输出封面标题、每页脚本、正文、CTA 和给图片模型的视觉 brief。"
                    "不要承诺收益，不虚构平台数据。"
                ),
                input_keys=["text_context", "editable_prompts"],
                output_keys=["title_options", "card_script", "post_description", "image_brief"],
                notes="这是 OpenAI 真正调用的核心文案 skill 步骤。",
            ),
            SkillSubflowStep(
                step_key="review_text_for_image",
                title="把文字转成图片 brief 并审核",
                node_type="review",
                model_or_tool=model,
                prompt_key="openai_text_skill.review_text_for_image",
                default_prompt=(
                    "检查标题和卡片脚本是否适合 3:4 卡通套图。"
                    "每页只保留一个画面动作，避免让图片承载大段文字。"
                ),
                final_prompt=(
                    "检查标题和卡片脚本是否适合 3:4 卡通套图。"
                    "每页只保留一个画面动作，避免让图片承载大段文字。"
                ),
                input_keys=["card_script", "image_style_rules"],
                output_keys=["image_brief"],
                notes="运营可在这里补充图文转换标准。",
            ),
        ],
    )


def _grok_subflow(state: Any) -> SkillSubflow:
    title = _selected_title(state)
    model = str(_get(state, "grok_image_model", "grok-imagine-image-quality")).strip() or "grok-imagine-image-quality"
    mode = str(_get(state, "grok_image_mode", "Expert")).strip() or "Expert"
    aspect_ratio = str(_get(state, "image_aspect_ratio", "3:4")).strip() or "3:4"
    style = str(_get(state, "image_style", "cartoon")).strip() or "cartoon"
    return SkillSubflow(
        skill_key="grok_image_skill",
        title="Grok Expert 套图 Skill 子流程",
        provider="grok",
        model=model,
        mode=mode,
        endpoint="https://api.x.ai/v1/images/generations",
        description="把 OpenAI 文案、参考图规则和本地视觉 skill 转成统一 3:4 卡通套图。",
        steps=[
            SkillSubflowStep(
                step_key="load_visual_rules",
                title="读取参考图和本地视觉规则",
                node_type="rule",
                model_or_tool="canvas-design + brand-guidelines",
                prompt_key="grok_image_skill.load_visual_rules",
                default_prompt=(
                    f"读取用户参考图规则和本地视觉 skill，固定 {aspect_ratio} 竖版、{style} 风格、统一角色、色板、线条和安全留白。"
                ),
                final_prompt=(
                    f"读取用户参考图规则和本地视觉 skill，固定 {aspect_ratio} 竖版、{style} 风格、统一角色、色板、线条和安全留白。"
                ),
                input_keys=["image_style_rules", "reference_image_notes", "reference_image_urls"],
                output_keys=["visual_rules"],
                notes="运营可在这里加入参考图风格、角色设定、色彩和镜头要求。",
            ),
            SkillSubflowStep(
                step_key="compose_page_prompts",
                title="Grok Expert 生成每页图片提示词",
                node_type="model",
                model_or_tool=model,
                prompt_key="grok_image_skill.compose_page_prompts",
                default_prompt=(
                    f"你是 Grok Expert 生图子流程。请基于选题「{title}」和每页文案生成一组 3:4 竖版卡通图。"
                    "每张图只表达一个动作或场景，套图像同一套小红书卡片。"
                ),
                final_prompt=(
                    f"你是 Grok Expert 生图子流程。请基于选题「{title}」和每页文案生成一组 3:4 竖版卡通图。"
                    "每张图只表达一个动作或场景，套图像同一套小红书卡片。"
                ),
                input_keys=["card_script", "image_brief", "visual_rules"],
                output_keys=["image_prompts", "image_url"],
                notes="这是 Grok 真正调用的核心生图 skill 步骤。",
            ),
            SkillSubflowStep(
                step_key="review_set_consistency",
                title="审核套图一致性",
                node_type="review",
                model_or_tool="workflow review",
                prompt_key="grok_image_skill.review_set_consistency",
                default_prompt=(
                    "检查套图是否保持主角、色板、线条、版式一致。"
                    "封面要强钩子，内页要清晰表达步骤，不要复制参考图。"
                ),
                final_prompt=(
                    "检查套图是否保持主角、色板、线条、版式一致。"
                    "封面要强钩子，内页要清晰表达步骤，不要复制参考图。"
                ),
                input_keys=["image_prompts", "image_style_rules"],
                output_keys=["consistency_notes"],
                notes="运营可在这里调整套图验收标准。",
            ),
        ],
    )


def skill_subflow_node(
    state: SkillSubflowNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> SkillSubflowNodeOutput:
    """
    title: OpenAI/Grok Skill 子流程
    desc: 构建可视化、可在线编辑的 OpenAI 文案 skill 和 Grok 生图 skill
    integrations:
    """
    skill_overrides = _get(state, "skill_flow_overrides", {}) or {}
    if not isinstance(skill_overrides, dict):
        skill_overrides = {}
    prompt_overrides = _get(state, "prompt_overrides", {}) or {}
    if not isinstance(prompt_overrides, dict):
        prompt_overrides = {}

    subflows = [
        _apply_overrides(_openai_subflow(state), skill_overrides, prompt_overrides),
        _apply_overrides(_grok_subflow(state), skill_overrides, prompt_overrides),
    ]
    return SkillSubflowNodeOutput(skill_subflows=subflows)
