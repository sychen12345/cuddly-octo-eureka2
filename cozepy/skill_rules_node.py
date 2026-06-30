"""
Skill规则与参考图节点。

把本地/下载的 skill 经验、用户参考图描述、3:4 卡通套图要求沉淀成明确规则。
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

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
    from graphs.state import (
        ImageStyleRule,
        SkillRulesNodeInput,
        SkillRulesNodeOutput,
        WorkflowStep,
    )
except ImportError:
    from .state import (
        ImageStyleRule,
        SkillRulesNodeInput,
        SkillRulesNodeOutput,
        WorkflowStep,
    )


def _get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def skill_rules_node(
    state: SkillRulesNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> SkillRulesNodeOutput:
    """
    title: Skill规则与参考图
    desc: 参考本地/下载 skill 与用户参考图，生成 3:4 卡通套图规则
    integrations:
    """
    aspect_ratio = str(_get(state, "image_aspect_ratio", "3:4")).strip() or "3:4"
    style = str(_get(state, "image_style", "cartoon")).strip() or "cartoon"
    reference_image_notes = _as_list(_get(state, "reference_image_notes", []))
    reference_image_urls = _as_list(_get(state, "reference_image_urls", []))

    must_have = [
        "固定 3:4 竖版构图，适合小红书图文卡片",
        "卡通风格，但保持主题信息清楚，不做幼稚化涂鸦",
        "每张图只承载一个核心信息，文字少、层级清楚、留白足",
        "套图保持主角、色彩、线条粗细、背景质感一致",
        "参考 canvas-design 的原则：视觉先行、文字只做必要锚点、画面要像精修作品",
        "参考 brand-guidelines 的原则：固定色板、字体层级和品牌语气，避免一页一套风格",
    ]
    if reference_image_notes:
        must_have.append("吸收用户参考图中的角色、镜头、颜色、线条、材质和情绪规则")

    avoid = [
        "不要 1:1 横图或无比例说明的泛泛生图提示",
        "不要每页角色和画风漂移",
        "不要把大段文案塞进图片",
        "不要承诺收益、涨粉、阅读量或虚构真实平台数据",
        "不要复制对标原图，只学习构图和表达方式",
    ]

    consistency_rules = [
        "同一套图共用一个主角或核心视觉符号",
        "同一套图共用 2-3 个主色和 1 个强调色",
        "封面更强钩子，内页更重步骤和证据",
        "所有画面保留给标题和小标签的安全区域",
    ]

    image_style_rules = ImageStyleRule(
        aspect_ratio=aspect_ratio,
        style=style,
        reference_image_notes=reference_image_notes,
        reference_image_urls=reference_image_urls,
        must_have=must_have,
        avoid=avoid,
        consistency_rules=consistency_rules,
    )

    workflow_steps = [
        WorkflowStep(
            node_key="benchmark_and_demand",
            title="对标与需求挖掘",
            model_or_tool="Skill: xhs-content-workflow",
            output_keys=["research_brief", "benchmark_accounts", "demand_insights"],
        ),
        WorkflowStep(
            node_key="topic_selection",
            title="选题库与高浏览选题",
            model_or_tool="规则评分 + 用户指定优先",
            output_keys=["topic_bank", "selected_topic"],
        ),
        WorkflowStep(
            node_key="skill_rules",
            title="Skill规则与参考图",
            model_or_tool="local skills + reference images",
            output_keys=["image_style_rules", "workflow_steps"],
        ),
        WorkflowStep(
            node_key="skill_subflows",
            title="OpenAI/Grok Skill 子流程",
            model_or_tool="editable subflows",
            output_keys=["skill_subflows"],
        ),
        WorkflowStep(
            node_key="prompt_editor",
            title="在线提示词编辑",
            model_or_tool="prompt_overrides + skill_flow_overrides",
            output_keys=["editable_prompts"],
        ),
        WorkflowStep(
            node_key="openai_text",
            title="OpenAI GPT5.5 超高推理文案",
            model_or_tool=str(_get(state, "openai_text_model", "gpt-5.5")),
            prompt_key="openai_text_skill",
            output_keys=["openai_text_package"],
            status="parallel_branch",
        ),
        WorkflowStep(
            node_key="grok_image_set",
            title="Grok Expert 3:4 卡通套图",
            model_or_tool=str(_get(state, "grok_image_model", "grok-imagine-image-quality")),
            prompt_key="grok_image_skill",
            output_keys=["grok_image_set"],
            status="parallel_branch",
        ),
        WorkflowStep(
            node_key="finalize",
            title="结果审核打包",
            model_or_tool="workflow packager",
            prompt_key="final_review",
            output_keys=["card_package", "workflow_summary", "next_commands"],
            status="join",
        ),
    ]

    return SkillRulesNodeOutput(image_style_rules=image_style_rules, workflow_steps=workflow_steps)
