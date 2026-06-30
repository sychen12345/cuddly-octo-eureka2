"""
子工作流定义
──────────────
1. skill_rules_subgraph: Skill规则子工作流
   内部节点: 风格选择 → 尺寸选择 → 必选项 → 禁选项 → 一致性规则 → 规则同步回写

2. skill_subflow_subgraph: Skill子流程子工作流
   内部节点: [OpenAI步骤 || Grok步骤] → 子流程同步回写
"""
from langgraph.graph import StateGraph, END, START

from graphs.state import (
    SkillRulesSubgraphState,
    SkillRulesSubgraphInput,
    SkillRulesSubgraphOutput,
    SkillSubflowSubgraphState,
    SkillSubflowSubgraphInput,
    SkillSubflowSubgraphOutput,
)
from graphs.nodes.style_select_node import style_select_node
from graphs.nodes.aspect_ratio_node import aspect_ratio_node
from graphs.nodes.must_have_node import must_have_node
from graphs.nodes.avoid_node import avoid_node
from graphs.nodes.consistency_rules_node import consistency_rules_node
from graphs.nodes.rules_sync_node import rules_sync_node
from graphs.nodes.openai_steps_node import openai_steps_node
from graphs.nodes.grok_steps_node import grok_steps_node
from graphs.nodes.subflow_sync_node import subflow_sync_node


# ═══════════════════════════════════════════════════════════
#  Skill Rules 子工作流
#  并行扇出：5个配置节点同时执行 → 汇聚到同步回写节点
# ═══════════════════════════════════════════════════════════

sr_builder = StateGraph(
    SkillRulesSubgraphState,
    input_schema=SkillRulesSubgraphInput,
    output_schema=SkillRulesSubgraphOutput,
)

sr_builder.add_node("style_select", style_select_node)
sr_builder.add_node("aspect_ratio_select", aspect_ratio_node)
sr_builder.add_node("must_have_config", must_have_node)
sr_builder.add_node("avoid_config", avoid_node)
sr_builder.add_node("consistency_rules", consistency_rules_node)
sr_builder.add_node("rules_sync", rules_sync_node)

# 并行扇出：START → 5个配置节点
sr_builder.add_edge(START, "style_select")
sr_builder.add_edge(START, "aspect_ratio_select")
sr_builder.add_edge(START, "must_have_config")
sr_builder.add_edge(START, "avoid_config")
sr_builder.add_edge(START, "consistency_rules")

# 并行汇聚：5个配置节点 → rules_sync
sr_builder.add_edge(
    ["style_select", "aspect_ratio_select", "must_have_config", "avoid_config", "consistency_rules"],
    "rules_sync"
)
sr_builder.add_edge("rules_sync", END)

skill_rules_subgraph = sr_builder.compile()


# ═══════════════════════════════════════════════════════════
#  Skill Subflow 子工作流
#  并行：OpenAI步骤 || Grok步骤 → 子流程同步回写
# ═══════════════════════════════════════════════════════════

sf_builder = StateGraph(
    SkillSubflowSubgraphState,
    input_schema=SkillSubflowSubgraphInput,
    output_schema=SkillSubflowSubgraphOutput,
)

sf_builder.add_node("openai_steps", openai_steps_node)
sf_builder.add_node("grok_steps", grok_steps_node)
sf_builder.add_node("subflow_sync", subflow_sync_node)

# 并行扇出：START → OpenAI / Grok 两个步骤节点
sf_builder.add_edge(START, "openai_steps")
sf_builder.add_edge(START, "grok_steps")

# 并行汇聚：两个步骤节点 → subflow_sync
sf_builder.add_edge(["openai_steps", "grok_steps"], "subflow_sync")
sf_builder.add_edge("subflow_sync", END)

skill_subflow_subgraph = sf_builder.compile()
