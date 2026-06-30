"""
Skill规则子工作流 — 一致性规则节点
从配置文件读取一致性规则列表（支持 Jinja2 模板），运营可在画布上增删规则
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from jinja2 import Template

from graphs.state import ConsistencyRulesNodeInput, ConsistencyRulesNodeOutput


def _load_image_style() -> Dict[str, Any]:
    """从配置文件读取图片风格"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("image_style", {})


def _render_list(items: List[Any], context: Dict[str, Any]) -> List[str]:
    """渲染列表中的每个字符串为 Jinja2 模板"""
    result: List[str] = []
    for item in items:
        if isinstance(item, str) and "{{" in item:
            try:
                tpl = Template(item)
                rendered = tpl.render(**context)
                result.append(rendered)
            except Exception:
                result.append(str(item))
        else:
            result.append(str(item))
    return result


def consistency_rules_node(
    state: ConsistencyRulesNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ConsistencyRulesNodeOutput:
    """
    title: 一致性规则
    desc: 从配置读取一致性规则列表（模板变量从选题动态注入），运营可在画布上增删规则
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取当前一致性规则
    image_style = _load_image_style()
    rules_raw = image_style.get("consistency_rules", [])
    rules_raw_list: List[Any] = list(rules_raw) if isinstance(rules_raw, list) else []

    # 2. 构建模板渲染上下文
    render_ctx: Dict[str, Any] = {
        "niche": state.niche,
        "audience": state.audience,
    }
    consistency_rules: List[str] = _render_list(rules_raw_list, render_ctx)

    # 3. 如果有运行时 override，使用覆盖值
    consistency_rules_changed = False
    if state.image_style_override and isinstance(state.image_style_override, dict):
        override_rules = state.image_style_override.get("consistency_rules")
        if isinstance(override_rules, list):
            new_rules = _render_list(override_rules, render_ctx)
            if set(new_rules) != set(consistency_rules):
                consistency_rules_changed = True
            consistency_rules = new_rules

    return ConsistencyRulesNodeOutput(consistency_rules=consistency_rules, consistency_rules_changed=consistency_rules_changed)
