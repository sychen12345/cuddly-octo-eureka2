"""
节点6: OpenAI GPT5.5 文案 (openai_text_node)
──────────────────────────────────────────────
输入: selected_topic, audience, niche, openai_text_model, ... , openai_api_key
输出: openai_text_package
"""
import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    OpenAITextNodeInput,
    OpenAITextNodeOutput,
    EditablePrompt,
    SkillSubflow,
    TextDescriptionPackage,
    ModelRequest,
    TopicRecord,
)
from graphs.nodes.http_utils import call_openai

logger = logging.getLogger(__name__)


# ── 通用辅助 ──────────────────────────────────────────────
def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _find_prompt(prompts: List[EditablePrompt], key: str) -> str:
    for p in prompts:
        if p.key == key:
            return p.final_prompt
    return ""


# ── 节点函数 ──────────────────────────────────────────────
def openai_text_node(
    state: OpenAITextNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> OpenAITextNodeOutput:
    """
    title: OpenAI GPT5.5 文案
    desc: 调用 OpenAI API 生成小红书图文卡片文案，无 key 时降级为 dry_run
    integrations: OpenAI API
    """
    selected_topic: TopicRecord = _get(state, "selected_topic", TopicRecord(title="", audience="", hook="", demand_source="", differentiation=""))
    audience: str = _get(state, "audience", "")
    niche: str = _get(state, "niche", "")
    model: str = _get(state, "openai_text_model", "gpt-5.5")
    reasoning_mode: str = _get(state, "openai_reasoning_mode", "ultra_high")
    card_count: int = _get(state, "card_count", 6)
    aspect_ratio: str = _get(state, "image_aspect_ratio", "3:4")
    style: str = _get(state, "image_style", "cartoon")
    editable_prompts: List[EditablePrompt] = _get(state, "editable_prompts", [])
    skill_subflows: List[SkillSubflow] = _get(state, "skill_subflows", [])
    execute: bool = _get(state, "execute_model_calls", False)
    api_key: str = _get(state, "openai_api_key", "")
    constraints: List[str] = _get(state, "constraints", [])
    goal: str = _get(state, "goal", "")
    brand_voice: str = _get(state, "brand_voice", "")

    prompt_text: str = _find_prompt(editable_prompts, "openai_text_prompt")

    # 构建 system + user 消息
    system_msg: str = (
        "你是小红书内容创作专家。请严格按照以下格式输出 JSON：\n"
        '{"title_options": ["标题1", "标题2", "标题3"], '
        '"post_description": "正文描述", '
        '"card_script": ["第1页脚本", "第2页脚本", ...], '
        '"image_brief": "给生图模型的视觉说明"}'
    )
    user_msg: str = prompt_text or (
        f"领域：{niche}\n目标人群：{audience}\n选题：{selected_topic.title}\n"
        f"卡片数：{card_count}\n语气：{brand_voice}\n限制：{'; '.join(constraints)}\n"
        f"请生成标题选项、正文、每页卡片脚本和视觉说明。"
    )

    request: ModelRequest = ModelRequest(
        provider="openai",
        model=model,
        mode=reasoning_mode,
        endpoint="https://api.openai.com/v1/chat/completions",
        skill_key="openai_text_skill",
        prompt_key="openai_text_prompt",
        payload={"model": model, "temperature": 0.4, "max_tokens": 4096},
        dry_run=not execute or not api_key,
        status="planned",
    )

    title_options: List[str] = []
    post_description: str = ""
    card_script: List[str] = []
    image_brief: str = ""

    if execute and api_key:
        try:
            resp: Dict[str, Any] = call_openai(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.4,
                max_tokens=4096,
                reasoning_effort=reasoning_mode if reasoning_mode else None,
            )
            content: str = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            parsed: Dict[str, Any] = json.loads(content) if content.startswith("{") else {}
            title_options = parsed.get("title_options", [selected_topic.title])
            post_description = parsed.get("post_description", "")
            card_script = parsed.get("card_script", [])
            image_brief = parsed.get("image_brief", "")
            request.status = "completed"
        except Exception as exc:
            logger.error("OpenAI API 调用失败: %s", exc)
            request.status = "failed"
    else:
        # dry_run: 用选题信息构建降级内容
        title_options = [selected_topic.title]
        post_description = f"关于「{selected_topic.title}」的小红书图文卡片正文。"
        card_script = [f"第{i+1}页：{selected_topic.outline[i] if i < len(selected_topic.outline) else '待补充'}" for i in range(card_count)]
        image_brief = f"{aspect_ratio} {style}风格；领域：{niche}；选题：{selected_topic.title}"
        request.status = "dry_run"

    text_package: TextDescriptionPackage = TextDescriptionPackage(
        provider="openai",
        model=model,
        reasoning_mode=reasoning_mode,
        request=request,
        title_options=title_options,
        post_description=post_description,
        card_script=card_script,
        image_brief=image_brief,
        status=request.status,
    )

    return OpenAITextNodeOutput(openai_text_package=text_package)
