"""
小红书内容全栈工作流 — 全局状态 & 图/节点 IO 定义
──────────────────────────────────────────────────────
节点: 对标与需求挖掘 → 选题库 → Skill规则 → 子流程 → 提示词编辑
      ─┬─ OpenAI 文案  (并行)
       └─ Grok 套图   (并行)
      → 结果审核打包
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
#  复合子结构
# ═══════════════════════════════════════════════════════════

class BenchmarkAccount(BaseModel):
    name: str = Field(default="", description="对标账号/线索名称")
    platform: str = Field(default="", description="平台")
    signal: str = Field(default="", description="捕捉到的信号（标题/封面/结构）")
    content_patterns: List[str] = Field(default_factory=list, description="内容模式")
    visual_patterns: List[str] = Field(default_factory=list, description="视觉模式")
    risk_notes: List[str] = Field(default_factory=list, description="风险与合规提示")

class DemandInsight(BaseModel):
    cluster: str = Field(default="", description="需求聚类标签")
    user_words: List[str] = Field(default_factory=list, description="用户原话")
    pain: str = Field(default="", description="痛点描述")
    desired_outcome: str = Field(default="", description="期望结果")
    content_angle: str = Field(default="", description="内容切入角度")
    confidence: str = Field(default="medium", description="置信度 high/medium/low")

class TopicRecord(BaseModel):
    title: str = Field(default="", description="选题标题")
    audience: str = Field(default="", description="目标人群")
    hook: str = Field(default="", description="开头钩子")
    demand_source: str = Field(default="", description="需求来源")
    outline: List[str] = Field(default_factory=list, description="大纲")
    proof_needed: List[str] = Field(default_factory=list, description="需补充证据")
    differentiation: str = Field(default="", description="差异化说明")
    priority: str = Field(default="medium", description="优先级 high/medium/low")
    expected_view_score: int = Field(default=0, description="预期浏览分")
    view_evidence: List[str] = Field(default_factory=list, description="浏览分依据")
    selected: bool = Field(default=False, description="是否被选中")
    selection_reason: str = Field(default="", description="选中/落选理由")

class CardPage(BaseModel):
    page: int = Field(default=0, description="页码")
    headline: str = Field(default="", description="卡片标题")
    body: str = Field(default="", description="卡片正文")
    visual_prompt: str = Field(default="", description="视觉提示词")

class SkillSubflowStep(BaseModel):
    step_key: str = Field(default="", description="步骤标识")
    title: str = Field(default="", description="步骤标题")
    node_type: str = Field(default="", description="节点类型 model/prompt/rule")
    model_or_tool: str = Field(default="", description="使用的模型/工具")
    prompt_key: str = Field(default="", description="提示词 key")
    default_prompt: str = Field(default="", description="默认提示词")
    final_prompt: str = Field(default="", description="最终提示词")
    input_keys: List[str] = Field(default_factory=list, description="输入 key")
    output_keys: List[str] = Field(default_factory=list, description="输出 key")
    editable: bool = Field(default=True, description="是否可编辑")
    enabled: bool = Field(default=True, description="是否启用")
    notes: str = Field(default="", description="备注")

class SkillSubflowDef(BaseModel):
    skill_key: str = Field(default="", description="子流程标识")
    title: str = Field(default="", description="子流程标题")
    provider: str = Field(default="", description="提供商 openai/grok")
    model: str = Field(default="", description="模型")
    mode: str = Field(default="", description="模式")
    endpoint: str = Field(default="", description="API 端点")
    description: str = Field(default="", description="描述")
    editable: bool = Field(default=True, description="是否可编辑")
    steps: List[SkillSubflowStep] = Field(default_factory=list, description="步骤列表")
    status: str = Field(default="ready", description="状态 ready/dry_run/done")

class EditablePrompt(BaseModel):
    key: str = Field(default="", description="提示词 key")
    title: str = Field(default="", description="标题")
    target_model: str = Field(default="", description="目标模型")
    default_prompt: str = Field(default="", description="默认提示词")
    final_prompt: str = Field(default="", description="最终提示词")
    editable: bool = Field(default=True, description="是否可编辑")

class ImageStyleRules(BaseModel):
    aspect_ratio: str = Field(default="3:4", description="宽高比")
    style: str = Field(default="cartoon", description="风格")
    reference_image_notes: List[str] = Field(default_factory=list, description="参考图备注")
    reference_image_urls: List[str] = Field(default_factory=list, description="参考图 URL")
    must_have: List[str] = Field(default_factory=list, description="必须包含")
    avoid: List[str] = Field(default_factory=list, description="避免")
    consistency_rules: List[str] = Field(default_factory=list, description="一致性规则")

class GrokImageItem(BaseModel):
    page: int = Field(default=0, description="页码")
    headline: str = Field(default="", description="标题")
    prompt: str = Field(default="", description="生图提示词")
    aspect_ratio: str = Field(default="3:4", description="宽高比")
    style: str = Field(default="cartoon", description="风格")
    request: Dict[str, Any] = Field(default_factory=dict, description="API 请求体")
    image_url: str = Field(default="", description="生成的图片 URL")
    status: str = Field(default="dry_run", description="状态 dry_run/planned/done")

class OpenAITextPackage(BaseModel):
    provider: str = Field(default="openai", description="提供商")
    model: str = Field(default="gpt-5.5", description="模型")
    reasoning_mode: str = Field(default="ultra_high", description="推理模式")
    request: Dict[str, Any] = Field(default_factory=dict, description="API 请求体")
    title_options: List[str] = Field(default_factory=list, description="标题选项")
    post_description: str = Field(default="", description="正文描述")
    card_script: List[str] = Field(default_factory=list, description="卡片脚本")
    image_brief: str = Field(default="", description="图片简要说明")
    status: str = Field(default="dry_run", description="状态 dry_run/done")

class GrokImageSet(BaseModel):
    provider: str = Field(default="grok", description="提供商")
    model: str = Field(default="grok-imagine-image-quality", description="模型")
    mode: str = Field(default="Expert", description="模式")
    aspect_ratio: str = Field(default="3:4", description="宽高比")
    style: str = Field(default="cartoon", description="风格")
    images: List[GrokImageItem] = Field(default_factory=list, description="图片列表")
    consistency_rules: List[str] = Field(default_factory=list, description="一致性规则")
    status: str = Field(default="dry_run", description="状态 dry_run/planned/done")

class CardPackage(BaseModel):
    topic_title: str = Field(default="", description="选题标题")
    cover_options: List[str] = Field(default_factory=list, description="封面标题选项")
    cards: List[CardPage] = Field(default_factory=list, description="卡片列表")
    caption: str = Field(default="", description="正文")
    hashtags: List[str] = Field(default_factory=list, description="话题标签")
    cta: str = Field(default="", description="行动号召")
    review_checklist: List[str] = Field(default_factory=list, description="审核清单")

class WorkflowStepInfo(BaseModel):
    node_key: str = Field(default="", description="节点 key")
    title: str = Field(default="", description="节点标题")
    model_or_tool: str = Field(default="", description="使用的模型/工具")
    prompt_key: str = Field(default="", description="提示词 key")
    output_keys: List[str] = Field(default_factory=list, description="输出 key")
    status: str = Field(default="ready", description="状态")

class WorkflowDiagramNode(BaseModel):
    id: str = Field(default="", description="节点 ID")
    title: str = Field(default="", description="节点标题")
    type: str = Field(default="", description="节点类型")
    x: int = Field(default=0, description="X 坐标")
    y: int = Field(default=0, description="Y 坐标")

class WorkflowDiagramEdge(BaseModel):
    source: str = Field(default="", description="源节点 ID")
    target: str = Field(default="", description="目标节点 ID")
    label: str = Field(default="", description="边标签")

class OperatorEditPanel(BaseModel):
    key: str = Field(default="", description="面板 key")
    title: str = Field(default="", description="面板标题")
    panel_type: str = Field(default="", description="面板类型 prompt/subflow/image")
    editable: bool = Field(default=True, description="是否可编辑")
    content: Any = Field(default=None, description="面板内容")

class OperatorControl(BaseModel):
    edit_panels: List[OperatorEditPanel] = Field(default_factory=list, description="编辑面板列表")
    actions: List[str] = Field(default_factory=list, description="可用操作列表")
    status: str = Field(default="ready", description="状态")


# ═══════════════════════════════════════════════════════════
#  全局状态
# ═══════════════════════════════════════════════════════════

class GlobalState(BaseModel):
    """全局状态：工作流执行过程中的共享数据"""
    # 输入
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    goal: str = Field(default="生成一组小红书图文卡片", description="目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标笔记信号")
    comment_notes: List[str] = Field(default_factory=list, description="评论信号")
    constraints: List[str] = Field(default_factory=list, description="约束")
    brand_voice: str = Field(default="", description="品牌语气")
    card_count: int = Field(default=6, description="卡片数量")
    openai_api_key: str = Field(default="", description="OpenAI API Key（可选）")
    grok_api_key: str = Field(default="", description="Grok API Key（可选）")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型")
    # 中间结果
    research_brief: str = Field(default="", description="研究简报")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list, description="对标账号列表")
    demand_insights: List[DemandInsight] = Field(default_factory=list, description="需求洞察列表")
    topic_bank: List[TopicRecord] = Field(default_factory=list, description="选题库")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    image_style_rules: Optional[ImageStyleRules] = Field(default=None, description="图片风格规则")
    skill_subflows: List[SkillSubflowDef] = Field(default_factory=list, description="Skill 子流程列表")
    editable_prompts: List[EditablePrompt] = Field(default_factory=list, description="可编辑提示词")
    openai_text_package: Optional[OpenAITextPackage] = Field(default=None, description="OpenAI 文案包")
    grok_image_set: Optional[GrokImageSet] = Field(default=None, description="Grok 套图集")
    # 最终结果
    card_package: Optional[CardPackage] = Field(default=None, description="图文卡片包")
    workflow_summary: str = Field(default="", description="工作流摘要")
    workflow_steps: List[WorkflowStepInfo] = Field(default_factory=list, description="工作流步骤")
    next_commands: List[str] = Field(default_factory=list, description="下一步指令")
    # 运算器 & 可视化
    operator_control: Optional[OperatorControl] = Field(default=None, description="运算器控制")
    workflow_diagram_nodes: List[WorkflowDiagramNode] = Field(default_factory=list, description="工作流节点图")
    workflow_diagram_edges: List[WorkflowDiagramEdge] = Field(default_factory=list, description="工作流边图")


# ═══════════════════════════════════════════════════════════
#  图的输入输出
# ═══════════════════════════════════════════════════════════

class GraphInput(BaseModel):
    """工作流的输入参数"""
    niche: str = Field(..., description="赛道/领域")
    audience: str = Field(..., description="目标人群")
    goal: str = Field(default="生成一组小红书图文卡片", description="目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标笔记信号")
    comment_notes: List[str] = Field(default_factory=list, description="评论信号")
    constraints: List[str] = Field(default_factory=list, description="约束")
    brand_voice: str = Field(default="", description="品牌语气")
    card_count: int = Field(default=6, description="卡片数量")
    openai_api_key: str = Field(default="", description="OpenAI API Key（可选）")
    grok_api_key: str = Field(default="", description="Grok API Key（可选）")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型")

class GraphOutput(BaseModel):
    """工作流的输出结果"""
    workflow_summary: str = Field(..., description="工作流摘要")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list, description="对标账号列表")
    demand_insights: List[DemandInsight] = Field(default_factory=list, description="需求洞察列表")
    topic_bank: List[TopicRecord] = Field(default_factory=list, description="选题库")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    image_style_rules: Optional[ImageStyleRules] = Field(default=None, description="图片风格规则")
    skill_subflows: List[SkillSubflowDef] = Field(default_factory=list, description="Skill 子流程列表")
    editable_prompts: List[EditablePrompt] = Field(default_factory=list, description="可编辑提示词")
    openai_text_package: Optional[OpenAITextPackage] = Field(default=None, description="OpenAI 文案包")
    grok_image_set: Optional[GrokImageSet] = Field(default=None, description="Grok 套图集")
    card_package: Optional[CardPackage] = Field(default=None, description="图文卡片包")
    workflow_steps: List[WorkflowStepInfo] = Field(default_factory=list, description="工作流步骤")
    next_commands: List[str] = Field(default_factory=list, description="下一步指令")
    operator_control: Optional[OperatorControl] = Field(default=None, description="运算器控制")
    workflow_diagram_nodes: List[WorkflowDiagramNode] = Field(default_factory=list, description="工作流节点图")
    workflow_diagram_edges: List[WorkflowDiagramEdge] = Field(default_factory=list, description="工作流边图")


# ═══════════════════════════════════════════════════════════
#  节点独立 IO 类型
# ═══════════════════════════════════════════════════════════

# greeting_node: 对标与需求挖掘
class GreetingNodeInput(BaseModel):
    niche: str = Field(..., description="赛道/领域")
    audience: str = Field(..., description="目标人群")
    goal: str = Field(default="生成一组小红书图文卡片", description="目标")
    benchmark_notes: List[str] = Field(default_factory=list, description="对标笔记信号")
    comment_notes: List[str] = Field(default_factory=list, description="评论信号")
    constraints: List[str] = Field(default_factory=list, description="约束")
    brand_voice: str = Field(default="", description="品牌语气")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    grok_api_key: str = Field(default="", description="Grok API Key")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型")

class GreetingNodeOutput(BaseModel):
    research_brief: str = Field(..., description="研究简报")
    benchmark_accounts: List[BenchmarkAccount] = Field(..., description="对标账号列表")
    demand_insights: List[DemandInsight] = Field(..., description="需求洞察列表")

# process_node: 选题库与高浏览选题
class ProcessNodeInput(BaseModel):
    niche: str = Field(..., description="赛道/领域")
    audience: str = Field(..., description="目标人群")
    brand_voice: str = Field(default="", description="品牌语气")
    research_brief: str = Field(default="", description="研究简报")
    benchmark_accounts: List[BenchmarkAccount] = Field(default_factory=list, description="对标账号列表")
    demand_insights: List[DemandInsight] = Field(default_factory=list, description="需求洞察列表")
    card_count: int = Field(default=6, description="卡片数量")

class ProcessNodeOutput(BaseModel):
    topic_bank: List[TopicRecord] = Field(..., description="选题库")
    selected_topic: Optional[TopicRecord] = Field(..., description="选中选题")

# skill_rules_node: Skill规则与参考图
class SkillRulesNodeInput(BaseModel):
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    card_count: int = Field(default=6, description="卡片数量")

class SkillRulesNodeOutput(BaseModel):
    image_style_rules: Optional[ImageStyleRules] = Field(..., description="图片风格规则")
    workflow_steps: List[WorkflowStepInfo] = Field(default_factory=list, description="工作流步骤")

# skill_subflow_node: OpenAI/Grok Skill 子流程
class SkillSubflowNodeInput(BaseModel):
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    image_style_rules: Optional[ImageStyleRules] = Field(default=None, description="图片风格规则")

class SkillSubflowNodeOutput(BaseModel):
    skill_subflows: List[SkillSubflowDef] = Field(..., description="Skill 子流程列表")

# prompt_node: 在线提示词编辑
class PromptNodeInput(BaseModel):
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    brand_voice: str = Field(default="", description="品牌语气")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    image_style_rules: Optional[ImageStyleRules] = Field(default=None, description="图片风格规则")
    skill_subflows: List[SkillSubflowDef] = Field(default_factory=list, description="Skill 子流程列表")

class PromptNodeOutput(BaseModel):
    editable_prompts: List[EditablePrompt] = Field(..., description="可编辑提示词列表")

# openai_text_node: OpenAI GPT5.5 文案
class OpenAITextNodeInput(BaseModel):
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    brand_voice: str = Field(default="", description="品牌语气")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    editable_prompts: List[EditablePrompt] = Field(default_factory=list, description="可编辑提示词")
    skill_subflows: List[SkillSubflowDef] = Field(default_factory=list, description="Skill 子流程列表")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型")

class OpenAITextNodeOutput(BaseModel):
    openai_text_package: Optional[OpenAITextPackage] = Field(..., description="OpenAI 文案包")

# grok_image_node: Grok Expert 套图
class GrokImageNodeInput(BaseModel):
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    image_style_rules: Optional[ImageStyleRules] = Field(default=None, description="图片风格规则")
    editable_prompts: List[EditablePrompt] = Field(default_factory=list, description="可编辑提示词")
    skill_subflows: List[SkillSubflowDef] = Field(default_factory=list, description="Skill 子流程列表")
    grok_api_key: str = Field(default="", description="Grok API Key")
    execute_model_calls: bool = Field(default=False, description="是否真实调用模型")

class GrokImageNodeOutput(BaseModel):
    grok_image_set: Optional[GrokImageSet] = Field(..., description="Grok 套图集")

# finalize_node: 结果审核打包
class FinalizeNodeInput(BaseModel):
    niche: str = Field(default="", description="赛道/领域")
    audience: str = Field(default="", description="目标人群")
    selected_topic: Optional[TopicRecord] = Field(default=None, description="选中选题")
    image_style_rules: Optional[ImageStyleRules] = Field(default=None, description="图片风格规则")
    skill_subflows: List[SkillSubflowDef] = Field(default_factory=list, description="Skill 子流程列表")
    editable_prompts: List[EditablePrompt] = Field(default_factory=list, description="可编辑提示词")
    openai_text_package: Optional[OpenAITextPackage] = Field(default=None, description="OpenAI 文案包")
    grok_image_set: Optional[GrokImageSet] = Field(default=None, description="Grok 套图集")
    workflow_steps: List[WorkflowStepInfo] = Field(default_factory=list, description="工作流步骤")
    constraints: List[str] = Field(default_factory=list, description="约束")

class FinalizeNodeOutput(BaseModel):
    card_package: Optional[CardPackage] = Field(..., description="图文卡片包")
    workflow_summary: str = Field(..., description="工作流摘要")
    next_commands: List[str] = Field(default_factory=list, description="下一步指令")
    operator_control: Optional[OperatorControl] = Field(default=None, description="运算器控制")
    workflow_diagram_nodes: List[WorkflowDiagramNode] = Field(default_factory=list, description="工作流节点图")
    workflow_diagram_edges: List[WorkflowDiagramEdge] = Field(default_factory=list, description="工作流边图")
