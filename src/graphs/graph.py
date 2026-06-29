"""
主工作流编排
执行流程：
    GraphInput → model_select → greeting → [grok_call, openai_call] → merge → process → GraphOutput

其中 grok_call 和 openai_call 是并行执行的，两个都完成后才进入 merge 汇聚。
"""
from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
)
from graphs.nodes.model_select_node import model_select_node
from graphs.nodes.greeting_node import greeting_node
from graphs.nodes.grok_node import grok_node
from graphs.nodes.openai_node import openai_node
from graphs.nodes.merge_node import merge_node
from graphs.nodes.process_node import process_node


# 创建状态图
builder = StateGraph(
    GlobalState,
    input_schema=GraphInput,
    output_schema=GraphOutput
)

# ============= 添加节点 =============
builder.add_node(
    "model_select",
    model_select_node,
    metadata={"type": "agent", "llm_cfg": "config/model_select_cfg.json"}
)
builder.add_node(
    "greeting",
    greeting_node,
    metadata={"type": "agent", "llm_cfg": "config/greeting_cfg.json"}
)
builder.add_node("grok_call", grok_node)
builder.add_node("openai_call", openai_node)
builder.add_node(
    "merge",
    merge_node,
    metadata={"type": "agent", "llm_cfg": "config/merge_cfg.json"}
)
builder.add_node(
    "process",
    process_node,
    metadata={"type": "agent", "llm_cfg": "config/process_cfg.json"}
)

# ============= 设置工作流执行路径 =============
builder.set_entry_point("model_select")

# 串行链路
builder.add_edge("model_select", "greeting")

# 并行分支：greeting 后分叉到 grok_call 和 openai_call
builder.add_edge("greeting", "grok_call")
builder.add_edge("greeting", "openai_call")

# 汇聚：两个并行分支都完成后才执行 merge
builder.add_edge(["grok_call", "openai_call"], "merge")

# 后续链路
builder.add_edge("merge", "process")
builder.add_edge("process", END)

# ============= 编译图 =============
main_graph = builder.compile()