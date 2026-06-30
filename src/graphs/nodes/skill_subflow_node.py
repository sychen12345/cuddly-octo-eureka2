"""
Skill子流程子工作流 — 包装节点
在主图中作为 skill_subflow 节点，内部调用 skill_subflow_subgraph 子工作流
运营在画布上展开此节点可看到 OpenAI/Grok 步骤配置子节点
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    SkillSubflowNodeInput,
    SkillSubflowNodeOutput,
    SkillSubflowDef,
    SkillSubflowStep,
    EditablePrompt,
)
from graphs.loop_graph import skill_subflow_subgraph


def _to_dict(obj: Any) -> Any:
    """将 BaseModel 转为 dict"""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return obj


def _parse_subflow_def(raw: Any) -> Optional[SkillSubflowDef]:
    """将 dict 或 BaseModel 解析为 SkillSubflowDef"""
    if isinstance(raw, SkillSubflowDef):
        return raw
    if isinstance(raw, dict):
        steps_raw = raw.get("steps", [])
        steps: List[SkillSubflowStep] = []
        for s in steps_raw:
            if isinstance(s, SkillSubflowStep):
                steps.append(s)
            elif isinstance(s, dict):
                steps.append(SkillSubflowStep(**s))
        try:
            return SkillSubflowDef(
                skill_key=raw.get("skill_key", ""),
                title=raw.get("title", ""),
                provider=raw.get("provider", ""),
                model=raw.get("model", ""),
                mode=raw.get("mode", ""),
                endpoint=raw.get("endpoint", ""),
                description=raw.get("description", ""),
                editable=raw.get("editable", True),
                steps=steps,
                status="ready"
            )
        except Exception:
            return None
    return None


def _parse_editable_prompt(raw: Any) -> Optional[EditablePrompt]:
    """将 dict 或 BaseModel 解析为 EditablePrompt"""
    if isinstance(raw, EditablePrompt):
        return raw
    if isinstance(raw, dict):
        try:
            return EditablePrompt(**raw)
        except Exception:
            return None
    return None


def skill_subflow_node(
    state: SkillSubflowNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SkillSubflowNodeOutput:
    """
    title: OpenAI/Grok Skill子流程
    desc: 调用Skill子流程子工作流（OpenAI/Grok步骤配置），运营可展开编辑各子节点
    integrations:
    """
    ctx = runtime.context

    # 1. 构建子工作流输入
    selected_topic_dict = _to_dict(state.selected_topic) if state.selected_topic else None
    subgraph_input = {
        "niche": state.niche,
        "audience": state.audience,
        "brand_voice": state.brand_voice,
        "selected_topic": selected_topic_dict,
        "skill_subflows_override": state.skill_subflows_override,
    }

    # 2. 调用子工作流
    result = skill_subflow_subgraph.invoke(subgraph_input)

    # 3. 解析子工作流输出
    skill_subflows_raw = result.get("skill_subflows", [])
    skill_subflows: List[SkillSubflowDef] = []
    if isinstance(skill_subflows_raw, list):
        for sf in skill_subflows_raw:
            parsed = _parse_subflow_def(sf)
            if parsed is not None:
                skill_subflows.append(parsed)

    editable_prompts_raw = result.get("editable_prompts", [])
    editable_prompts: List[EditablePrompt] = []
    if isinstance(editable_prompts_raw, list):
        for p in editable_prompts_raw:
            parsed = _parse_editable_prompt(p)
            if parsed is not None:
                editable_prompts.append(parsed)

    synced_cfg_raw = result.get("synced_skill_subflows_cfg", [])
    synced_cfg: List[Dict[str, Any]] = []
    if isinstance(synced_cfg_raw, list):
        for item in synced_cfg_raw:
            synced_cfg.append(_to_dict(item) if not isinstance(item, dict) else item)

    return SkillSubflowNodeOutput(
        skill_subflows=skill_subflows,
        editable_prompts=editable_prompts,
        synced_skill_subflows_cfg=synced_cfg,
    )
