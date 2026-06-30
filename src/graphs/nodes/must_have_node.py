"""
图片制作技能 — 必备元素节点
运营在这里维护每张图必须保留的画面元素和信息。
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from jinja2 import Template

from graphs.state import MustHaveNodeInput, MustHaveNodeOutput


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


def must_have_node(
    state: MustHaveNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> MustHaveNodeOutput:
    """
    title: 图片制作技能：必备元素
    desc: 确认每张图必须出现的元素，运营可在画布上增删标签
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取当前必选项
    image_style = _load_image_style()
    must_have_raw = image_style.get("must_have", [])
    must_have_raw_list: List[Any] = list(must_have_raw) if isinstance(must_have_raw, list) else []

    # 2. 构建模板渲染上下文
    render_ctx: Dict[str, Any] = {
        "niche": state.niche,
        "audience": state.audience,
    }
    must_have: List[str] = _render_list(must_have_raw_list, render_ctx)

    # 3. 如果有运行时 override，使用覆盖值
    must_have_changed = False
    if state.image_style_override and isinstance(state.image_style_override, dict):
        override_must = state.image_style_override.get("must_have")
        if isinstance(override_must, list):
            new_must = _render_list(override_must, render_ctx)
            if set(new_must) != set(must_have):
                must_have_changed = True
            must_have = new_must

    return MustHaveNodeOutput(must_have=must_have, must_have_changed=must_have_changed)
