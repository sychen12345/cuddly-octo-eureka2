"""
Skill规则与参考图节点
从 config/skill_rules.json 读取规则，输出 operator_control 可编辑面板
运营可在画布上修改：风格、尺寸、必选项、禁选项、一致性规则、工作流步骤
修改后通过 override 参数传入，自动同步回配置文件
"""
import os
import json
import copy
from typing import List, Dict, Optional, Any

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import SkillRulesNodeInput, SkillRulesNodeOutput


def _load_skill_rules() -> Dict[str, Any]:
    """从配置文件读取 skill 规则"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_operator_panels(
    image_style: Dict[str, Any],
    workflow_steps: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """构建 operator_control 的 edit_panels，让运营在画布上可编辑"""
    panels: List[Dict[str, Any]] = []

    # 面板1: 图片风格设置
    style_panel = {
        "key": "image_style",
        "title": "图片风格设置",
        "panel_type": "form",
        "editable": True,
        "fields": [
            {
                "key": "aspect_ratio",
                "label": "画面比例",
                "type": "select",
                "options": ["3:4", "1:1", "4:5", "16:9"],
                "value": image_style.get("aspect_ratio", "3:4")
            },
            {
                "key": "style",
                "label": "视觉风格",
                "type": "select",
                "options": ["cartoon", "flat", "minimal", "realistic", "handdrawn"],
                "value": image_style.get("style", "cartoon")
            },
            {
                "key": "must_have",
                "label": "必选项",
                "type": "tag_list",
                "value": image_style.get("must_have", []),
                "addable": True
            },
            {
                "key": "avoid",
                "label": "禁选项",
                "type": "tag_list",
                "value": image_style.get("avoid", []),
                "addable": True
            },
            {
                "key": "consistency_rules",
                "label": "一致性规则",
                "type": "tag_list",
                "value": image_style.get("consistency_rules", []),
                "addable": True
            }
        ]
    }
    panels.append(style_panel)

    # 面板2: 工作流步骤（可拖拽排序）
    steps_panel = {
        "key": "workflow_steps",
        "title": "工作流步骤（可拖拽排序）",
        "panel_type": "sortable_list",
        "editable": True,
        "items": []
    }
    for step in workflow_steps:
        step_item = {
            "key": step.get("node_key", ""),
            "title": step.get("title", ""),
            "model_or_tool": step.get("model_or_tool", ""),
            "enabled": True,
            "draggable": True
        }
        steps_panel["items"].append(step_item)
    panels.append(steps_panel)

    return panels


def skill_rules_node(
    state: SkillRulesNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SkillRulesNodeOutput:
    """
    title: Skill规则与参考图
    desc: 从配置文件读取图片风格规则和工作流步骤，输出可编辑面板供运营在画布上修改
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取规则
    rules_cfg = _load_skill_rules()
    image_style: Dict[str, Any] = rules_cfg.get("image_style", {})
    workflow_steps: List[Dict[str, Any]] = rules_cfg.get("workflow_steps", [])

    # 2. 如果有运行时 override，合并覆盖
    if state.image_style_override:
        image_style.update(state.image_style_override)
    if state.workflow_steps_override:
        workflow_steps = state.workflow_steps_override

    # 3. 根据领域微调规则
    niche = state.niche
    must_have = list(image_style.get("must_have", []))
    if niche and f"领域：{niche}" not in must_have:
        must_have.append(f"领域：{niche}")
    image_style["must_have"] = must_have

    # 4. 构建 operator_control 可编辑面板
    edit_panels = _build_operator_panels(image_style, workflow_steps)

    # 5. 构建完整性规则
    consistency_rules: List[str] = list(image_style.get("consistency_rules", []))

    return SkillRulesNodeOutput(
        image_style_rules={
            "aspect_ratio": image_style.get("aspect_ratio", "3:4"),
            "style": image_style.get("style", "cartoon"),
            "reference_image_notes": image_style.get("reference_image_notes", []),
            "reference_image_urls": image_style.get("reference_image_urls", []),
            "must_have": image_style.get("must_have", []),
            "avoid": image_style.get("avoid", []),
            "consistency_rules": consistency_rules
        },
        workflow_steps=workflow_steps,
        operator_control_edit_panels=edit_panels,
        synced_skill_rules_cfg=image_style
    )
