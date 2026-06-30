"""
结果审核打包节点
整合所有节点输出，将 Grok 生成图片插入到 GPT5.5 文案卡片中，生成选题话题标签
"""
import json
import os
import re
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


# 中文停用词（常见无意义词，不适合作为话题标签）
_STOP_WORDS: set = {
    "的", "是", "在", "和", "了", "也", "就", "都", "要", "会", "可以", "这个", "那个",
    "一个", "一种", "一些", "什么", "怎么", "如何", "为什么", "因为", "所以",
    "如果", "虽然", "但是", "而且", "或者", "然后", "从", "到", "对", "把", "被", "让",
    "用", "做", "有", "没有", "能", "去", "来", "看", "想", "知道", "觉得",
    "上", "下", "中", "里", "外", "前", "后", "左", "右", "这", "那", "哪",
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "自己",
    "不", "很", "更", "最", "太", "真", "非常", "比较", "特别",
    "点出", "给出", "说明", "补充", "需要", "使用", "通过", "进行",
    "基于", "按照", "针对", "关于", "对于", "以及", "及其",
    "真实", "卡点", "证据", "风险", "边界", "步骤", "角度",
}


def _extract_topic_keywords(selected_topic: Any, niche: str) -> List[str]:
    """从选题结构化字段中提取话题标签关键词"""
    keywords: List[str] = []

    # 辅助：从字符串中提取 2-5 字有效短词
    def extract_from_text(text: str) -> List[str]:
        result: List[str] = []
        if not isinstance(text, str) or not text:
            return result
        segments = re.split(r'[：:，,。！？、；\s]+', text)
        for seg in segments:
            seg = seg.strip()
            if 2 <= len(seg) <= 5 and seg not in _STOP_WORDS:
                result.append(seg)
        return result

    # 1. 赛道关键词（优先级最高）
    if niche and niche not in _STOP_WORDS:
        keywords.append(niche)

    # 2. 从需求来源提取（如 "路径不清: 拍照效果, 美甲推荐" → "拍照效果", "美甲推荐"）
    demand_source = ""
    if isinstance(selected_topic, BaseModel):
        demand_source = getattr(selected_topic, "demand_source", "")
    elif isinstance(selected_topic, dict):
        demand_source = selected_topic.get("demand_source", "")
    for kw in extract_from_text(demand_source):
        if kw not in keywords and len(keywords) < 5:
            keywords.append(kw)

    # 3. 从受众提取
    audience = ""
    if isinstance(selected_topic, BaseModel):
        audience = getattr(selected_topic, "audience", "")
    elif isinstance(selected_topic, dict):
        audience = selected_topic.get("audience", "")
    for kw in extract_from_text(audience):
        if kw not in keywords and len(keywords) < 5:
            keywords.append(kw)

    # 4. 从大纲提取
    outline: List[str] = []
    if isinstance(selected_topic, BaseModel):
        outline = getattr(selected_topic, "outline", [])
    elif isinstance(selected_topic, dict):
        outline = selected_topic.get("outline", [])
    if isinstance(outline, list):
        for item in outline[:3]:
            if isinstance(item, str):
                for kw in extract_from_text(item):
                    if kw not in keywords and len(keywords) < 6:
                        keywords.append(kw)

    # 5. 从选题标题提取（兜底）
    topic_title = ""
    if isinstance(selected_topic, BaseModel):
        topic_title = getattr(selected_topic, "title", "")
    elif isinstance(selected_topic, dict):
        topic_title = selected_topic.get("title", "")
    for kw in extract_from_text(topic_title):
        if kw not in keywords and len(keywords) < 6:
            keywords.append(kw)

    return keywords[:6]


def _generate_hashtags(selected_topic: Any, niche: str) -> List[str]:
    """生成话题标签，格式如 #芯片 #拍照 #美甲"""
    keywords = _extract_topic_keywords(selected_topic, niche)
    hashtags: List[str] = []
    seen: set = set()

    for kw in keywords:
        tag = f"#{kw}"
        if tag not in seen:
            seen.add(tag)
            hashtags.append(tag)

    # 确保至少有 3 个标签
    if len(hashtags) < 3:
        fallbacks = ["#小红书运营", "#内容选题", "#选题库"]
        for fb in fallbacks:
            if fb not in seen and len(hashtags) < 5:
                seen.add(fb)
                hashtags.append(fb)

    return hashtags[:6]


def _build_card_package(
    selected_topic: Any,
    openai_text_package: Any,
    grok_image_set: Any,
    card_count: int,
    niche: str
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

    # 智能生成话题标签
    hashtags = _generate_hashtags(selected_topic, niche)

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
    """构建工作流图（17 节点主画布平铺结构）"""
    nodes = [
        # 需求阶段
        {"id": "greeting", "title": "对标与需求挖掘", "type": "agent", "x": 0, "y": 0},
        {"id": "process", "title": "选题库与高浏览选题", "type": "agent", "x": 1, "y": 0},
        # Skill 规则子流程（画布平铺）
        {"id": "style_select", "title": "风格选择", "type": "task", "x": 2, "y": 0},
        {"id": "aspect_ratio", "title": "尺寸选择", "type": "task", "x": 3, "y": 0},
        {"id": "must_have", "title": "必选项配置", "type": "task", "x": 4, "y": 0},
        {"id": "avoid", "title": "禁选项配置", "type": "task", "x": 5, "y": 0},
        {"id": "consistency_rules", "title": "一致性规则", "type": "task", "x": 6, "y": 0},
        {"id": "grok_rules_judge", "title": "规则智能判断", "type": "agent", "x": 7, "y": 0},
        {"id": "rules_sync", "title": "规则同步回写", "type": "task", "x": 7, "y": -1},
        # Skill 子流程（画布平铺）
        {"id": "openai_steps", "title": "OpenAI 步骤配置", "type": "task", "x": 8, "y": -1},
        {"id": "grok_steps", "title": "Grok 步骤配置", "type": "task", "x": 8, "y": 1},
        {"id": "grok_subflow_judge", "title": "子流程智能判断", "type": "agent", "x": 9, "y": 0},
        {"id": "subflow_sync", "title": "子流程同步回写", "type": "task", "x": 9, "y": -1},
        # 生成阶段
        {"id": "prompt", "title": "提示词编辑", "type": "task", "x": 10, "y": 0},
        {"id": "openai_text", "title": "OpenAI GPT5.5 文案", "type": "task", "x": 11, "y": -1},
        {"id": "grok_image", "title": "Grok Expert 套图", "type": "task", "x": 11, "y": 1},
        {"id": "finalize", "title": "结果审核打包", "type": "task", "x": 12, "y": 0},
    ]
    edges = [
        # 需求阶段
        {"source": "greeting", "target": "process", "label": ""},
        # Skill 规则线性
        {"source": "process", "target": "style_select", "label": ""},
        {"source": "style_select", "target": "aspect_ratio", "label": ""},
        {"source": "aspect_ratio", "target": "must_have", "label": ""},
        {"source": "must_have", "target": "avoid", "label": ""},
        {"source": "avoid", "target": "consistency_rules", "label": ""},
        {"source": "consistency_rules", "target": "grok_rules_judge", "label": ""},
        # 规则判断分支
        {"source": "grok_rules_judge", "target": "rules_sync", "label": "规则修改→同步"},
        {"source": "grok_rules_judge", "target": "openai_steps", "label": "内容调整→跳过"},
        {"source": "rules_sync", "target": "openai_steps", "label": ""},
        # 子流程并行
        {"source": "openai_steps", "target": "grok_steps", "label": ""},
        {"source": "grok_steps", "target": "grok_subflow_judge", "label": ""},
        # 子流程判断分支
        {"source": "grok_subflow_judge", "target": "subflow_sync", "label": "规则修改→同步"},
        {"source": "grok_subflow_judge", "target": "prompt", "label": "内容调整→跳过"},
        {"source": "subflow_sync", "target": "prompt", "label": ""},
        # 生成并行
        {"source": "prompt", "target": "openai_text", "label": ""},
        {"source": "prompt", "target": "grok_image", "label": ""},
        {"source": "openai_text", "target": "finalize", "label": ""},
        {"source": "grok_image", "target": "finalize", "label": ""},
    ]
    return {"nodes": nodes, "edges": edges}


def finalize_node(
    state: FinalizeNodeInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> FinalizeNodeOutput:
    """
    title: 结果审核打包
    desc: 整合所有节点输出，将 Grok 生成的图片 URL 嵌入到 GPT5.5 文案卡片中，并智能生成选题话题标签（如 #芯片 #拍照 #美甲）
    integrations:
    """
    ctx = runtime.context

    # 1. 构建卡片包（含 Grok 图片 URL 嵌入 + 智能标签）
    card_package = _build_card_package(
        state.selected_topic,
        state.openai_text_package,
        state.grok_image_set,
        state.card_count,
        state.niche
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

    # 6. 构建运算器控制
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
