## 项目概述
- **名称**: 工作流模板（含并行分支）
- **功能**: 展示 Agent 节点 + 并行 API 调用 + 汇聚节点的完整工作流模板

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| model_select | `nodes/model_select_node.py` | agent | 调用大模型根据用户名称推荐问候风格 | - | `config/model_select_cfg.json` |
| greeting | `nodes/greeting_node.py` | agent | 调用大模型根据名称和风格生成个性化问候 | - | `config/greeting_cfg.json` |
| grok_call | `nodes/grok_node.py` | task | 调用 Grok API 分析问候语质量 | - | - |
| openai_call | `nodes/openai_node.py` | task | 调用 OpenAI API 分析问候语质量 | - | - |
| merge | `nodes/merge_node.py` | agent | 调用大模型对比合并两个模型的分析结果 | - | `config/merge_cfg.json` |
| process | `nodes/process_node.py` | agent | 调用大模型整合问候和分析为最终输出 | - | `config/process_cfg.json` |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 并行分支
- `grok_call` 和 `openai_call` 为并行分支，在 `greeting` 之后同时执行
- 两者都完成后由 `merge` 节点汇聚结果

## 子图清单
暂无子图

## 技能使用
- 节点 `model_select`、`greeting`、`merge`、`process` 使用大语言模型技能

## 环境变量
使用前需配置以下环境变量：
- `GROK_API_KEY`：xAI Grok API Key
- `OPENAI_API_KEY`：OpenAI API Key