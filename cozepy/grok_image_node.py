"""Grok Expert 3:4 卡通套图节点."""
from __future__ import annotations

from typing import Any, Dict

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
    from graphs.state import (
        GrokImageNodeInput,
        GrokImageNodeOutput,
        ImageGenerationItem,
        ImageSetPackage,
        ModelRequest,
    )
except ImportError:
    from .state import (
        GrokImageNodeInput,
        GrokImageNodeOutput,
        ImageGenerationItem,
        ImageSetPackage,
        ModelRequest,
    )

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


def _extract_image_url(response: Dict[str, Any]) -> str:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        return ""
    first = data[0]
    if not isinstance(first, dict):
        return ""
    url = first.get("url")
    if isinstance(url, str) and url.strip():
        return url.strip()
    b64_json = first.get("b64_json")
    if isinstance(b64_json, str) and b64_json.strip():
        return "b64_json"
    return ""


def grok_image_node(
    state: GrokImageNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> GrokImageNodeOutput:
    """
    title: Grok Expert 3:4 卡通套图
    desc: 调用/规划 Grok Expert 为每页图文生成 3:4 卡通套图
    integrations:
    """
    image_rules = _dump(_get(state, "image_style_rules", {}))
    text_package = _dump(_get(state, "openai_text_package", {}))
    model = str(_get(state, "grok_image_model", "grok-imagine-image-quality")).strip() or "grok-imagine-image-quality"
    mode = str(_get(state, "grok_image_mode", "Expert")).strip() or "Expert"
    aspect_ratio = str(image_rules.get("aspect_ratio") or _get(state, "image_aspect_ratio", "3:4"))
    style = str(image_rules.get("style") or _get(state, "image_style", "cartoon"))
    base_prompt = _prompt(state, "grok_expert_image_set")
    consistency_rules = list(image_rules.get("consistency_rules", []) or [])
    must_have = "；".join(image_rules.get("must_have", []) or [])
    avoid = "；".join(image_rules.get("avoid", []) or [])
    reference_notes = "；".join(image_rules.get("reference_image_notes", []) or [])
    image_count = max(3, min(int(_get(state, "image_count", 6) or 6), 9))
    scripts = list(text_package.get("card_script", []) or [])[:image_count]
    execute_model_calls = bool(_get(state, "execute_model_calls", False))
    api_key = str(_get(state, "grok_api_key", "")).strip()

    images = []
    completed = 0
    failed = 0
    for index, script in enumerate(scripts, start=1):
        headline = script.split("：", 1)[0] if "：" in script else f"第 {index} 页"
        prompt = (
            f"{base_prompt}\n"
            f"第 {index} 张：{script}\n"
            f"画面规格：{aspect_ratio} 竖版，{style} 卡通风格。\n"
            f"必须遵守：{must_have}\n"
            f"参考图规则：{reference_notes or '无参考图时使用统一角色、统一色板、统一线条。'}\n"
            f"避免：{avoid}\n"
            "输出应像一套完整小红书卡片，不是单张孤立插画。"
        )
        request = ModelRequest(
            provider="grok",
            model=model,
            mode=mode,
            endpoint="https://api.x.ai/v1/images/generations",
            prompt_key="grok_expert_image_set",
            payload={
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "response_format": "url",
                "n": 1,
            },
            dry_run=not execute_model_calls,
            status="dry_run" if not execute_model_calls else "ready",
        )
        status = "dry_run"
        image_url = ""
        if execute_model_calls:
            try:
                response = post_json(request.endpoint, api_key, request.payload, timeout=120)
                image_url = _extract_image_url(response)
                status = "completed" if image_url else "failed"
                request.status = "completed" if image_url else "failed: missing image url"
            except ModelCallError as error:
                safe_message = redact_secrets(error, [api_key])[:180]
                status = "failed"
                request.status = f"failed: {safe_message}"

        if status == "completed":
            completed += 1
        elif status == "failed":
            failed += 1

        images.append(
            ImageGenerationItem(
                page=index,
                headline=headline,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                style=style,
                request=request,
                image_url=image_url,
                status=status,
            )
        )

    image_set_status = "dry_run"
    if execute_model_calls:
        if not images:
            image_set_status = "failed"
        elif completed == len(images) and not failed:
            image_set_status = "completed"
        else:
            image_set_status = "partial_failed" if completed else "failed"

    image_set = ImageSetPackage(
        provider="grok",
        model=model,
        mode=mode,
        aspect_ratio=aspect_ratio,
        style=style,
        images=images,
        consistency_rules=consistency_rules,
        status=image_set_status,
    )
    return GrokImageNodeOutput(grok_image_set=image_set)
