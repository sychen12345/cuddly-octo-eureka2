"""
主图编排 — 小红书内容生产智能工作流

拓扑（17 业务节点 + 1 智能入口）：
  需求接收 → 意图路由 →
    ├─「竞品调研」→ 竞品调研分析 → END
    ├─「爆款选题」→ 竞品调研分析 → 爆款选题筛选 → END
    ├─「数据复盘」→ 竞品调研分析 → END
    └─「完整流程/文案生成/图片制作」→ 竞品调研分析 → 爆款选题筛选
       → 视觉风格设定 → 图片尺寸设定 → 内容必选项 → 内容禁选项
       → 套图一致性规则 → 规则变更判断
         ├─ 同步规则 → 规则同步保存 → 文案生成步骤
         └─ 跳过 → 文案生成步骤
       → 图片生成步骤 → 步骤变更判断
         ├─ 同步步骤 → 步骤同步保存 → 提示词最终确认
         └─ 跳过 → 提示词最终确认
       → AI文案生成 ∥ AI图片生成
       → 内容审核打包 → END
"""

from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
    RulesJudgePath,
    SubflowJudgePath,
    IntentPath,
)
from graphs.nodes.intent_analysis_node import intent_analysis_node
from graphs.nodes.greeting_node import greeting_node
from graphs.nodes.process_node import process_node
from graphs.nodes.style_select_node import style_select_node
from graphs.nodes.aspect_ratio_node import aspect_ratio_node
from graphs.nodes.must_have_node import must_have_node
from graphs.nodes.avoid_node import avoid_node
from graphs.nodes.consistency_rules_node import consistency_rules_node
from graphs.nodes.grok_rules_judge_node import grok_rules_judge_node
from graphs.nodes.rules_sync_node import rules_sync_node
from graphs.nodes.openai_steps_node import openai_steps_node
from graphs.nodes.grok_steps_node import grok_steps_node
from graphs.nodes.grok_subflow_judge_node import grok_subflow_judge_node
from graphs.nodes.subflow_sync_node import subflow_sync_node
from graphs.nodes.prompt_node import prompt_node
from graphs.nodes.openai_text_node import openai_text_node
from graphs.nodes.grok_image_node import grok_image_node
from graphs.nodes.finalize_node import finalize_node


# ═══════════════════════════════════════════════════════════
#  条件路由函数
# ═══════════════════════════════════════════════════════════

def intent_path(state: IntentPath) -> str:
    """
    title: 意图路由
    desc: 根据 AI 识别的运营意图，决定走哪个工作流分支：
          竞品调研→只看数据 | 爆款选题→选完即止 | 完整流程→全部执行
    """
    intent: str = state.intent
    if intent == "竞品调研":
        return "竞品调研"
    elif intent == "爆款选题":
        return "爆款选题"
    elif intent == "数据复盘":
        return "数据复盘"
    else:
        return "完整流程"


def should_sync_rules(state: RulesJudgePath) -> str:
    """
    title: 规则变更路由
    desc: 根据 AI 判断结果决定是否同步规则到配置文件
    """
    if state.rules_judge_decision == "sync_rules":
        return "同步规则"
    else:
        return "跳过规则同步"


def should_sync_subflows(state: SubflowJudgePath) -> str:
    """
    title: 步骤变更路由
    desc: 根据 AI 判断结果决定是否同步步骤到配置文件
    """
    if state.subflows_judge_decision == "sync_subflows":
        return "同步步骤"
    else:
        return "跳过步骤同步"


# ═══════════════════════════════════════════════════════════
#  主图构建
# ═══════════════════════════════════════════════════════════

builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# —— 智能入口 ——
builder.add_node(
    "需求接收",
    intent_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/intent_analysis_cfg.json"},
)

# —— 竞品调研与选题 ——
builder.add_node(
    "竞品调研分析",
    greeting_node,
    metadata={"type": "agent", "llm_cfg": "config/greeting_llm_cfg.json"},
)
builder.add_node(
    "爆款选题筛选",
    process_node,
    metadata={"type": "agent", "llm_cfg": "config/process_llm_cfg.json"},
)

# —— 图片风格规则 ——
builder.add_node("视觉风格设定", style_select_node)
builder.add_node("图片尺寸设定", aspect_ratio_node)
builder.add_node("内容必选项", must_have_node)
builder.add_node("内容禁选项", avoid_node)
builder.add_node("套图一致性规则", consistency_rules_node)

# —— 规则判断与同步 ——
builder.add_node(
    "规则变更判断",
    grok_rules_judge_node,
    metadata={"type": "agent", "llm_cfg": "config/grok_rules_judge_cfg.json"},
)
builder.add_node("规则同步保存", rules_sync_node)

# —— 子流程步骤配置 ——
builder.add_node("文案生成步骤", openai_steps_node)
builder.add_node("图片生成步骤", grok_steps_node)

# —— 步骤判断与同步 ——
builder.add_node(
    "步骤变更判断",
    grok_subflow_judge_node,
    metadata={"type": "agent", "llm_cfg": "config/grok_subflow_judge_cfg.json"},
)
builder.add_node("步骤同步保存", subflow_sync_node)

# —— 提示词与生成 ——
builder.add_node("提示词最终确认", prompt_node)
builder.add_node("AI文案生成", openai_text_node)
builder.add_node("AI图片生成", grok_image_node)

# —— 审核打包 ——
builder.add_node("内容审核打包", finalize_node)

# ═══════════════════════════════════════════════════════════
#  边编排
# ═══════════════════════════════════════════════════════════

# 入口 → 意图路由
builder.set_entry_point("需求接收")
builder.add_conditional_edges(
    source="需求接收",
    path=intent_path,
    path_map={
        "竞品调研": "竞品调研分析",
        "爆款选题": "竞品调研分析",
        "数据复盘": "竞品调研分析",
        "完整流程": "竞品调研分析",
    },
)

# 竞品调研 → 根据意图分流
# 竞品调研 / 数据复盘 → END（只看数据，不进入内容生产）
# 爆款选题 → 爆款选题筛选 → END
# 完整流程 / 文案生成 / 图片制作 → 爆款选题筛选 → 继续
# 注：竞品调研分析 后统一走 爆款选题筛选，
# 然后在爆款选题筛选后用条件分支决定是否继续
# 简化处理：竞品调研分析 → 爆款选题筛选 → 意图二次路由
builder.add_edge("竞品调研分析", "爆款选题筛选")

# 爆款选题筛选后：根据意图决定是结束还是继续
# 这里用条件边把 "竞品调研" 和 "数据复盘" 引向 END
builder.add_conditional_edges(
    source="爆款选题筛选",
    path=intent_path,
    path_map={
        "竞品调研": END,
        "爆款选题": END,
        "数据复盘": END,
        "完整流程": "视觉风格设定",
    },
)

# 风格规则线性链
builder.add_edge("视觉风格设定", "图片尺寸设定")
builder.add_edge("图片尺寸设定", "内容必选项")
builder.add_edge("内容必选项", "内容禁选项")
builder.add_edge("内容禁选项", "套图一致性规则")

# 规则判断 → 条件路由
builder.add_edge("套图一致性规则", "规则变更判断")
builder.add_conditional_edges(
    source="规则变更判断",
    path=should_sync_rules,
    path_map={
        "同步规则": "规则同步保存",
        "跳过规则同步": "文案生成步骤",
    },
)
builder.add_edge("规则同步保存", "文案生成步骤")

# 子流程步骤
builder.add_edge("文案生成步骤", "图片生成步骤")

# 步骤判断 → 条件路由
builder.add_edge("图片生成步骤", "步骤变更判断")
builder.add_conditional_edges(
    source="步骤变更判断",
    path=should_sync_subflows,
    path_map={
        "同步步骤": "步骤同步保存",
        "跳过步骤同步": "提示词最终确认",
    },
)
builder.add_edge("步骤同步保存", "提示词最终确认")

# 并行生成
builder.add_edge("提示词最终确认", "AI文案生成")
builder.add_edge("提示词最终确认", "AI图片生成")

# 汇聚到审核打包
builder.add_edge(["AI文案生成", "AI图片生成"], "内容审核打包")
builder.add_edge("内容审核打包", END)

# 编译
main_graph = builder.compile()
