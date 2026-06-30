"""
Skill规则子工作流 — 风格选择节点
从配置文件读取视觉风格，运营可在画布上切换 cartoon/flat/realistic 等
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import StyleSelectNodeInput, StyleSelectNodeOutput


def _load_image_style() -> Dict[str, Any]:
    """从配置文件读取图片风格"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("image_style", {})


def style_select_node(
    state: StyleSelectNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> StyleSelectNodeOutput:
    """
    title: 风格选择
    desc: 从配置读取视觉风格（cartoon/flat/realistic等），运营可在画布上切换
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取当前风格
    image_style = _load_image_style()
    current_style: str = image_style.get("style", "cartoon")

    # 2. 如果有运行时 override，使用覆盖值
    if state.image_style_override and isinstance(state.image_style_override, dict):
        override_style = state.image_style_override.get("style")
        if isinstance(override_style, str) and override_style:
            current_style = override_style

    return StyleSelectNodeOutput(style=current_style)
