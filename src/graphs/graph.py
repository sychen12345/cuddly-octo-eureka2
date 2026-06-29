"""
主工作流编排
定义工作流的执行流程：GraphInput -> 节点A -> 节点B -> ... -> GraphOutput
"""
from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
)
from graphs.nodes.greeting_node import greeting_node
from graphs.nodes.process_node import process_node


# 创建状态图
# input_schema: 定义工作流的输入参数
# output_schema: 定义工作流的输出结果
builder = StateGraph(
    GlobalState,
    input_schema=GraphInput,
    output_schema=GraphOutput
)

# ============= 添加节点 =============
builder.add_node("greeting", greeting_node)
builder.add_node("process", process_node)

# ============= 设置工作流执行路径 =============
# 设置入口点：工作流从这里开始
builder.set_entry_point("greeting")

# 添加边：定义节点之间的执行顺序
builder.add_edge("greeting", "process")
builder.add_edge("process", END)

# ============= 编译图 =============
main_graph = builder.compile()