"""
对标与评论需求挖掘节点。

从领域、对标素材和评论原话中提取对标结构与用户需求，
生成 research_brief 供下游节点引用。
"""
from typing import Any, Dict, Iterable, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    BenchmarkAccount,
    BenchmarkDemandNodeInput,
    BenchmarkDemandNodeOutput,
    DemandInsight,
)


def _get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, Iterable):
        items = []
        for item in value:
            text = str(item).strip()
            if text:
                items.append(text)
        return items
    return [str(value).strip()]


def _clip(text: str, limit: int = 80) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _check_api_keys(state: Any) -> str:
    grok_api_key = str(_get(state, "grok_api_key", "")).strip()
    openai_api_key = str(_get(state, "openai_api_key", "")).strip()
    missing = []
    if not grok_api_key:
        missing.append("Grok API Key")
    if not openai_api_key:
        missing.append("OpenAI API Key")
    if missing:
        return f"未提供 {', '.join(missing)}，本轮仅执行规则匹配，未调用外部模型。"
    return "已收到 Grok 和 OpenAI API Key，仅用于本次运行，不会写入输出。"


def _benchmark_patterns(note: str) -> List[str]:
    patterns = []
    if any(word in note for word in ["标题", "封面", "钩子", "普通人", "别再"]):
        patterns.append("用强场景标题先点出读者处境，再给可执行承诺")
    if any(word in note for word in ["步骤", "清单", "路线", "从0", "从 0"]):
        patterns.append("正文采用步骤清单结构，降低新手行动门槛")
    if any(word in note for word in ["案例", "数据", "截图", "结果", "验证"]):
        patterns.append("用案例、截图或验证过程建立可信度")
    if any(word in note for word in ["领取", "模板", "资料", "评论"]):
        patterns.append("结尾用资料、模板或清单做轻 CTA")
    if not patterns:
        patterns.append("拆解标题、开头痛点、正文步骤、证据展示和轻 CTA")
    return patterns


def _visual_patterns(note: str) -> List[str]:
    patterns = []
    if any(word in note for word in ["封面", "大字", "标题"]):
        patterns.append("封面用大标题和明确人群，第一眼说明收益点")
    if any(word in note for word in ["截图", "对比", "表格"]):
        patterns.append("用截图、对比表或清单页增强真实感")
    if any(word in note for word in ["卡片", "图文", "多页"]):
        patterns.append("多页卡片一页一个观点，避免单页信息过载")
    if not patterns:
        patterns.append("保持小红书图文卡片的短句、分层和留白")
    return patterns


def _classify_comment(comment: str) -> str:
    lowered = comment.lower()
    if any(word in comment for word in ["小白", "没有基础", "零基础", "不会", "不懂"]) or (
        "基础" in comment and any(word in comment for word in ["没有", "无", "零"])
    ):
        return "新手门槛"
    if any(word in comment for word in ["下班", "时间", "多久", "每天", "副业"]):
        return "时间约束"
    if any(word in comment for word in ["怎么", "步骤", "从0", "从 0", "流程", "路径"]):
        return "路径不清"
    if any(word in comment for word in ["资料", "模板", "清单", "案例", "能不能给"]):
        return "资源请求"
    if any(word in comment for word in ["钱", "成本", "免费", "付费", "贵"]):
        return "成本顾虑"
    if any(word in lowered for word in ["ai", "chatgpt", "gpt", "codex"]):
        return "工具焦虑"
    return "未分类需求"


def _insight_for_cluster(cluster: str, words: List[str]) -> DemandInsight:
    mapping: Dict[str, tuple] = {
        "新手门槛": (
            "用户担心自己没有经验、技能或背景，迈不出第一步",
            "得到低门槛、可照做的入门路径",
            "用新手视角拆出第一周行动清单",
        ),
        "时间约束": (
            "用户只有碎片时间，害怕项目占用过多精力",
            "找到下班后也能推进的小步骤",
            "设计低时间成本的验证路线",
        ),
        "路径不清": (
            "用户知道方向但不知道先做什么、后做什么",
            "获得从 0 到 1 的顺序和检查点",
            "做一篇路线图或避坑清单",
        ),
        "资源请求": (
            "用户希望直接拿到模板、清单、案例或资料",
            "得到可以保存和复用的工具包",
            "把内容设计成可收藏的资料清单",
        ),
        "成本顾虑": (
            "用户担心投入太多钱或试错成本过高",
            "先用低成本方式验证需求",
            "强调免费工具、最小验证和风险边界",
        ),
        "工具焦虑": (
            "用户被工具名和技术路线劝退",
            "知道该用什么工具以及为什么用",
            "把工具选择翻译成任务选择",
        ),
        "未分类需求": (
            "评论表达了兴趣，但缺少足够上下文",
            "需要继续追问具体场景",
            "把问题转成调研卡片，继续采样评论",
        ),
    }
    pain, outcome, angle = mapping.get(cluster, mapping["未分类需求"])
    confidence = "high" if len(words) >= 3 else "medium" if len(words) >= 1 else "low"
    return DemandInsight(
        cluster=cluster,
        user_words=[_clip(word, 48) for word in words[:4]],
        pain=pain,
        desired_outcome=outcome,
        content_angle=angle,
        confidence=confidence,
    )


def _build_benchmarks(niche: str, notes: List[str]) -> List[BenchmarkAccount]:
    if not notes:
        return [
            BenchmarkAccount(
                name="待采样对标账号",
                signal=f"当前未提供真实对标素材，需要围绕「{niche}」补充近期起号账号、爆款标题和评论截图",
                content_patterns=[
                    "优先采样近期起号、连续发布且内容结构稳定的账号",
                    "记录标题、开头痛点、正文结构、证明方式和 CTA",
                ],
                visual_patterns=["采集封面大字、卡片页数、截图/表格使用方式"],
                risk_notes=["未联网验证前，不声称任何真实阅读量、粉丝量或爆款数据"],
            )
        ]

    benchmarks = []
    for index, note in enumerate(notes[:6], start=1):
        benchmarks.append(
            BenchmarkAccount(
                name=f"对标线索 {index}",
                signal=_clip(note, 96),
                content_patterns=_benchmark_patterns(note),
                visual_patterns=_visual_patterns(note),
                risk_notes=["只复用结构和需求信号，不复刻原文、封面或人设"],
            )
        )
    return benchmarks


def _build_insights(comments: List[str]) -> List[DemandInsight]:
    if not comments:
        return [
            DemandInsight(
                cluster="待采样评论",
                user_words=[],
                pain="当前缺少评论原话，无法确认真实需求强度",
                desired_outcome="先补齐评论、私信或问答样本",
                content_angle="输出评论采样清单，再做需求聚类",
                confidence="low",
            )
        ]

    grouped: Dict[str, List[str]] = {}
    for comment in comments:
        grouped.setdefault(_classify_comment(comment), []).append(comment)

    return [_insight_for_cluster(cluster, words) for cluster, words in grouped.items()]


def benchmark_demand_node(
    state: BenchmarkDemandNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> BenchmarkDemandNodeOutput:
    """
    title: 对标与需求挖掘
    desc: 从领域、对标素材和评论原话中提取对标结构与用户需求
    integrations:
    """
    api_key_status = _check_api_keys(state)
    niche = str(_get(state, "niche", "")).strip()
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    goal = str(_get(state, "goal", "生成小红书图文卡片")).strip()
    benchmark_notes = _as_list(_get(state, "benchmark_notes", []))
    comment_notes = _as_list(_get(state, "comment_notes", []))

    benchmarks = _build_benchmarks(niche, benchmark_notes)
    insights = _build_insights(comment_notes)

    evidence_note = "已使用用户提供的对标和评论素材"
    if not benchmark_notes or not comment_notes:
        missing = []
        if not benchmark_notes:
            missing.append("对标素材")
        if not comment_notes:
            missing.append("评论素材")
        evidence_note = f"缺少{'、'.join(missing)}，本轮输出会标注为假设或采样框架"

    research_brief = (
        f"围绕「{niche}」为「{audience}」完成「{goal}」的前置研究。"
        f"对标线索 {len(benchmark_notes)} 条，评论线索 {len(comment_notes)} 条。"
        f"{evidence_note}。{api_key_status}"
    )

    return BenchmarkDemandNodeOutput(
        research_brief=research_brief,
        benchmark_accounts=benchmarks,
        demand_insights=insights,
    )
