"""
并行分支2 task节点
调用 OpenAI API 对问候消息进行分析
需要环境变量 OPENAI_API_KEY
"""
import os
import json
from urllib import request, error as urllib_error
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import Task2NodeInput, Task2NodeOutput

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def task2_node(
    state: Task2NodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> Task2NodeOutput:
    """
    title: 并行分支2
    desc: 调用 OpenAI API 分析问候消息的质量和风格
    integrations: 
    """
    ctx = runtime.context

    api_key: str = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("环境变量 OPENAI_API_KEY 未设置，请配置你的 OpenAI API Key")

    greeting: str = state.greeting_message

    payload: dict = {
        "model": "gpt-4o-mini",
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
            OPENAI_API_URL,
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
                result = "OpenAI 未返回有效结果"
    except urllib_error.HTTPError as e:
        error_body: str = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"OpenAI API 请求失败 (HTTP {e.code}): {error_body}")
    except urllib_error.URLError as e:
        raise Exception(f"OpenAI API 网络错误: {e.reason}")
    except Exception as e:
        raise Exception(f"OpenAI API 调用异常: {str(e)}")

    return Task2NodeOutput(task2_result=result.strip())