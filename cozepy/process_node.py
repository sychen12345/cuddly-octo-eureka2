"""
选题库与高浏览选题节点。

该节点只负责选题：把评论需求、对标结构和浏览量/热词线索沉淀为选题库，
再选出本轮最值得交给 OpenAI 写文案、Grok 生成套图的高潜选题。
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

try:
    from langchain_core.runnables import RunnableConfig
except ImportError:  # pragma: no cover - local fallback
    RunnableConfig = Dict[str, Any]  # type: ignore

try:
    from langgraph.runtime import Runtime
except ImportError:  # pragma: no cover - local fallback
    Runtime = Any  # type: ignore

try:
    from coze_coding_utils.runtime_ctx.context import Context
except ImportError:  # pragma: no cover - local fallback
    Context = Any  # type: ignore

try:
    from .state import ProcessNodeInput, ProcessNodeOutput, TopicRecord
except ImportError:
    from graphs.state import ProcessNodeInput, ProcessNodeOutput, TopicRecord


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


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _insight_text(insight: Any, key: str, default: str = "") -> str:
    return str(_dump(insight).get(key, default)).strip()


def _insight_words(insight: Any) -> List[str]:
    return _as_list(_dump(insight).get("user_words", []))


def _view_boost(title: str, evidence: List[str]) -> tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    joined = " ".join([title, *evidence])
    high_view_terms = ["浏览", "爆", "高赞", "收藏", "评论", "热词", "搜索", "近期", "起号"]
    for term in high_view_terms:
        if term in joined:
            score += 4
            reasons.append(f"包含高浏览信号：{term}")
    for raw in evidence:
        digits = "".join(ch for ch in raw if ch.isdigit())
        if digits and int(digits[:6]) >= 1000:
            score += 8
            reasons.append(f"含可量化热度线索：{raw[:36]}")
            break
    return min(score, 24), reasons[:4]


def _topic_for_insight(
    niche: str,
    audience: str,
    insight: Any,
    index: int,
    view_evidence: List[str],
) -> TopicRecord:
    cluster = _insight_text(insight, "cluster", "核心需求")
    angle = _insight_text(insight, "content_angle", "把需求拆成可执行步骤")
    confidence = _insight_text(insight, "confidence", "medium")
    source_words = _insight_words(insight)

    title_map = {
        "新手门槛": f"零基础做「{niche}」，先别学一堆工具",
        "时间约束": f"下班后做「{niche}」，每天只推进这 3 件事",
        "路径不清": f"{audience}从 0 开始做「{niche}」的路线图",
        "资源请求": f"做「{niche}」前，先存下这份资料清单",
        "成本顾虑": f"低成本验证「{niche}」，别一上来就花钱",
        "工具焦虑": f"做「{niche}」到底该用哪些 AI 工具",
        "待采样评论": f"想做「{niche}」，先去评论区验证这 5 个问题",
    }
    title = title_map.get(cluster, f"「{niche}」新手最常问的 {index} 个问题")
    demand_source = cluster if not source_words else f"{cluster}: {' / '.join(source_words[:2])}"

    confidence_score = {"high": 20, "medium": 12, "low": 5}.get(confidence, 10)
    view_score, view_reasons = _view_boost(title, view_evidence)
    priority_bonus = max(0, 10 - index)
    expected_view_score = min(100, 48 + confidence_score + view_score + priority_bonus)

    view_evidence_out = [
        *view_reasons,
        f"需求来源：{demand_source}",
        f"适合内容角度：{angle}",
    ]

    return TopicRecord(
        title=title,
        audience=audience,
        hook=f"如果你也想做「{niche}」，先看懂「{cluster}」这类需求。",
        demand_source=demand_source,
        outline=[
            f"点出{audience}在「{cluster}」上的真实卡点",
            f"用对标结构转译为：{angle}",
            "给出 3 个可立即执行的小步骤",
            "说明需要补充的证据和风险边界",
            "用轻 CTA 引导收藏、评论或领取清单",
        ],
        proof_needed=[
            "真实评论或私信截图",
            "对标笔记标题与结构拆解",
            "浏览量、收藏、评论或搜索热词证据",
        ],
        differentiation="从用户原话和热度证据重组选题，不复刻对标标题和正文。",
        priority="high" if expected_view_score >= 76 else "medium",
        expected_view_score=expected_view_score,
        view_evidence=view_evidence_out,
    )


def _fallback_topic(niche: str, audience: str, view_evidence: List[str]) -> TopicRecord:
    view_score, view_reasons = _view_boost(niche, view_evidence)
    return TopicRecord(
        title=f"普通人做「{niche}」，先完成这 3 步验证",
        audience=audience,
        hook=f"别急着开干，先确认「{niche}」有没有真实需求。",
        demand_source="缺少评论样本时的默认验证选题",
        outline=[
            "找 5 篇近期对标内容，记录标题、浏览量和评论",
            "把评论按新手门槛、路径不清、资源请求分类",
            "选一个热度和痛点都清晰的主题做首篇图文",
            "发布后继续收集评论修正选题库",
        ],
        proof_needed=["对标截图", "评论样本", "浏览量或收藏证据"],
        differentiation="把方法写成验证流程，而不是承诺结果。",
        priority="medium",
        expected_view_score=58 + view_score,
        view_evidence=view_reasons or ["缺少浏览量证据，建议用户补充或手动指定选题"],
    )


def _select_topic(topics: List[TopicRecord], user_selected_topic: str) -> TopicRecord:
    if user_selected_topic:
        for topic in topics:
            if user_selected_topic in topic.title or topic.title in user_selected_topic:
                topic.selected = True
                topic.selection_reason = "用户指定选题，优先进入生产链路。"
                return topic
        custom = topics[0].model_copy() if hasattr(topics[0], "model_copy") else topics[0].copy()
        custom.title = user_selected_topic
        custom.selected = True
        custom.selection_reason = "用户指定了新选题，沿用最高分选题的需求和证据框架。"
        return custom

    selected = max(topics, key=lambda item: item.expected_view_score)
    selected.selected = True
    selected.selection_reason = "未指定选题，自动选择预估浏览潜力最高的选题。"
    return selected


def process_node(
    state: ProcessNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> ProcessNodeOutput:
    """
    title: 选题库与高浏览选题
    desc: 构建选题库，结合浏览量/热词证据或用户指定选出本轮主题
    integrations:
    """
    niche = str(_get(state, "niche", "")).strip()
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    insights = list(_get(state, "demand_insights", []) or [])
    topic_research_notes = _as_list(_get(state, "topic_research_notes", []))
    benchmark_notes = _as_list(_get(state, "benchmark_notes", []))
    user_selected_topic = str(_get(state, "user_selected_topic", "")).strip()
    view_evidence = [*topic_research_notes, *benchmark_notes]

    topic_bank = [
        _topic_for_insight(niche, audience, insight, index, view_evidence)
        for index, insight in enumerate(insights[:6], start=1)
    ]
    if not topic_bank:
        topic_bank.append(_fallback_topic(niche, audience, view_evidence))

    selected_topic = _select_topic(topic_bank, user_selected_topic)
    for topic in topic_bank:
        if topic.title == selected_topic.title:
            topic.selected = True
            topic.selection_reason = selected_topic.selection_reason

    return ProcessNodeOutput(topic_bank=topic_bank, selected_topic=selected_topic)
