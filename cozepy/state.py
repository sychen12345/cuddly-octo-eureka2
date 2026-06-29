"""
小红书内容工作流状态定义。

这个文件映射 Coze 低代码工作流中的开始节点、业务节点和结束节点：
开始节点接收用户输入，业务节点逐步补充状态，结束节点返回结构化结果。
"""
from typing import List

from pydantic import BaseModel, Field


class BenchmarkAccount(BaseModel):
    """对标账号或对标笔记线索。"""

    name: str = Field(..., description="账号名、笔记名或对标线索标签")
    platform: str = Field(default="小红书", description="平台")
    signal: str = Field(..., description="选择该对标的原因或信号")
    content_patterns: List[str] = Field(
        default_factory=list,
        description="可学习的标题、开头、正文、证明、CTA 等结构",
    )
    visual_patterns: List[str] = Field(
        default_factory=list,
        description="封面、排版、截图、卡片风格等视觉结构",
    )
    risk_notes: List[str] = Field(
        default_factory=list,
        description="需要避免复制或需要补充验证的地方",
    )


class DemandInsight(BaseModel):
    """从评论、私信或用户问题中提取的需求洞察。"""

    cluster: str = Field(..., description="需求分类")
    user_words: List[str] = Field(default_factory=list, description="匿名化用户原话")
    pain: str = Field(..., description="用户痛点")
    desired_outcome: str = Field(..., description="用户想达成的结果")
    content_angle: str = Field(..., description="适合转成内容的角度")
    confidence: str = Field(default="medium", description="证据置信度：high/medium/low")


class TopicRecord(BaseModel):
    """可沉淀到选题库的记录。"""

    title: str = Field(..., description="选题标题")
    audience: str = Field(..., description="目标读者")
    hook: str = Field(..., description="开头钩子")
    demand_source: str = Field(..., description="需求或对标来源")
    outline: List[str] = Field(default_factory=list, description="内容大纲")
    proof_needed: List[str] = Field(default_factory=list, description="发布前需要补充的证据")
    differentiation: str = Field(..., description="和对标内容的差异点")
    priority: str = Field(default="medium", description="优先级：high/medium/low")


class CardPage(BaseModel):
    """图文卡片中的单页。"""

    page: int = Field(..., description="页码")
    headline: str = Field(..., description="本页标题")
    body: str = Field(..., description="本页正文")
    visual_prompt: str = Field(..., description="视觉方向或生图提示")


class CardPackage(BaseModel):
    """小红书图文卡片成品包。"""

    topic_title: str = Field(..., description="选中的选题标题")
    cover_options: List[str] = Field(default_factory=list, description="封面标题备选")
    cards: List[CardPage] = Field(default_factory=list, description="卡片页列表")
    caption: str = Field(..., description="小红书正文")
    hashtags: List[str] = Field(default_factory=list, description="话题标签")
    cta: str = Field(..., description="软性行动引导")
    review_checklist: List[str] = Field(
        default_factory=list,
        description="发布前审核清单",
    )


# ============= 全局状态定义 =============
class GlobalState(BaseModel):
    """工作流执行过程中的共享数据。"""

    grok_api_key: str = Field(default="", repr=False, description="Grok API Key")
    openai_api_key: str = Field(default="", repr=False, description="OpenAI API Key")
    niche: str = Field(default="", description="领域或产品方向")
    audience: str = Field(default="小红书新手用户", description="目标人群")
    goal: str = Field(default="生成小红书图文卡片", description="本轮目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标素材")
    comment_notes: List[str] = Field(default_factory=list, description="评论或私信素材")
    constraints: List[str] = Field(default_factory=list, description="限制条件")
    brand_voice: str = Field(default="清醒、实操、少废话", description="账号语气")
    card_count: int = Field(default=6, description="卡片页数")

    research_brief: str = Field(default="", description="对标与需求研究摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)
    topic_bank: List[TopicRecord] = Field(default_factory=list)
    card_package: CardPackage = Field(
        default_factory=lambda: CardPackage(
            topic_title="",
            caption="",
            cta="",
        ),
        description="图文卡片成品包",
    )
    workflow_summary: str = Field(default="", description="最终流程摘要")
    next_commands: List[str] = Field(default_factory=list, description="下一步指令")


# ============= 图的输入输出定义 =============
class GraphInput(BaseModel):
    """Coze 开始节点输入。"""

    grok_api_key: str = Field(
        ...,
        repr=False,
        description="运行时必须由用户输入的 Grok API Key；仅用于节点调用，不会出现在输出中",
    )
    openai_api_key: str = Field(
        ...,
        repr=False,
        description="运行时必须由用户输入的 OpenAI API Key；仅用于节点调用，不会出现在输出中",
    )
    niche: str = Field(..., description="领域或产品方向")
    audience: str = Field(default="小红书新手用户", description="目标人群")
    goal: str = Field(default="生成小红书图文卡片", description="本轮目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标素材")
    comment_notes: List[str] = Field(default_factory=list, description="评论或私信素材")
    constraints: List[str] = Field(default_factory=list, description="限制条件")
    brand_voice: str = Field(default="清醒、实操、少废话", description="账号语气")
    card_count: int = Field(default=6, description="卡片页数")


class GraphOutput(BaseModel):
    """Coze 结束节点输出。"""

    workflow_summary: str = Field(..., description="最终流程摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)
    topic_bank: List[TopicRecord] = Field(default_factory=list)
    card_package: CardPackage = Field(..., description="图文卡片成品包")
    next_commands: List[str] = Field(default_factory=list)


# ============= 节点的输入输出定义 =============
class ResearchNodeInput(BaseModel):
    """对标与需求挖掘节点输入。"""

    grok_api_key: str = Field(
        ...,
        repr=False,
        description="运行时必须由用户输入的 Grok API Key；仅用于节点调用，不会出现在输出中",
    )
    openai_api_key: str = Field(
        ...,
        repr=False,
        description="运行时必须由用户输入的 OpenAI API Key；仅用于节点调用，不会出现在输出中",
    )
    niche: str = Field(..., description="领域或产品方向")
    audience: str = Field(default="小红书新手用户", description="目标人群")
    goal: str = Field(default="生成小红书图文卡片", description="本轮目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标素材")
    comment_notes: List[str] = Field(default_factory=list, description="评论或私信素材")
    constraints: List[str] = Field(default_factory=list, description="限制条件")
    brand_voice: str = Field(default="清醒、实操、少废话", description="账号语气")
    card_count: int = Field(default=6, description="卡片页数")


class ResearchNodeOutput(BaseModel):
    """对标与需求挖掘节点输出。"""

    research_brief: str = Field(..., description="对标与需求研究摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)


class ProcessNodeInput(BaseModel):
    """选题库与图文卡片节点输入。"""

    grok_api_key: str = Field(default="", repr=False, description="Grok API Key")
    openai_api_key: str = Field(default="", repr=False, description="OpenAI API Key")
    niche: str = Field(..., description="领域或产品方向")
    audience: str = Field(default="小红书新手用户", description="目标人群")
    goal: str = Field(default="生成小红书图文卡片", description="本轮目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标素材")
    comment_notes: List[str] = Field(default_factory=list, description="评论或私信素材")
    constraints: List[str] = Field(default_factory=list, description="限制条件")
    brand_voice: str = Field(default="清醒、实操、少废话", description="账号语气")
    card_count: int = Field(default=6, description="卡片页数")
    research_brief: str = Field(default="", description="对标与需求研究摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)


class ProcessNodeOutput(BaseModel):
    """选题库与图文卡片节点输出。"""

    topic_bank: List[TopicRecord] = Field(default_factory=list)
    card_package: CardPackage = Field(..., description="图文卡片成品包")
    workflow_summary: str = Field(..., description="最终流程摘要")
    next_commands: List[str] = Field(default_factory=list)


# 兼容 Coze 生成模板里的文件命名和节点名。
GreetingNodeInput = ResearchNodeInput
GreetingNodeOutput = ResearchNodeOutput
