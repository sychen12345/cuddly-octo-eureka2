## 项目概述
- **名称**: 小红书内容创作工作流
- **功能**: 从对标挖掘、选题库构建、Skill规则/子流程配置、提示词编辑，到OpenAI文案+Grok套图并行生成，最终审核打包的完整内容生产流水线

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | agent | 对标与需求挖掘 | - | `config/greeting_llm_cfg.json` |
| process | `nodes/process_node.py` | agent | 选题库与高浏览选题 | - | `config/process_llm_cfg.json` |
| style_select | `nodes/style_select_node.py` | task | 风格选择：从配置读取图片风格选项 | - | - |
| aspect_ratio | `nodes/aspect_ratio_node.py` | task | 尺寸选择：从配置读取图片尺寸比例 | - | - |
| must_have | `nodes/must_have_node.py` | task | 必选项配置：从配置读取图片必须包含元素 | - | - |
| avoid | `nodes/avoid_node.py` | task | 禁选项配置：从配置读取图片应避免元素 | - | - |
| consistency_rules | `nodes/consistency_rules_node.py` | task | 一致性规则：从配置读取卡片一致性规则 | - | - |
| rules_sync | `nodes/rules_sync_node.py` | task | Skill规则同步回写：组装规则并写回配置文件 | - | - |
| openai_steps | `nodes/openai_steps_node.py` | task | OpenAI步骤配置：从配置读取OpenAI子流程步骤 | - | - |
| grok_steps | `nodes/grok_steps_node.py` | task | Grok步骤配置：从配置读取Grok子流程步骤 | - | - |
| subflow_sync | `nodes/subflow_sync_node.py` | task | 子流程同步回写：组装子流程并写回配置文件 | - | - |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑 | - | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI GPT5.5 文案生成 | - | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图生成 | - | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包 | - | - |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

### 主图拓扑
```
greeting → process → style_select → aspect_ratio → must_have → avoid → consistency_rules → rules_sync → openai_steps → subflow_sync → prompt → [openai_text || grok_image] → finalize → END
                                                                                                                              ↑
                                                                                                                   grok_steps ─┘
```

### 配置文件
| 配置文件 | 用途 |
|---------|------|
| `config/greeting_llm_cfg.json` | 对标与需求挖掘 Agent 模型配置 |
| `config/process_llm_cfg.json` | 选题库 Agent 模型配置 |
| `assets/skill_config/skill_rules.json` | 图片风格规则配置（风格/尺寸/必选项/禁选项/一致性规则） |
| `assets/skill_config/skill_subflows.json` | OpenAI/Grok 子流程步骤配置 |

## 技能使用
- 节点 `greeting` 使用大语言模型技能
- 节点 `process` 使用大语言模型技能
