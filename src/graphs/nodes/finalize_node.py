"""
节点8: 结果审核打包 (finalize_node)
─────────────────────────────────────
输入: niche, selected_topic, openai_text_package, grok_image_set, ...
输出: card_package, workflow_summary, next_commands
"""
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    FinalizeNodeInput,
    FinalizeNodeOutput,
    CardPage,
    CardPackage,
    EditablePrompt,
    ImageSetPackage,
    SkillSubflow,
    TextDescriptionPackage,
    TopicRecord,
    WorkflowStep,
)


# ── 通用辅助 ──────────────────────────────────────────────
def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _dump(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_dump(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _dump(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: _dump(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


# ── 节点函数 ──────────────────────────────────────────────
def finalize_node(
    state: FinalizeNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> FinalizeNodeOutput:
    """
    title: 结果审核打包
    desc: 整合文案和套图，生成最终图文卡片包、流程摘要和下一步指令
    integrations:
    """
    niche: str = _get(state, "niche", "")
    selected_topic: TopicRecord = _get(state, "selected_topic", TopicRecord(title="", audience="", hook="", demand_source="", differentiation=""))
    text_pkg: TextDescriptionPackage = _get(state, "openai_text_package", TextDescriptionPackage())
    image_set: ImageSetPackage = _get(state, "grok_image_set", ImageSetPackage())
    editable_prompts: List[EditablePrompt] = _get(state, "editable_prompts", [])
    skill_subflows: List[SkillSubflow] = _get(state, "skill_subflows", [])
    workflow_steps: List[WorkflowStep] = _get(state, "workflow_steps", [])
    topic_bank: List[TopicRecord] = _get(state, "topic_bank", [])

    # 构建卡片页
    cards: List[CardPage] = []
    max_pages: int = max(len(text_pkg.card_script), len(image_set.images))
    for i in range(max_pages):
        headline: str = ""
        body: str = ""
        if i < len(text_pkg.card_script):
            headline = text_pkg.card_script[i][:30]
            body = text_pkg.card_script[i]
        visual: str = ""
        if i < len(image_set.images):
            img = image_set.images[i]
            visual = img.prompt

        cards.append(CardPage(
            page=i + 1,
            headline=headline,
            body=body,
            visual_prompt=visual,
        ))

    # 封面标题选项
    cover_options: List[str] = text_pkg.title_options if text_pkg.title_options else [selected_topic.title]

    # 正文
    caption: str = text_pkg.post_description or f"关于「{selected_topic.title}」的小红书图文卡片。"

    # 话题标签
    hashtags: List[str] = [f"#{niche}", "#小红书运营", "#内容选题"]

    # CTA
    cta: str = "想继续做的话，把你的对标标题和评论原话贴进来，我会继续扩成下一组卡片。"

    # 审核清单
    review_checklist: List[str] = [
        "是否所有真实数据都有来源",
        "是否没有承诺阅读量、涨粉或收益",
        "是否只学习对标结构，没有复制原文",
        "是否每页卡片只有一个核心信息",
        "是否保留了下一轮评论采样入口",
    ]

    card_package: CardPackage = CardPackage(
        topic_title=selected_topic.title,
        cover_options=cover_options,
        cards=cards,
        caption=caption,
        hashtags=hashtags,
        cta=cta,
        review_checklist=review_checklist,
    )

    # 流程摘要
    topic_count: int = len(topic_bank)
    insight_count: int = sum(1 for t in topic_bank if t.demand_source)
    summary: str = (
        f"已完成「{niche}」内容工作流："
        f"沉淀 {topic_count} 个选题，"
        f"生成 {len(cards)} 页图文卡片规格"
        f"（文案状态：{text_pkg.status}，套图状态：{image_set.status}）。"
    )

    # 下一步指令
    next_commands: List[str] = [
        f"继续扩写「{selected_topic.title}」，生成更口语化的卡片文案。",
        f"把「{niche}」的评论需求整理成选题库 Markdown。",
        "补充真实评论和对标标题，重新排序选题优先级。",
        "把当前卡片包改成更强封面标题和更短页面正文。",
    ]

    return FinalizeNodeOutput(
        card_package=card_package,
        workflow_summary=summary,
        next_commands=next_commands,
    )
