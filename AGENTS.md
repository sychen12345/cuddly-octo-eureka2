## 项目概述
- **名称**: 小红书内容全栈工作流
- **功能**: 输入赛道/对标/评论等信息，自动生成小红书图文卡片（文案+套图）

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | task | 对标与需求挖掘 | - | - |
| process | `nodes/process_node.py` | task | 选题库与高浏览选题 | - | - |
| skill_rules | `nodes/skill_rules_node.py` | task | Skill规则与参考图 | - | - |
| skill_subflow | `nodes/skill_subflow_node.py` | task | OpenAI/Grok Skill 子流程定义 | - | - |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑 | - | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI GPT5.5 文案生成 | - | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图生成 | - | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

### 并行结构
`prompt` 节点后并行执行 `openai_text` 和 `grok_image`，两个分支完成后汇聚到 `finalize`：
```
greeting → process → skill_rules → skill_subflow → prompt
                                                        ├── openai_text ──┐
                                                        └── grok_image  ──┘──→ finalize
```

## 工具模块
| 文件 | 说明 |
|------|------|
| `nodes/http_utils.py` | HTTP 请求工具（OpenAI/Grok API 调用封装） |

## 技能使用
- 节点 `openai_text` 调用 OpenAI API（需 OPENAI_API_KEY）
- 节点 `grok_image` 调用 Grok/xAI API（需 GROK_API_KEY）
- 支持 `execute_model_calls=false` 干跑模式（无需 API key）

## 扩展指南
- 新增节点：在 `nodes/` 下创建 `xxx_node.py`，在 `state.py` 定义 Input/Output，在 `graph.py` 注册
- 修改提示词：调整 `prompt_node.py` 中的 editable_prompts
- 接入真实 API：传入 `execute_model_calls=true` + 对应 API key
