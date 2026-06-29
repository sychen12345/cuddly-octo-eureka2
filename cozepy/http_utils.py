"""Small HTTP helpers for direct model calls.

The workflow stores request payloads for auditability, but API keys should only
travel in transient headers during a live call.
"""
from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any, Dict, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelCallError(RuntimeError):
    """Raised when a direct model API request fails."""


def redact_secrets(message: Any, secrets: Iterable[str] = ()) -> str:
    """Remove known API-key shapes and exact runtime secrets from an error string."""
    redacted = str(message)
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED_API_KEY]")

    patterns = [
        r"\bsk-[A-Za-z0-9_\-]{8,}\b",
        r"\bgsk[_-][A-Za-z0-9_\-]{8,}\b",
        r"\bxai-[A-Za-z0-9_\-]{8,}\b",
    ]
    for pattern in patterns:
        redacted = re.sub(pattern, "[REDACTED_API_KEY]", redacted)
    return redacted


def post_json(endpoint: str, api_key: str, payload: Dict[str, Any], timeout: int = 90) -> Dict[str, Any]:
    """POST JSON with bearer auth and return the decoded JSON body."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")[:800]
        message = redact_secrets(f"HTTP {error.code}: {error_body}", [api_key])
        raise ModelCallError(message) from error
    except (OSError, TimeoutError, URLError) as error:
        message = redact_secrets(f"request failed: {error}", [api_key])
        raise ModelCallError(message) from error

    try:
        decoded = json.loads(raw)
    except JSONDecodeError as error:
        message = redact_secrets(f"invalid JSON response: {raw[:800]}", [api_key])
        raise ModelCallError(message) from error

    if not isinstance(decoded, dict):
        raise ModelCallError("invalid JSON response: expected object")
    return decoded
