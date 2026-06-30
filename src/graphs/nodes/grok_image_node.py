"""节点 7/8 — Grok Expert 套图 (grok_image)"""

import json, os
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    EditablePrompt, GrokImageItem, GrokImageSet, ImageStyleRules, SkillSubflowDef, TopicRecord,
    GrokImageNodeInput, GrokImageNodeOutput,
)
from graphs.nodes.http_utils import call_grok_image


def _find_prompt(prompts: List[EditablePrompt], key: str) -> str:
    for p in prompts:
        if p.key == key:
            return p.final_prompt or p.default_prompt
    return ""


def _build_image_items(
    topic_title: str,
    card_script: List[str],
    base_prompt: str,
    style_rules: Optional[ImageStyleRules],
    execute: bool,
    api_key: str,
) -> List[GrokImageItem]:
    items: List[GrokImageItem] = []
    for idx, script in enumerate(card_script, 1):
        prompt_text = f"{base_prompt}；第{idx}页；标题：{script}；小红书图文卡片；短句；层级清楚"
        image_url = ""
        status = "dry_run"
        request_body: Dict[str, Any] = {
            "provider": "grok", "model": "grok-imagine-image-quality", "mode": "Expert",
            "endpoint": "https://api.x.ai/v1/images/generations",
            "skill_key": "grok_image_skill", "prompt_key": "grok_image_prompt",
            "payload": {"model": "grok-imagine-image-quality", "n": 1, "size": "1024x1365", "quality": "hd"},
            "dry_run": not execute, "status": "planned" if not execute else "pending",
        }

        if execute and api_key:
            try:
                image_url = call_grok_image(api_key, prompt=prompt_text)
                status = "done"
                request_body["status"] = "done"
            except Exception:
                status = "failed"
                request_body["status"] = "failed"

        items.append(GrokImageItem(
            page=idx,
            headline=script,
            prompt=prompt_text,
            aspect_ratio=style_rules.aspect_ratio if style_rules else "3:4",
            style=style_rules.style if style_rules else "cartoon",
            request=request_body,
            image_url=image_url,
            status=status,
        ))
    return items


def grok_image_node(
    state: GrokImageNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> GrokImageNodeOutput:
    """
    title: Grok Expert 套图
    desc: 调用 Grok API 生成小红书图文卡片套图（支持 dry_run 和真实调用）
    integrations: Grok
    """
    ctx = runtime.context

    topic_title = state.selected_topic.title if state.selected_topic else state.niche
    base_prompt = _find_prompt(state.editable_prompts, "grok_image_prompt")
    if not base_prompt:
        base_prompt = f"生成小红书 3:4 卡通风格图文卡片套图。选题：{topic_title}"

    # 从 openai_text 的结果中取卡片脚本（如果有）
    card_script: List[str] = []
    for subflow in state.skill_subflows:
        if subflow.skill_key == "openai_text_skill":
            for step in subflow.steps:
                if step.output_keys and "card_script" in step.output_keys:
                    card_script = [f"第{i}页：{topic_title}" for i in range(1, 7)]

    if not card_script:
        card_script = [f"第{i}页：{topic_title}" for i in range(1, 7)]

    execute = state.execute_model_calls and bool(state.grok_api_key)
    images = _build_image_items(
        topic_title, card_script, base_prompt,
        state.image_style_rules, execute, state.grok_api_key,
    )

    consistency = state.image_style_rules.consistency_rules if state.image_style_rules else []

    image_set = GrokImageSet(
        provider="grok",
        model="grok-imagine-image-quality",
        mode="Expert",
        aspect_ratio=state.image_style_rules.aspect_ratio if state.image_style_rules else "3:4",
        style=state.image_style_rules.style if state.image_style_rules else "cartoon",
        images=images,
        consistency_rules=consistency,
        status="done" if execute else "dry_run",
    )

    return GrokImageNodeOutput(grok_image_set=image_set)
