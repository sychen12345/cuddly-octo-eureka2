"""节点 5/8 — 在线提示词编辑 (prompt)"""

from typing import List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    EditablePrompt, ImageStyleRules, SkillSubflowDef, TopicRecord,
    PromptNodeInput, PromptNodeOutput,
)


def _build_prompts(
    niche: str,
    audience: str,
    brand_voice: str,
    selected_topic: Optional[TopicRecord],
    image_style_rules: Optional[ImageStyleRules],
    skill_subflows: List[SkillSubflowDef],
) -> List[EditablePrompt]:
    topic_title = selected_topic.title if selected_topic else niche
    prompts: List[EditablePrompt] = []

    # OpenAI 文案提示词
    prompts.append(EditablePrompt(
        key="openai_text_prompt",
        title="OpenAI 文案提示词",
        target_model="gpt-5.5",
        default_prompt=(
            f"你是小红书内容创作专家，擅长按「{brand_voice}」语气写作。\n"
            f"领域：{niche}\n"
            f"目标人群：{audience}\n"
            f"选题：{topic_title}\n"
            f"请生成图文卡片的标题选项、正文、每页脚本和视觉说明。"
        ),
        final_prompt=(
            f"你是小红书内容创作专家，擅长按「{brand_voice}」语气写作。\n"
            f"领域：{niche}\n"
            f"目标人群：{audience}\n"
            f"选题：{topic_title}\n"
            f"请生成图文卡片的标题选项、正文、每页脚本和视觉说明。"
        ),
        editable=True,
    ))

    # Grok 生图提示词
    prompts.append(EditablePrompt(
        key="grok_image_prompt",
        title="Grok 生图提示词",
        target_model="grok-imagine-image-quality",
        default_prompt=(
            f"生成小红书 3:4 卡通风格图文卡片套图。\n"
            f"选题：{topic_title}\n"
            f"风格：卡通、短句、层级清楚、留白充足。\n"
            f"每页一个核心信息，配色统一。"
        ),
        final_prompt=(
            f"生成小红书 3:4 卡通风格图文卡片套图。\n"
            f"选题：{topic_title}\n"
            f"风格：卡通、短句、层级清楚、留白充足。\n"
            f"每页一个核心信息，配色统一。"
        ),
        editable=True,
    ))

    # 从 skill_subflows 中提取步骤提示词
    for subflow in skill_subflows:
        for step in subflow.steps:
            if step.prompt_key and step.prompt_key not in [p.key for p in prompts]:
                prompts.append(EditablePrompt(
                    key=step.prompt_key,
                    title=step.title,
                    target_model=step.model_or_tool,
                    default_prompt=step.default_prompt,
                    final_prompt=step.final_prompt,
                    editable=step.editable,
                ))

    return prompts


def prompt_node(
    state: PromptNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> PromptNodeOutput:
    """
    title: 在线提示词编辑
    desc: 为每个子流程步骤生成可编辑的提示词，支持用户在线修改
    integrations:
    """
    ctx = runtime.context
    editable_prompts = _build_prompts(
        state.niche, state.audience, state.brand_voice,
        state.selected_topic, state.image_style_rules, state.skill_subflows,
    )
    return PromptNodeOutput(editable_prompts=editable_prompts)
