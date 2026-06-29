## 项目概述
- **名称**: 小红书内容全栈工作流
- **功能**: 找对标 → 挖评论需求 → 沉淀选题库 → 生成图文卡片

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| benchmark_and_demand | `nodes/benchmark_demand_node.py` | task | 从对标素材和评论原话中提取对标结构与用户需求 | - | - |
| topic_and_card | `nodes/topic_card_node.py` | task | 将对标和评论需求沉淀为选题库，并生成图文卡片规格 | - | - |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
暂无子图

## 输入参数
- `niche`: 领域或产品方向（必填）
- `audience`: 目标人群
- `goal`: 本轮目标
- `benchmark_notes`: 对标素材列表
- `comment_notes`: 评论或私信素材列表
- `constraints`: 限制条件
- `brand_voice`: 账号语气
- `card_count`: 卡片页数
- `grok_api_key`: Grok API Key（可选，预留后续接入）
- `openai_api_key`: OpenAI API Key（可选，预留后续接入）

## 输出结果
- `workflow_summary`: 流程摘要
- `benchmark_accounts`: 对标分析列表
- `demand_insights`: 评论需求洞察列表
- `topic_bank`: 选题库
- `card_package`: 图文卡片成品包
- `next_commands`: 下一步指令
