"""
节点7: Grok Expert 3:4 卡通套图 (grok_image_node)
───────────────────────────────────────────────────
输入: image_style_rules, openai_text_package, skill_subflows, grok_image_model, ... , grok_api_key
输出: grok_image_set
"""
import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    GrokImageNodeInput,
    GrokImageNodeOutput,
    EditablePrompt,
    ImageStyleRule,
    ImageGenerationItem,
    ImageSetPackage,
    ModelRequest,
    SkillSubflow,
    TextDescriptionPackage,
)
from graphs.nodes.http_utils import call_grok_image

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
def grok_image_node(
    state: GrokImageNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> GrokImageNodeOutput:
    """
    title: Grok Expert 套图
    desc: 调用 Grok API 生成 3:4 卡通风格套图，无 key 时降级为 dry_run
    integrations: Grok API
    """
    style_rules: ImageStyleRule = _get(state, "image_style_rules", ImageStyleRule())
    text_package: TextDescriptionPackage = _get(state, "openai_text_package", TextDescriptionPackage())
    skill_subflows: List[SkillSubflow] = _get(state, "skill_subflows", [])
    grok_model: str = _get(state, "grok_image_model", "grok-imagine-image-quality")
    grok_mode: str = _get(state, "grok_image_mode", "Expert")
    aspect_ratio: str = _get(state, "image_aspect_ratio", "3:4")
    style: str = _get(state, "image_style", "cartoon")
    editable_prompts: List[EditablePrompt] = _get(state, "editable_prompts", [])
    image_count: int = _get(state, "image_count", 6)
    execute: bool = _get(state, "execute_model_calls", False)
    grok_api_key: str = _get(state, "grok_api_key", "")

    prompt_text: str = _find_prompt(editable_prompts, "grok_image_prompt")

    # 构建每页图片
    images: List[ImageGenerationItem] = []
    size_map: Dict[str, str] = {"3:4": "1024x1365", "1:1": "1024x1024", "4:3": "1365x1024"}
    size: str = size_map.get(aspect_ratio, "1024x1365")

    for i in range(image_count):
        headline: str = text_package.card_script[i] if i < len(text_package.card_script) else f"第{i+1}页"
        visual_desc: str = prompt_text or text_package.image_brief or f"{aspect_ratio} {style}风格小红书图文卡片"
        page_prompt: str = (
            f"{visual_desc}；第{i+1}页；标题：{headline}；"
            f"{'；'.join(style_rules.must_have[:3])}；"
            f"小红书图文卡片；短句；层级清楚"
        )

        item: ImageGenerationItem = ImageGenerationItem(
            page=i + 1,
            headline=headline[:30],
            prompt=page_prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            request=ModelRequest(
                provider="grok",
                model=grok_model,
                mode=grok_mode,
                endpoint="https://api.x.ai/v1/images/generations",
                skill_key="grok_image_skill",
                prompt_key="grok_image_prompt",
                payload={"model": grok_model, "n": 1, "size": size, "quality": "hd"},
                dry_run=not execute or not grok_api_key,
                status="planned",
            ),
            status="dry_run",
        )
        images.append(item)

    # 真实调用
    if execute and grok_api_key:
        for img in images:
            try:
                resp: Dict[str, Any] = call_grok_image(
                    api_key=grok_api_key,
                    model=grok_model,
                    prompt=img.prompt,
                    n=1,
                    size=size,
                    quality="hd",
                )
                data_list: list = resp.get("data", [])
                if data_list:
                    img.image_url = data_list[0].get("url", "")
                img.status = "completed"
                img.request.status = "completed"
            except Exception as exc:
                logger.error("Grok API 第%d页调用失败: %s", img.page, exc)
                img.status = "failed"
                img.request.status = "failed"

    image_set: ImageSetPackage = ImageSetPackage(
        provider="grok",
        model=grok_model,
        mode=grok_mode,
        aspect_ratio=aspect_ratio,
        style=style,
        images=images,
        consistency_rules=style_rules.consistency_rules,
        status="completed" if (execute and grok_api_key) else "dry_run",
    )

    return GrokImageNodeOutput(grok_image_set=image_set)
