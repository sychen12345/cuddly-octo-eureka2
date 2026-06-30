"""
图片制作技能 — 比例选择节点
为当前小红书套图选择画面比例，运营可以在画布上切换 3:4/1:1/16:9 等。
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import AspectRatioNodeInput, AspectRatioNodeOutput


def _load_image_style() -> Dict[str, Any]:
    """从配置文件读取图片风格"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("image_style", {})


def aspect_ratio_node(
    state: AspectRatioNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> AspectRatioNodeOutput:
    """
    title: 图片制作技能：定比例
    desc: 选择小红书图片比例，例如 3:4、1:1 或 16:9
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取当前比例
    image_style = _load_image_style()
    current_ratio: str = image_style.get("aspect_ratio", "3:4")

    # 2. 如果有运行时 override，使用覆盖值
    ratio_changed = False
    if state.image_style_override and isinstance(state.image_style_override, dict):
        override_ratio = state.image_style_override.get("aspect_ratio")
        if isinstance(override_ratio, str) and override_ratio:
            if override_ratio != current_ratio:
                ratio_changed = True
            current_ratio = override_ratio

    return AspectRatioNodeOutput(aspect_ratio=current_ratio, ratio_changed=ratio_changed)
