"""
选题库与图文卡片生成节点。

该节点消费上游的对标与评论洞察，输出可沉淀的选题库，以及一组可直接
交给设计或生图工具继续制作的小红书图文卡片规格。
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
    from graphs.state import (
        CardPackage,
        CardPage,
        DemandInsight,
        ProcessNodeInput,
        ProcessNodeOutput,
        TopicRecord,
    )
except ImportError:
    from .state import (
        CardPackage,
        CardPage,
        DemandInsight,
        ProcessNodeInput,
        ProcessNodeOutput,
        TopicRecord,
    )


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


def _clean_hashtag(text: str) -> str:
    cleaned = "".join(ch for ch in text if ch.isalnum() or ch in ["_", "-"])
    return f"#{cleaned}" if cleaned else "#小红书运营"


def _insight_text(insight: Any, key: str, default: str = "") -> str:
    data = _dump(insight)
    return str(data.get(key, default)).strip()


def _insight_words(insight: Any) -> List[str]:
    data = _dump(insight)
    return _as_list(data.get("user_words", []))


def _topic_for_insight(
    niche: str,
    audience: str,
    insight: Any,
    index: int,
) -> TopicRecord:
    cluster = _insight_text(insight, "cluster", "核心需求")
    angle = _insight_text(insight, "content_angle", "把需求拆成可执行步骤")
    confidence = _insight_text(insight, "confidence", "medium")
    source_words = _insight_words(insight)
    priority = "high" if confidence == "high" or index == 1 else "medium"

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

    demand_source = cluster
    if source_words:
        demand_source = f"{cluster}: {' / '.join(source_words[:2])}"

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
            "至少 3 条真实评论或私信截图",
            "1-2 个对标笔记结构拆解",
            "发布前补充个人实践、案例或工具截图",
        ],
        differentiation="从用户原话出发重组结构，不复刻对标标题和正文。",
        priority=priority,
    )


def _fallback_topic(niche: str, audience: str) -> TopicRecord:
    return TopicRecord(
        title=f"普通人做「{niche}」，先完成这 3 步验证",
        audience=audience,
        hook=f"别急着开干，先确认「{niche}」有没有真实需求。",
        demand_source="缺少评论样本时的默认验证选题",
        outline=[
            "找 5 篇近期对标内容，记录标题和评论",
            "把评论按新手门槛、路径不清、资源请求分类",
            "选一个最清晰的痛点做首篇图文",
            "发布后继续收集评论修正选题库",
        ],
        proof_needed=["对标截图", "评论样本", "自己的执行记录"],
        differentiation="把方法写成验证流程，而不是承诺结果。",
        priority="medium",
    )


def _build_topic_bank(niche: str, audience: str, insights: List[Any]) -> List[TopicRecord]:
    topics = [
        _topic_for_insight(niche, audience, insight, index)
        for index, insight in enumerate(insights[:5], start=1)
    ]
    if not topics:
        topics.append(_fallback_topic(niche, audience))
    return topics


def _card_pages(topic: TopicRecord, niche: str, count: int, voice: str) -> List[CardPage]:
    count = max(3, min(count or 6, 8))
    blueprints = [
        (
            topic.title,
            topic.hook,
            "封面，大字标题，干净背景，突出目标人群和核心承诺",
        ),
        (
            "先看真实卡点",
            f"这类需求不是缺工具，而是缺顺序：{topic.demand_source}",
            "评论气泡或便签墙，把用户原话做匿名化展示",
        ),
        (
            "别一上来就做大项目",
            "先用一篇笔记验证：有没有人收藏、追问、要清单。",
            "错误路径与正确路径左右对比",
        ),
        (
            "3 步开始",
            "1. 找对标结构\n2. 挖评论需求\n3. 做一个可收藏清单",
            "编号清单卡片，使用清晰图标和留白",
        ),
        (
            "发布前补证据",
            "至少准备评论截图、对标拆解、自己的执行记录，避免空口承诺。",
            "证据清单、截图占位、勾选框",
        ),
        (
            "下一步",
            f"按「{voice}」的语气，把这篇做成一套可复用模板。",
            "结尾页，轻 CTA，提示收藏或评论关键词",
        ),
        (
            "选题库沉淀",
            "把标题、需求来源、证明材料、差异化写回知识库。",
            "表格或数据库视图风格",
        ),
        (
            "复盘指标",
            "看收藏、评论问题和私信关键词，再决定下一篇写什么。",
            "简洁数据看板，不展示虚构数据",
        ),
    ]

    return [
        CardPage(
            page=index,
            headline=headline,
            body=body,
            visual_prompt=f"{visual}；小红书图文卡片；短句；层级清楚；领域：{niche}",
        )
        for index, (headline, body, visual) in enumerate(blueprints[:count], start=1)
    ]


def _build_card_package(
    topic: TopicRecord,
    niche: str,
    audience: str,
    constraints: List[str],
    voice: str,
    card_count: int,
) -> CardPackage:
    cover_options = [
        topic.title,
        f"{audience}做「{niche}」，先别急着发笔记",
        f"评论区问爆的「{niche}」问题，我拆成 3 步",
        f"想做「{niche}」，先存这份验证清单",
    ]
    cards = _card_pages(topic, niche, card_count, voice)
    constraint_text = "；".join(constraints) if constraints else "不承诺收益，不虚构数据"
    caption = (
        f"很多人想做「{niche}」，但第一步就卡住。我的建议是先别追工具，"
        f"先从对标结构和评论区需求里找证据。\\n\\n"
        f"这篇按「{topic.demand_source}」拆成了可执行步骤，适合{audience}先收藏，"
        f"再用自己的素材补证据。\\n\\n"
        f"发布前提醒：{constraint_text}。"
    )
    hashtags = [
        _clean_hashtag(niche),
        "#小红书运营",
        "#内容选题",
        "#对标分析",
        "#评论区需求",
        "#图文笔记",
    ]
    return CardPackage(
        topic_title=topic.title,
        cover_options=cover_options,
        cards=cards,
        caption=caption,
        hashtags=hashtags,
        cta="想继续做的话，把你的对标标题和评论原话贴进来，我会继续扩成下一组卡片。",
        review_checklist=[
            "是否所有真实数据都有来源",
            "是否没有承诺阅读量、涨粉或收益",
            "是否只学习对标结构，没有复制原文",
            "是否每页卡片只有一个核心信息",
            "是否保留了下一轮评论采样入口",
        ],
    )


def process_node(
    state: ProcessNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> ProcessNodeOutput:
    """
    title: 选题库与图文卡片
    desc: 将对标和评论需求沉淀为选题库，并生成图文卡片规格
    integrations:
    """
    niche = str(_get(state, "niche", "")).strip()
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    constraints = _as_list(_get(state, "constraints", []))
    voice = str(_get(state, "brand_voice", "清醒、实操、少废话")).strip()
    card_count = int(_get(state, "card_count", 6) or 6)
    insights = list(_get(state, "demand_insights", []) or [])
    benchmarks = list(_get(state, "benchmark_accounts", []) or [])

    topic_bank = _build_topic_bank(niche, audience, insights)
    selected_topic = topic_bank[0]
    card_package = _build_card_package(
        selected_topic,
        niche=niche,
        audience=audience,
        constraints=constraints,
        voice=voice,
        card_count=card_count,
    )

    workflow_summary = (
        f"已完成「{niche}」内容工作流：整理 {len(benchmarks)} 条对标线索、"
        f"{len(insights)} 组评论需求，沉淀 {len(topic_bank)} 个选题，"
        f"并生成 {len(card_package.cards)} 页图文卡片规格。"
    )
    next_commands = [
        f"继续扩写「{selected_topic.title}」，生成更口语化的 {card_count} 页卡片文案。",
        f"把「{niche}」的评论需求整理成 Obsidian 选题库 Markdown。",
        "补充 5 条真实评论和 3 个对标标题，重新排序选题优先级。",
        "把当前卡片包改成更强封面标题和更短页面正文。",
    ]

    return ProcessNodeOutput(
        topic_bank=topic_bank,
        card_package=card_package,
        workflow_summary=workflow_summary,
        next_commands=next_commands,
    )
