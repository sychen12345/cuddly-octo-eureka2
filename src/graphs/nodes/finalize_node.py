"""
结果审核打包节点
整合所有节点输出，生成最终结果
配置回写已由子工作流的同步节点处理
"""
import json
import os
from typing import List, Dict, Optional, Any, Union

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import FinalizeNodeInput, FinalizeNodeOutput


def _get_attr(data: Any, key: str, default: Any = None) -> Any:
    """统一获取属性：支持 BaseModel 属性访问和 dict 的 .get()"""
    if isinstance(data, BaseModel):
        return getattr(data, key, default)
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def _build_card_package(
    selected_topic: Any,
    openai_text_package: Any,
    grok_image_set: Any,
    card_count: int
) -> Dict[str, Any]:
    """构建最终卡片包"""
    topic_title = ""
    if isinstance(selected_topic, BaseModel):
        topic_title = getattr(selected_topic, "title", "")
    elif isinstance(selected_topic, dict):
        topic_title = selected_topic.get("title", "")

    # 封面选项
    title_options: List[str] = _get_attr(openai_text_package, "title_options", [topic_title])
    if not isinstance(title_options, list):
        title_options = [topic_title]
    cover_options = title_options[:4] if title_options else [topic_title]

    # 卡片脚本
    card_script: List[str] = _get_attr(openai_text_package, "card_script", [])
    if not isinstance(card_script, list):
        card_script = []

    # 图片
    grok_images_raw = _get_attr(grok_image_set, "images", [])
    grok_images: List[Dict[str, Any]] = []
    if isinstance(grok_images_raw, list):
        for img in grok_images_raw:
            if isinstance(img, BaseModel):
                grok_images.append(img.model_dump())
            elif isinstance(img, dict):
                grok_images.append(img)

    # 组装每页卡片
    cards: List[Dict[str, Any]] = []
    for i in range(card_count):
        page = i + 1
        headline = card_script[i] if i < len(card_script) else f"第{page}页：待补充"
        body = headline

        # 匹配对应的 grok 图片
        visual_prompt = ""
        for img in grok_images:
            if isinstance(img, dict) and img.get("page") == page:
                visual_prompt = img.get("prompt", "")
                break

        cards.append({
            "page": page,
            "headline": headline,
            "body": body,
            "visual_prompt": visual_prompt
        })

    # 正文描述
    post_description = _get_attr(openai_text_package, "post_description", "")
    caption = post_description if post_description else f"关于「{topic_title}」的小红书图文卡片正文。"

    # 标签
    hashtags = [f"#{topic_title}", "#小红书运营", "#内容选题"]

    return {
        "topic_title": topic_title,
        "cover_options": cover_options,
        "cards": cards,
        "caption": caption,
        "hashtags": hashtags,
        "cta": "想继续做的话，把你的对标标题和评论原话贴进来，我会继续扩成下一组卡片。",
        "review_checklist": [
            "是否所有真实数据都有来源",
            "是否没有承诺阅读量、涨粉或收益",
            "是否只学习对标结构，没有复制原文",
            "是否每页卡片只有一个核心信息",
            "是否保留了下一轮评论采样入口"
        ]
    }


def _build_workflow_summary(
    niche: str,
    benchmark_accounts: Any,
    demand_insights: Any,
    topic_bank: Any,
    card_package: Dict[str, Any],
    openai_text_package: Any,
    grok_image_set: Any
) -> str:
    """构建工作流摘要"""
    text_status = _get_attr(openai_text_package, "status", "dry_run")
    image_status = _get_attr(grok_image_set, "status", "dry_run")
    topic_count = len(topic_bank) if isinstance(topic_bank, list) else 0
    card_count = len(card_package.get("cards", []))
    return (
        f"已完成「{niche}」内容工作流："
        f"沉淀 {topic_count} 个选题，"
        f"生成 {card_count} 页图文卡片规格"
        f"（文案状态：{text_status}，套图状态：{image_status}）。"
    )


def _build_workflow_steps(workflow_steps_cfg: List[Any]) -> List[Dict[str, Any]]:
    """构建工作流步骤概览"""
    result: List[Dict[str, Any]] = []
    for step in workflow_steps_cfg:
        step_dict = step.model_dump() if isinstance(step, BaseModel) else step
        if isinstance(step_dict, dict):
            result.append({
                "node_key": step_dict.get("node_key", ""),
                "title": step_dict.get("title", ""),
                "model_or_tool": step_dict.get("model_or_tool", ""),
                "prompt_key": step_dict.get("prompt_key", ""),
                "output_keys": step_dict.get("output_keys", []),
                "status": "ready"
            })
    return result


def _build_workflow_diagram() -> Dict[str, Any]:
    """构建工作流图（含子工作流标记和并行结构）"""
    nodes = [
        {"id": "greeting", "title": "对标与需求挖掘", "type": "task", "x": 0, "y": 0},
        {"id": "process", "title": "选题库", "type": "task", "x": 1, "y": 0},
        {"id": "skill_rules", "title": "Skill规则(子工作流)", "type": "subgraph", "x": 2, "y": 0},
        {"id": "skill_subflow", "title": "子流程(子工作流)", "type": "subgraph", "x": 3, "y": 0},
        {"id": "prompt", "title": "提示词编辑", "type": "task", "x": 4, "y": 0},
        {"id": "openai_text", "title": "OpenAI 文案", "type": "task", "x": 5, "y": -1},
        {"id": "grok_image", "title": "Grok 套图", "type": "task", "x": 5, "y": 1},
        {"id": "finalize", "title": "结果打包", "type": "task", "x": 6, "y": 0}
    ]
    edges = [
        {"source": "greeting", "target": "process", "label": ""},
        {"source": "process", "target": "skill_rules", "label": ""},
        {"source": "skill_rules", "target": "skill_subflow", "label": ""},
        {"source": "skill_subflow", "target": "prompt", "label": ""},
        {"source": "prompt", "target": "openai_text", "label": ""},
        {"source": "prompt", "target": "grok_image", "label": ""},
        {"source": "openai_text", "target": "finalize", "label": ""},
        {"source": "grok_image", "target": "finalize", "label": ""}
    ]
    return {"nodes": nodes, "edges": edges}


def finalize_node(
    state: FinalizeNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> FinalizeNodeOutput:
    """
    title: 结果审核打包
    desc: 整合所有节点输出，生成最终卡片包和工作流摘要；配置回写由子工作流同步节点处理
    integrations:
    """
    ctx = runtime.context

    # 1. 构建卡片包
    card_package = _build_card_package(
        state.selected_topic,
        state.openai_text_package,
        state.grok_image_set,
        state.card_count
    )

    # 2. 构建工作流摘要
    workflow_summary = _build_workflow_summary(
        state.niche,
        state.benchmark_accounts,
        state.demand_insights,
        state.topic_bank,
        card_package,
        state.openai_text_package,
        state.grok_image_set
    )

    # 3. 构建工作流步骤
    workflow_steps = _build_workflow_steps(state.workflow_steps)

    # 4. 构建工作流图
    diagram = _build_workflow_diagram()

    # 5. 构建下一步指令
    topic_title = ""
    if isinstance(state.selected_topic, BaseModel):
        topic_title = getattr(state.selected_topic, "title", "")
    elif isinstance(state.selected_topic, dict):
        topic_title = state.selected_topic.get("title", "")
    next_commands = [
        f"继续扩写「{topic_title}」，生成更口语化的卡片文案。",
        f"把「{state.niche}」的评论需求整理成选题库 Markdown。",
        "补充真实评论和对标标题，重新排序选题优先级。",
        "把当前卡片包改成更强封面标题和更短页面正文。"
    ]

    # 6. 构建运算器控制（简化版，子工作流已处理编辑面板）
    operator_control = {
        "edit_panels": [],
        "actions": ["edit_prompt", "toggle_step", "rerun", "reorder_step", "sync_config"],
        "status": "ready"
    }

    return FinalizeNodeOutput(
        card_package=card_package,
        workflow_summary=workflow_summary,
        workflow_steps=workflow_steps,
        next_commands=next_commands,
        workflow_diagram_nodes=diagram["nodes"],
        workflow_diagram_edges=diagram["edges"],
        operator_control=operator_control
    )
