"""OpenAI GPT5.5 超高推理文案节点."""
from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any, Dict, List

try:
    from langchain_core.runnables import RunnableConfig
except ImportError:  # pragma: no cover
    RunnableConfig = Dict[str, Any]  # type: ignore

try:
    from langgraph.runtime import Runtime
except ImportError:  # pragma: no cover
    Runtime = Any  # type: ignore

try:
    from coze_coding_utils.runtime_ctx.context import Context
except ImportError:  # pragma: no cover
    Context = Any  # type: ignore

try:
    from graphs.state import ModelRequest, OpenAITextNodeInput, OpenAITextNodeOutput, TextDescriptionPackage
except ImportError:
    from .state import ModelRequest, OpenAITextNodeInput, OpenAITextNodeOutput, TextDescriptionPackage

try:
    from graphs.nodes.http_utils import ModelCallError, post_json, redact_secrets
except ImportError:
    from .http_utils import ModelCallError, post_json, redact_secrets


def _get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _dump(model: Any) -> Dict[str, Any]:
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return {}


def _prompt(state: Any, key: str) -> str:
    for prompt in _get(state, "editable_prompts", []) or []:
        data = _dump(prompt)
        if data.get("key") == key:
            return str(data.get("final_prompt", "")).strip()
    return ""


def _selected_topic(state: Any) -> Dict[str, Any]:
    return _dump(_get(state, "selected_topic", {}))


def _card_script(title: str, audience: str, count: int) -> List[str]:
    count = max(3, min(count or 6, 8))
    pages = [
        f"封面：{title}",
        f"痛点：{audience}最容易卡在第一步，不是不会努力，而是没看清需求。",
        "证据：先看评论区反复出现的问题，再看对标内容为什么被收藏。",
        "方法：找对标结构、挖评论需求、只做一个可验证的小选题。",
        "行动：今天先整理 5 条评论和 3 个对标标题，别急着做大项目。",
        "收口：收藏这套流程，下次直接用评论原话反推选题。",
        "复盘：发布后看收藏、评论追问和私信关键词，再决定下一篇。",
        "沉淀：把标题、需求来源、证据、差异化写回选题库。",
    ]
    return pages[:count]


def _api_reasoning_effort(reasoning_mode: str) -> str:
    normalized = reasoning_mode.strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "ultra": "xhigh",
        "ultra_high": "xhigh",
        "very_high": "xhigh",
        "extra_high": "xhigh",
        "x_high": "xhigh",
        "xhigh": "xhigh",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "minimal": "minimal",
        "none": "none",
    }
    return mapping.get(normalized, "xhigh")


def _response_schema(card_count: int) -> Dict[str, Any]:
    count = max(3, min(card_count or 6, 8))
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["title_options", "card_script", "post_description", "image_brief"],
        "properties": {
            "title_options": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {"type": "string"},
            },
            "card_script": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {"type": "string"},
            },
            "post_description": {"type": "string"},
            "image_brief": {"type": "string"},
        },
    }


def _model_input(state: Any, prompt: str, topic: Dict[str, Any], card_count: int) -> str:
    context = {
        "niche": _get(state, "niche", ""),
        "audience": _get(state, "audience", ""),
        "brand_voice": _get(state, "brand_voice", ""),
        "goal": _get(state, "goal", ""),
        "selected_topic": topic,
        "constraints": _get(state, "constraints", []),
        "card_count": card_count,
        "image_aspect_ratio": _get(state, "image_aspect_ratio", "3:4"),
        "image_style": _get(state, "image_style", "cartoon"),
    }
    return (
        f"{prompt}\n\n"
        "请为小红书图文卡片生成文案。必须只返回 JSON，不要 Markdown。"
        "card_script 每一项使用「短标题：正文」格式。\n\n"
        f"上下文：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def _extract_output_text(response: Dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: List[str] = []
    for item in response.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text") or content.get("refusal")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def _parse_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("OpenAI response JSON must be an object")
    return parsed


def _as_string_list(value: Any, fallback: List[str], limit: int | None = None) -> List[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = []
    if not items:
        items = fallback
    if limit is not None:
        items = items[:limit]
    return items


def _build_payload(model: str, api_effort: str, model_input: str, card_count: int) -> Dict[str, Any]:
    return {
        "model": model,
        "input": model_input,
        "reasoning": {"effort": api_effort},
        "text": {
            "format": {
                "type": "json_schema",
                "name": "xhs_text_package",
                "strict": True,
                "schema": _response_schema(card_count),
            },
            "verbosity": "medium",
        },
        "store": False,
    }


def openai_text_node(
    state: OpenAITextNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> OpenAITextNodeOutput:
    """
    title: OpenAI GPT5.5 超高推理文案
    desc: 调用/规划 OpenAI 生成小红书文字描述和给 Grok 的视觉 brief
    integrations:
    """
    topic = _selected_topic(state)
    title = str(topic.get("title", "")).strip()
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    niche = str(_get(state, "niche", "")).strip()
    model = str(_get(state, "openai_text_model", "gpt-5.5")).strip() or "gpt-5.5"
    reasoning_mode = str(_get(state, "openai_reasoning_mode", "ultra_high")).strip() or "ultra_high"
    api_effort = _api_reasoning_effort(reasoning_mode)
    card_count = max(3, min(int(_get(state, "card_count", 6) or 6), 8))
    prompt = _prompt(state, "openai_text_description")
    execute_model_calls = bool(_get(state, "execute_model_calls", False))

    title_options = [
        title,
        f"{audience}做「{niche}」，先别急着发笔记",
        f"评论区问爆的「{niche}」问题，我拆成 3 步",
        f"想做「{niche}」，先存这份验证清单",
    ]
    card_script = _card_script(title, audience, card_count)
    post_description = (
        f"这组选题来自「{topic.get('demand_source', '用户需求')}」。"
        f"先用评论和对标内容确认需求，再让 OpenAI 生成文字描述，最后交给 Grok 生成 3:4 卡通套图。"
        "发布前补齐真实截图或案例，避免把猜测写成结论。"
    )
    image_brief = (
        f"为小红书选题「{title}」生成统一卡通套图。主角面向{audience}，"
        "画面要有清晰层级、少量中文标签、统一色板和 3:4 竖版构图。"
    )

    model_input = _model_input(state, prompt, topic, card_count)
    request = ModelRequest(
        provider="openai",
        model=model,
        mode=f"reasoning={reasoning_mode}; api_effort={api_effort}",
        endpoint="https://api.openai.com/v1/responses",
        prompt_key="openai_text_description",
        payload=_build_payload(model, api_effort, model_input, card_count),
        dry_run=not execute_model_calls,
        status="dry_run" if not execute_model_calls else "ready",
    )
    status = "dry_run"
    if execute_model_calls:
        api_key = str(_get(state, "openai_api_key", "")).strip()
        try:
            response = post_json(request.endpoint, api_key, request.payload)
            parsed = _parse_json_object(_extract_output_text(response))
            title_options = _as_string_list(parsed.get("title_options"), title_options, 5)
            card_script = _as_string_list(parsed.get("card_script"), card_script, max(3, min(card_count, 8)))
            post_description = str(parsed.get("post_description") or post_description).strip()
            image_brief = str(parsed.get("image_brief") or image_brief).strip()
            status = "completed"
            request.status = "completed"
        except (ModelCallError, JSONDecodeError, ValueError) as error:
            safe_message = redact_secrets(error, [api_key])[:180]
            status = "failed"
            request.status = f"failed: {safe_message}"

    package = TextDescriptionPackage(
        provider="openai",
        model=model,
        reasoning_mode=reasoning_mode,
        request=request,
        title_options=title_options,
        post_description=post_description,
        card_script=card_script,
        image_brief=image_brief,
        status=status,
    )
    return OpenAITextNodeOutput(openai_text_package=package)
