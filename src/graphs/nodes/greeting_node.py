"""
节点1: 对标与需求挖掘 (greeting_node)
──────────────────────────────────────
输入: niche, audience, goal, benchmark_notes, comment_notes
输出: research_brief, benchmark_accounts, demand_insights
"""
import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    GreetingNodeInput,
    GreetingNodeOutput,
    BenchmarkAccount,
    DemandInsight,
)


# ── 通用辅助 ──────────────────────────────────────────────
def _get(obj: Any, key: str, default: Any = None) -> Any:
    """从 dict / pydantic / namespace 取值。"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _dump(obj: Any) -> Any:
    """转为 JSON-safe 结构。"""
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


# ── 分类映射 ──────────────────────────────────────────────
_PAIN_KEYWORDS: Dict[str, List[str]] = {
    "新手门槛": ["基础", "入门", "不会", "零基础", "小白", "开始", "从0", "第一步", "能不能做"],
    "时间约束": ["下班", "碎片", "兼职", "时间", "忙碌", "副业", "每天"],
    "路径不清": ["怎么开始", "步骤", "路线", "方向", "不知道先做什么", "顺序"],
    "变现焦虑": ["赚钱", "收入", "变现", "收益", "月入", "副业收入"],
    "信任缺失": ["真的吗", "靠谱", "骗子", "割韭菜", "真假"],
    "技能焦虑": ["不会编程", "没有经验", "专业", "技术", "技能"],
}


def _classify_comment(text: str) -> str:
    t: str = text.lower()
    for cluster, kws in _PAIN_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return cluster
    return "其他需求"


def _build_benchmark(note: str, idx: int) -> BenchmarkAccount:
    parts: List[str] = [p.strip() for p in re.split(r"[，,；;\n]", note) if p.strip()]
    signal: str = parts[0] if parts else note[:60]
    content_patterns: List[str] = parts[1:3] if len(parts) > 1 else []
    visual_patterns: List[str] = parts[3:5] if len(parts) > 3 else []
    risk_notes: List[str] = ["只复用结构和需求信号，不复刻原文、封面或人设"]
    return BenchmarkAccount(
        name=f"对标线索 {idx}",
        platform="小红书",
        signal=signal,
        content_patterns=content_patterns,
        visual_patterns=visual_patterns,
        risk_notes=risk_notes,
    )


def _build_insight(comment: str) -> DemandInsight:
    cluster: str = _classify_comment(comment)
    return DemandInsight(
        cluster=cluster,
        user_words=[comment],
        pain=f"用户在「{cluster}」上的真实卡点",
        desired_outcome=f"解决「{cluster}」问题",
        content_angle=f"从{cluster}角度切入内容",
        confidence="medium",
    )


def _merge_insights(insights: List[DemandInsight]) -> List[DemandInsight]:
    merged: Dict[str, DemandInsight] = {}
    for ins in insights:
        key: str = ins.cluster
        if key in merged:
            existing: DemandInsight = merged[key]
            existing.user_words.extend(ins.user_words)
        else:
            merged[key] = ins.model_copy(deep=True)
    return list(merged.values())


# ── 节点函数 ──────────────────────────────────────────────
def greeting_node(
    state: GreetingNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> GreetingNodeOutput:
    """
    title: 对标与需求挖掘
    desc: 整理对标素材与评论需求，沉淀可复用的对标线索和需求洞察
    integrations:
    """
    niche: str = _get(state, "niche", "")
    audience: str = _get(state, "audience", "")
    goal: str = _get(state, "goal", "")
    benchmark_notes: List[str] = _get(state, "benchmark_notes", [])
    comment_notes: List[str] = _get(state, "comment_notes", [])

    # 构建对标线索
    benchmark_accounts: List[BenchmarkAccount] = []
    for idx, note in enumerate(benchmark_notes, 1):
        benchmark_accounts.append(_build_benchmark(note, idx))

    # 构建需求洞察
    raw_insights: List[DemandInsight] = []
    for c in comment_notes:
        raw_insights.append(_build_insight(c))
    demand_insights: List[DemandInsight] = _merge_insights(raw_insights)

    # 生成摘要
    brief_parts: List[str] = []
    if niche:
        brief_parts.append(f"领域：{niche}")
    if audience:
        brief_parts.append(f"人群：{audience}")
    if goal:
        brief_parts.append(f"目标：{goal}")
    brief_parts.append(f"对标线索 {len(benchmark_accounts)} 条")
    brief_parts.append(f"需求洞察 {len(demand_insights)} 组")
    research_brief: str = "；".join(brief_parts)

    return GreetingNodeOutput(
        research_brief=research_brief,
        benchmark_accounts=benchmark_accounts,
        demand_insights=demand_insights,
    )
