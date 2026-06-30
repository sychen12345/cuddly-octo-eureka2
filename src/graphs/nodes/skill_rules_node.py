"""
节点3: Skill规则与参考图 (skill_rules_node)
─────────────────────────────────────────────
输入: image_aspect_ratio, image_style, reference_image_notes, reference_image_urls,
      openai_text_model, grok_image_model
输出: image_style_rules, workflow_steps
"""
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    SkillRulesNodeInput,
    SkillRulesNodeOutput,
    ImageStyleRule,
    WorkflowStep,
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


# ── 节点函数 ──────────────────────────────────────────────
def skill_rules_node(
    state: SkillRulesNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SkillRulesNodeOutput:
    """
    title: Skill规则与参考图
    desc: 根据参考图和图片风格设定，生成 Grok 套图的视觉规则和完整工作流步骤清单
    integrations:
    """
    aspect_ratio: str = _get(state, "image_aspect_ratio", "3:4")
    style: str = _get(state, "image_style", "cartoon")
    ref_notes: List[str] = _get(state, "reference_image_notes", [])
    ref_urls: List[str] = _get(state, "reference_image_urls", [])
    openai_model: str = _get(state, "openai_text_model", "gpt-5.5")
    grok_model: str = _get(state, "grok_image_model", "grok-imagine-image-quality")

    must_have: List[str] = ref_notes if ref_notes else [
        "小红书图文卡片；短句；层级清楚",
    ]
    avoid: List[str] = [
        "不要生成真人照片或写真",
        "不要使用过于复杂的配色",
        "不要在小图上放长段落",
    ]
    consistency_rules: List[str] = [
        "全部卡片使用同一配色方案",
        "标题字体、大小保持一致",
        "每页最多一个核心信息",
        "封面与内页风格统一",
    ]

    image_style_rules: ImageStyleRule = ImageStyleRule(
        aspect_ratio=aspect_ratio,
        style=style,
        reference_image_notes=ref_notes,
        reference_image_urls=ref_urls,
        must_have=must_have,
        avoid=avoid,
        consistency_rules=consistency_rules,
    )

    workflow_steps: List[WorkflowStep] = [
        WorkflowStep(node_key="greeting", title="对标与需求挖掘", model_or_tool="", prompt_key="", output_keys=["research_brief", "benchmark_accounts", "demand_insights"]),
        WorkflowStep(node_key="process", title="选题库与高浏览选题", model_or_tool="", prompt_key="", output_keys=["topic_bank", "selected_topic"]),
        WorkflowStep(node_key="skill_rules", title="Skill规则与参考图", model_or_tool="", prompt_key="", output_keys=["image_style_rules", "workflow_steps"]),
        WorkflowStep(node_key="skill_subflow", title="OpenAI/Grok Skill 子流程", model_or_tool="openai+grok", prompt_key="", output_keys=["skill_subflows"]),
        WorkflowStep(node_key="prompt", title="在线提示词编辑", model_or_tool="", prompt_key="", output_keys=["editable_prompts"]),
        WorkflowStep(node_key="openai_text", title="OpenAI GPT5.5 文案", model_or_tool=openai_model, prompt_key="openai_text_prompt", output_keys=["openai_text_package"]),
        WorkflowStep(node_key="grok_image", title="Grok Expert 套图", model_or_tool=grok_model, prompt_key="grok_image_prompt", output_keys=["grok_image_set"]),
        WorkflowStep(node_key="finalize", title="结果审核打包", model_or_tool="", prompt_key="", output_keys=["card_package", "workflow_summary", "next_commands"]),
    ]

    return SkillRulesNodeOutput(
        image_style_rules=image_style_rules,
        workflow_steps=workflow_steps,
    )
