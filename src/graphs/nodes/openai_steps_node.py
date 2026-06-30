"""
文案生成技能 — 步骤展开节点
把文案生成技能展开成运营可查看、可拖动、可交给 AI 分析的步骤。
"""
import os
import json
import copy
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from jinja2 import Template

from graphs.state import OpenAIStepsNodeInput, OpenAIStepsNodeOutput, EditablePrompt


def _load_subflows() -> List[Dict[str, Any]]:
    """从配置文件读取子流程列表"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_subflows.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("subflows", [])


def _render_openai_prompts(
    steps: List[Dict[str, Any]],
    render_ctx: Dict[str, Any],
) -> List[EditablePrompt]:
    """渲染文案技能步骤提示词。"""
    prompts: List[EditablePrompt] = []
    for step in steps:
        prompt_key = step.get("prompt_key", "")
        if "openai" not in prompt_key:
            continue
        # 从配置读取 default_prompt，用 Jinja2 渲染
        default_prompt_raw = step.get("default_prompt", "")
        try:
            tpl = Template(default_prompt_raw)
            dp = tpl.render(**render_ctx)
        except Exception:
            dp = default_prompt_raw

        if "openai_text_prompt" in prompt_key:
            title = "文案生成方向"
            target = "gpt-5.5"
        elif "openai_generate_prompt" in prompt_key:
            title = "生成可发布的图文文案"
            target = "gpt-5.5"
        else:
            title = "文案技能步骤"
            target = "gpt-5.5"

        prompts.append(EditablePrompt(
            key=prompt_key,
            title=title,
            target_model=target,
            default_prompt=dp,
            final_prompt=dp,
            editable=True
        ))
    return prompts


def openai_steps_node(
    state: OpenAIStepsNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> OpenAIStepsNodeOutput:
    """
    title: 文案技能：拆步骤
    desc: 展开文案生成技能，运营可让 AI 分析或调整每个步骤
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取子流程
    subflows = _load_subflows()

    # 2. 查找 OpenAI 子流程
    openai_subflow: Dict[str, Any] = {}
    for sf in subflows:
        if sf.get("skill_key") == "openai_text_skill":
            openai_subflow = copy.deepcopy(sf)
            break

    # 3. 如果有 override，合并覆盖并检测变更
    openai_steps_changed = False
    if state.skill_subflows_override and isinstance(state.skill_subflows_override, list):
        for sf in state.skill_subflows_override:
            if isinstance(sf, dict) and sf.get("skill_key") == "openai_text_skill":
                if json.dumps(sf, sort_keys=True, ensure_ascii=False) != json.dumps(openai_subflow, sort_keys=True, ensure_ascii=False):
                    openai_steps_changed = True
                openai_subflow = copy.deepcopy(sf)
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
    steps = openai_subflow.get("steps", [])
    openai_prompts = _render_openai_prompts(steps, render_ctx)

    # 6. 将渲染后的提示词写回步骤
    for step in steps:
        prompt_key = step.get("prompt_key", "")
        for prompt in openai_prompts:
            if prompt.key == prompt_key:
                step["default_prompt"] = prompt.default_prompt
                step["final_prompt"] = prompt.final_prompt
                break

    return OpenAIStepsNodeOutput(
        openai_subflow=openai_subflow,
        openai_prompts=openai_prompts,
        openai_steps_changed=openai_steps_changed
    )
