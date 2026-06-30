"""
小红书内容工作流 — 主图编排
───────────────────────────
开始 -> 对标与需求挖掘 -> 选题库与高浏览选题 -> Skill规则与参考图
-> OpenAI/Grok Skill 子流程 -> 在线提示词编辑 -> OpenAI GPT5.5 文案
-> Grok Expert 套图 -> 结果审核打包 -> 结束
"""
from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
)
from graphs.nodes.greeting_node import greeting_node
from graphs.nodes.process_node import process_node
from graphs.nodes.skill_rules_node import skill_rules_node
from graphs.nodes.skill_subflow_node import skill_subflow_node
from graphs.nodes.prompt_node import prompt_node
from graphs.nodes.openai_text_node import openai_text_node
from graphs.nodes.grok_image_node import grok_image_node
from graphs.nodes.finalize_node import finalize_node


builder = StateGraph(
    GlobalState,
    input_schema=GraphInput,
    output_schema=GraphOutput,
)

# ── 注册节点 ──────────────────────────────────────────────
builder.add_node("greeting", greeting_node)
builder.add_node("process", process_node)
builder.add_node("skill_rules", skill_rules_node)
builder.add_node("skill_subflow", skill_subflow_node)
builder.add_node("prompt", prompt_node)
builder.add_node("openai_text", openai_text_node)
builder.add_node("grok_image", grok_image_node)
builder.add_node("finalize", finalize_node)

# ── 设置入口 ──────────────────────────────────────────────
builder.set_entry_point("greeting")

# ── 线性链路 ──────────────────────────────────────────────
builder.add_edge("greeting", "process")
builder.add_edge("process", "skill_rules")
builder.add_edge("skill_rules", "skill_subflow")
builder.add_edge("skill_subflow", "prompt")
builder.add_edge("prompt", "openai_text")
builder.add_edge("openai_text", "grok_image")
builder.add_edge("grok_image", "finalize")
builder.add_edge("finalize", END)

# ── 编译 ──────────────────────────────────────────────────
main_graph = builder.compile()
