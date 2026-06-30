"""节点 1/8 — 对标与需求挖掘 (greeting)"""

import json, os
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from jinja2 import Template

from graphs.state import (
    BenchmarkAccount, DemandInsight,
    GreetingNodeInput, GreetingNodeOutput,
)
from graphs.nodes.http_utils import call_openai_chat


def _require_api_keys(state: GreetingNodeInput) -> str:
    missing: List[str] = []
    if state.execute_model_calls and not state.openai_api_key:
        missing.append("OpenAI API Key")
    if state.execute_model_calls and not state.grok_api_key:
        missing.append("Grok API Key")
    if missing:
        raise ValueError(f"运行工作流前必须输入：{', '.join(missing)}。")
    return "ok"


def _build_benchmark_accounts(benchmark_notes: List[str]) -> List[BenchmarkAccount]:
    accounts: List[BenchmarkAccount] = []
    for idx, note in enumerate(benchmark_notes, 1):
        accounts.append(BenchmarkAccount(
            name=f"对标线索 {idx}",
            platform="小红书",
            signal=note,
            content_patterns=[note],
            visual_patterns=[],
            risk_notes=["只复用结构和需求信号，不复刻原文、封面或人设"],
        ))
    return accounts


def _build_demand_insights(comment_notes: List[str]) -> List[DemandInsight]:
    insights: List[DemandInsight] = []
    # 简单聚类：每条评论作为一个需求簇
    clusters: Dict[str, List[str]] = {}
    for note in comment_notes:
        label = "新手门槛" if any(w in note for w in ["基础", "不会", "没有", "能不能"]) else \
                "时间约束" if any(w in note for w in ["下班", "时间", "碎片"]) else \
                "路径不清"
        clusters.setdefault(label, []).append(note)

    for label, notes in clusters.items():
        insights.append(DemandInsight(
            cluster=label,
            user_words=notes,
            pain=f"用户在「{label}」上的真实卡点",
            desired_outcome=f"解决「{label}」问题",
            content_angle=f"从{label}角度切入内容",
            confidence="medium",
        ))
    return insights


def greeting_node(
    state: GreetingNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> GreetingNodeOutput:
    """
    title: 对标与需求挖掘
    desc: 从对标笔记信号和评论信号中提取对标账号和需求洞察
    integrations:
    """
    ctx = runtime.context
    api_key_status = _require_api_keys(state)

    benchmark_accounts = _build_benchmark_accounts(state.benchmark_notes)
    demand_insights = _build_demand_insights(state.comment_notes)

    # 如果需要真实调用模型，用 OpenAI 做深度分析
    if state.execute_model_calls and state.openai_api_key:
        sp = f"你是小红书内容策略专家。赛道：{state.niche}，目标人群：{state.audience}。"
        up = (
            f"请基于以下对标信号和评论信号，分别提炼 2-3 条对标账号洞察和 2-3 个需求洞察。\n"
            f"对标信号：{json.dumps(state.benchmark_notes, ensure_ascii=False)}\n"
            f"评论信号：{json.dumps(state.comment_notes, ensure_ascii=False)}\n"
            f"约束：{json.dumps(state.constraints, ensure_ascii=False)}\n"
            f"请返回 JSON：{{\"benchmark_accounts\": [...], \"demand_insights\": [...]}}"
        )
        raw = call_openai_chat(state.openai_api_key, system_prompt=sp, user_prompt=up)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                ba_list = parsed.get("benchmark_accounts", [])
                di_list = parsed.get("demand_insights", [])
                if isinstance(ba_list, list) and len(ba_list) > 0:
                    benchmark_accounts = [BenchmarkAccount(**a) if isinstance(a, dict) else a for a in ba_list]
                if isinstance(di_list, list) and len(di_list) > 0:
                    demand_insights = [DemandInsight(**d) if isinstance(d, dict) else d for d in di_list]
        except (json.JSONDecodeError, TypeError):
            pass  # fallback to rule-based results

    research_brief = (
        f"赛道「{state.niche}」面向「{state.audience}」，"
        f"已整理 {len(benchmark_accounts)} 条对标线索、"
        f"{len(demand_insights)} 组需求。"
    )

    return GreetingNodeOutput(
        research_brief=research_brief,
        benchmark_accounts=benchmark_accounts,
        demand_insights=demand_insights,
    )
