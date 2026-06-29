"""
主工作流编排
执行流程：
    GraphInput → model_select → greeting → [task1, task2] → process → GraphOutput

其中 task1 和 task2 是并行执行的，两个都完成后才进入 process 汇聚。
"""
from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
)
from graphs.nodes.model_select_node import model_select_node
from graphs.nodes.greeting_node import greeting_node
from graphs.nodes.task1_node import task1_node
from graphs.nodes.task2_node import task2_node
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
builder.add_node("task1", task1_node)
builder.add_node("task2", task2_node)
builder.add_node(
    "process",
    process_node,
    metadata={"type": "agent", "llm_cfg": "config/process_cfg.json"}
)

# ============= 设置工作流执行路径 =============
builder.set_entry_point("model_select")

# 串行链路
builder.add_edge("model_select", "greeting")

# 并行分支：greeting 后分叉到 task1 和 task2
builder.add_edge("greeting", "task1")
builder.add_edge("greeting", "task2")

# 汇聚：两个并行分支都完成后才执行 process
builder.add_edge(["task1", "task2"], "process")

# 后续链路
builder.add_edge("process", END)

# ============= 编译图 =============
main_graph = builder.compile()