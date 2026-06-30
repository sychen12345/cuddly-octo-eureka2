# 小红书 AI 内容运营工作流

## 项目概述

- **定位**: 给运营使用的低代码内容生产画布。
- **输入**: 运营需求、小红书竞品链接、对标线索、评论原话、运营指定选题、OpenAI API Key、Grok API Key。
- **输出**: 竞品和用户需求分析、爆款选题机会池、可展开技能子树、AI 文案、AI 套图、成品审核与复盘建议。
- **关键约定**: 运营看到的是业务动作和技能流程，不需要看到代码、JSON 或底层文件名。

## 业务树

```text
运营需求入口
└─ AI理解运营目标
   ├─ 竞品和用户需求分析
   ├─ 爆款选题机会池
   │  ├─ 运营指定选题优先
   │  └─ 有竞品链接时由 OpenAI 联网查询并给出选题灵感
   ├─ 图片制作技能
   │  ├─ 图片制作技能：选风格
   │  ├─ 图片制作技能：定比例
   │  ├─ 图片制作技能：必备元素
   │  ├─ 图片制作技能：避坑清单
   │  └─ 图片制作技能：套图统一
   ├─ AI技能教练
   │  ├─ 检查图片规则是否值得长期保留
   │  └─ 检查文案/图片生成流程是否值得长期保留
   ├─ 内容生成技能
   │  ├─ 文案技能：拆步骤
   │  └─ 图片技能：拆步骤
   ├─ 运营确认生成方案
   ├─ AI生成小红书文案
   ├─ AI生成小红书套图
   └─ 成品审核与复盘建议
```

## 节点清单

| 运营可见节点 | 文件位置 | 类型 | 业务说明 |
| --- | --- | --- | --- |
| 运营需求入口 | `src/graphs/nodes/intent_analysis_node.py` | agent | 接收运营自然语言、小红书链接和指定选题 |
| AI理解运营目标 | `src/graphs/nodes/intent_analysis_node.py` | agent | 判断本次做调研、选题、数据复盘或完整生产 |
| 竞品和用户需求分析 | `src/graphs/nodes/greeting_node.py` | agent | 拆解竞品结构、评论需求和内容机会 |
| 爆款选题机会池 | `src/graphs/nodes/process_node.py` | agent | 从竞品链接和需求中生成选题，运营指定选题优先 |
| 图片制作技能：选风格 | `src/graphs/nodes/style_select_node.py` | skill step | 选择整体画面风格 |
| 图片制作技能：定比例 | `src/graphs/nodes/aspect_ratio_node.py` | skill step | 选择小红书图片比例 |
| 图片制作技能：必备元素 | `src/graphs/nodes/must_have_node.py` | skill step | 确认画面必须出现的元素 |
| 图片制作技能：避坑清单 | `src/graphs/nodes/avoid_node.py` | skill step | 确认画面要避开的元素 |
| 图片制作技能：套图统一 | `src/graphs/nodes/consistency_rules_node.py` | skill step | 保持整组图统一 |
| AI技能教练：检查图片规则 | `src/graphs/nodes/grok_rules_judge_node.py` | agent | 判断图片技能改动是否值得长期保留 |
| 沉淀图片制作经验 | `src/graphs/nodes/rules_sync_node.py` | skill memory | 保存运营确认的长期图片制作经验 |
| 文案技能：拆步骤 | `src/graphs/nodes/openai_steps_node.py` | subAgent | 展开文案生成技能 |
| 图片技能：拆步骤 | `src/graphs/nodes/grok_steps_node.py` | subAgent | 展开套图生成技能 |
| AI技能教练：检查生成流程 | `src/graphs/nodes/grok_subflow_judge_node.py` | agent | 判断文案/图片流程改动是否值得长期保留 |
| 沉淀内容生成经验 | `src/graphs/nodes/subflow_sync_node.py` | skill memory | 保存运营确认的长期生成流程 |
| 运营确认生成方案 | `src/graphs/nodes/prompt_node.py` | review | 运营确认文案方向和套图方向 |
| AI生成小红书文案 | `src/graphs/nodes/openai_text_node.py` | content | 生成标题、正文和每页脚本 |
| AI生成小红书套图 | `src/graphs/nodes/grok_image_node.py` | content | 生成小红书图文套图 |
| 成品审核与复盘建议 | `src/graphs/nodes/finalize_node.py` | review | 输出卡片包、审核清单和下一轮建议 |

## 运行要求

- `GraphInput.openai_api_key` 和 `GraphInput.grok_api_key` 是运行前必填字段。
- 运营可通过 `user_selected_topic` 指定选题或话题标签；指定后优先进入生产链路。
- 运营提供 `xiaohongshu_url` 且真实运行时，`爆款选题机会池` 使用 OpenAI 联网查询竞品链接来生成选题灵感。
- 最终话题标签来自上游选题或运营显式输入，不在审核节点写死行业词。

## 本地运行

```bash
bash scripts/local_run.sh -m flow
bash scripts/local_run.sh -m node -n node_name
bash scripts/http_run.sh -m http -p 5000
```
