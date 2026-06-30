"""
Skill子流程子工作流 — Grok步骤配置节点
从配置文件读取 Grok 套图子流程定义，Jinja2 模板渲染提示词，运营可编辑
"""
import os
import json
import copy
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from jinja2 import Template

from graphs.state import GrokStepsNodeInput, GrokStepsNodeOutput, EditablePrompt


def _load_subflows() -> List[Dict[str, Any]]:
    """从配置文件读取子流程列表"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_subflows.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("subflows", [])


def _render_grok_prompts(
    steps: List[Dict[str, Any]],
    render_ctx: Dict[str, Any],
) -> List[EditablePrompt]:
    """渲染 Grok 相关步骤的提示词（从配置 default_prompt 用 Jinja2 渲染）"""
    prompts: List[EditablePrompt] = []
    for step in steps:
        prompt_key = step.get("prompt_key", "")
        if "grok" not in prompt_key:
            continue
        # 从配置读取 default_prompt，用 Jinja2 渲染
        default_prompt_raw = step.get("default_prompt", "")
        try:
            tpl = Template(default_prompt_raw)
            dp = tpl.render(**render_ctx)
        except Exception:
            dp = default_prompt_raw

        if "grok_plan_prompt" in prompt_key:
            title = "规划套图视觉方向"
            target = "grok-imagine-image-quality"
        elif "grok_image_prompt" in prompt_key:
            title = "Grok 生图提示词"
            target = "grok-imagine-image-quality"
        else:
            title = "Grok 步骤"
            target = "grok-imagine-image-quality"

        prompts.append(EditablePrompt(
            key=prompt_key,
            title=title,
            target_model=target,
            default_prompt=dp,
            final_prompt=dp,
            editable=True
        ))
    return prompts


def grok_steps_node(
    state: GrokStepsNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> GrokStepsNodeOutput:
    """
    title: Grok步骤配置
    desc: 从配置读取 Grok 套图子流程定义，Jinja2 模板渲染提示词（niche/audience/brand_voice/topic 动态注入），运营可编辑
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取子流程
    subflows = _load_subflows()

    # 2. 查找 Grok 子流程
    grok_subflow: Dict[str, Any] = {}
    for sf in subflows:
        if sf.get("skill_key") == "grok_image_skill":
            grok_subflow = copy.deepcopy(sf)
            break

    # 3. 如果有 override，合并覆盖并检测变更
    grok_steps_changed = False
    if state.skill_subflows_override and isinstance(state.skill_subflows_override, list):
        for sf in state.skill_subflows_override:
            if isinstance(sf, dict) and sf.get("skill_key") == "grok_image_skill":
                if json.dumps(sf, sort_keys=True, ensure_ascii=False) != json.dumps(grok_subflow, sort_keys=True, ensure_ascii=False):
                    grok_steps_changed = True
                grok_subflow = copy.deepcopy(sf)
                break

    # 4. 构建 Jinja2 渲染上下文
    selected_topic_title = ""
    if state.selected_topic is not None:
        selected_topic_title = state.selected_topic.title

    render_ctx: Dict[str, Any] = {
        "niche": state.niche,
        "audience": state.audience,
        "brand_voice": state.brand_voice,
        "selected_topic_title": selected_topic_title,
    }

    # 5. 渲染提示词
    steps = grok_subflow.get("steps", [])
    grok_prompts = _render_grok_prompts(steps, render_ctx)

    # 6. 将渲染后的提示词写回步骤
    for step in steps:
        prompt_key = step.get("prompt_key", "")
        for prompt in grok_prompts:
            if prompt.key == prompt_key:
                step["default_prompt"] = prompt.default_prompt
                step["final_prompt"] = prompt.final_prompt
                break

    return GrokStepsNodeOutput(
        grok_subflow=grok_subflow,
        grok_prompts=grok_prompts,
        grok_steps_changed=grok_steps_changed
    )
