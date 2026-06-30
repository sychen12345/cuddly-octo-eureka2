"""
主工作流编排。

GraphInput -> 对标与需求挖掘 -> 选题库与高浏览选题 -> Skill规则与参考图
-> OpenAI/Grok Skill 子流程 -> 在线提示词编辑 -> OpenAI GPT5.5 文案
                                     └-> Grok Expert 套图
OpenAI/Grok 两个生成分支在结果审核打包节点汇合。
"""
from __future__ import annotations

from typing import Any, Dict

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - local fallback
    END = "__end__"
    StateGraph = None  # type: ignore

try:
    from .finalize_node import finalize_node
    from .greeting_node import greeting_node
    from .grok_image_node import grok_image_node
    from .openai_text_node import openai_text_node
    from .prompt_node import prompt_node
    from .process_node import process_node
    from .skill_subflow_node import skill_subflow_node
    from .skill_rules_node import skill_rules_node
    from .state import GlobalState, GraphInput, GraphOutput
except ImportError:
    from graphs.nodes.finalize_node import finalize_node
    from graphs.nodes.greeting_node import greeting_node
    from graphs.nodes.grok_image_node import grok_image_node
    from graphs.nodes.openai_text_node import openai_text_node
    from graphs.nodes.prompt_node import prompt_node
    from graphs.nodes.process_node import process_node
    from graphs.nodes.skill_subflow_node import skill_subflow_node
    from graphs.nodes.skill_rules_node import skill_rules_node
    from graphs.state import GlobalState, GraphInput, GraphOutput


def _dump(model: Any) -> Dict[str, Any]:
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return {}


class LocalContentWorkflow:
    """Minimal local runner used when LangGraph is unavailable."""

    def invoke(self, input_data: Dict[str, Any] | GraphInput) -> Dict[str, Any]:
        graph_input = input_data if isinstance(input_data, GraphInput) else GraphInput(**input_data)
        state = GlobalState(**_dump(graph_input))

        research_output = greeting_node(state)
        state = GlobalState(**{**_dump(state), **_dump(research_output)})

        topic_output = process_node(state)
        state = GlobalState(**{**_dump(state), **_dump(topic_output)})

        rules_output = skill_rules_node(state)
        state = GlobalState(**{**_dump(state), **_dump(rules_output)})

        subflow_output = skill_subflow_node(state)
        state = GlobalState(**{**_dump(state), **_dump(subflow_output)})

        prompt_output = prompt_node(state)
        state = GlobalState(**{**_dump(state), **_dump(prompt_output)})

        branch_state = state
        text_output = openai_text_node(branch_state)
        image_output = grok_image_node(branch_state)
        state = GlobalState(**{**_dump(state), **_dump(text_output), **_dump(image_output)})

        final_output = finalize_node(state)
        state = GlobalState(**{**_dump(state), **_dump(final_output)})

        return _dump(
            GraphOutput(
                workflow_summary=state.workflow_summary,
                workflow_steps=state.workflow_steps,
                benchmark_accounts=state.benchmark_accounts,
                demand_insights=state.demand_insights,
                topic_bank=state.topic_bank,
                selected_topic=state.selected_topic,
                image_style_rules=state.image_style_rules,
                workflow_diagram_nodes=state.workflow_diagram_nodes,
                workflow_diagram_edges=state.workflow_diagram_edges,
                operator_edit_panels=state.operator_edit_panels,
                skill_subflows=state.skill_subflows,
                editable_prompts=state.editable_prompts,
                openai_text_package=state.openai_text_package,
                grok_image_set=state.grok_image_set,
                card_package=state.card_package,
                next_commands=state.next_commands,
            )
        )


if StateGraph is not None:
    builder = StateGraph(
        GlobalState,
        input_schema=GraphInput,
        output_schema=GraphOutput,
    )

    builder.add_node("benchmark_and_demand", greeting_node)
    builder.add_node("topic_selection", process_node)
    builder.add_node("skill_rules", skill_rules_node)
    builder.add_node("skill_subflows", skill_subflow_node)
    builder.add_node("prompt_editor", prompt_node)
    builder.add_node("openai_text", openai_text_node)
    builder.add_node("grok_image_set", grok_image_node)
    builder.add_node("finalize", finalize_node)

    builder.set_entry_point("benchmark_and_demand")
    builder.add_edge("benchmark_and_demand", "topic_selection")
    builder.add_edge("topic_selection", "skill_rules")
    builder.add_edge("skill_rules", "skill_subflows")
    builder.add_edge("skill_subflows", "prompt_editor")
    builder.add_edge("prompt_editor", "openai_text")
    builder.add_edge("prompt_editor", "grok_image_set")
    builder.add_edge("openai_text", "finalize")
    builder.add_edge("grok_image_set", "finalize")
    builder.add_edge("finalize", END)

    main_graph = builder.compile()
else:
    main_graph = LocalContentWorkflow()
