"""
Skill规则子工作流 — 必选项配置节点
从配置文件读取必选项列表，运营可在画布上增删标签
"""
import os
import json
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import MustHaveNodeInput, MustHaveNodeOutput


def _load_image_style() -> Dict[str, Any]:
    """从配置文件读取图片风格"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_rules.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("image_style", {})


def must_have_node(
    state: MustHaveNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> MustHaveNodeOutput:
    """
    title: 必选项配置
    desc: 从配置读取必须包含的元素列表，运营可在画布上增删标签
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取当前必选项
    image_style = _load_image_style()
    must_have_raw = image_style.get("must_have", [])
    must_have: List[str] = list(must_have_raw) if isinstance(must_have_raw, list) else []

    # 2. 如果有运行时 override，使用覆盖值
    if state.image_style_override and isinstance(state.image_style_override, dict):
        override_must = state.image_style_override.get("must_have")
        if isinstance(override_must, list):
            must_have = [str(item) for item in override_must]

    # 3. 根据赛道补充领域上下文
    niche = state.niche
    if niche and f"领域：{niche}" not in must_have:
        must_have.append(f"领域：{niche}")

    return MustHaveNodeOutput(must_have=must_have)
