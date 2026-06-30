"""爆款选题机会池节点"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional

try:
    from langchain_core.runnables import RunnableConfig
except ImportError:  # pragma: no cover - local unit-test fallback
    RunnableConfig = Dict[str, Any]  # type: ignore

try:
    from langgraph.runtime import Runtime
except ImportError:  # pragma: no cover - local unit-test fallback
    Runtime = Any  # type: ignore

try:
    from coze_coding_utils.runtime_ctx.context import Context
except ImportError:  # pragma: no cover - local unit-test fallback
    Context = Any  # type: ignore

from graphs.state import (
    BenchmarkAccount, DemandInsight, TopicRecord,
    ProcessNodeInput, ProcessNodeOutput,
)
from graphs.nodes.http_utils import call_openai_web_search


_HASHTAG_RE = re.compile(r"#[0-9A-Za-z_\-\u4e00-\u9fff]+")


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _dump(model: Any) -> Dict[str, Any]:
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return {}


def _clean_hashtag(value: str) -> str:
    tag = str(value or "").strip()
    if not tag:
        return ""
    if tag.startswith("#"):
        return tag
    compact = re.sub(r"\s+", "", tag)
    return f"#{compact}" if compact else ""


def _explicit_hashtags(*texts: Any) -> List[str]:
    tags: List[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in _HASHTAG_RE.findall(str(text or "")):
            tag = _clean_hashtag(match)
            if tag and tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def _normalize_hashtags(values: Any, *fallback_texts: Any) -> List[str]:
    tags: List[str] = []
    seen: set[str] = set()

    for raw in [*_as_list(values), *_explicit_hashtags(*fallback_texts)]:
        tag = _clean_hashtag(raw)
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags[:10]


def _score_topic(insight: DemandInsight, evidence: List[str]) -> int:
    score = 50
    if insight.confidence == "high":
        score += 20
    elif insight.confidence == "medium":
        score += 10
    if len(insight.user_words) > 1:
        score += 10
    if any(any(term in item for term in ["浏览", "高赞", "收藏", "评论", "热词", "搜索"]) for item in evidence):
        score += 8
    return min(score, 100)


def _topic_from_insight(
    niche: str,
    audience: str,
    insight: DemandInsight,
    index: int,
    evidence: List[str],
) -> TopicRecord:
    cluster = insight.cluster or "核心需求"
    title = f"从{cluster}切入，做一篇「{niche}」小红书图文"
    demand_source = cluster if not insight.user_words else f"{cluster}: {' / '.join(insight.user_words[:2])}"
    expected_view_score = _score_topic(insight, evidence)
    hashtags = _normalize_hashtags([], title, niche, demand_source)
    if not hashtags and niche:
        hashtags = [_clean_hashtag(niche)]

    return TopicRecord(
        title=title,
        audience=audience,
        hook=f"如果你也关注「{niche}」，先看懂「{cluster}」这类需求。",
        demand_source=demand_source,
        hashtags=hashtags,
        outline=[
            f"点出{audience}在「{cluster}」上的真实卡点",
            f"用对标结构转译为：{insight.content_angle}",
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
        view_evidence=[f"需求来源：{demand_source}", *evidence[:4]],
        selected=False,
        selection_reason="",
    )


def _fallback_topic(niche: str, audience: str, evidence: List[str]) -> TopicRecord:
    title = f"围绕「{niche or '当前赛道'}」验证一个可发布选题"
    hashtags = _normalize_hashtags([], title, niche, *evidence)
    if not hashtags and niche:
        hashtags = [_clean_hashtag(niche)]

    return TopicRecord(
        title=title,
        audience=audience,
        hook="先从竞品结构和评论需求里验证这个选题是否值得做。",
        demand_source="缺少评论样本时的默认验证选题",
        hashtags=hashtags,
        outline=[
            "找近期竞品内容，记录标题、互动和评论问题",
            "把评论按痛点、阻碍、想要结果分类",
            "选一个热度和痛点都清晰的主题做首篇图文",
            "发布后继续收集评论修正选题库",
        ],
        proof_needed=["竞品链接", "评论样本", "浏览量或收藏证据"],
        differentiation="把方法写成验证流程，而不是承诺结果。",
        priority="medium",
        expected_view_score=58,
        view_evidence=evidence or ["缺少公开热度证据，建议补充竞品链接或手动指定选题"],
    )


def _json_from_model_text(text: str) -> Dict[str, Any]:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(raw[start:end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def _topic_from_dict(raw: Dict[str, Any], niche: str, audience: str) -> Optional[TopicRecord]:
    title = str(raw.get("title", "")).strip()
    if not title:
        return None

    hashtags = _normalize_hashtags(
        raw.get("hashtags", raw.get("tags", [])),
        title,
        raw.get("demand_source", ""),
        raw.get("view_evidence", []),
    )
    if not hashtags and niche:
        hashtags = [_clean_hashtag(niche)]

    try:
        score = int(raw.get("expected_view_score", 60))
    except (TypeError, ValueError):
        score = 60

    return TopicRecord(
        title=title,
        audience=str(raw.get("audience", audience)).strip() or audience,
        hook=str(raw.get("hook", "")).strip(),
        demand_source=str(raw.get("demand_source", "OpenAI联网竞品调研")).strip(),
        hashtags=hashtags,
        outline=_as_list(raw.get("outline", [])),
        proof_needed=_as_list(raw.get("proof_needed", [])),
        differentiation=str(raw.get("differentiation", "")).strip(),
        priority=str(raw.get("priority", "medium")).strip() or "medium",
        expected_view_score=max(0, min(score, 100)),
        view_evidence=_as_list(raw.get("view_evidence", [])),
        selected=bool(raw.get("selected", False)),
        selection_reason=str(raw.get("selection_reason", "")).strip(),
    )


def _topics_from_openai_web(state: ProcessNodeInput) -> List[TopicRecord]:
    if not (state.execute_model_calls and state.openai_api_key and state.xiaohongshu_url):
        return []

    benchmark_payload = [
        item.model_dump() if isinstance(item, BenchmarkAccount) else item
        for item in state.benchmark_accounts
    ]
    demand_payload = [
        item.model_dump() if isinstance(item, DemandInsight) else item
        for item in state.demand_insights
    ]
    sp = (
        "你是小红书选题策略专家。必须使用联网搜索工具查询运营提供的竞品链接，"
        "只学习公开可见的主题、结构、评论需求和热度信号，不复制原文。"
        "请只返回 JSON，不要返回 Markdown。"
    )
    up = (
        f"竞品链接：{state.xiaohongshu_url}\n"
        f"运营需求：{state.user_request or '（未填写）'}\n"
        f"运营指定选题：{state.user_selected_topic or '（未指定）'}\n"
        f"赛道：{state.niche or '（未指定）'}\n"
        f"目标人群：{state.audience or '（未指定）'}\n"
        f"已有对标线索：{json.dumps(benchmark_payload, ensure_ascii=False)}\n"
        f"已有需求洞察：{json.dumps(demand_payload, ensure_ascii=False)}\n"
        f"限制：{json.dumps(state.constraints, ensure_ascii=False)}\n\n"
        "请联网查询后输出：\n"
        "{\n"
        "  \"topic_bank\": [\n"
        "    {\n"
        "      \"title\": \"选题标题\",\n"
        "      \"audience\": \"目标人群\",\n"
        "      \"hook\": \"开头钩子\",\n"
        "      \"demand_source\": \"来自哪个竞品结构/评论需求/搜索线索\",\n"
        "      \"hashtags\": [\"#话题1\", \"#话题2\"],\n"
        "      \"outline\": [\"3-6条内容大纲\"],\n"
        "      \"proof_needed\": [\"发布前要补的证据\"],\n"
        "      \"differentiation\": \"如何区别于竞品\",\n"
        "      \"priority\": \"high|medium|low\",\n"
        "      \"expected_view_score\": 0,\n"
        "      \"view_evidence\": [\"只写公开可见或搜索到的证据\"]\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    raw = call_openai_web_search(
        state.openai_api_key,
        system_prompt=sp,
        user_prompt=up,
    )
    parsed = _json_from_model_text(raw)
    topic_items = parsed.get("topic_bank", [])
    if not isinstance(topic_items, list):
        return []
    topics = [
        topic for topic in (
            _topic_from_dict(item, state.niche, state.audience)
            for item in topic_items
            if isinstance(item, dict)
        )
        if topic is not None
    ]
    return topics


def _requested_topic(state: ProcessNodeInput) -> str:
    explicit = str(state.user_selected_topic or "").strip()
    if explicit:
        return explicit
    tags = _explicit_hashtags(state.user_request)
    return tags[0] if tags else ""


def _requested_hashtags(requested_topic: str) -> List[str]:
    requested = requested_topic.strip()
    if not requested:
        return []
    if requested.startswith("#"):
        return _normalize_hashtags([requested])
    return _explicit_hashtags(requested)


def _select_topic(topics: List[TopicRecord], requested_topic: str) -> TopicRecord:
    if not topics:
        topics.append(_fallback_topic("", "", []))

    requested = requested_topic.strip()
    if requested:
        requested_norm = requested.lstrip("#")
        for topic in topics:
            topic_values = [topic.title, *topic.hashtags]
            if any(requested in value or requested_norm == value.lstrip("#") for value in topic_values):
                topic.selected = True
                topic.selection_reason = "运营指定选题，优先进入生产链路。"
                explicit_tags = _requested_hashtags(requested)
                topic.hashtags = explicit_tags or topic.hashtags
                return topic

        base = max(topics, key=lambda item: item.expected_view_score)
        custom = base.model_copy(deep=True)
        custom.title = requested
        custom.hashtags = _requested_hashtags(requested) or base.hashtags
        custom.selected = True
        custom.selection_reason = "运营指定了新选题，沿用最高分选题的需求和证据框架。"
        topics.append(custom)
        return custom

    selected = max(topics, key=lambda item: item.expected_view_score)
    selected.selected = True
    selected.selection_reason = selected.selection_reason or "未指定选题，自动选择预估浏览潜力最高的选题。"
    return selected


def _local_topics(state: ProcessNodeInput) -> List[TopicRecord]:
    evidence = [
        *state.benchmark_notes,
        *[item.signal for item in state.benchmark_accounts if item.signal],
        state.xiaohongshu_url,
    ]
    topics = [
        _topic_from_insight(state.niche, state.audience, insight, index, evidence)
        for index, insight in enumerate(state.demand_insights[:6], start=1)
    ]
    if not topics:
        topics.append(_fallback_topic(state.niche, state.audience, evidence))
    if state.xiaohongshu_url and not state.execute_model_calls:
        for topic in topics:
            topic.view_evidence.append("已提供竞品链接；真实运行时会用 OpenAI 联网查询后刷新选题。")
    return topics


def process_node(
    state: ProcessNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> ProcessNodeOutput:
    """
    title: 爆款选题机会池
    desc: 从竞品链接、用户需求和运营指定选题里生成选题池；有竞品链接时由 OpenAI 联网查询
    integrations: OpenAI Web Search
    """
    ctx = runtime.context

    try:
        topic_bank = _topics_from_openai_web(state)
    except Exception:
        topic_bank = []

    if not topic_bank:
        topic_bank = _local_topics(state)

    selected = _select_topic(topic_bank, _requested_topic(state))
    for topic in topic_bank:
        topic.selected = topic.title == selected.title
        if topic.selected:
            topic.selection_reason = selected.selection_reason

    return ProcessNodeOutput(topic_bank=topic_bank, selected_topic=selected)
