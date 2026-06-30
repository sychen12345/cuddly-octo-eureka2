## 项目概述
- **名称**: 小红书内容创作工作流
- **功能**: 从对标挖掘、选题库构建、Skill规则/子流程配置（含智能判断是否需同步）、提示词编辑，到OpenAI文案+Grok套图并行生成，最终审核打包的完整内容生产流水线

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | agent | 对标与需求挖掘 | - | `config/greeting_llm_cfg.json` |
| process | `nodes/process_node.py` | agent | 选题库与高浏览选题 | - | `config/process_llm_cfg.json` |
| style_select | `nodes/style_select_node.py` | task | 风格选择：从配置读取图片风格选项，检测运营修改 | - | - |
| aspect_ratio | `nodes/aspect_ratio_node.py` | task | 尺寸选择：从配置读取图片尺寸比例，检测运营修改 | - | - |
| must_have | `nodes/must_have_node.py` | task | 必选项配置：从配置读取图片必须包含元素，检测运营修改 | - | - |
| avoid | `nodes/avoid_node.py` | task | 禁选项配置：从配置读取图片应避免元素，检测运营修改 | - | - |
| consistency_rules | `nodes/consistency_rules_node.py` | task | 一致性规则：从配置读取卡片一致性规则，检测运营修改 | - | - |
| grok_rules_judge | `nodes/grok_rules_judge_node.py` | agent | 智能判断规则变更：用LLM判断变更是否需要同步回skill配置 | "sync_rules"→rules_sync, "skip"→openai_steps | `config/grok_rules_judge_cfg.json` |
| rules_sync | `nodes/rules_sync_node.py` | task | Skill规则同步回写：组装规则并写回配置文件 | - | - |
| openai_steps | `nodes/openai_steps_node.py` | task | OpenAI步骤配置：从配置读取OpenAI子流程步骤，检测运营修改 | - | - |
| grok_steps | `nodes/grok_steps_node.py` | task | Grok步骤配置：从配置读取Grok子流程步骤，检测运营修改 | - | - |
| grok_subflow_judge | `nodes/grok_subflow_judge_node.py` | agent | 智能判断子流程变更：用LLM判断变更是否需要同步回skill配置 | "sync_subflows"→subflow_sync, "skip"→prompt | `config/grok_subflow_judge_cfg.json` |
| subflow_sync | `nodes/subflow_sync_node.py` | task | 子流程同步回写：组装子流程并写回配置文件 | - | - |
| prompt | `nodes/prompt_node.py` | task | 在线提示词编辑 | - | - |
| openai_text | `nodes/openai_text_node.py` | task | OpenAI GPT5.5 文案生成 | - | - |
| grok_image | `nodes/grok_image_node.py` | task | Grok Expert 套图生成 | - | - |
| finalize | `nodes/finalize_node.py` | task | 结果审核打包：将Grok图片URL嵌入GPT5.5卡片文案，智能生成话题标签（如#芯片 #拍照 #美甲） | - | - |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

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
- **grok_rules_judge**: 当运营修改了规则节点（风格/尺寸/必选项/禁选项/一致性规则），LLM 判断变更类型：
  - 规则修改（如 style: cartoon→realistic）→ `"sync_rules"` → 走 rules_sync 同步回写 skill_rules.json
  - 内容调整（如修改领域/受众描述）→ `"skip"` → 跳过同步，直接进入下一步
- **grok_subflow_judge**: 当运营修改了子流程节点（OpenAI/Grok步骤），LLM 判断变更类型：
  - 子流程规则修改（如步骤配置/提示词模板）→ `"sync_subflows"` → 走 subflow_sync 同步回写 skill_subflows.json
  - 内容调整 → `"skip"` → 跳过同步

### 配置文件
| 配置文件 | 用途 |
|---------|------|
| `config/greeting_llm_cfg.json` | 对标与需求挖掘 Agent 模型配置 |
| `config/process_llm_cfg.json` | 选题库 Agent 模型配置 |
| `config/grok_rules_judge_cfg.json` | 规则变更智能判断 Agent 模型配置 |
| `config/grok_subflow_judge_cfg.json` | 子流程变更智能判断 Agent 模型配置 |
| `assets/skill_config/skill_rules.json` | 图片风格规则配置（风格/尺寸/必选项/禁选项/一致性规则） |
| `assets/skill_config/skill_subflows.json` | OpenAI/Grok 子流程步骤配置 |

## 技能使用
- 节点 `greeting` 使用大语言模型技能
- 节点 `process` 使用大语言模型技能
- 节点 `grok_rules_judge` 使用大语言模型技能（doubao-seed-2-0-lite）
- 节点 `grok_subflow_judge` 使用大语言模型技能（doubao-seed-2-0-lite）
