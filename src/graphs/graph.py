"""
小红书内容全栈工作流 — 主图编排
──────────────────────────────────────────────────────
完整流程（15 个画布可见节点）：
  对标与需求挖掘 → 选题库 → 风格选择 → 尺寸选择 → 必选项 → 禁选项 → 一致性规则 → 规则同步
      ─┬─ OpenAI步骤配置  (并行)
       └─ Grok步骤配置   (并行)
      → 子流程同步 → 提示词编辑
      ─┬─ OpenAI 文案  (并行)
       └─ Grok 套图   (并行)
      → 结果审核打包
"""
from langgraph.graph import StateGraph, END

from graphs.state import GlobalState, GraphInput, GraphOutput

# 主图节点导入
from graphs.nodes.greeting_node import greeting_node
from graphs.nodes.process_node import process_node
# Skill 规则子流程 — 画布可见节点
from graphs.nodes.style_select_node import style_select_node
from graphs.nodes.aspect_ratio_node import aspect_ratio_node
from graphs.nodes.must_have_node import must_have_node
from graphs.nodes.avoid_node import avoid_node
from graphs.nodes.consistency_rules_node import consistency_rules_node
from graphs.nodes.rules_sync_node import rules_sync_node
# Skill 子流程 — 画布可见节点
from graphs.nodes.openai_steps_node import openai_steps_node
from graphs.nodes.grok_steps_node import grok_steps_node
from graphs.nodes.subflow_sync_node import subflow_sync_node
# 生成 & 结果
from graphs.nodes.prompt_node import prompt_node
from graphs.nodes.openai_text_node import openai_text_node
from graphs.nodes.grok_image_node import grok_image_node
from graphs.nodes.finalize_node import finalize_node

# ── 创建状态图 ──
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# ── 注册节点 ──
# 需求阶段
builder.add_node("greeting", greeting_node, metadata={"type": "agent", "llm_cfg": "config/greeting_llm_cfg.json"})
builder.add_node("process", process_node, metadata={"type": "agent", "llm_cfg": "config/process_llm_cfg.json"})

# Skill 规则 — 画布上直接可见的节点
builder.add_node("style_select", style_select_node)
builder.add_node("aspect_ratio", aspect_ratio_node)
builder.add_node("must_have", must_have_node)
builder.add_node("avoid", avoid_node)
builder.add_node("consistency_rules", consistency_rules_node)
builder.add_node("rules_sync", rules_sync_node)

# Skill 子流程 — 画布上直接可见的节点
builder.add_node("openai_steps", openai_steps_node)
builder.add_node("grok_steps", grok_steps_node)
builder.add_node("subflow_sync", subflow_sync_node)

# 生成 & 结果
builder.add_node("prompt", prompt_node)
builder.add_node("openai_text", openai_text_node)
builder.add_node("grok_image", grok_image_node)
builder.add_node("finalize", finalize_node)

# ── 设置入口点 ──
builder.set_entry_point("greeting")

# ── 添加边 ──
# 需求阶段：greeting → process
builder.add_edge("greeting", "process")

# Skill 规则阶段：process → 风格选择 → 尺寸选择 → 必选项 → 禁选项 → 一致性规则 → 规则同步
builder.add_edge("process", "style_select")
builder.add_edge("style_select", "aspect_ratio")
builder.add_edge("aspect_ratio", "must_have")
builder.add_edge("must_have", "avoid")
builder.add_edge("avoid", "consistency_rules")
builder.add_edge("consistency_rules", "rules_sync")

# Skill 子流程阶段：规则同步 → [OpenAI步骤 / Grok步骤] → 子流程同步（并行汇聚）
builder.add_edge("rules_sync", "openai_steps")
builder.add_edge("rules_sync", "grok_steps")
builder.add_edge(["openai_steps", "grok_steps"], "subflow_sync")

# 提示词编辑
builder.add_edge("subflow_sync", "prompt")

# 生成阶段：prompt → [OpenAI文案 / Grok套图] → finalize（并行汇聚）
builder.add_edge("prompt", "openai_text")
builder.add_edge("prompt", "grok_image")
builder.add_edge(["openai_text", "grok_image"], "finalize")

# 结束
builder.add_edge("finalize", END)

# ── 编译图 ──
main_graph = builder.compile()
