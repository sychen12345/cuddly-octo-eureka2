# 小红书内容全栈工作流

这个项目把 Coze 生成的最小 Python 工作流，改造成一个「找对标 -> 挖评论需求 -> 沉淀选题库 -> 生成图文卡片」的内容生产流程。目标是让使用者只输入几句指令，就能得到可审核、可复用、可继续生产的小红书图文方案。

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
- `constraints`：限制条件，例如 `不要承诺收益`、`强调免费工具`、`卡片 6 页以内`。
- `brand_voice`：账号语气，例如 `清醒、实操、少废话`。
- `card_count`：希望输出的卡片页数。

没有对标或评论素材时，工作流会先生成一版研究框架和采样清单，不伪造真实平台数据。

## 节点设计

### 1. 对标与需求挖掘节点

文件：`cozepy/greeting_node.py`

职责：

- 归一化用户输入。
- 从 `benchmark_notes` 中提取对标账号、内容风格、发布信号和可复用结构。
- 从 `comment_notes` 中提取用户需求、痛点、阻碍、购买/领取意图和评论原话。
- 生成 `research_brief`，供下游节点引用。

### 2. 选题库与图文卡片节点

文件：`cozepy/process_node.py`

职责：

- 将对标信息和评论需求沉淀成 `topic_bank`。
- 为优先选题生成小红书图文卡片包：封面标题、每页卡片文案、视觉提示词、正文 caption、CTA、审核清单。
- 生成下一步几句指令，让使用者继续迭代、扩写或交给设计工具出图。

## 输出

结束节点输出：

- `workflow_summary`：本轮流程摘要。
- `benchmark_accounts`：对标分析列表。
- `demand_insights`：评论需求洞察列表。
- `topic_bank`：可沉淀到知识库的选题库。
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
    "constraints": ["不要承诺收益", "强调先验证需求", "卡片不超过6页"],
    "brand_voice": "清醒、实操、少废话",
    "card_count": 6
})
```

## 审核原则

- 不把猜测包装成真实平台数据。
- 不在日志、文档、选题库或最终输出里展示 API Key。
- 不承诺阅读量、涨粉或收益。
- 对标只学习结构、节奏、表达和需求信号，不复制原文。
- 评论需求保留用户原话，但输出时做匿名化处理。
- 图文卡片先满足信息清楚，再追求风格。
