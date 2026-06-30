"""
内容生成技能 — 经验沉淀节点
把运营确认的文案和图片生成步骤保存为长期技能，供下次内容生产复用。
"""
import os
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import SubflowSyncNodeInput, SubflowSyncNodeOutput, SkillSubflowDef, SkillSubflowStep, EditablePrompt


def _to_dict(obj: Any) -> Any:
    """将 BaseModel 转为 dict，已经是 dict 则原样返回"""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return obj


def _sync_back_config(data: Dict[str, Any]) -> None:
    """将配置写回文件"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_subflows.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_subflow_def(raw: Dict[str, Any]) -> SkillSubflowDef:
    """将 dict 解析为 SkillSubflowDef"""
    steps_raw = raw.get("steps", [])
    steps: List[SkillSubflowStep] = []
    for s in steps_raw:
        if isinstance(s, dict):
            steps.append(SkillSubflowStep(
                step_key=s.get("step_key", ""),
                title=s.get("title", ""),
                node_type=s.get("node_type", ""),
                model_or_tool=s.get("model_or_tool", ""),
                prompt_key=s.get("prompt_key", ""),
                default_prompt=s.get("default_prompt", ""),
                final_prompt=s.get("final_prompt", ""),
                input_keys=s.get("input_keys", []),
                output_keys=s.get("output_keys", []),
                editable=s.get("editable", True),
                enabled=s.get("enabled", True),
                notes=s.get("notes", "")
            ))
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


def subflow_sync_node(
    state: SubflowSyncNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SubflowSyncNodeOutput:
    """
    title: 沉淀内容生成经验
    desc: 把运营确认的文案和图片生成步骤沉淀为长期技能
    integrations:
    """
    ctx = runtime.context

    # 1. 合并两个子流程
    all_subflows_raw: List[Dict[str, Any]] = []
    if state.openai_subflow and isinstance(state.openai_subflow, dict) and state.openai_subflow.get("skill_key"):
        all_subflows_raw.append(state.openai_subflow)
    if state.grok_subflow and isinstance(state.grok_subflow, dict) and state.grok_subflow.get("skill_key"):
        all_subflows_raw.append(state.grok_subflow)

    # 2. 转换为 SkillSubflowDef
    skill_subflows: List[SkillSubflowDef] = []
    for raw in all_subflows_raw:
        skill_subflows.append(_parse_subflow_def(raw))

    # 3. 合并提示词
    editable_prompts: List[EditablePrompt] = []
    for p in state.openai_prompts:
        editable_prompts.append(p)
    for p in state.grok_prompts:
        editable_prompts.append(p)

    # 4. 仅在 AI 技能教练建议长期保留时保存
    if state.subflows_judge_decision == "sync":
        synced_cfg: List[Dict[str, Any]] = [_to_dict(sf) for sf in all_subflows_raw]
        _sync_back_config({"subflows": synced_cfg})
    else:
        synced_cfg: List[Dict[str, Any]] = [_to_dict(sf) for sf in all_subflows_raw]

    return SubflowSyncNodeOutput(
        skill_subflows=skill_subflows,
        editable_prompts=editable_prompts,
        synced_skill_subflows_cfg=synced_cfg
    )
