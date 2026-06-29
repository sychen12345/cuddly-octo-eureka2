"""
主工作流编排。

GraphInput -> 对标与需求挖掘 -> 选题库与图文卡片 -> GraphOutput
"""
from __future__ import annotations

from typing import Any, Dict

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - local fallback
    END = "__end__"
    StateGraph = None  # type: ignore

try:
    from graphs.nodes.greeting_node import greeting_node
    from graphs.nodes.process_node import process_node
    from graphs.state import GlobalState, GraphInput, GraphOutput
except ImportError:
    from .greeting_node import greeting_node
    from .process_node import process_node
    from .state import GlobalState, GraphInput, GraphOutput


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

        process_output = process_node(state)
        state = GlobalState(**{**_dump(state), **_dump(process_output)})

        return _dump(
            GraphOutput(
                workflow_summary=state.workflow_summary,
                benchmark_accounts=state.benchmark_accounts,
                demand_insights=state.demand_insights,
                topic_bank=state.topic_bank,
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
    builder.add_node("topic_and_card", process_node)

    builder.set_entry_point("benchmark_and_demand")
    builder.add_edge("benchmark_and_demand", "topic_and_card")
    builder.add_edge("topic_and_card", END)

    main_graph = builder.compile()
else:
    main_graph = LocalContentWorkflow()
