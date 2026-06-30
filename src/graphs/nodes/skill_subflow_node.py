"""节点 4/8 — OpenAI/Grok Skill 子流程 (skill_subflow)"""

from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    ImageStyleRules, SkillSubflowDef, SkillSubflowStep, TopicRecord,
    SkillSubflowNodeInput, SkillSubflowNodeOutput,
)


def _build_openai_subflow(
    niche: str,
    audience: str,
    selected_topic: Optional[TopicRecord],
    image_style_rules: Optional[ImageStyleRules],
) -> SkillSubflowDef:
    topic_title = selected_topic.title if selected_topic else niche
    return SkillSubflowDef(
        skill_key="openai_text_skill",
        title="OpenAI GPT5.5 文案子流程",
        provider="openai",
        model="gpt-5.5",
        mode="ultra_high",
        endpoint="https://api.openai.com/v1/chat/completions",
        description="生成小红书图文卡片文案：标题、正文、每页脚本、视觉说明",
        editable=True,
        steps=[
            SkillSubflowStep(
                step_key="openai_analyze",
                title="分析选题与需求",
                node_type="model",
                model_or_tool="gpt-5.5",
                prompt_key="openai_text_prompt",
                default_prompt=f"分析选题「{topic_title}」的核心需求，生成图文卡片文案。",
                final_prompt=f"分析选题「{topic_title}」的核心需求，生成图文卡片文案。",
                input_keys=["selected_topic", "audience", "niche"],
                output_keys=["title_options", "card_script", "image_brief"],
                editable=True,
                enabled=True,
                notes="可修改提示词来调整文案风格",
            ),
            SkillSubflowStep(
                step_key="openai_generate",
                title="生成正文与卡片脚本",
                node_type="prompt",
                model_or_tool="gpt-5.5",
                prompt_key="openai_generate_prompt",
                default_prompt=f"根据分析结果，生成{audience}的图文卡片正文和每页脚本。",
                final_prompt=f"根据分析结果，生成{audience}的图文卡片正文和每页脚本。",
                input_keys=["openai_text_prompt_output"],
                output_keys=["post_description", "card_script"],
                editable=True,
                enabled=True,
                notes="可调整每页卡片的内容密度",
            ),
        ],
        status="ready",
    )


def _build_grok_subflow(
    niche: str,
    audience: str,
    selected_topic: Optional[TopicRecord],
    image_style_rules: Optional[ImageStyleRules],
) -> SkillSubflowDef:
    topic_title = selected_topic.title if selected_topic else niche
    return SkillSubflowDef(
        skill_key="grok_image_skill",
        title="Grok Expert 套图子流程",
        provider="grok",
        model="grok-imagine-image-quality",
        mode="Expert",
        endpoint="https://api.x.ai/v1/images/generations",
        description=f"生成 {image_style_rules.aspect_ratio if image_style_rules else '3:4'} cartoon 风格的小红书图文套图",
        editable=True,
        steps=[
            SkillSubflowStep(
                step_key="grok_plan",
                title="规划套图视觉方向",
                node_type="rule",
                model_or_tool="grok-imagine-image-quality",
                prompt_key="grok_plan_prompt",
                default_prompt=f"为选题「{topic_title}」规划 3:4 cartoon 风格套图。",
                final_prompt=f"为选题「{topic_title}」规划 3:4 cartoon 风格套图。",
                input_keys=["image_style_rules", "openai_text_package"],
                output_keys=["grok_image_plan"],
                editable=True,
                enabled=True,
                notes="可修改视觉方向",
            ),
            SkillSubflowStep(
                step_key="grok_generate",
                title="生成套图",
                node_type="model",
                model_or_tool="grok-imagine-image-quality",
                prompt_key="grok_image_prompt",
                default_prompt="按规划生成3:4 cartoon风格的小红书图文卡片。",
                final_prompt="按规划生成3:4 cartoon风格的小红书图文卡片。",
                input_keys=["grok_image_plan"],
                output_keys=["grok_image_set"],
                editable=True,
                enabled=True,
                notes="可修改生图提示词",
            ),
        ],
        status="ready",
    )


def skill_subflow_node(
    state: SkillSubflowNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SkillSubflowNodeOutput:
    """
    title: OpenAI/Grok Skill 子流程
    desc: 为 OpenAI 文案和 Grok 套图分别生成子流程定义
    integrations:
    """
    ctx = runtime.context
    openai_subflow = _build_openai_subflow(state.niche, state.audience, state.selected_topic, state.image_style_rules)
    grok_subflow = _build_grok_subflow(state.niche, state.audience, state.selected_topic, state.image_style_rules)
    return SkillSubflowNodeOutput(skill_subflows=[openai_subflow, grok_subflow])
