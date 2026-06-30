"""
Skill规则子工作流 — 禁选项配置节点
从配置文件读取禁选项列表，运营可在画布上增删标签
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import AvoidNodeInput, AvoidNodeOutput


def _load_image_style() -> Dict[str, Any]:
    """从配置文件读取图片风格"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("image_style", {})


def avoid_node(
    state: AvoidNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> AvoidNodeOutput:
    """
    title: 禁选项配置
    desc: 从配置读取需要避免的元素列表，运营可在画布上增删标签
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取当前禁选项
    image_style = _load_image_style()
    avoid_raw = image_style.get("avoid", [])
    avoid: List[str] = list(avoid_raw) if isinstance(avoid_raw, list) else []

    # 2. 如果有运行时 override，使用覆盖值
    avoid_changed = False
    if state.image_style_override and isinstance(state.image_style_override, dict):
        override_avoid = state.image_style_override.get("avoid")
        if isinstance(override_avoid, list):
            new_avoid = [str(item) for item in override_avoid]
            if set(new_avoid) != set(avoid):
                avoid_changed = True
            avoid = new_avoid

    return AvoidNodeOutput(avoid=avoid, avoid_changed=avoid_changed)
