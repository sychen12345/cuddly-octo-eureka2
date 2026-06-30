"""
Skill 子流程节点
从 config/skill_subflows.json 读取子流程定义，步骤可拖拽排序
运营可在画布上：启用/禁用步骤、调整步骤顺序、编辑提示词
修改后通过 override 参数传入，自动同步回配置文件
"""
import os
import json
import copy
from typing import List, Dict, Optional, Any

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import SkillSubflowNodeInput, SkillSubflowNodeOutput


def _load_skill_subflows() -> Dict[str, Any]:
    """从配置文件读取 skill 子流程定义"""
    cfg_path = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), "assets", "skill_config", "skill_subflows.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_subflow_panels(
    subflows: List[Dict[str, Any]],
    niche: str,
    audience: str,
    selected_topic_title: str,
    brand_voice: str
) -> List[Dict[str, Any]]:
    """构建 operator_control 的子流程编辑面板"""
    panels: List[Dict[str, Any]] = []

    for sf in subflows:
        # 渲染每个步骤的 default_prompt 和 final_prompt
        steps_with_prompts = []
        for step in sf.get("steps", []):
            rendered_step = copy.deepcopy(step)
            prompt_key = step.get("prompt_key", "")

            if "openai_text_prompt" in prompt_key:
                rendered_step["default_prompt"] = (
                    f"你是小红书内容创作专家，擅长按「{brand_voice}」语气写作。\n"
                    f"领域：{niche}\n目标人群：{audience}\n"
                    f"选题：{selected_topic_title}\n"
                    f"请生成图文卡片的标题选项、正文、每页脚本和视觉说明。"
                )
            elif "openai_generate_prompt" in prompt_key:
                rendered_step["default_prompt"] = (
                    f"根据分析结果，按「{brand_voice}」语气生成"
                    f"{audience}的图文卡片正文和每页脚本。"
                )
            elif "grok_plan_prompt" in prompt_key:
                rendered_step["default_prompt"] = (
                    f"为选题「{selected_topic_title}」规划 3:4 cartoon 风格套图。"
                )
            elif "grok_image_prompt" in prompt_key:
                rendered_step["default_prompt"] = (
                    f"生成小红书 3:4 卡通风格图文卡片套图。\n"
                    f"选题：{selected_topic_title}\n"
                    f"风格：卡通、短句、层级清楚、留白充足。\n"
                    f"每页一个核心信息，配色统一。"
                )

            rendered_step["final_prompt"] = rendered_step.get("default_prompt", "")
            steps_with_prompts.append(rendered_step)

        panel = {
            "key": sf.get("skill_key", ""),
            "title": sf.get("title", ""),
            "panel_type": "subflow",
            "editable": sf.get("editable", True),
            "content": {
                "skill_key": sf.get("skill_key", ""),
                "title": sf.get("title", ""),
                "provider": sf.get("provider", ""),
                "model": sf.get("model", ""),
                "mode": sf.get("mode", ""),
                "endpoint": sf.get("endpoint", ""),
                "description": sf.get("description", ""),
                "editable": sf.get("editable", True),
                "steps": steps_with_prompts,
                "status": "ready"
            }
        }
        panels.append(panel)

    return panels


def _build_prompt_panels(
    subflows: List[Dict[str, Any]],
    niche: str,
    audience: str,
    selected_topic_title: str,
    brand_voice: str
) -> List[Dict[str, Any]]:
    """构建可编辑提示词面板"""
    panels: List[Dict[str, Any]] = []

    for sf in subflows:
        for step in sf.get("steps", []):
            prompt_key = step.get("prompt_key", "")
            if not prompt_key:
                continue

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
            elif "grok_plan_prompt" in prompt_key:
                dp = f"为选题「{selected_topic_title}」规划 3:4 cartoon 风格套图。"
                title = "规划套图视觉方向"
                target = "grok-imagine-image-quality"
            elif "grok_image_prompt" in prompt_key:
                dp = (
                    f"生成小红书 3:4 卡通风格图文卡片套图。\n"
                    f"选题：{selected_topic_title}\n"
                    f"风格：卡通、短句、层级清楚、留白充足。\n"
                    f"每页一个核心信息，配色统一。"
                )
                title = "Grok 生图提示词"
                target = "grok-imagine-image-quality"
            else:
                continue

            panels.append({
                "key": prompt_key,
                "title": title,
                "panel_type": "prompt",
                "editable": True,
                "content": {
                    "key": prompt_key,
                    "title": title,
                    "target_model": target,
                    "default_prompt": dp,
                    "final_prompt": dp,
                    "editable": True
                }
            })

    return panels


def skill_subflow_node(
    state: SkillSubflowNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SkillSubflowNodeOutput:
    """
    title: OpenAI/Grok Skill 子流程
    desc: 从配置文件读取子流程定义，步骤可拖拽排序，运营可编辑提示词和调整顺序
    integrations:
    """
    ctx = runtime.context

    # 1. 从配置文件读取子流程
    subflows_cfg = _load_skill_subflows()
    subflows: List[Dict[str, Any]] = subflows_cfg.get("subflows", [])

    # 2. 如果有运行时 override，合并覆盖
    if state.skill_subflows_override:
        subflows = state.skill_subflows_override

    # 3. 获取上下文信息
    niche = state.niche
    audience = state.audience
    selected_topic_title = ""
    if isinstance(state.selected_topic, dict):
        selected_topic_title = state.selected_topic.get("title", "")
    brand_voice = state.brand_voice

    # 4. 构建子流程编辑面板
    subflow_panels = _build_subflow_panels(
        subflows, niche, audience, selected_topic_title, brand_voice
    )

    # 5. 构建提示词编辑面板
    prompt_panels = _build_prompt_panels(
        subflows, niche, audience, selected_topic_title, brand_voice
    )

    # 6. 构建完整子流程输出（含渲染后的提示词）
    rendered_subflows = []
    for panel in subflow_panels:
        rendered_subflows.append(panel["content"])

    # 7. 构建可编辑提示词输出
    editable_prompts = []
    for panel in prompt_panels:
        editable_prompts.append(panel["content"])

    return SkillSubflowNodeOutput(
        skill_subflows=rendered_subflows,
        editable_prompts=editable_prompts,
        operator_control_subflow_panels=subflow_panels,
        operator_control_prompt_panels=prompt_panels,
        synced_skill_subflows_cfg=subflows
    )
