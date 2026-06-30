"""
HTTP 工具函数 — 封装 OpenAI / Grok REST API 调用。
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _request(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: int = 60,
) -> Dict[str, Any]:
    """通用 HTTP POST，返回 JSON dict 或抛异常。"""
    data: bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body: bytes = resp.read()
            return json.loads(body.decode("utf-8"))  # type: ignore[no-any-return]
    except urllib.error.HTTPError as exc:
        err_body: bytes = exc.read()
        logger.error("HTTP %s %s → %s", exc.code, url, err_body[:500])
        raise RuntimeError(f"HTTP {exc.code}: {err_body[:500].decode('utf-8', errors='replace')}") from exc
    except Exception as exc:
        logger.error("Request failed %s: %s", url, exc)
        raise


def call_openai(
    api_key: str,
    model: str,
    messages: list,
    temperature: float = 0.4,
    max_tokens: int = 4096,
    reasoning_effort: Optional[str] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """调用 OpenAI Chat Completions API。"""
    url: str = "https://api.openai.com/v1/chat/completions"
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
    return _request(url, headers, payload, timeout=timeout)


def call_grok_image(
    api_key: str,
    model: str,
    prompt: str,
    n: int = 1,
    size: str = "1024x1365",
    quality: str = "hd",
    timeout: int = 180,
) -> Dict[str, Any]:
    """调用 Grok (xAI) 图像生成 API。"""
    url: str = "https://api.x.ai/v1/images/generations"
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "quality": quality,
    }
    return _request(url, headers, payload, timeout=timeout)
