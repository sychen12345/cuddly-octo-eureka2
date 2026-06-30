"""
Skill子流程子工作流 — OpenAI步骤配置节点
从配置文件读取 OpenAI 文案子流程定义，渲染提示词，运营可编辑
"""
import os
import json
import copy
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import OpenAIStepsNodeInput, OpenAIStepsNodeOutput, EditablePrompt


def _load_subflows() -> List[Dict[str, Any]]:
    """从配置文件读取子流程列表"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_subflows.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("subflows", [])


def _render_openai_prompts(
    steps: List[Dict[str, Any]],
    niche: str,
    audience: str,
    brand_voice: str,
    selected_topic_title: str
) -> List[EditablePrompt]:
    """渲染 OpenAI 相关步骤的提示词"""
    prompts: List[EditablePrompt] = []
    for step in steps:
        prompt_key = step.get("prompt_key", "")
        if "openai_text_prompt" in prompt_key:
            dp = (
                f"你是小红书内容创作专家，擅长按「{brand_voice}」语气写作。\n"
                f"领域：{niche}\n目标人群：{audience}\n"
                f"选题：{selected_topic_title}\n"
                f"请生成图文卡片的标题选项、正文、每页脚本和视觉说明。"
            )
            title = "OpenAI 文案提示词"
            target = "gpt-5.5"
        elif "openai_generate_prompt" in prompt_key:
            dp = (
                f"根据分析结果，按「{brand_voice}」语气生成"
                f"{audience}的图文卡片正文和每页脚本。"
            )
            title = "生成正文与卡片脚本"
            target = "gpt-5.5"
        else:
            continue
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
    title: OpenAI步骤配置
    desc: 从配置读取 OpenAI 文案子流程定义并渲染提示词，运营可编辑
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

    # 3. 如果有 override，合并覆盖
    if state.skill_subflows_override and isinstance(state.skill_subflows_override, list):
        for sf in state.skill_subflows_override:
            if isinstance(sf, dict) and sf.get("skill_key") == "openai_text_skill":
                openai_subflow = copy.deepcopy(sf)
                break

    # 4. 获取上下文信息
    niche = state.niche
    audience = state.audience
    brand_voice = state.brand_voice
    selected_topic_title = ""
    if state.selected_topic is not None:
        selected_topic_title = state.selected_topic.title

    # 5. 渲染提示词
    steps = openai_subflow.get("steps", [])
    openai_prompts = _render_openai_prompts(
        steps, niche, audience, brand_voice, selected_topic_title
    )

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
        openai_prompts=openai_prompts
    )
