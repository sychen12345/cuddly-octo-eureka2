"""
主图编排 — 小红书内容生产智能工作流

拓扑（运营业务树 + 可展开技能子树）：
  运营需求入口 → AI理解运营目标 →
    ├─「竞品调研」→ 竞品和用户需求分析 → 爆款选题机会池 → END
    ├─「爆款选题」→ 竞品和用户需求分析 → 爆款选题机会池 → END
    ├─「数据复盘」→ 竞品和用户需求分析 → 爆款选题机会池 → END
    └─「完整流程/文案生成/图片制作」
       → 竞品和用户需求分析 → 爆款选题机会池
       → 图片制作技能：选风格 → 图片制作技能：定比例
       → 图片制作技能：必备元素 → 图片制作技能：避坑清单
       → 图片制作技能：套图统一 → AI技能教练：检查图片规则
         ├─ 沉淀为图片技能 → 沉淀图片制作经验 → 文案技能：拆步骤
         └─ 仅本次使用 → 文案技能：拆步骤
       → 图片技能：拆步骤 → AI技能教练：检查生成流程
         ├─ 沉淀为生成技能 → 沉淀内容生成经验 → 运营确认生成方案
         └─ 仅本次使用 → 运营确认生成方案
       → AI生成小红书文案 ∥ AI生成小红书套图
       → 成品审核与复盘建议 → END
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
#  条件分支函数
# ═══════════════════════════════════════════════════════════

def intent_path(state: IntentPath) -> str:
    """
    title: AI理解运营目标
    desc: 根据运营输入判断当次要做竞品调研、爆款选题、数据复盘，还是完整生成内容。
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
    title: AI技能教练：判断图片技能是否值得沉淀
    desc: 判断运营的图片制作改动是本次临时使用，还是值得沉淀成长期图片技能。
    """
    if state.rules_judge_decision in {"sync", "sync_rules"}:
        return "沉淀为图片技能"
    else:
        return "仅本次使用"


def should_sync_subflows(state: SubflowJudgePath) -> str:
    """
    title: AI技能教练：判断生成技能是否值得沉淀
    desc: 判断运营的文案/图片步骤改动是本次临时使用，还是值得沉淀成长期生成技能。
    """
    if state.subflows_judge_decision in {"sync", "sync_subflows"}:
        return "沉淀为生成技能"
    else:
        return "仅本次使用"


# ═══════════════════════════════════════════════════════════
#  主图构建
# ═══════════════════════════════════════════════════════════

builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# —— 智能入口 ——
builder.add_node(
    "运营需求入口",
    intent_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/intent_analysis_cfg.json"},
)

# —— 竞品调研与选题 ——
builder.add_node(
    "竞品和用户需求分析",
    greeting_node,
    metadata={"type": "agent", "llm_cfg": "config/greeting_llm_cfg.json"},
)
builder.add_node(
    "爆款选题机会池",
    process_node,
    metadata={"type": "agent", "llm_cfg": "config/process_llm_cfg.json"},
)

# —— 图片风格规则 ——
builder.add_node("图片制作技能：选风格", style_select_node)
builder.add_node("图片制作技能：定比例", aspect_ratio_node)
builder.add_node("图片制作技能：必备元素", must_have_node)
builder.add_node("图片制作技能：避坑清单", avoid_node)
builder.add_node("图片制作技能：套图统一", consistency_rules_node)

# —— 图片技能检查与经验沉淀 ——
builder.add_node(
    "AI技能教练：检查图片规则",
    grok_rules_judge_node,
    metadata={"type": "agent", "llm_cfg": "config/grok_rules_judge_cfg.json"},
)
builder.add_node("沉淀图片制作经验", rules_sync_node)

# —— 文案/图片技能展开 ——
builder.add_node("文案技能：拆步骤", openai_steps_node)
builder.add_node("图片技能：拆步骤", grok_steps_node)

# —— 生成流程检查与经验沉淀 ——
builder.add_node(
    "AI技能教练：检查生成流程",
    grok_subflow_judge_node,
    metadata={"type": "agent", "llm_cfg": "config/grok_subflow_judge_cfg.json"},
)
builder.add_node("沉淀内容生成经验", subflow_sync_node)

# —— 提示词与生成 ——
builder.add_node("运营确认生成方案", prompt_node)
builder.add_node("AI生成小红书文案", openai_text_node)
builder.add_node("AI生成小红书套图", grok_image_node)

# —— 审核打包 ——
builder.add_node("成品审核与复盘建议", finalize_node)

# ═══════════════════════════════════════════════════════════
#  边编排
# ═══════════════════════════════════════════════════════════

# 入口 → AI理解运营目标
builder.set_entry_point("运营需求入口")
builder.add_conditional_edges(
    source="运营需求入口",
    path=intent_path,
    path_map={
        "竞品调研": "竞品和用户需求分析",
        "爆款选题": "竞品和用户需求分析",
        "数据复盘": "竞品和用户需求分析",
        "完整流程": "竞品和用户需求分析",
    },
)

# 竞品调研 → 根据运营目标分流
# 竞品调研 / 数据复盘 → END（只看数据，不进入内容生产）
# 爆款选题 → 爆款选题筛选 → END
# 完整流程 / 文案生成 / 图片制作 → 爆款选题筛选 → 继续
# 注：竞品调研分析 后统一走 爆款选题筛选，
# 然后在爆款选题筛选后用条件分支决定是否继续
# 简化处理：竞品和用户需求分析 → 爆款选题机会池 → 运营目标二次分支
builder.add_edge("竞品和用户需求分析", "爆款选题机会池")

# 爆款选题筛选后：根据意图决定是结束还是继续
# 这里用条件边把 "竞品调研" 和 "数据复盘" 引向 END
builder.add_conditional_edges(
    source="爆款选题机会池",
    path=intent_path,
    path_map={
        "竞品调研": END,
        "爆款选题": END,
        "数据复盘": END,
        "完整流程": "图片制作技能：选风格",
    },
)

# 风格规则线性链
builder.add_edge("图片制作技能：选风格", "图片制作技能：定比例")
builder.add_edge("图片制作技能：定比例", "图片制作技能：必备元素")
builder.add_edge("图片制作技能：必备元素", "图片制作技能：避坑清单")
builder.add_edge("图片制作技能：避坑清单", "图片制作技能：套图统一")

# 图片技能检查 → 条件分支
builder.add_edge("图片制作技能：套图统一", "AI技能教练：检查图片规则")
builder.add_conditional_edges(
    source="AI技能教练：检查图片规则",
    path=should_sync_rules,
    path_map={
        "沉淀为图片技能": "沉淀图片制作经验",
        "仅本次使用": "文案技能：拆步骤",
    },
)
builder.add_edge("沉淀图片制作经验", "文案技能：拆步骤")

# 子流程步骤
builder.add_edge("文案技能：拆步骤", "图片技能：拆步骤")

# 生成流程检查 → 条件分支
builder.add_edge("图片技能：拆步骤", "AI技能教练：检查生成流程")
builder.add_conditional_edges(
    source="AI技能教练：检查生成流程",
    path=should_sync_subflows,
    path_map={
        "沉淀为生成技能": "沉淀内容生成经验",
        "仅本次使用": "运营确认生成方案",
    },
)
builder.add_edge("沉淀内容生成经验", "运营确认生成方案")

# 并行生成
builder.add_edge("运营确认生成方案", "AI生成小红书文案")
builder.add_edge("运营确认生成方案", "AI生成小红书套图")

# 汇聚到审核打包
builder.add_edge(["AI生成小红书文案", "AI生成小红书套图"], "成品审核与复盘建议")
builder.add_edge("成品审核与复盘建议", END)

# 编译
main_graph = builder.compile()
