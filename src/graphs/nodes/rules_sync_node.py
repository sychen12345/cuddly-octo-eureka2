"""
Skill规则子工作流 — 规则同步节点
将所有子节点输出的风格、尺寸、必选项、禁选项、一致性规则合并，
写回 skill_rules.json 配置文件
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import RulesSyncNodeInput, RulesSyncNodeOutput, ImageStyleRules, WorkflowStepInfo


def _load_full_config() -> Dict[str, Any]:
    """从配置文件读取完整 skill_rules 配置"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _sync_back_config(data: Dict[str, Any]) -> None:
    """将配置写回文件"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def rules_sync_node(
    state: RulesSyncNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RulesSyncNodeOutput:
    """
    title: 规则同步回写
    desc: 合并所有子节点输出的风格规则，仅在智能判断结果为"规则修改"时写回 skill_rules.json 配置文件
    integrations:
    """
    ctx = runtime.context

    # 1. 读取当前完整配置（保留 workflow_steps 等非风格字段）
    full_cfg = _load_full_config()

    # 2. 合并各子节点的输出到 image_style
    merged_image_style: Dict[str, Any] = {
        "aspect_ratio": state.aspect_ratio,
        "style": state.style,
        "must_have": state.must_have,
        "avoid": state.avoid,
        "consistency_rules": state.consistency_rules,
    }
    # 保留配置文件中的 reference_image_notes 等字段
    old_image_style = full_cfg.get("image_style", {})
    for preserve_key in ["reference_image_notes", "reference_image_urls"]:
        if preserve_key in old_image_style:
            merged_image_style[preserve_key] = old_image_style[preserve_key]

    # 3. 构建 ImageStyleRules
    image_style_rules = ImageStyleRules(
        aspect_ratio=state.aspect_ratio,
        style=state.style,
        reference_image_notes=merged_image_style.get("reference_image_notes", []),
        reference_image_urls=merged_image_style.get("reference_image_urls", []),
        must_have=state.must_have,
        avoid=state.avoid,
        consistency_rules=state.consistency_rules
    )

    # 4. 构建 workflow_steps
    workflow_steps: List[WorkflowStepInfo] = []
    if state.workflow_steps_override and isinstance(state.workflow_steps_override, list):
        for step in state.workflow_steps_override:
            if isinstance(step, dict):
                workflow_steps.append(WorkflowStepInfo(
                    node_key=step.get("node_key", ""),
                    title=step.get("title", ""),
                    model_or_tool=step.get("model_or_tool", ""),
                    prompt_key=step.get("prompt_key", ""),
                    output_keys=step.get("output_keys", []),
                    status="ready"
                ))
    else:
        # 使用配置文件中的 workflow_steps
        for step in full_cfg.get("workflow_steps", []):
            if isinstance(step, dict):
                workflow_steps.append(WorkflowStepInfo(
                    node_key=step.get("node_key", ""),
                    title=step.get("title", ""),
                    model_or_tool=step.get("model_or_tool", ""),
                    prompt_key=step.get("prompt_key", ""),
                    output_keys=step.get("output_keys", []),
                    status="ready"
                ))

    # 5. 仅在智能判断结果为"规则修改"时写回配置文件
    did_sync = False
    if state.rules_judge_decision == "sync":
        synced_cfg = {
            "image_style": merged_image_style,
            "workflow_steps": [step.model_dump() for step in workflow_steps]
        }
        _sync_back_config(synced_cfg)
        did_sync = True

    return RulesSyncNodeOutput(
        image_style_rules=image_style_rules,
        workflow_steps=workflow_steps,
        synced_skill_rules_cfg=merged_image_style,
        rules_judge_decision=state.rules_judge_decision,
        rules_synced=did_sync
    )
