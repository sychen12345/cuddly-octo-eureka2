"""节点 8/8 — 结果审核打包 (finalize)"""

from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    CardPage, CardPackage, EditablePrompt, GrokImageSet, ImageStyleRules,
    OpenAITextPackage, OperatorControl, OperatorEditPanel, SkillSubflowDef,
    TopicRecord, WorkflowDiagramNode, WorkflowDiagramEdge, WorkflowStepInfo,
    FinalizeNodeInput, FinalizeNodeOutput,
)


def _build_card_package(
    selected_topic: Optional[TopicRecord],
    openai_pkg: Optional[OpenAITextPackage],
    grok_set: Optional[GrokImageSet],
) -> CardPackage:
    topic_title = selected_topic.title if selected_topic else ""
    cover_options = openai_pkg.title_options if openai_pkg and openai_pkg.title_options else [topic_title]
    caption = openai_pkg.post_description if openai_pkg else ""
    cards: List[CardPage] = []

    # 合并文案和图片
    scripts = openai_pkg.card_script if openai_pkg else []
    images = grok_set.images if grok_set else []

    max_pages = max(len(scripts), len(images), 1)
    for i in range(max_pages):
        page = i + 1
        headline = scripts[i] if i < len(scripts) else f"第{page}页：待补充"
        body = headline
        visual = images[i].prompt if i < len(images) else ""
        cards.append(CardPage(page=page, headline=headline, body=body, visual_prompt=visual))

    return CardPackage(
        topic_title=topic_title,
        cover_options=cover_options,
        cards=cards,
        caption=caption,
        hashtags=[f"#{topic_title}", "#小红书运营", "#内容选题"],
        cta="想继续做的话，把你的对标标题和评论原话贴进来，我会继续扩成下一组卡片。",
        review_checklist=[
            "是否所有真实数据都有来源",
            "是否没有承诺阅读量、涨粉或收益",
            "是否只学习对标结构，没有复制原文",
            "是否每页卡片只有一个核心信息",
            "是否保留了下一轮评论采样入口",
        ],
    )


def _build_operator_control(
    skill_subflows: List[SkillSubflowDef],
    editable_prompts: List[EditablePrompt],
) -> OperatorControl:
    panels: List[OperatorEditPanel] = []

    for subflow in skill_subflows:
        panels.append(OperatorEditPanel(
            key=subflow.skill_key,
            title=subflow.title,
            panel_type="subflow",
            editable=subflow.editable,
            content=subflow.model_dump(),
        ))

    for prompt in editable_prompts:
        panels.append(OperatorEditPanel(
            key=prompt.key,
            title=prompt.title,
            panel_type="prompt",
            editable=prompt.editable,
            content=prompt.model_dump(),
        ))

    return OperatorControl(
        edit_panels=panels,
        actions=["edit_prompt", "toggle_step", "rerun"],
        status="ready",
    )


def _build_diagram(workflow_steps: List[WorkflowStepInfo]) -> tuple:
    nodes: List[WorkflowDiagramNode] = []
    edges: List[WorkflowDiagramEdge] = []
    positions = [
        ("greeting", "对标与需求挖掘", "task", 0, 0),
        ("process", "选题库", "task", 1, 0),
        ("skill_rules", "Skill规则", "task", 2, 0),
        ("skill_subflow", "子流程", "task", 3, 0),
        ("prompt", "提示词编辑", "task", 4, 0),
        ("openai_text", "OpenAI 文案", "task", 5, -1),
        ("grok_image", "Grok 套图", "task", 5, 1),
        ("finalize", "结果打包", "task", 6, 0),
    ]
    for pid, title, ptype, x, y in positions:
        nodes.append(WorkflowDiagramNode(id=pid, title=title, type=ptype, x=x, y=y))

    chain = ["greeting", "process", "skill_rules", "skill_subflow", "prompt"]
    for i in range(len(chain) - 1):
        edges.append(WorkflowDiagramEdge(source=chain[i], target=chain[i + 1]))

    # prompt 分两路并行
    edges.append(WorkflowDiagramEdge(source="prompt", target="openai_text"))
    edges.append(WorkflowDiagramEdge(source="prompt", target="grok_image"))
    # 并行汇聚到 finalize
    edges.append(WorkflowDiagramEdge(source="openai_text", target="finalize"))
    edges.append(WorkflowDiagramEdge(source="grok_image", target="finalize"))

    return nodes, edges


def _build_workflow_summary(
    niche: str,
    selected_topic: Optional[TopicRecord],
    openai_pkg: Optional[OpenAITextPackage],
    grok_set: Optional[GrokImageSet],
    topic_count: int,
    card_count: int,
) -> str:
    topic_title = selected_topic.title if selected_topic else niche
    text_status = openai_pkg.status if openai_pkg else "dry_run"
    image_status = grok_set.status if grok_set else "dry_run"
    return (
        f"已完成「{niche}」内容工作流："
        f"沉淀 {topic_count} 个选题，"
        f"生成 {card_count} 页图文卡片规格"
        f"（文案状态：{text_status}，套图状态：{image_status}）。"
    )


def finalize_node(
    state: FinalizeNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> FinalizeNodeOutput:
    """
    title: 结果审核打包
    desc: 合并 OpenAI 文案和 Grok 套图，生成最终卡片包、工作流摘要和运算器控制面板
    integrations:
    """
    ctx = runtime.context

    card_package = _build_card_package(state.selected_topic, state.openai_text_package, state.grok_image_set)
    operator_control = _build_operator_control(state.skill_subflows, state.editable_prompts)
    diagram_nodes, diagram_edges = _build_diagram(state.workflow_steps)
    workflow_summary = _build_workflow_summary(
        state.niche, state.selected_topic,
        state.openai_text_package, state.grok_image_set,
        len(state.selected_topic.outline) if state.selected_topic and state.selected_topic.outline else 0,
        len(card_package.cards),
    )

    next_commands = [
        f"继续扩写「{card_package.topic_title}」，生成更口语化的卡片文案。",
        f"把「{state.niche}」的评论需求整理成选题库 Markdown。",
        "补充真实评论和对标标题，重新排序选题优先级。",
        "把当前卡片包改成更强封面标题和更短页面正文。",
    ]

    return FinalizeNodeOutput(
        card_package=card_package,
        workflow_summary=workflow_summary,
        next_commands=next_commands,
        operator_control=operator_control,
        workflow_diagram_nodes=diagram_nodes,
        workflow_diagram_edges=diagram_edges,
    )
