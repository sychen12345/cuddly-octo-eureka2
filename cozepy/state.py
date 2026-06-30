"""
小红书内容工作流状态定义。

这个版本按完整 Coze 画布拆分为多节点：
开始 -> 对标与需求挖掘 -> 选题库与高浏览选题 -> Skill规则与参考图
-> 在线提示词编辑 -> OpenAI GPT5.5 文案 -> Grok Expert 套图 -> 结果审核打包 -> 结束。
"""
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class BenchmarkAccount(BaseModel):
    """对标账号或对标笔记线索。"""

    name: str = Field(..., description="账号名、笔记名或对标线索标签")
    platform: str = Field(default="小红书", description="平台")
    signal: str = Field(..., description="选择该对标的原因或信号")
    content_patterns: List[str] = Field(default_factory=list, description="可学习的内容结构")
    visual_patterns: List[str] = Field(default_factory=list, description="可学习的视觉结构")
    risk_notes: List[str] = Field(default_factory=list, description="需要避免复制或补充验证的地方")


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
    expected_view_score: int = Field(default=60, description="预估浏览潜力分，0-100")
    view_evidence: List[str] = Field(default_factory=list, description="浏览潜力依据")
    selected: bool = Field(default=False, description="是否被选为本轮生产选题")
    selection_reason: str = Field(default="", description="选择原因")


class ImageStyleRule(BaseModel):
    """Grok 套图生成规则。"""

    aspect_ratio: str = Field(default="3:4", description="图片比例")
    style: str = Field(default="cartoon", description="图片风格")
    reference_image_notes: List[str] = Field(default_factory=list, description="参考图观察记录")
    reference_image_urls: List[str] = Field(default_factory=list, description="参考图链接")
    must_have: List[str] = Field(default_factory=list, description="必须保持的视觉规则")
    avoid: List[str] = Field(default_factory=list, description="必须避免的视觉问题")
    consistency_rules: List[str] = Field(default_factory=list, description="套图一致性规则")


class EditablePrompt(BaseModel):
    """在线可修改的提示词块。"""

    key: str = Field(..., description="提示词键名，用于 prompt_overrides 覆盖")
    title: str = Field(..., description="提示词标题")
    target_model: str = Field(..., description="目标模型或节点")
    default_prompt: str = Field(..., description="默认提示词")
    final_prompt: str = Field(..., description="应用用户覆盖后的最终提示词")
    editable: bool = Field(default=True, description="是否允许在线编辑")


class SkillSubflowStep(BaseModel):
    """可视化 skill 子流程中的一个可编辑步骤。"""

    step_key: str = Field(..., description="子流程步骤键名")
    title: str = Field(..., description="步骤标题")
    node_type: str = Field(default="prompt", description="prompt/model/review/rule")
    model_or_tool: str = Field(default="", description="该步骤使用的模型或工具")
    prompt_key: str = Field(default="", description="关联提示词键名")
    default_prompt: str = Field(default="", description="默认步骤提示词")
    final_prompt: str = Field(default="", description="运营修改后的最终步骤提示词")
    input_keys: List[str] = Field(default_factory=list, description="步骤输入字段")
    output_keys: List[str] = Field(default_factory=list, description="步骤输出字段")
    editable: bool = Field(default=True, description="是否允许在工作流中编辑")
    enabled: bool = Field(default=True, description="是否启用该步骤")
    notes: str = Field(default="", description="给运营看的编辑说明")


class SkillSubflow(BaseModel):
    """OpenAI/Grok 可视化可编辑 skill 子流程。"""

    skill_key: str = Field(..., description="子流程 skill 键名")
    title: str = Field(..., description="子流程标题")
    provider: str = Field(..., description="模型供应商")
    model: str = Field(default="", description="默认模型")
    mode: str = Field(default="", description="推理或生成模式")
    endpoint: str = Field(default="", description="真实调用 endpoint")
    description: str = Field(default="", description="子流程用途")
    editable: bool = Field(default=True, description="是否允许运营在线修改")
    steps: List[SkillSubflowStep] = Field(default_factory=list, description="可视化步骤")
    status: str = Field(default="ready", description="ready/dry_run/completed/failed")


class ModelRequest(BaseModel):
    """模型调用计划或真实调用摘要。API Key 不进入 payload。"""

    provider: str = Field(..., description="模型供应商")
    model: str = Field(..., description="模型名")
    mode: str = Field(default="", description="推理/生成模式")
    endpoint: str = Field(default="", description="建议 API endpoint")
    skill_key: str = Field(default="", description="关联 skill/subflow key")
    prompt_key: str = Field(default="", description="关联提示词键名")
    payload: Dict[str, Any] = Field(default_factory=dict, description="建议请求载荷")
    dry_run: bool = Field(default=True, description="是否仅生成请求计划")
    status: str = Field(default="planned", description="planned/dry_run/ready/completed/failed")


class TextDescriptionPackage(BaseModel):
    """OpenAI 文字描述结果。"""

    provider: str = Field(default="openai")
    model: str = Field(default="gpt-5.5")
    reasoning_mode: str = Field(default="ultra_high")
    request: ModelRequest = Field(default_factory=lambda: ModelRequest(provider="openai", model="gpt-5.5"))
    title_options: List[str] = Field(default_factory=list)
    post_description: str = Field(default="", description="图文正文描述")
    card_script: List[str] = Field(default_factory=list, description="每页图文脚本")
    image_brief: str = Field(default="", description="给 Grok 的总视觉说明")
    status: str = Field(default="dry_run", description="文字生成状态")


class ImageGenerationItem(BaseModel):
    """Grok Expert 套图中的单张图。"""

    page: int = Field(..., description="页码")
    headline: str = Field(..., description="该图承载的短标题")
    prompt: str = Field(..., description="Grok Expert 生图提示词")
    aspect_ratio: str = Field(default="3:4")
    style: str = Field(default="cartoon")
    request: ModelRequest = Field(
        default_factory=lambda: ModelRequest(provider="grok", model="grok-imagine-image-quality")
    )
    image_url: str = Field(default="", description="真实调用后可填充的图片链接")
    status: str = Field(default="dry_run")


class ImageSetPackage(BaseModel):
    """Grok Expert 生成的套图计划或结果。"""

    provider: str = Field(default="grok")
    model: str = Field(default="grok-imagine-image-quality")
    mode: str = Field(default="Expert")
    aspect_ratio: str = Field(default="3:4")
    style: str = Field(default="cartoon")
    images: List[ImageGenerationItem] = Field(default_factory=list)
    consistency_rules: List[str] = Field(default_factory=list)
    status: str = Field(default="dry_run")


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
    review_checklist: List[str] = Field(default_factory=list, description="发布前审核清单")


class WorkflowStep(BaseModel):
    """用于在输出中直观看到完整 skill/Coze 流程。"""

    node_key: str = Field(..., description="节点键名")
    title: str = Field(..., description="节点标题")
    model_or_tool: str = Field(default="", description="使用的模型或工具")
    prompt_key: str = Field(default="", description="关联提示词")
    output_keys: List[str] = Field(default_factory=list, description="该节点输出字段")
    status: str = Field(default="ready", description="节点状态")


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
    topic_research_notes: List[str] = Field(default_factory=list, description="浏览量、热词或选题证据")
    user_selected_topic: str = Field(default="", description="用户指定选题")
    constraints: List[str] = Field(default_factory=list, description="限制条件")
    brand_voice: str = Field(default="清醒、实操、少废话", description="账号语气")
    card_count: int = Field(default=6, description="卡片页数")
    image_count: int = Field(default=6, description="套图张数")
    image_aspect_ratio: str = Field(default="3:4", description="图片比例")
    image_style: str = Field(default="cartoon", description="图片风格")
    reference_image_notes: List[str] = Field(default_factory=list, description="参考图规则")
    reference_image_urls: List[str] = Field(default_factory=list, description="参考图链接")
    prompt_overrides: Dict[str, str] = Field(default_factory=dict, description="在线提示词覆盖")
    skill_flow_overrides: Dict[str, Any] = Field(default_factory=dict, description="在线修改 OpenAI/Grok 子流程")
    openai_text_model: str = Field(default="gpt-5.5", description="OpenAI 文案模型")
    openai_reasoning_mode: str = Field(default="ultra_high", description="OpenAI 推理模式")
    grok_image_model: str = Field(default="grok-imagine-image-quality", description="Grok 生图模型")
    grok_image_mode: str = Field(default="Expert", description="Grok 生图模式")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型 API")

    research_brief: str = Field(default="", description="对标与需求研究摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)
    topic_bank: List[TopicRecord] = Field(default_factory=list)
    selected_topic: TopicRecord = Field(
        default_factory=lambda: TopicRecord(
            title="",
            audience="",
            hook="",
            demand_source="",
            differentiation="",
        )
    )
    image_style_rules: ImageStyleRule = Field(default_factory=ImageStyleRule)
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)
    skill_subflows: List[SkillSubflow] = Field(default_factory=list)
    editable_prompts: List[EditablePrompt] = Field(default_factory=list)
    openai_text_package: TextDescriptionPackage = Field(default_factory=TextDescriptionPackage)
    grok_image_set: ImageSetPackage = Field(default_factory=ImageSetPackage)
    card_package: CardPackage = Field(default_factory=lambda: CardPackage(topic_title="", caption="", cta=""))
    workflow_summary: str = Field(default="", description="最终流程摘要")
    next_commands: List[str] = Field(default_factory=list, description="下一步指令")


# ============= 图的输入输出定义 =============
class GraphInput(BaseModel):
    """Coze 开始节点输入。"""

    grok_api_key: str = Field(..., repr=False, description="运行时必须由用户输入的 Grok API Key")
    openai_api_key: str = Field(..., repr=False, description="运行时必须由用户输入的 OpenAI API Key")
    niche: str = Field(..., description="领域或产品方向")
    audience: str = Field(default="小红书新手用户", description="目标人群")
    goal: str = Field(default="生成小红书图文卡片", description="本轮目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标素材")
    comment_notes: List[str] = Field(default_factory=list, description="评论或私信素材")
    topic_research_notes: List[str] = Field(default_factory=list, description="浏览量、热词或选题证据")
    user_selected_topic: str = Field(default="", description="用户指定选题")
    constraints: List[str] = Field(default_factory=list, description="限制条件")
    brand_voice: str = Field(default="清醒、实操、少废话", description="账号语气")
    card_count: int = Field(default=6, description="卡片页数")
    image_count: int = Field(default=6, description="套图张数")
    image_aspect_ratio: str = Field(default="3:4", description="图片比例")
    image_style: str = Field(default="cartoon", description="图片风格")
    reference_image_notes: List[str] = Field(default_factory=list, description="参考图规则")
    reference_image_urls: List[str] = Field(default_factory=list, description="参考图链接")
    prompt_overrides: Dict[str, str] = Field(default_factory=dict, description="在线提示词覆盖")
    skill_flow_overrides: Dict[str, Any] = Field(default_factory=dict, description="在线修改 OpenAI/Grok 子流程")
    openai_text_model: str = Field(default="gpt-5.5", description="OpenAI 文案模型")
    openai_reasoning_mode: str = Field(default="ultra_high", description="OpenAI 推理模式")
    grok_image_model: str = Field(default="grok-imagine-image-quality", description="Grok 生图模型")
    grok_image_mode: str = Field(default="Expert", description="Grok 生图模式")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型 API")


class GraphOutput(BaseModel):
    """Coze 结束节点输出。注意不会输出 API Key。"""

    workflow_summary: str = Field(..., description="最终流程摘要")
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)
    topic_bank: List[TopicRecord] = Field(default_factory=list)
    selected_topic: TopicRecord = Field(..., description="本轮选中的高潜选题")
    image_style_rules: ImageStyleRule = Field(..., description="3:4 卡通套图规则")
    skill_subflows: List[SkillSubflow] = Field(default_factory=list, description="OpenAI/Grok 可编辑子流程")
    editable_prompts: List[EditablePrompt] = Field(default_factory=list)
    openai_text_package: TextDescriptionPackage = Field(..., description="OpenAI GPT5.5 文案包")
    grok_image_set: ImageSetPackage = Field(..., description="Grok Expert 套图计划或结果")
    card_package: CardPackage = Field(..., description="最终图文卡片包")
    next_commands: List[str] = Field(default_factory=list)


# ============= 节点的输入输出定义 =============
class ResearchNodeInput(GraphInput):
    """对标与需求挖掘节点输入。"""


class ResearchNodeOutput(BaseModel):
    """对标与需求挖掘节点输出。"""

    research_brief: str = Field(..., description="对标与需求研究摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list)
    demand_insights: List[DemandInsight] = Field(default_factory=list)


class TopicNodeInput(GlobalState):
    """选题库与高浏览选题节点输入。"""


class TopicNodeOutput(BaseModel):
    """选题库与高浏览选题节点输出。"""

    topic_bank: List[TopicRecord] = Field(default_factory=list)
    selected_topic: TopicRecord = Field(..., description="本轮选中的高潜选题")


class SkillRulesNodeInput(GlobalState):
    """Skill规则与参考图节点输入。"""


class SkillRulesNodeOutput(BaseModel):
    """Skill规则与参考图节点输出。"""

    image_style_rules: ImageStyleRule = Field(..., description="3:4 卡通套图规则")
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)


class SkillSubflowNodeInput(GlobalState):
    """OpenAI/Grok 子流程构建节点输入。"""


class SkillSubflowNodeOutput(BaseModel):
    """OpenAI/Grok 子流程构建节点输出。"""

    skill_subflows: List[SkillSubflow] = Field(default_factory=list)


class PromptNodeInput(GlobalState):
    """在线提示词编辑节点输入。"""


class PromptNodeOutput(BaseModel):
    """在线提示词编辑节点输出。"""

    editable_prompts: List[EditablePrompt] = Field(default_factory=list)


class OpenAITextNodeInput(GlobalState):
    """OpenAI GPT5.5 文案节点输入。"""


class OpenAITextNodeOutput(BaseModel):
    """OpenAI GPT5.5 文案节点输出。"""

    openai_text_package: TextDescriptionPackage = Field(..., description="OpenAI 文案包")


class GrokImageNodeInput(GlobalState):
    """Grok Expert 套图节点输入。"""


class GrokImageNodeOutput(BaseModel):
    """Grok Expert 套图节点输出。"""

    grok_image_set: ImageSetPackage = Field(..., description="Grok 套图计划或结果")


class FinalizeNodeInput(GlobalState):
    """结果审核打包节点输入。"""


class FinalizeNodeOutput(BaseModel):
    """结果审核打包节点输出。"""

    card_package: CardPackage = Field(..., description="最终图文卡片包")
    workflow_summary: str = Field(..., description="最终流程摘要")
    next_commands: List[str] = Field(default_factory=list)


# 兼容旧文件命名和 Coze 模板里的节点名。
GreetingNodeInput = ResearchNodeInput
GreetingNodeOutput = ResearchNodeOutput
ProcessNodeInput = TopicNodeInput
ProcessNodeOutput = TopicNodeOutput
