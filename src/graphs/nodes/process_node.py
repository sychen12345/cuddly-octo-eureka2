"""
节点2: 选题库与高浏览选题 (process_node)
──────────────────────────────────────────
输入: niche, audience, demand_insights, topic_research_notes, benchmark_notes, user_selected_topic
输出: topic_bank, selected_topic
"""
import re
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    ProcessNodeInput,
    ProcessNodeOutput,
    DemandInsight,
    TopicRecord,
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


# ── 选题生成 ──────────────────────────────────────────────
def _generate_topic(
    niche: str,
    audience: str,
    insight: DemandInsight,
    benchmark_hints: List[str],
) -> TopicRecord:
    hook: str = f"如果你也想做「{niche}」，先看懂「{insight.cluster}」这类需求。"
    outline: List[str] = [
        f"点出{audience}在「{insight.cluster}」上的真实卡点",
        f"用对标结构转译为：{insight.content_angle}",
        "给出 3 个可立即执行的小步骤",
        "说明需要补充的证据和风险边界",
        "用轻 CTA 引导收藏、评论或领取清单",
    ]
    proof: List[str] = [
        "至少 3 条真实评论或私信截图",
        "1-2 个对标笔记结构拆解",
        "发布前补充个人实践、案例或工具截图",
    ]
    title: str = f"{insight.content_angle}做「{niche}」"
    return TopicRecord(
        title=title,
        audience=audience,
        hook=hook,
        demand_source=f"{insight.cluster}: {insight.user_words[0] if insight.user_words else ''}",
        outline=outline,
        proof_needed=proof,
        differentiation="从用户原话出发重组结构，不复刻对标标题和正文。",
        priority="high" if insight.confidence == "high" else "medium",
        expected_view_score=75 if insight.confidence == "high" else 60,
        view_evidence=[f"需求来源: {insight.cluster}"],
    )


def _select_topic(topics: List[TopicRecord], user_selected: str) -> TopicRecord:
    if user_selected:
        for t in topics:
            if user_selected in t.title or t.title in user_selected:
                t.selected = True
                t.selection_reason = "用户指定选题"
                return t
    if not topics:
        return TopicRecord(
            title=f"关于「{user_selected or '待定'}」的选题",
            audience="",
            hook="",
            demand_source="",
            differentiation="",
        )
    best: TopicRecord = max(topics, key=lambda t: t.expected_view_score)
    best.selected = True
    best.selection_reason = f"浏览潜力最高({best.expected_view_score}分)"
    return best


# ── 节点函数 ──────────────────────────────────────────────
def process_node(
    state: ProcessNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> ProcessNodeOutput:
    """
    title: 选题库与高浏览选题
    desc: 根据需求洞察和对标线索生成选题库，并选出本轮最高潜力的选题
    integrations:
    """
    niche: str = _get(state, "niche", "")
    audience: str = _get(state, "audience", "小红书新手用户")
    demand_insights: List[DemandInsight] = _get(state, "demand_insights", [])
    benchmark_notes: List[str] = _get(state, "benchmark_notes", [])
    user_selected_topic: str = _get(state, "user_selected_topic", "")

    topic_bank: List[TopicRecord] = []
    for insight in demand_insights:
        topic_bank.append(_generate_topic(niche, audience, insight, benchmark_notes))

    selected: TopicRecord = _select_topic(topic_bank, user_selected_topic)

    return ProcessNodeOutput(
        topic_bank=topic_bank,
        selected_topic=selected,
    )
