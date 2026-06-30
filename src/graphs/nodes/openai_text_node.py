"""AI生成小红书文案节点"""

import json, os
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    EditablePrompt, OpenAITextPackage, SkillSubflowDef, TopicRecord,
    OpenAITextNodeInput, OpenAITextNodeOutput,
)
from graphs.nodes.http_utils import call_openai_chat


def _find_prompt(prompts: List[EditablePrompt], key: str) -> str:
    for p in prompts:
        if p.key == key:
            return p.final_prompt or p.default_prompt
    return ""


def _dry_run_text(state: OpenAITextNodeInput, up: str) -> OpenAITextPackage:
    topic_title = state.selected_topic.title if state.selected_topic else state.niche
    return OpenAITextPackage(
        provider="openai",
        model="gpt-5.5",
        reasoning_mode="ultra_high",
        request={"provider": "openai", "model": "gpt-5.5", "mode": "ultra_high",
                 "endpoint": "https://api.openai.com/v1/chat/completions",
                 "skill_key": "openai_text_skill", "prompt_key": "openai_text_prompt",
                 "payload": {"model": "gpt-5.5", "temperature": 0.4, "max_tokens": 4096},
                 "dry_run": True, "status": "dry_run"},
        title_options=[topic_title],
        post_description=f"关于「{topic_title}」的小红书图文卡片正文。",
        card_script=[f"第{i}页：待补充" for i in range(1, 7)],
        image_brief=f"3:4 cartoon风格；领域：{state.niche}；选题：{topic_title}",
        status="dry_run",
    )


def _real_call_text(state: OpenAITextNodeInput, up: str) -> OpenAITextPackage:
    topic_title = state.selected_topic.title if state.selected_topic else state.niche
    sp = f"你是小红书内容创作专家，擅长按「{state.brand_voice}」语气写作。领域：{state.niche}，目标人群：{state.audience}。"
    raw = call_openai_chat(state.openai_api_key, system_prompt=sp, user_prompt=up)
    try:
        parsed = json.loads(raw)
        return OpenAITextPackage(
            provider="openai", model="gpt-5.5", reasoning_mode="ultra_high",
            request={"status": "done"},
            title_options=parsed.get("title_options", [topic_title]),
            post_description=parsed.get("post_description", ""),
            card_script=parsed.get("card_script", []),
            image_brief=parsed.get("image_brief", ""),
            status="done",
        )
    except (json.JSONDecodeError, TypeError):
        return _dry_run_text(state, up)


def openai_text_node(
    state: OpenAITextNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> OpenAITextNodeOutput:
    """
    title: AI生成小红书文案
    desc: 根据运营确认的文案技能生成标题、正文、每页脚本和视觉说明
    integrations: OpenAI
    """
    ctx = runtime.context
    up = _find_prompt(state.editable_prompts, "openai_text_prompt")

    if state.execute_model_calls and state.openai_api_key:
        pkg = _real_call_text(state, up)
    else:
        pkg = _dry_run_text(state, up)

    return OpenAITextNodeOutput(openai_text_package=pkg)
