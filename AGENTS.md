## 项目概述
- **名称**: 小红书内容全栈工作流
- **功能**: 从对标分析到图文卡片生成的一站式小红书内容工作流

### 工作流结构
```
开始 → 对标与需求挖掘 → 选题库与高浏览选题 → Skill规则与参考图
     → OpenAI/Grok Skill 子流程 → 在线提示词编辑 → OpenAI GPT5.5 文案
     → Grok Expert 套图 → 结果审核打包 → 结束
```

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 配置文件 |
|-------|---------|------|---------|---------|
| greeting | `nodes/greeting_node.py` | task | 对标与需求挖掘：整理对标素材与评论需求 | - |
| process | `nodes/process_node.py` | task | 选题库与高浏览选题：生成选题库并选出高潜选题 | - |
| skill_rules | `nodes/skill_rules_node.py` | task | Skill规则与参考图：生成视觉规则和工作流步骤 | - |
| skill_subflow | `nodes/skill_subflow_node.py` | task | OpenAI/Grok Skill 子流程：构建可编辑子流程 | - |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑：汇总可编辑提示词 | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI GPT5.5 文案：调用 OpenAI API 生成文案 | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图：调用 Grok API 生成套图 | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包：整合为最终卡片包 | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

### 工具模块
| 模块 | 文件位置 | 功能 |
|------|---------|------|
| http_utils | `nodes/http_utils.py` | 封装 OpenAI / Grok REST API 调用 |

## 技能使用
- `openai_text_node` 调用 OpenAI Chat Completions API
- `grok_image_node` 调用 Grok (xAI) 图像生成 API

## API Key 配置
- `openai_api_key`: 通过 GraphInput 传入或环境变量 `OPENAI_API_KEY`
- `grok_api_key`: 通过 GraphInput 传入或环境变量 `GROK_API_KEY`
- `execute_model_calls`: 设为 `true` 才会真实调用 API，否则为 dry_run 模式
