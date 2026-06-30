"""
OpenAI/Grok 可编辑 skill 子流程节点。

这个节点把两个模型调用拆成可视化子流程，便于运营在低代码工作流中
修改每一步 prompt、模型模式和启用状态。
"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    from langchain_core.runnables import RunnableConfig
except ImportError:  # pragma: no cover
    RunnableConfig = Dict[str, Any]  # type: ignore

try:
    from langgraph.runtime import Runtime
except ImportError:  # pragma: no cover
    Runtime = Any  # type: ignore

try:
    from coze_coding_utils.runtime_ctx.context import Context
except ImportError:  # pragma: no cover
    Context = Any  # type: ignore

try:
    from graphs.state import (
        OperatorControl,
        OperatorEditPanel,
        SkillSubflow,
        SkillSubflowNodeInput,
        SkillSubflowNodeOutput,
        SkillSubflowStep,
        WorkflowDiagramEdge,
        WorkflowDiagramNode,
    )
except ImportError:
    from .state import (
        OperatorControl,
        OperatorEditPanel,
        SkillSubflow,
        SkillSubflowNodeInput,
        SkillSubflowNodeOutput,
        SkillSubflowStep,
        WorkflowDiagramEdge,
        WorkflowDiagramNode,
    )


def _get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _dump(model: Any) -> Dict[str, Any]:
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return {}


def _selected_title(state: Any) -> str:
    selected = _dump(_get(state, "selected_topic", {}))
    return str(selected.get("title", "")).strip()


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on", "enable", "enabled"}:
            return True
        if lowered in {"false", "0", "no", "off", "disable", "disabled"}:
            return False
    return bool(value)


def _step_overrides(skill_override: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw_steps = skill_override.get("steps", {})
    if isinstance(raw_steps, dict):
        return {str(key): value for key, value in raw_steps.items() if isinstance(value, dict)}
    if isinstance(raw_steps, list):
        out: Dict[str, Dict[str, Any]] = {}
        for item in raw_steps:
            if isinstance(item, dict) and item.get("step_key"):
                out[str(item["step_key"])] = item
        return out
    return {}


def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _operator_field_overrides(state: Any) -> Dict[str, Any]:
    """Map plain visual form fields to subflow overrides."""
    openai_prompt = str(_get(state, "openai_text_skill_prompt", "")).strip()
    grok_prompt = str(_get(state, "grok_image_skill_prompt", "")).strip()
    visual_prompt = str(_get(state, "grok_visual_rules_prompt", "")).strip()

    overrides: Dict[str, Any] = {
        "openai_text_skill": {
            "steps": {
                "review_text_for_image": {
                    "enabled": bool(_get(state, "openai_review_enabled", True)),
                }
            }
        },
        "grok_image_skill": {
            "steps": {
                "review_set_consistency": {
                    "enabled": bool(_get(state, "grok_review_enabled", True)),
                }
            }
        },
    }
    if openai_prompt:
        overrides["openai_text_skill"]["steps"]["generate_xhs_text"] = {"prompt": openai_prompt}
    if grok_prompt:
        overrides["grok_image_skill"]["steps"]["compose_page_prompts"] = {"prompt": grok_prompt}
    if visual_prompt:
        overrides["grok_image_skill"]["steps"]["load_visual_rules"] = {"prompt": visual_prompt}
    return overrides


def _combined_skill_overrides(state: Any) -> Dict[str, Any]:
    visual_overrides = _operator_field_overrides(state)
    advanced_overrides = _get(state, "skill_flow_overrides", {}) or {}
    if not isinstance(advanced_overrides, dict):
        advanced_overrides = {}
    return _deep_merge(visual_overrides, advanced_overrides)


def _apply_overrides(
    subflow: SkillSubflow,
    skill_overrides: Dict[str, Any],
    prompt_overrides: Dict[str, str],
) -> SkillSubflow:
    skill_override = skill_overrides.get(subflow.skill_key, {})
    if not isinstance(skill_override, dict):
        skill_override = {}

    subflow.title = str(skill_override.get("title", subflow.title)).strip() or subflow.title
    subflow.description = str(skill_override.get("description", subflow.description)).strip() or subflow.description
    subflow.model = str(skill_override.get("model", subflow.model)).strip() or subflow.model
    subflow.mode = str(skill_override.get("mode", subflow.mode)).strip() or subflow.mode
    subflow.endpoint = str(skill_override.get("endpoint", subflow.endpoint)).strip() or subflow.endpoint
    subflow.editable = _as_bool(skill_override.get("editable"), subflow.editable)

    step_overrides = _step_overrides(skill_override)
    patched_steps: List[SkillSubflowStep] = []
    for step in subflow.steps:
        step_override = step_overrides.get(step.step_key, {})
        if step_override:
            step.title = str(step_override.get("title", step.title)).strip() or step.title
            step.node_type = str(step_override.get("node_type", step.node_type)).strip() or step.node_type
            step.model_or_tool = str(step_override.get("model_or_tool", step.model_or_tool)).strip() or step.model_or_tool
            step.notes = str(step_override.get("notes", step.notes)).strip() or step.notes
            step.editable = _as_bool(step_override.get("editable"), step.editable)
            step.enabled = _as_bool(step_override.get("enabled"), step.enabled)
            if isinstance(step_override.get("input_keys"), list):
                step.input_keys = [str(item) for item in step_override["input_keys"]]
            if isinstance(step_override.get("output_keys"), list):
                step.output_keys = [str(item) for item in step_override["output_keys"]]

        final_prompt = (
            step_override.get("final_prompt")
            or step_override.get("prompt")
            or prompt_overrides.get(step.prompt_key)
            or prompt_overrides.get(step.step_key)
            or step.default_prompt
        )
        step.final_prompt = str(final_prompt).strip() or step.default_prompt
        patched_steps.append(step)

    subflow.steps = patched_steps
    return subflow


def _diagram_nodes(subflows: List[SkillSubflow]) -> List[WorkflowDiagramNode]:
    nodes = [
        WorkflowDiagramNode(node_key="start", title="开始", node_type="start", lane="入口", row=0, column=1),
        WorkflowDiagramNode(
            node_key="benchmark_and_demand",
            title="对标与需求挖掘",
            lane="研究",
            row=1,
            column=1,
            output_keys=["research_brief", "benchmark_accounts", "demand_insights"],
        ),
        WorkflowDiagramNode(
            node_key="topic_selection",
            title="选题库与高浏览选题",
            lane="研究",
            row=2,
            column=1,
            output_keys=["topic_bank", "selected_topic"],
        ),
        WorkflowDiagramNode(
            node_key="skill_rules",
            title="Skill规则与参考图",
            lane="规则",
            row=3,
            column=1,
            editable=True,
            input_keys=["image_aspect_ratio", "image_style", "reference_image_notes"],
            output_keys=["image_style_rules"],
        ),
        WorkflowDiagramNode(
            node_key="skill_subflows",
            title="OpenAI/Grok Skill 子流程",
            lane="可视化编辑",
            row=4,
            column=1,
            editable=True,
            output_keys=["skill_subflows", "operator_edit_panels"],
        ),
        WorkflowDiagramNode(
            node_key="prompt_editor",
            title="在线提示词编辑",
            lane="可视化编辑",
            row=5,
            column=1,
            editable=True,
            input_keys=["openai_text_skill_prompt", "grok_image_skill_prompt", "grok_visual_rules_prompt"],
            output_keys=["editable_prompts"],
        ),
        WorkflowDiagramNode(
            node_key="openai_text",
            title="OpenAI GPT5.5 文案",
            lane="并行生成",
            row=6,
            column=0,
            editable=True,
            subflow_key="openai_text_skill",
            output_keys=["openai_text_package"],
        ),
        WorkflowDiagramNode(
            node_key="grok_image_set",
            title="Grok Expert 套图",
            lane="并行生成",
            row=6,
            column=2,
            editable=True,
            subflow_key="grok_image_skill",
            output_keys=["grok_image_set"],
        ),
        WorkflowDiagramNode(
            node_key="finalize",
            title="结果审核打包",
            lane="汇合",
            row=7,
            column=1,
            output_keys=["card_package", "workflow_summary", "next_commands"],
        ),
        WorkflowDiagramNode(node_key="end", title="结束", node_type="end", lane="出口", row=8, column=1),
    ]
    for subflow in subflows:
        subflow_data = _dump(subflow)
        for index, step in enumerate(subflow_data.get("steps", []) or [], start=1):
            step_data = _dump(step)
            nodes.append(
                WorkflowDiagramNode(
                    node_key=f"{subflow_data.get('skill_key')}.{step_data.get('step_key')}",
                    title=str(step_data.get("title", "")),
                    node_type="step",
                    lane=str(subflow_data.get("title", "")),
                    subflow_key=str(subflow_data.get("skill_key", "")),
                    row=index,
                    column=0 if subflow_data.get("skill_key") == "openai_text_skill" else 2,
                    editable=bool(step_data.get("editable", True)),
                    input_keys=list(step_data.get("input_keys", []) or []),
                    output_keys=list(step_data.get("output_keys", []) or []),
                )
            )
    return nodes


def _diagram_edges(subflows: List[SkillSubflow]) -> List[WorkflowDiagramEdge]:
    edges = [
        WorkflowDiagramEdge(from_node="start", to_node="benchmark_and_demand"),
        WorkflowDiagramEdge(from_node="benchmark_and_demand", to_node="topic_selection"),
        WorkflowDiagramEdge(from_node="topic_selection", to_node="skill_rules"),
        WorkflowDiagramEdge(from_node="skill_rules", to_node="skill_subflows"),
        WorkflowDiagramEdge(from_node="skill_subflows", to_node="prompt_editor"),
        WorkflowDiagramEdge(
            from_node="prompt_editor",
            to_node="openai_text",
            label="并行分支：文案",
            edge_type="parallel",
        ),
        WorkflowDiagramEdge(
            from_node="prompt_editor",
            to_node="grok_image_set",
            label="并行分支：套图",
            edge_type="parallel",
        ),
        WorkflowDiagramEdge(from_node="openai_text", to_node="finalize", label="汇合", edge_type="join"),
        WorkflowDiagramEdge(from_node="grok_image_set", to_node="finalize", label="汇合", edge_type="join"),
        WorkflowDiagramEdge(from_node="finalize", to_node="end"),
    ]
    for subflow in subflows:
        subflow_data = _dump(subflow)
        skill_key = str(subflow_data.get("skill_key", ""))
        steps = [_dump(step).get("step_key") for step in subflow_data.get("steps", []) or []]
        for left, right in zip(steps, steps[1:]):
            edges.append(
                WorkflowDiagramEdge(
                    from_node=f"{skill_key}.{left}",
                    to_node=f"{skill_key}.{right}",
                    edge_type="subflow",
                )
            )
    return edges


def _operator_panels(state: Any) -> List[OperatorEditPanel]:
    return [
        OperatorEditPanel(
            panel_key="openai_text_skill",
            title="OpenAI 文案 Skill",
            description="运营只需要改这些表单项，不需要写 JSON 或代码。",
            controls=[
                OperatorControl(
                    control_key="openai_text_skill_prompt",
                    label="文案生成要求",
                    control_type="textarea",
                    input_key="openai_text_skill_prompt",
                    current_value=str(_get(state, "openai_text_skill_prompt", "")),
                    placeholder="例如：用更适合新手的语气，生成封面标题、6页脚本、正文和视觉 brief。",
                    target_path="openai_text_skill.steps.generate_xhs_text.prompt",
                    help_text="改这里就等于修改 OpenAI 文案子流程的核心生成节点。",
                ),
                OperatorControl(
                    control_key="openai_reasoning_mode",
                    label="推理强度",
                    control_type="select",
                    input_key="openai_reasoning_mode",
                    current_value=str(_get(state, "openai_reasoning_mode", "ultra_high")),
                    options=["ultra_high", "high", "medium", "low"],
                    target_path="openai_text_skill.mode",
                    help_text="默认 ultra_high，会映射到 OpenAI reasoning.effort=xhigh。",
                ),
                OperatorControl(
                    control_key="openai_review_enabled",
                    label="启用文案转图片审核",
                    control_type="toggle",
                    input_key="openai_review_enabled",
                    current_value=bool(_get(state, "openai_review_enabled", True)),
                    target_path="openai_text_skill.steps.review_text_for_image.enabled",
                    help_text="关闭后，该审核步骤不会进入 OpenAI 模型输入。",
                ),
            ],
        ),
        OperatorEditPanel(
            panel_key="grok_image_skill",
            title="Grok 套图 Skill",
            description="运营用表单改图片比例、风格、参考图规则和生图要求。",
            controls=[
                OperatorControl(
                    control_key="image_aspect_ratio",
                    label="图片比例",
                    control_type="select",
                    input_key="image_aspect_ratio",
                    current_value=str(_get(state, "image_aspect_ratio", "3:4")),
                    options=["3:4", "1:1", "4:5", "9:16"],
                    target_path="image_style_rules.aspect_ratio",
                    help_text="小红书图文默认用 3:4。",
                ),
                OperatorControl(
                    control_key="image_style",
                    label="图片风格",
                    control_type="select",
                    input_key="image_style",
                    current_value=str(_get(state, "image_style", "cartoon")),
                    options=["cartoon", "flat illustration", "3d cartoon", "hand-drawn"],
                    target_path="image_style_rules.style",
                    help_text="默认 cartoon，可以按账号视觉改。",
                ),
                OperatorControl(
                    control_key="grok_visual_rules_prompt",
                    label="参考图和视觉规则",
                    control_type="textarea",
                    input_key="grok_visual_rules_prompt",
                    current_value=str(_get(state, "grok_visual_rules_prompt", "")),
                    placeholder="例如：圆润线条、明亮色板、统一主角、画面留出标题安全区。",
                    target_path="grok_image_skill.steps.load_visual_rules.prompt",
                    help_text="改这里会影响 Grok 子流程读取视觉规则的节点。",
                ),
                OperatorControl(
                    control_key="grok_image_skill_prompt",
                    label="每页生图要求",
                    control_type="textarea",
                    input_key="grok_image_skill_prompt",
                    current_value=str(_get(state, "grok_image_skill_prompt", "")),
                    placeholder="例如：每页一个动作，统一角色，像一套完整小红书卡片。",
                    target_path="grok_image_skill.steps.compose_page_prompts.prompt",
                    help_text="改这里就等于修改 Grok 生图子流程的核心生成节点。",
                ),
                OperatorControl(
                    control_key="grok_review_enabled",
                    label="启用套图一致性审核",
                    control_type="toggle",
                    input_key="grok_review_enabled",
                    current_value=bool(_get(state, "grok_review_enabled", True)),
                    target_path="grok_image_skill.steps.review_set_consistency.enabled",
                    help_text="关闭后，该审核步骤不会进入 Grok 图片 prompt。",
                ),
            ],
        ),
    ]


def _openai_subflow(state: Any) -> SkillSubflow:
    title = _selected_title(state)
    audience = str(_get(state, "audience", "小红书新手用户")).strip()
    brand_voice = str(_get(state, "brand_voice", "清醒、实操、少废话")).strip()
    model = str(_get(state, "openai_text_model", "gpt-5.5")).strip() or "gpt-5.5"
    mode = str(_get(state, "openai_reasoning_mode", "ultra_high")).strip() or "ultra_high"
    return SkillSubflow(
        skill_key="openai_text_skill",
        title="OpenAI 图文文案 Skill 子流程",
        provider="openai",
        model=model,
        mode=mode,
        endpoint="https://api.openai.com/v1/responses",
        description="把选题、对标和评论需求转成小红书标题、卡片脚本、正文和视觉 brief。",
        steps=[
            SkillSubflowStep(
                step_key="collect_topic_context",
                title="整理选题和需求上下文",
                node_type="rule",
                model_or_tool="xhs-content-workflow",
                prompt_key="openai_text_skill.collect_topic_context",
                default_prompt=(
                    f"围绕选题「{title}」整理目标人群、评论痛点、浏览量证据、限制条件和账号语气。"
                    "只使用已提供证据，缺口标为待补充。"
                ),
                final_prompt=(
                    f"围绕选题「{title}」整理目标人群、评论痛点、浏览量证据、限制条件和账号语气。"
                    "只使用已提供证据，缺口标为待补充。"
                ),
                input_keys=["selected_topic", "demand_insights", "topic_research_notes", "constraints"],
                output_keys=["text_context"],
                notes="运营可在这里改变文案取材重点，例如更重评论原话或更重对标结构。",
            ),
            SkillSubflowStep(
                step_key="generate_xhs_text",
                title="GPT5.5 超高推理生成图文文字",
                node_type="model",
                model_or_tool=model,
                prompt_key="openai_text_skill.generate_xhs_text",
                default_prompt=(
                    f"你是 GPT5.5 超高推理模式。请为「{audience}」生成小红书图文文案，"
                    f"账号语气是「{brand_voice}」。输出封面标题、每页脚本、正文、CTA 和给图片模型的视觉 brief。"
                    "不要承诺收益，不虚构平台数据。"
                ),
                final_prompt=(
                    f"你是 GPT5.5 超高推理模式。请为「{audience}」生成小红书图文文案，"
                    f"账号语气是「{brand_voice}」。输出封面标题、每页脚本、正文、CTA 和给图片模型的视觉 brief。"
                    "不要承诺收益，不虚构平台数据。"
                ),
                input_keys=["text_context", "editable_prompts"],
                output_keys=["title_options", "card_script", "post_description", "image_brief"],
                notes="这是 OpenAI 真正调用的核心文案 skill 步骤。",
            ),
            SkillSubflowStep(
                step_key="review_text_for_image",
                title="把文字转成图片 brief 并审核",
                node_type="review",
                model_or_tool=model,
                prompt_key="openai_text_skill.review_text_for_image",
                default_prompt=(
                    "检查标题和卡片脚本是否适合 3:4 卡通套图。"
                    "每页只保留一个画面动作，避免让图片承载大段文字。"
                ),
                final_prompt=(
                    "检查标题和卡片脚本是否适合 3:4 卡通套图。"
                    "每页只保留一个画面动作，避免让图片承载大段文字。"
                ),
                input_keys=["card_script", "image_style_rules"],
                output_keys=["image_brief"],
                notes="运营可在这里补充图文转换标准。",
            ),
        ],
    )


def _grok_subflow(state: Any) -> SkillSubflow:
    title = _selected_title(state)
    model = str(_get(state, "grok_image_model", "grok-imagine-image-quality")).strip() or "grok-imagine-image-quality"
    mode = str(_get(state, "grok_image_mode", "Expert")).strip() or "Expert"
    aspect_ratio = str(_get(state, "image_aspect_ratio", "3:4")).strip() or "3:4"
    style = str(_get(state, "image_style", "cartoon")).strip() or "cartoon"
    return SkillSubflow(
        skill_key="grok_image_skill",
        title="Grok Expert 套图 Skill 子流程",
        provider="grok",
        model=model,
        mode=mode,
        endpoint="https://api.x.ai/v1/images/generations",
        description="把 OpenAI 文案、参考图规则和本地视觉 skill 转成统一 3:4 卡通套图。",
        steps=[
            SkillSubflowStep(
                step_key="load_visual_rules",
                title="读取参考图和本地视觉规则",
                node_type="rule",
                model_or_tool="canvas-design + brand-guidelines",
                prompt_key="grok_image_skill.load_visual_rules",
                default_prompt=(
                    f"读取用户参考图规则和本地视觉 skill，固定 {aspect_ratio} 竖版、{style} 风格、统一角色、色板、线条和安全留白。"
                ),
                final_prompt=(
                    f"读取用户参考图规则和本地视觉 skill，固定 {aspect_ratio} 竖版、{style} 风格、统一角色、色板、线条和安全留白。"
                ),
                input_keys=["image_style_rules", "reference_image_notes", "reference_image_urls"],
                output_keys=["visual_rules"],
                notes="运营可在这里加入参考图风格、角色设定、色彩和镜头要求。",
            ),
            SkillSubflowStep(
                step_key="compose_page_prompts",
                title="Grok Expert 生成每页图片提示词",
                node_type="model",
                model_or_tool=model,
                prompt_key="grok_image_skill.compose_page_prompts",
                default_prompt=(
                    f"你是 Grok Expert 生图子流程。请基于选题「{title}」和每页文案生成一组 3:4 竖版卡通图。"
                    "每张图只表达一个动作或场景，套图像同一套小红书卡片。"
                ),
                final_prompt=(
                    f"你是 Grok Expert 生图子流程。请基于选题「{title}」和每页文案生成一组 3:4 竖版卡通图。"
                    "每张图只表达一个动作或场景，套图像同一套小红书卡片。"
                ),
                input_keys=["card_script", "image_brief", "visual_rules"],
                output_keys=["image_prompts", "image_url"],
                notes="这是 Grok 真正调用的核心生图 skill 步骤。",
            ),
            SkillSubflowStep(
                step_key="review_set_consistency",
                title="审核套图一致性",
                node_type="review",
                model_or_tool="workflow review",
                prompt_key="grok_image_skill.review_set_consistency",
                default_prompt=(
                    "检查套图是否保持主角、色板、线条、版式一致。"
                    "封面要强钩子，内页要清晰表达步骤，不要复制参考图。"
                ),
                final_prompt=(
                    "检查套图是否保持主角、色板、线条、版式一致。"
                    "封面要强钩子，内页要清晰表达步骤，不要复制参考图。"
                ),
                input_keys=["image_prompts", "image_style_rules"],
                output_keys=["consistency_notes"],
                notes="运营可在这里调整套图验收标准。",
            ),
        ],
    )


def skill_subflow_node(
    state: SkillSubflowNodeInput,
    config: RunnableConfig | None = None,
    runtime: Runtime[Context] | None = None,
) -> SkillSubflowNodeOutput:
    """
    title: OpenAI/Grok Skill 子流程
    desc: 构建可视化、可在线编辑的 OpenAI 文案 skill 和 Grok 生图 skill
    integrations:
    """
    skill_overrides = _combined_skill_overrides(state)
    prompt_overrides = _get(state, "prompt_overrides", {}) or {}
    if not isinstance(prompt_overrides, dict):
        prompt_overrides = {}

    subflows = [
        _apply_overrides(_openai_subflow(state), skill_overrides, prompt_overrides),
        _apply_overrides(_grok_subflow(state), skill_overrides, prompt_overrides),
    ]
    return SkillSubflowNodeOutput(
        skill_subflows=subflows,
        workflow_diagram_nodes=_diagram_nodes(subflows),
        workflow_diagram_edges=_diagram_edges(subflows),
        operator_edit_panels=_operator_panels(state),
    )
