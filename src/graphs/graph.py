"""
小红书内容工作流 - 主图编排。

GraphInput -> 对标与需求挖掘 -> 选题库与图文卡片 -> GraphOutput
"""
from langgraph.graph import END, StateGraph

from graphs.state import GlobalState, GraphInput, GraphOutput
from graphs.nodes.benchmark_demand_node import benchmark_demand_node
from graphs.nodes.topic_card_node import topic_card_node


builder = StateGraph(
    GlobalState,
    input_schema=GraphInput,
    output_schema=GraphOutput,
)

builder.add_node("benchmark_and_demand", benchmark_demand_node)
builder.add_node("topic_and_card", topic_card_node)

builder.set_entry_point("benchmark_and_demand")
builder.add_edge("benchmark_and_demand", "topic_and_card")
builder.add_edge("topic_and_card", END)

main_graph = builder.compile()
