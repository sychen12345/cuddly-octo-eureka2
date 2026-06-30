"""节点 3/8 — Skill规则与参考图 (skill_rules)"""

from typing import List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    ImageStyleRules, TopicRecord, WorkflowStepInfo,
    SkillRulesNodeInput, SkillRulesNodeOutput,
)


def _build_image_style(niche: str, selected_topic: Optional[TopicRecord], card_count: int) -> ImageStyleRules:
    return ImageStyleRules(
        aspect_ratio="3:4",
        style="cartoon",
        reference_image_notes=[],
        reference_image_urls=[],
        must_have=["小红书图文卡片；短句；层级清楚"],
        avoid=[
            "不要生成真人照片或写真",
            "不要使用过于复杂的配色",
            "不要在小图上放长段落",
        ],
        consistency_rules=[
            "全部卡片使用同一配色方案",
            "标题字体、大小保持一致",
            "每页最多一个核心信息",
            "封面与内页风格统一",
        ],
    )


def _build_workflow_steps() -> List[WorkflowStepInfo]:
    return [
        WorkflowStepInfo(node_key="greeting", title="对标与需求挖掘", model_or_tool="", prompt_key="", output_keys=["research_brief", "benchmark_accounts", "demand_insights"], status="ready"),
        WorkflowStepInfo(node_key="process", title="选题库与高浏览选题", model_or_tool="", prompt_key="", output_keys=["topic_bank", "selected_topic"], status="ready"),
        WorkflowStepInfo(node_key="skill_rules", title="Skill规则与参考图", model_or_tool="", prompt_key="", output_keys=["image_style_rules", "workflow_steps"], status="ready"),
        WorkflowStepInfo(node_key="skill_subflow", title="OpenAI/Grok Skill 子流程", model_or_tool="openai+grok", prompt_key="", output_keys=["skill_subflows"], status="ready"),
        WorkflowStepInfo(node_key="prompt", title="在线提示词编辑", model_or_tool="", prompt_key="", output_keys=["editable_prompts"], status="ready"),
        WorkflowStepInfo(node_key="openai_text", title="OpenAI GPT5.5 文案", model_or_tool="gpt-5.5", prompt_key="openai_text_prompt", output_keys=["openai_text_package"], status="ready"),
        WorkflowStepInfo(node_key="grok_image", title="Grok Expert 套图", model_or_tool="grok-imagine-image-quality", prompt_key="grok_image_prompt", output_keys=["grok_image_set"], status="ready"),
        WorkflowStepInfo(node_key="finalize", title="结果审核打包", model_or_tool="", prompt_key="", output_keys=["card_package", "workflow_summary", "next_commands"], status="ready"),
    ]


def skill_rules_node(
    state: SkillRulesNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SkillRulesNodeOutput:
    """
    title: Skill规则与参考图
    desc: 根据选题和赛道生成图片风格规则与工作流步骤概览
    integrations:
    """
    ctx = runtime.context
    image_style_rules = _build_image_style(state.niche, state.selected_topic, state.card_count)
    workflow_steps = _build_workflow_steps()
    return SkillRulesNodeOutput(image_style_rules=image_style_rules, workflow_steps=workflow_steps)
