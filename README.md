# 小红书内容全栈工作流

这个项目把 Coze 生成的最小 Python 工作流，改造成一个「找对标 -> 挖评论需求 -> 选择高浏览选题 -> 在线改提示词 -> OpenAI 生成文字描述 -> Grok 生成 3:4 卡通套图 -> 审核打包」的内容生产流程。目标是让使用者只输入几句指令，就能得到可审核、可复用、可继续生产的小红书图文方案。

## 资料依据

- Coze 官方低代码工作流文档：https://docs.coze.cn/guides_workflow
  - 低代码工作流是一组可执行指令，用来实现业务逻辑或完成特定任务。
  - 工作流适合顺序执行节点来完成数据自动化处理；对话流更适合对话场景。
  - 节点是独立步骤，具备输入和输出；每个低代码工作流默认有开始节点和结束节点。
  - 开始节点定义启动工作流需要的输入参数，结束节点返回工作流运行结果。
  - 节点之间通过引用上游节点输出形成数据链路，变量可使用 String、Integer、Number、Boolean、Object、File、Array 等类型。
- 微信分享：https://mp.weixin.qq.com/s/DYH-t-w4eA7A4WDpfIAppw
  - 标题：小红书篇篇 5 位数阅读！我自研了一套全栈爆款笔记 Skills
  - 作者：小肥肠AI纪
  - 发布时间：2026-06-04 18:49:54 CST
  - 核心方法：确定领域、找到对标、评论区需求挖掘、制作选题库、做笔记。
  - 架构启发：不要把搜索爆款、抓详情、抓评论、分析账号、写入知识库、生成报告、生成笔记和图文卡片全部塞进一个大技能；更好的方式是拆成可自由编排的能力模块，由人负责最终决策、取舍和审核。

## Skill 盘点

当前目录下的 `SKILL.md` 包括：

- `algorithmic-art`
- `brand-guidelines`
- `canvas-design`
- `claude-api`
- `doc-coauthoring`
- `docx`
- `frontend-design`
- `internal-comms`
- `mcp-builder`
- `pdf`
- `pptx`
- `skill-creator`
- `slack-gif-creator`
- `theme-factory`
- `template`
- `web-artifacts-builder`
- `webapp-testing`
- `xhs-content-workflow`
- `xlsx`

本机当前可发现/已安装的 skill：

- `/home/csy/.codex/skills/frontend-design`
- `/home/csy/.codex/skills/.system/imagegen`
- `/home/csy/.codex/skills/.system/openai-docs`
- `/home/csy/.codex/skills/.system/plugin-creator`
- `/home/csy/.codex/skills/.system/skill-creator`
- `/home/csy/.codex/skills/.system/skill-installer`
- `/home/csy/.agents/skills/find-skills`

其中 `skills/xhs-content-workflow` 是本次新增的内容工作流 skill。

## 输入

工作流开始节点输入：

- `grok_api_key`：运行时必须由用户输入的 Grok API Key，仅用于本次节点调用，不写入输出。
- `openai_api_key`：运行时必须由用户输入的 OpenAI API Key，仅用于本次节点调用，不写入输出。
- `niche`：领域或产品方向，例如 `AI 副业`、`考研资料`、`亲子英语启蒙`。
- `audience`：目标人群，例如 `上班族新手`。
- `goal`：本轮目标，例如 `生成一组小红书图文卡片`。
- `benchmark_notes`：已知对标账号、爆款笔记、标题、正文、数据或风格摘录。
- `comment_notes`：评论区原话、私信问题、用户抱怨、求资料表达。
- `topic_research_notes`：浏览量、收藏、评论、高赞、热词等选题证据。
- `user_selected_topic`：用户指定选题；填写后优先使用用户选题。
- `constraints`：限制条件，例如 `不要承诺收益`、`强调免费工具`、`卡片 6 页以内`。
- `brand_voice`：账号语气，例如 `清醒、实操、少废话`。
- `card_count`：希望输出的卡片页数。
- `image_count`：希望 Grok 生成的套图张数。
- `image_aspect_ratio`：默认 `3:4`。
- `image_style`：默认 `cartoon`。
- `reference_image_notes`：用户提供参考图时，把角色、色彩、线条、镜头、情绪等观察写入这里。
- `reference_image_urls`：参考图链接。
- `prompt_overrides`：在线修改工作流提示词，支持 `topic_selection`、`openai_text_description`、`grok_expert_image_set`、`final_review`。
- `openai_text_model`：默认 `gpt-5.5`，用于 OpenAI 文案节点。
- `openai_reasoning_mode`：默认 `ultra_high`，用于 GPT5.5 超高推理模式。
- `grok_image_model`：默认 `grok-imagine-image-quality`，用于 Grok Expert/xAI 生图节点。
- `grok_image_mode`：默认 `Expert`。
- `execute_model_calls`：默认 `false`，只生成可审核请求计划；设为 `true` 时直接调用 OpenAI Responses API 和 xAI/Grok 图片生成 API，并把状态或图片 URL 写入结果。API Key 只放在运行时请求头里，不写入输出。

没有对标或评论素材时，工作流会先生成一版研究框架和采样清单，不伪造真实平台数据。

## 节点设计

### 1. 对标与需求挖掘节点

文件：`cozepy/greeting_node.py`

职责：

- 归一化用户输入。
- 从 `benchmark_notes` 中提取对标账号、内容风格、发布信号和可复用结构。
- 从 `comment_notes` 中提取用户需求、痛点、阻碍、购买/领取意图和评论原话。
- 生成 `research_brief`，供下游节点引用。

### 2. 选题库与高浏览选题节点

文件：`cozepy/process_node.py`

职责：

- 将对标信息、评论需求、浏览量/收藏/评论/热词证据沉淀成 `topic_bank`。
- 自动选择预估浏览潜力最高的选题；如果用户填写 `user_selected_topic`，优先使用用户指定选题。

### 3. Skill 规则与参考图节点

文件：`cozepy/skill_rules_node.py`

职责：

- 参考本地/下载的视觉类 skill，把 3:4、卡通风格、套图一致性、参考图吸收规则写入 `image_style_rules`。
- 输出完整 `workflow_steps`，让画布和结果都能直观看到完整 skill 流程。

### 4. 在线提示词编辑节点

文件：`cozepy/prompt_node.py`

职责：

- 输出 `editable_prompts`，包含默认提示词和应用 `prompt_overrides` 后的最终提示词。
- 让用户在线修改 OpenAI 文案提示词、Grok 生图提示词、最终审核提示词。

### 5. OpenAI GPT5.5 超高推理文案节点

文件：`cozepy/openai_text_node.py`

职责：

- 使用 `openai_text_model` 和 `openai_reasoning_mode` 生成文字描述；默认 `ultra_high` 会映射为 OpenAI API 的 `reasoning.effort=xhigh`。
- `execute_model_calls=false` 时只输出可审核请求计划；`true` 时真实请求 `https://api.openai.com/v1/responses`。
- 输出封面标题、每页脚本、小红书正文、给 Grok 的视觉 brief。

### 6. Grok Expert 3:4 卡通套图节点

文件：`cozepy/grok_image_node.py`

职责：

- 使用 `grok_image_model` 和 `grok_image_mode` 为每页生成 3:4 竖版卡通图提示词。
- `execute_model_calls=false` 时只输出图片请求计划；`true` 时真实请求 `https://api.x.ai/v1/images/generations` 并回填 `image_url`。
- 继承参考图规则、套图一致性规则和避免事项。

### 7. 结果审核打包节点

文件：`cozepy/finalize_node.py`

职责：

- 汇总选题、OpenAI 文案、Grok 套图提示、审核清单和下一步指令。
- 确认 API Key 不进入任何输出字段。

## 输出

结束节点输出：

- `workflow_summary`：本轮流程摘要。
- `workflow_steps`：完整节点链路。
- `benchmark_accounts`：对标分析列表。
- `demand_insights`：评论需求洞察列表。
- `topic_bank`：可沉淀到知识库的选题库。
- `selected_topic`：本轮选中的高潜选题。
- `image_style_rules`：3:4 卡通套图规则。
- `editable_prompts`：在线可修改提示词。
- `openai_text_package`：OpenAI GPT5.5 文案包、请求计划或真实调用状态。
- `grok_image_set`：Grok Expert 套图提示、请求计划或真实图片 URL。
- `card_package`：图文卡片成品规格。
- `next_commands`：继续使用 skill/workflow 的短指令。

## 使用示例

```python
from cozepy.graph import main_graph

result = main_graph.invoke({
    "grok_api_key": "gsk_xxx_运行时输入",
    "openai_api_key": "sk-xxx_运行时输入",
    "niche": "AI 副业",
    "audience": "想用 AI 做副业但没方向的上班族",
    "goal": "生成一组小红书图文卡片",
    "benchmark_notes": [
        "近期起号账号，标题常用「普通人也能做」和「别再只学工具」",
        "爆款笔记结构：先讲焦虑场景，再给 3 个可执行路径，最后引导领取清单"
    ],
    "comment_notes": [
        "评论：我没有编程基础可以做吗",
        "评论：有没有适合下班后做的项目",
        "评论：能不能给一个从0开始的步骤"
    ],
    "topic_research_notes": [
        "对标标题 1.8 万浏览，评论集中问零基础和下班后怎么做",
        "搜索热词：AI副业、普通人副业、零基础AI"
    ],
    "user_selected_topic": "",
    "constraints": ["不要承诺收益", "强调先验证需求", "卡片不超过6页"],
    "brand_voice": "清醒、实操、少废话",
    "card_count": 6,
    "image_count": 6,
    "image_aspect_ratio": "3:4",
    "image_style": "cartoon",
    "execute_model_calls": False,
    "reference_image_notes": ["圆润线条", "明亮但不刺眼", "主角表情夸张但不幼稚"],
    "prompt_overrides": {
        "grok_expert_image_set": "生成 3:4 竖版卡通套图，统一角色、统一色板、每页只表达一个核心动作。"
    }
})
```

## 审核原则

- 不把猜测包装成真实平台数据。
- 不在日志、文档、选题库或最终输出里展示 API Key。
- 不承诺阅读量、涨粉或收益。
- 对标只学习结构、节奏、表达和需求信号，不复制原文。
- 评论需求保留用户原话，但输出时做匿名化处理。
- 图文卡片先满足信息清楚，再追求风格。
