## 项目概述
- **名称**: 小红书AI内容运营工作流
- **功能**: 运营只需输入需求（文字+可选小红书链接），Grok 智能识别意图后自动路由到对应流程：竞品调研 → 爆款选题 → 视觉设定 → 文案生成 → 图片生成 → 审核打包

## 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 配置文件 |
|-------|---------|------|---------|---------|
| 需求接收 | `nodes/intent_analysis_node.py` | task | 接收运营自由文本+链接输入 | - |
| Grok意图识别 | `nodes/intent_analysis_node.py` | agent | AI分析运营意图，决定走哪条路径 | `config/intent_analysis_cfg.json` |
| 竞品调研分析 | `nodes/greeting_node.py` | agent | 对标账号结构拆解与需求挖掘 | `config/greeting_llm_cfg.json` |
| 爆款选题筛选 | `nodes/process_node.py` | agent | 选题库生成与高浏览潜力评分 | `config/process_llm_cfg.json` |
| 视觉风格设定 | `nodes/style_select_node.py` | task | 从配置读取视觉风格（运营可切换） | - |
| 图片尺寸设定 | `nodes/aspect_ratio_node.py` | task | 从配置读取图片比例 | - |
| 内容必选项 | `nodes/must_have_node.py` | task | 必须包含的内容元素（模板渲染） | - |
| 内容禁选项 | `nodes/avoid_node.py` | task | 禁止出现的内容（模板渲染） | - |
| 套图一致性规则 | `nodes/consistency_rules_node.py` | task | 多图统一风格约束（模板渲染） | - |
| 规则变更判断 | `nodes/grok_rules_judge_node.py` | agent | AI判断运营修改的是规则还是内容 | `config/grok_rules_judge_cfg.json` |
| 规则同步保存 | `nodes/rules_sync_node.py` | task | 将规则修改写回 skill_rules.json | - |
| 文案生成步骤 | `nodes/openai_steps_node.py` | task | 配置GPT文案生成步骤 | - |
| 图片生成步骤 | `nodes/grok_steps_node.py` | task | 配置Grok图片生成步骤 | - |
| 步骤变更判断 | `nodes/grok_subflow_judge_node.py` | agent | AI判断运营修改的是步骤还是内容 | `config/grok_subflow_judge_cfg.json` |
| 步骤同步保存 | `nodes/subflow_sync_node.py` | task | 将步骤修改写回 skill_subflows.json | - |
| 提示词最终确认 | `nodes/prompt_node.py` | task | 运营最终确认提示词 | - |
| AI文案生成 | `nodes/openai_text_node.py` | task | GPT生成图文卡片文案 | - |
| AI图片生成 | `nodes/grok_image_node.py` | task | Grok生成卡片套图 | - |
| 内容审核打包 | `nodes/finalize_node.py` | task | 审核并输出最终内容 | - |

**类型说明**: task(任务节点) / agent(AI大模型) / condition(条件分支)

## 条件分支
| 分支名 | 文件位置 | 条件 | 路由 |
|-------|---------|------|------|
| intent_path | `graph.py` | Grok意图识别结果 | 竞品调研/爆款选题/数据复盘→END，完整流程→继续 |
| should_sync_rules | `graph.py` | 规则变更判断 | sync_rules→规则同步保存，skip→文案生成步骤 |
| should_sync_subflows | `graph.py` | 步骤变更判断 | sync_subflows→步骤同步保存，skip→提示词最终确认 |

## 配置文件
- `assets/skill_config/skill_rules.json` — 图片风格规则（Jinja2模板）
- `assets/skill_config/skill_subflows.json` — 子流程步骤配置（Jinja2模板）
- `config/intent_analysis_cfg.json` — Grok意图识别 LLM 配置
- `config/greeting_llm_cfg.json` — 竞品调研 LLM 配置
- `config/process_llm_cfg.json` — 选题筛选 LLM 配置
- `config/grok_rules_judge_cfg.json` — 规则判断 LLM 配置
- `config/grok_subflow_judge_cfg.json` — 步骤判断 LLM 配置

## 技能使用
- `竞品调研分析` 使用 LLM (deepseek-v3-2-251201) 或 OpenAI
- `爆款选题筛选` 使用 LLM (deepseek-v3-2-251201)
- `Grok意图识别` 使用 LLM (deepseek-v3-2-251201)
- `规则变更判断` 使用 LLM (deepseek-v3-2-251201)
- `步骤变更判断` 使用 LLM (deepseek-v3-2-251201)
- `AI文案生成` 使用 OpenAI GPT-5.5
- `AI图片生成` 使用 Grok Imagine

## 意图路由机制
运营输入自由文本（+ 可选小红书链接）→ Grok意图识别分析 → 输出 intent：
- `竞品调研` → 竞品调研分析 → END（只看数据）
- `爆款选题` → 竞品调研分析 → 爆款选题筛选 → END
- `完整流程` → 全部节点 → 内容审核打包 → END
- `数据复盘` → END（待扩展）
