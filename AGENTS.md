## 项目概述
- **名称**: 小红书内容创作工作流
- **功能**: 从对标挖掘、选题库构建、Skill规则/子流程配置（Jinja2模板动态注入 + 智能判断是否需同步）、提示词编辑，到OpenAI/DeepSeek文案+Grok套图并行生成，最终审核打包的完整内容生产流水线
- **模型**: 所有Agent节点默认使用 DeepSeek V3 (`deepseek-v3-2-251201`)，支持用户自带 DeepSeek API Key

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | agent | 对标与需求挖掘（优先DeepSeek，fallback OpenAI） | - | `config/greeting_llm_cfg.json` |
| process | `nodes/process_node.py` | agent | 选题库与高浏览选题 | - | `config/process_llm_cfg.json` |
| style_select | `nodes/style_select_node.py` | task | 风格选择：从配置读取图片风格选项 | - | - |
| aspect_ratio | `nodes/aspect_ratio_node.py` | task | 尺寸选择：从配置读取图片尺寸比例 | - | - |
| must_have | `nodes/must_have_node.py` | task | 必选项配置：Jinja2模板渲染（`{{niche}}`等动态注入），运营可增删标签 | - | - |
| avoid | `nodes/avoid_node.py` | task | 禁选项配置：Jinja2模板渲染，运营可增删标签 | - | - |
| consistency_rules | `nodes/consistency_rules_node.py` | task | 一致性规则：Jinja2模板渲染，运营可增删规则 | - | - |
| grok_rules_judge | `nodes/grok_rules_judge_node.py` | agent | 智能判断规则变更：DeepSeek判断变更是否需要同步回skill配置 | "sync_rules"→rules_sync, "skip"→openai_steps | `config/grok_rules_judge_cfg.json` |
| rules_sync | `nodes/rules_sync_node.py` | task | Skill规则同步回写：组装规则并写回配置文件 | - | - |
| openai_steps | `nodes/openai_steps_node.py` | task | OpenAI步骤配置：Jinja2模板渲染提示词（niche/audience/brand_voice/topic动态注入），运营可编辑 | - | - |
| grok_steps | `nodes/grok_steps_node.py` | task | Grok步骤配置：Jinja2模板渲染提示词（niche/audience/brand_voice/topic动态注入），运营可编辑 | - | - |
| grok_subflow_judge | `nodes/grok_subflow_judge_node.py` | agent | 智能判断子流程变更：DeepSeek判断变更是否需要同步回skill配置 | "sync_subflows"→subflow_sync, "skip"→prompt | `config/grok_subflow_judge_cfg.json` |
| subflow_sync | `nodes/subflow_sync_node.py` | task | 子流程同步回写：组装子流程并写回配置文件 | - | - |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑 | - | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI/DeepSeek GPT5.5 文案生成 | - | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图生成 | - | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包：将Grok图片URL嵌入GPT5.5卡片文案，智能生成话题标签 | - | - |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

### 模板渲染机制
- **配置即模板**: `skill_rules.json` 和 `skill_subflows.json` 中的字符串值支持 Jinja2 语法（如 `"领域：{{niche}}"`）
- **运行时注入**: must_have、avoid、consistency_rules、openai_steps、grok_steps 节点读取配置后用当前 State 值渲染模板
- **可用变量**: `niche`（领域）、`audience`（受众）、`brand_voice`（语气）、`selected_topic_title`（选题标题）
- **运营可编辑**: 渲染后的值运营可在画布上覆盖修改

### 主图拓扑
```
greeting → process → style_select → aspect_ratio → must_have → avoid → consistency_rules
  ↓
grok_rules_judge ──(条件分支)──┬→ rules_sync → openai_steps
                               └→ openai_steps
  ↓
openai_steps ──┐
grok_steps  ───┤
  ↓
grok_subflow_judge ──(条件分支)──┬→ subflow_sync → prompt
                                └→ prompt
  ↓
prompt → [openai_text || grok_image] → finalize → END
```

### 智能判断逻辑
- **grok_rules_judge**: DeepSeek V3 判断规则变更类型
- **grok_subflow_judge**: DeepSeek V3 判断子流程变更类型

### 配置文件
| 配置文件 | 用途 |
|---------|------|
| `config/greeting_llm_cfg.json` | 对标与需求挖掘 Agent 模型配置（DeepSeek V3） |
| `config/process_llm_cfg.json` | 选题库 Agent 模型配置（DeepSeek V3） |
| `config/grok_rules_judge_cfg.json` | 规则变更智能判断 Agent 模型配置（DeepSeek V3） |
| `config/grok_subflow_judge_cfg.json` | 子流程变更智能判断 Agent 模型配置（DeepSeek V3） |
| `assets/skill_config/skill_rules.json` | 图片风格规则模板（风格/尺寸/必选项/禁选项/一致性规则，支持 `{{niche}}` 等变量） |
| `assets/skill_config/skill_subflows.json` | OpenAI/Grok 子流程步骤模板（提示词支持 `{{niche}}`/`{{audience}}` 等变量） |

## 技能使用
- 节点 `grok_rules_judge` 使用大语言模型技能（deepseek-v3-2-251201）
- 节点 `grok_subflow_judge` 使用大语言模型技能（deepseek-v3-2-251201）
- 节点 `greeting` 优先使用用户 DeepSeek API Key 直调，fallback 到 OpenAI
