"""
Skill规则子工作流 — 包装节点
在主图中作为 skill_rules 节点，内部调用 skill_rules_subgraph 子工作流
运营在画布上展开此节点可看到子工作流内部的可编辑节点
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    SkillRulesNodeInput,
    SkillRulesNodeOutput,
    ImageStyleRules,
    WorkflowStepInfo,
)
from graphs.loop_graph import skill_rules_subgraph


def _to_dict(obj: Any) -> Any:
    """将 BaseModel 转为 dict"""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return obj


def skill_rules_node(
    state: SkillRulesNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SkillRulesNodeOutput:
    """
    title: Skill规则与参考图
    desc: 调用Skill规则子工作流（风格/尺寸/必选项/禁选项/一致性规则），运营可展开编辑各子节点
    integrations:
    """
    ctx = runtime.context

    # 1. 构建子工作流输入
    selected_topic_dict = _to_dict(state.selected_topic) if state.selected_topic else None
    subgraph_input = {
        "niche": state.niche,
        "selected_topic": selected_topic_dict,
        "card_count": state.card_count,
        "image_style_override": state.image_style_override,
        "workflow_steps_override": state.workflow_steps_override,
    }

    # 2. 调用子工作流
    result = skill_rules_subgraph.invoke(subgraph_input)

    # 3. 解析子工作流输出
    image_style_rules_raw = result.get("image_style_rules")
    image_style_rules: Optional[ImageStyleRules] = None
    if isinstance(image_style_rules_raw, BaseModel):
        image_style_rules = image_style_rules_raw
    elif isinstance(image_style_rules_raw, dict):
        image_style_rules = ImageStyleRules(**image_style_rules_raw)

    workflow_steps_raw = result.get("workflow_steps", [])
    workflow_steps: List[WorkflowStepInfo] = []
    if isinstance(workflow_steps_raw, list):
        for step in workflow_steps_raw:
            if isinstance(step, BaseModel):
                workflow_steps.append(step)
            elif isinstance(step, dict):
                workflow_steps.append(WorkflowStepInfo(**step))

    synced_cfg = result.get("synced_skill_rules_cfg", {})
    if not isinstance(synced_cfg, dict):
        synced_cfg = {}

    return SkillRulesNodeOutput(
        image_style_rules=image_style_rules,
        workflow_steps=workflow_steps,
        synced_skill_rules_cfg=synced_cfg,
    )
