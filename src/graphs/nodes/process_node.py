"""节点 2/8 — 选题库与高浏览选题 (process)"""

import json, os
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    BenchmarkAccount, DemandInsight, TopicRecord,
    ProcessNodeInput, ProcessNodeOutput,
)
from graphs.nodes.http_utils import call_openai_chat


def _score_topic(insight: DemandInsight, constraints: List[str]) -> int:
    score = 50
    if insight.confidence == "high":
        score += 20
    elif insight.confidence == "medium":
        score += 10
    if len(insight.user_words) > 1:
        score += 10
    return min(score, 100)


def _build_topics(
    niche: str,
    audience: str,
    brand_voice: str,
    demand_insights: List[DemandInsight],
    benchmark_accounts: List[BenchmarkAccount],
    card_count: int,
) -> List[TopicRecord]:
    topics: List[TopicRecord] = []
    for insight in demand_insights:
        title = f"从{insight.cluster}角度切入内容做「{niche}」"
        topic = TopicRecord(
            title=title,
            audience=audience,
            hook=f"如果你也想做「{niche}」，先看懂「{insight.cluster}」这类需求。",
            demand_source=f"{insight.cluster}: {', '.join(insight.user_words[:2])}",
            outline=[
                f"点出{audience}在「{insight.cluster}」上的真实卡点",
                f"用对标结构转译为：{insight.content_angle}",
                "给出 3 个可立即执行的小步骤",
                "说明需要补充的证据和风险边界",
                "用轻 CTA 引导收藏、评论或领取清单",
            ],
            proof_needed=[
                "至少 3 条真实评论或私信截图",
                "1-2 个对标笔记结构拆解",
                "发布前补充个人实践、案例或工具截图",
            ],
            differentiation="从用户原话出发重组结构，不复刻对标标题和正文。",
            priority="high" if insight.confidence == "high" else "medium",
            expected_view_score=0,
            view_evidence=[f"需求来源: {insight.cluster}"],
            selected=False,
            selection_reason="",
        )
        topic.expected_view_score = _score_topic(insight, [])
        topics.append(topic)

    # 选中浏览分最高的
    if topics:
        best = max(topics, key=lambda t: t.expected_view_score)
        best.selected = True
        best.selection_reason = f"浏览潜力最高({best.expected_view_score}分)"

    return topics


def process_node(
    state: ProcessNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> ProcessNodeOutput:
    """
    title: 选题库与高浏览选题
    desc: 从需求洞察生成选题库，自动选中浏览潜力最高的选题
    integrations:
    """
    ctx = runtime.context

    topic_bank = _build_topics(
        state.niche, state.audience, state.brand_voice,
        state.demand_insights, state.benchmark_accounts, state.card_count,
    )

    selected: Optional[TopicRecord] = None
    for t in topic_bank:
        if t.selected:
            selected = t
            break

    return ProcessNodeOutput(topic_bank=topic_bank, selected_topic=selected)
