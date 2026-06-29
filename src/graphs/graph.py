"""
主工作流编排
定义工作流的执行流程：GraphInput -> model_select -> greeting -> process -> GraphOutput
"""
from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
)
from graphs.nodes.model_select_node import model_select_node
from graphs.nodes.greeting_node import greeting_node
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
builder.add_node("greeting", greeting_node)
builder.add_node("process", process_node)

# ============= 设置工作流执行路径 =============
builder.set_entry_point("model_select")

builder.add_edge("model_select", "greeting")
builder.add_edge("greeting", "process")
builder.add_edge("process", END)

# ============= 编译图 =============
main_graph = builder.compile()