"""
成品审核与复盘建议节点
整合 AI 文案和 AI 图片结果，给运营一份可审核、可复盘、可继续改技能的图文卡片包。
"""
from __future__ import annotations

import re
from typing import List, Dict, Any

from pydantic import BaseModel
try:
    from langchain_core.runnables import RunnableConfig
except ImportError:  # pragma: no cover - local unit-test fallback
    RunnableConfig = Dict[str, Any]  # type: ignore

try:
    from langgraph.runtime import Runtime
except ImportError:  # pragma: no cover - local unit-test fallback
    Runtime = Any  # type: ignore

try:
    from coze_coding_utils.runtime_ctx.context import Context
except ImportError:  # pragma: no cover - local unit-test fallback
    Context = Any  # type: ignore

from graphs.state import FinalizeNodeInput, FinalizeNodeOutput


def _get_attr(data: Any, key: str, default: Any = None) -> Any:
    """统一获取属性：支持 BaseModel 属性访问和 dict 的 .get()"""
    if isinstance(data, BaseModel):
        return getattr(data, key, default)
    if isinstance(data, dict):
        return data.get(key, default)
    return default


_HASHTAG_RE = re.compile(r"#[0-9A-Za-z_\-\u4e00-\u9fff]+")


def _normalize_hashtag(value: Any) -> str:
    tag = str(value or "").strip()
    if not tag:
        return ""
    if tag.startswith("#"):
        return tag
    compact = re.sub(r"\s+", "", tag)
    return f"#{compact}" if compact else ""


def _topic_hashtags(selected_topic: Any) -> List[str]:
    """只使用选题节点或运营输入提供的话题标签，不在审核节点猜测主题。"""
    seen: set = set()
    result: List[str] = []

    raw_tags = _get_attr(selected_topic, "hashtags", [])
    if not isinstance(raw_tags, list):
        raw_tags = [raw_tags]
    for raw in raw_tags:
        tag = _normalize_hashtag(raw)
        if tag and tag not in seen:
            seen.add(tag)
            result.append(tag)

    text_fields = [
        _get_attr(selected_topic, "title", ""),
        _get_attr(selected_topic, "demand_source", ""),
        " ".join(_get_attr(selected_topic, "view_evidence", []) or []),
    ]
    for text in text_fields:
        for match in _HASHTAG_RE.findall(str(text or "")):
            tag = _normalize_hashtag(match)
            if tag and tag not in seen:
                seen.add(tag)
                result.append(tag)

    return result[:10]


def _build_card_package(
    selected_topic: Any,
    openai_text_package: Any,
    grok_image_set: Any,
    card_count: int,
) -> Dict[str, Any]:
    """构建最终卡片包，将 Grok 图片 URL 嵌入每张卡片"""
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

    # Grok 生成的图片列表 → 按页码建立索引
    grok_images_raw = _get_attr(grok_image_set, "images", [])
    if not isinstance(grok_images_raw, list):
        grok_images_raw = []

    grok_images_by_page: Dict[int, Dict[str, Any]] = {}
    for img in grok_images_raw:
        if isinstance(img, BaseModel):
            page = getattr(img, "page", 0)
            image_url = getattr(img, "image_url", "")
            prompt = getattr(img, "prompt", "")
            grok_images_by_page[page] = {"image_url": image_url, "prompt": prompt}
        elif isinstance(img, dict):
            page = img.get("page", 0)
            grok_images_by_page[page] = {
                "image_url": img.get("image_url", ""),
                "prompt": img.get("prompt", "")
            }

    # 组装每页卡片，插入对应的 Grok 图片 URL
    cards: List[Dict[str, Any]] = []
    for i in range(card_count):
        page = i + 1
        headline = card_script[i] if i < len(card_script) else f"第{page}页：待补充"
        body = headline

        # 匹配对应的 Grok 图片
        visual_prompt = ""
        image_url = ""
        matched_img = grok_images_by_page.get(page)
        if matched_img is not None:
            visual_prompt = matched_img.get("prompt", "")
            image_url = matched_img.get("image_url", "")

        cards.append({
            "page": page,
            "headline": headline,
            "body": body,
            "visual_prompt": visual_prompt,
            "image_url": image_url
        })

    # 正文描述
    post_description = _get_attr(openai_text_package, "post_description", "")
    caption = post_description if post_description else f"关于「{topic_title}」的小红书图文卡片正文。"

    return {
        "topic_title": topic_title,
        "cover_options": cover_options,
        "cards": cards,
        "caption": caption,
        "hashtags": _topic_hashtags(selected_topic),
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
    """构建运营可见的工作流树，含可展开技能子树和并行生成分支。"""
    nodes = [
        {"id": "运营需求入口", "title": "运营需求入口", "type": "start", "x": 0, "y": 0},
        {"id": "AI理解运营目标", "title": "AI理解运营目标", "type": "agent", "x": 1, "y": 0},
        {"id": "竞品和用户需求分析", "title": "竞品和用户需求分析", "type": "subtree", "x": 2, "y": -1},
        {"id": "爆款选题机会池", "title": "爆款选题机会池", "type": "subtree", "x": 3, "y": -1},
        {"id": "数据分析复盘", "title": "数据分析复盘", "type": "subtree", "x": 3, "y": 1},
        {"id": "图片制作技能", "title": "图片制作技能", "type": "skill", "x": 4, "y": 0},
        {"id": "图片制作技能：选风格", "title": "图片制作技能：选风格", "type": "skill_step", "x": 5, "y": -2},
        {"id": "图片制作技能：定比例", "title": "图片制作技能：定比例", "type": "skill_step", "x": 5, "y": -1},
        {"id": "图片制作技能：必备元素", "title": "图片制作技能：必备元素", "type": "skill_step", "x": 5, "y": 0},
        {"id": "图片制作技能：避坑清单", "title": "图片制作技能：避坑清单", "type": "skill_step", "x": 5, "y": 1},
        {"id": "图片制作技能：套图统一", "title": "图片制作技能：套图统一", "type": "skill_step", "x": 5, "y": 2},
        {"id": "AI技能教练：检查图片规则", "title": "AI技能教练：检查图片规则", "type": "agent", "x": 6, "y": 0},
        {"id": "沉淀图片制作经验", "title": "沉淀图片制作经验", "type": "skill_memory", "x": 7, "y": -1},
        {"id": "内容生成技能", "title": "内容生成技能", "type": "skill", "x": 8, "y": 0},
        {"id": "文案技能：拆步骤", "title": "文案技能：拆步骤", "type": "sub_agent", "x": 9, "y": -1},
        {"id": "图片技能：拆步骤", "title": "图片技能：拆步骤", "type": "sub_agent", "x": 9, "y": 1},
        {"id": "AI技能教练：检查生成流程", "title": "AI技能教练：检查生成流程", "type": "agent", "x": 10, "y": 0},
        {"id": "沉淀内容生成经验", "title": "沉淀内容生成经验", "type": "skill_memory", "x": 11, "y": -1},
        {"id": "运营确认生成方案", "title": "运营确认生成方案", "type": "review", "x": 12, "y": 0},
        {"id": "AI生成小红书文案", "title": "AI生成小红书文案", "type": "content", "x": 13, "y": -1},
        {"id": "AI生成小红书套图", "title": "AI生成小红书套图", "type": "content", "x": 13, "y": 1},
        {"id": "成品审核与复盘建议", "title": "成品审核与复盘建议", "type": "end", "x": 14, "y": 0},
    ]
    edges = [
        {"source": "运营需求入口", "target": "AI理解运营目标", "label": ""},
        {"source": "AI理解运营目标", "target": "竞品和用户需求分析", "label": "展开调研子树"},
        {"source": "竞品和用户需求分析", "target": "爆款选题机会池", "label": "提炼选题机会"},
        {"source": "爆款选题机会池", "target": "数据分析复盘", "label": "只做复盘时到这里"},
        {"source": "爆款选题机会池", "target": "图片制作技能", "label": "进入完整生产"},
        {"source": "图片制作技能", "target": "图片制作技能：选风格", "label": "展开图片技能"},
        {"source": "图片制作技能：选风格", "target": "图片制作技能：定比例", "label": ""},
        {"source": "图片制作技能：定比例", "target": "图片制作技能：必备元素", "label": ""},
        {"source": "图片制作技能：必备元素", "target": "图片制作技能：避坑清单", "label": ""},
        {"source": "图片制作技能：避坑清单", "target": "图片制作技能：套图统一", "label": ""},
        {"source": "图片制作技能：套图统一", "target": "AI技能教练：检查图片规则", "label": "交给AI分析"},
        {"source": "AI技能教练：检查图片规则", "target": "沉淀图片制作经验", "label": "值得长期保留"},
        {"source": "AI技能教练：检查图片规则", "target": "内容生成技能", "label": "本次临时使用"},
        {"source": "沉淀图片制作经验", "target": "内容生成技能", "label": ""},
        {"source": "内容生成技能", "target": "文案技能：拆步骤", "label": "展开文案子Agent"},
        {"source": "内容生成技能", "target": "图片技能：拆步骤", "label": "展开图片子Agent"},
        {"source": "文案技能：拆步骤", "target": "AI技能教练：检查生成流程", "label": ""},
        {"source": "图片技能：拆步骤", "target": "AI技能教练：检查生成流程", "label": ""},
        {"source": "AI技能教练：检查生成流程", "target": "沉淀内容生成经验", "label": "值得长期保留"},
        {"source": "AI技能教练：检查生成流程", "target": "运营确认生成方案", "label": "本次临时使用"},
        {"source": "沉淀内容生成经验", "target": "运营确认生成方案", "label": ""},
        {"source": "运营确认生成方案", "target": "AI生成小红书文案", "label": "并行生成"},
        {"source": "运营确认生成方案", "target": "AI生成小红书套图", "label": "并行生成"},
        {"source": "AI生成小红书文案", "target": "成品审核与复盘建议", "label": ""},
        {"source": "AI生成小红书套图", "target": "成品审核与复盘建议", "label": ""},
    ]
    return {"nodes": nodes, "edges": edges}


def _build_operator_control(state: FinalizeNodeInput) -> Dict[str, Any]:
    """构建运营编辑面板，把技能当作可拖拽、可交给 AI 分析的业务流程。"""
    topic_title = ""
    if isinstance(state.selected_topic, BaseModel):
        topic_title = getattr(state.selected_topic, "title", "")
    elif isinstance(state.selected_topic, dict):
        topic_title = state.selected_topic.get("title", "")

    return {
        "edit_panels": [
            {
                "key": "research_tree",
                "title": "竞品调研与爆款选题",
                "panel_type": "business_tree",
                "editable": True,
                "content": {
                    "goal": "整理对标账号、评论需求和高潜选题，帮助运营决定今天先做哪一篇。",
                    "current_topic": topic_title,
                    "operator_can_do": ["补充对标链接", "补充评论原话", "让AI重新评估选题优先级"],
                },
            },
            {
                "key": "image_skill_tree",
                "title": "图片制作技能",
                "panel_type": "skill_tree",
                "editable": True,
                "content": {
                    "goal": "把画面风格、比例、必须出现和必须避开的元素做成可复用图片技能。",
                    "sub_agent": "AI技能教练",
                    "operator_can_do": ["拖动方框调整顺序", "增删画面要求", "把本次好用的要求保存为长期经验"],
                },
            },
            {
                "key": "copy_skill_tree",
                "title": "文案生成技能",
                "panel_type": "skill_tree",
                "editable": True,
                "content": {
                    "goal": "把选题理解、标题、正文、每页脚本拆成可展开的文案子Agent。",
                    "sub_agent": "文案子Agent",
                    "operator_can_do": ["改写语气", "调整卡片密度", "让AI检查是否适合小红书发布"],
                },
            },
            {
                "key": "image_generation_skill_tree",
                "title": "套图生成技能",
                "panel_type": "skill_tree",
                "editable": True,
                "content": {
                    "goal": "把每页脚本转成统一套图，让图片子Agent生成可审核的画面方案。",
                    "sub_agent": "图片子Agent",
                    "operator_can_do": ["调整每页画面动作", "锁定统一角色和配色", "让AI分析套图是否一致"],
                },
            },
            {
                "key": "review_tree",
                "title": "成品审核与数据复盘",
                "panel_type": "review",
                "editable": True,
                "content": {
                    "goal": "检查内容风险、标题吸引力、卡片可读性，并把复盘结论反向喂给技能。",
                    "operator_can_do": ["标记低分卡片", "记录发布数据", "让AI给出下一轮改进建议"],
                },
            },
        ],
        "actions": [
            "展开技能流程",
            "让AI分析这个技能",
            "拖动方框调整顺序",
            "让AI检查改动",
            "保存为我的运营技能",
            "重新生成内容",
            "查看复盘建议",
        ],
        "status": "ready",
    }


def finalize_node(
    state: FinalizeNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> FinalizeNodeOutput:
    """
    title: 成品审核与复盘建议
    desc: 整合 AI 文案和 AI 图片，生成运营可审核的卡片包、话题标签和下一轮复盘建议
    integrations:
    """
    ctx = runtime.context

    # 1. 构建卡片包（含 Grok 图片 URL 嵌入 + 智能标签）
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

    # 6. 构建运营控制面板
    operator_control = _build_operator_control(state)

    return FinalizeNodeOutput(
        card_package=card_package,
        workflow_summary=workflow_summary,
        workflow_steps=workflow_steps,
        next_commands=next_commands,
        workflow_diagram_nodes=diagram["nodes"],
        workflow_diagram_edges=diagram["edges"],
        operator_control=operator_control
    )
