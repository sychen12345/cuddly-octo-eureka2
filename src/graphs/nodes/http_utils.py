"""HTTP 工具 — OpenAI / Grok API 调用封装"""

import json, logging, os, time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# ── 通用请求 ──────────────────────────────────────────────

def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    result: Dict[str, Any] = resp.json()
    return result

# ── OpenAI Chat ───────────────────────────────────────────

def call_openai_chat(
    api_key: str,
    model: str = "gpt-4o",
    system_prompt: str = "",
    user_prompt: str = "",
    temperature: float = 0.4,
    max_tokens: int = 4096,
    base_url: str = "https://api.openai.com/v1",
) -> str:
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = _post_json(url, headers, payload)
    content: str = data["choices"][0]["message"]["content"]
    return content

# ── Grok Image ────────────────────────────────────────────

def call_grok_image(
    api_key: str,
    prompt: str,
    model: str = "grok-2-image",
    n: int = 1,
    size: str = "1024x1365",
    quality: str = "hd",
    base_url: str = "https://api.x.ai/v1",
) -> str:
    url = f"{base_url}/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt, "n": n, "size": size, "quality": quality}
    data = _post_json(url, headers, payload, timeout=120)
    image_url: str = data["data"][0]["url"]
    return image_url

# ── DeepSeek Chat ──────────────────────────────────────────

def call_deepseek_chat(
    api_key: str,
    model: str = "deepseek-chat",
    system_prompt: str = "",
    user_prompt: str = "",
    temperature: float = 0.4,
    max_tokens: int = 4096,
    base_url: str = "https://api.deepseek.com/v1",
) -> str:
    """调用 DeepSeek Chat API"""
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = _post_json(url, headers, payload)
    content: str = data["choices"][0]["message"]["content"]
    return content
