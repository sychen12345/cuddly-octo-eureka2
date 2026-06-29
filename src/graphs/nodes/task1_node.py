"""
并行分支1 task节点
调用 Grok (xAI) API 对问候消息进行分析
需要环境变量 GROK_API_KEY
"""
import os
import json
from urllib import request, error as urllib_error
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import Task1NodeInput, Task1NodeOutput

GROK_API_URL = "https://api.x.ai/v1/chat/completions"


def task1_node(
    state: Task1NodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> Task1NodeOutput:
    """
    title: 并行分支1
    desc: 调用 Grok API 分析问候消息的质量和风格
    integrations: 
    """
    ctx = runtime.context

    api_key: str = os.getenv("GROK_API_KEY", "")
    if not api_key:
        raise ValueError("环境变量 GROK_API_KEY 未设置，请配置你的 Grok API Key")

    greeting: str = state.greeting_message

    payload: dict = {
        "model": "grok-2-1212",
        "messages": [
            {
                "role": "system",
                "content": "你是一个问候语质量分析师。请用一句话评价以下问候语的质量，并给出一个改进建议。"
            },
            {
                "role": "user",
                "content": greeting
            }
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }

    try:
        req = request.Request(
            GROK_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )
        with request.urlopen(req, timeout=30) as resp:
            body: dict = json.loads(resp.read().decode("utf-8"))
            choices: list = body.get("choices", [])
            if choices:
                result: str = choices[0].get("message", {}).get("content", "")
            else:
                result = "Grok 未返回有效结果"
    except urllib_error.HTTPError as e:
        error_body: str = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"Grok API 请求失败 (HTTP {e.code}): {error_body}")
    except urllib_error.URLError as e:
        raise Exception(f"Grok API 网络错误: {e.reason}")
    except Exception as e:
        raise Exception(f"Grok API 调用异常: {str(e)}")

    return Task1NodeOutput(task1_result=result.strip())