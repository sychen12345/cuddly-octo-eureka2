## 项目概述
- **名称**: 小红书内容全栈工作流
- **功能**: 输入赛道/对标/评论等信息，自动生成小红书图文卡片（文案+套图）

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | task | 对标与需求挖掘 | - | - |
| process | `nodes/process_node.py` | task | 选题库与高浏览选题 | - | - |
| skill_rules | `nodes/skill_rules_node.py` | subgraph | Skill规则子工作流（调用 skill_rules_subgraph） | - | `assets/skill_config/skill_rules.json` |
| skill_subflow | `nodes/skill_subflow_node.py` | subgraph | 子流程子工作流（调用 skill_subflow_subgraph） | - | `assets/skill_config/skill_subflows.json` |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑 | - | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI GPT5.5 文案生成 | - | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图生成 | - | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环) / subgraph(子工作流)

### 并行结构
`prompt` 节点后并行执行 `openai_text` 和 `grok_image`，两个分支完成后汇聚到 `finalize`：
```
greeting → process → skill_rules(子工作流) → skill_subflow(子工作流) → prompt
                                                                        ├── openai_text ──┐
                                                                        └── grok_image  ──┘──→ finalize
```

## 子图清单
| 子图名 | 文件位置 | 功能描述 | 被调用节点 |
|-------|---------|------|---------|
| skill_rules_subgraph | `graphs/loop_graph.py` | 图片风格规则子工作流（风格/尺寸/必选项/禁选项/一致性规则 + 同步回写） | skill_rules |
| skill_subflow_subgraph | `graphs/loop_graph.py` | Skill 子流程子工作流（OpenAI步骤/Grok步骤 + 同步回写） | skill_subflow |

### 子图内部节点

**skill_rules_subgraph 内部节点：**
| 节点名 | 文件位置 | 功能描述 |
|-------|---------|---------|
| style_select | `nodes/style_select_node.py` | 风格选择（从配置读取可选风格列表，输出当前风格） |
| aspect_ratio | `nodes/aspect_ratio_node.py` | 尺寸选择（从配置读取可选尺寸，输出当前尺寸） |
| must_have | `nodes/must_have_node.py` | 必选项配置（从配置读取必选项列表） |
| avoid | `nodes/avoid_node.py` | 禁选项配置（从配置读取禁选项列表） |
| consistency_rules | `nodes/consistency_rules_node.py` | 一致性规则配置（从配置读取一致性规则列表） |
| rules_sync | `nodes/rules_sync_node.py` | 汇聚子工作流结果 + 同步回写配置文件 |

**skill_subflow_subgraph 内部节点：**
| 节点名 | 文件位置 | 功能描述 |
|-------|---------|---------|
| openai_steps | `nodes/openai_steps_node.py` | OpenAI 子流程步骤配置（从配置读取 openai_text_skill 步骤） |
| grok_steps | `nodes/grok_steps_node.py` | Grok 子流程步骤配置（从配置读取 grok_image_skill 步骤） |
| subflow_sync | `nodes/subflow_sync_node.py` | 汇聚子流程结果 + 同步回写配置文件 |

## 工具模块
| 文件 | 说明 |
|------|------|
| `nodes/http_utils.py` | HTTP 请求工具（OpenAI/Grok API 调用封装） |

## Skill 配置文件
| 文件 | 说明 | 对应子工作流 |
|------|------|---------|
| `assets/skill_config/skill_rules.json` | 图片风格规则（风格/尺寸/必选项/禁选项/一致性规则） | skill_rules_subgraph |
| `assets/skill_config/skill_subflows.json` | 子流程定义（OpenAI/Grok 步骤、端点、提示词模板） | skill_subflow_subgraph |

### 画布拖拽 & 配置同步机制
- **skill_rules** 在画布上展示为子工作流，内部包含 5 个可编辑配置节点 + 1 个同步回写节点
  - 运营可以双击进入子工作流，看到「风格选择 → 尺寸选择 → 必选项 → 禁选项 → 一致性规则 → 同步回写」完整流程
  - 修改任意内部节点后，`rules_sync` 节点自动将变更写回 `assets/skill_config/skill_rules.json`
- **skill_subflow** 在画布上展示为子工作流，内部包含 2 个并行步骤配置节点 + 1 个同步回写节点
  - 运营可以双击进入子工作流，看到「OpenAI步骤配置 / Grok步骤配置 → 同步回写」完整流程
  - 修改步骤后，`subflow_sync` 节点自动将变更写回 `assets/skill_config/skill_subflows.json`

## 技能使用
- 节点 `openai_text` 调用 OpenAI API（需 OPENAI_API_KEY）
- 节点 `grok_image` 调用 Grok/xAI API（需 GROK_API_KEY）
- 支持 `execute_model_calls=false` 干跑模式（无需 API key）

## 扩展指南
- 新增节点：在 `nodes/` 下创建 `xxx_node.py`，在 `state.py` 定义 Input/Output，在 `graph.py` 注册
- 新增子工作流内部节点：创建节点文件 → 在 `state.py` 定义 Input/Output → 在 `loop_graph.py` 子图中注册
- 修改 Skill 规则：编辑 `assets/skill_config/skill_rules.json`，或在画布上修改子工作流内部节点
- 修改子流程步骤：编辑 `assets/skill_config/skill_subflows.json`，或在画布上修改子工作流内部节点
- 接入真实 API：传入 `execute_model_calls=true` + 对应 API key
