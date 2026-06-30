## 项目概述
- **名称**: 小红书内容全栈工作流
- **功能**: 输入赛道/对标/评论等信息，自动生成小红书图文卡片（文案+套图）

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | task | 对标与需求挖掘 | - | - |
| process | `nodes/process_node.py` | task | 选题库与高浏览选题 | - | - |
| skill_rules | `nodes/skill_rules_node.py` | task | Skill规则与参考图（从配置读取，输出可编辑面板） | - | `assets/skill_config/skill_rules.json` |
| skill_subflow | `nodes/skill_subflow_node.py` | task | OpenAI/Grok Skill 子流程定义（从配置读取，步骤可排序） | - | `assets/skill_config/skill_subflows.json` |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑 | - | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI GPT5.5 文案生成 | - | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图生成 | - | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包 + 配置回写 | - | - |

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

## Skill 配置文件
| 文件 | 说明 | 对应节点 |
|------|------|---------|
| `assets/skill_config/skill_rules.json` | 图片风格规则（风格/尺寸/必选项/禁选项/一致性规则） | skill_rules |
| `assets/skill_config/skill_subflows.json` | 子流程定义（OpenAI/Grok 步骤、端点、提示词模板） | skill_subflow |

### 画布拖拽 & 配置同步机制
- **skill_rules_node** 从 `assets/skill_config/skill_rules.json` 读取配置，输出 `operator_control` 面板（包含风格下拉框、尺寸选择、开关等控件）
- **skill_subflow_node** 从 `assets/skill_config/skill_subflows.json` 读取配置，输出可排序步骤面板
- **finalize_node** 在打包结果时，将运营修改后的规则和步骤**回写**到对应 JSON 配置文件
- 运营在前端修改面板内容 → 下次运行工作流时自动从配置文件读取最新值

## 技能使用
- 节点 `openai_text` 调用 OpenAI API（需 OPENAI_API_KEY）
- 节点 `grok_image` 调用 Grok/xAI API（需 GROK_API_KEY）
- 支持 `execute_model_calls=false` 干跑模式（无需 API key）

## 扩展指南
- 新增节点：在 `nodes/` 下创建 `xxx_node.py`，在 `state.py` 定义 Input/Output，在 `graph.py` 注册
- 修改 Skill 规则：编辑 `assets/skill_config/skill_rules.json`
- 修改子流程步骤：编辑 `assets/skill_config/skill_subflows.json`
- 接入真实 API：传入 `execute_model_calls=true` + 对应 API key
