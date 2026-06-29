## 项目概述
- **名称**: 工作流模板
- **功能**: 展示 Agent 节点 + 任务节点的完整工作流模板，包含模型选取、问候生成、结果处理

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| model_select | `nodes/model_select_node.py` | agent | 调用大模型根据用户名称推荐问候风格 | - | `config/model_select_cfg.json` |
| greeting | `nodes/greeting_node.py` | task | 根据名称和风格生成个性化问候 | - | - |
| process | `nodes/process_node.py` | task | 处理问候消息生成最终结果 | - | - |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
暂无子图

## 技能使用
- 节点 `model_select` 使用大语言模型技能

## 快速开始
1. 查看状态定义：`src/graphs/state.py`
2. 查看节点实现：`src/graphs/nodes/`
3. 查看工作流编排：`src/graphs/graph.py`
4. 运行测试：传入 user_name 执行 test_run

## 扩展指南
### 添加新节点
1. 在 `src/graphs/state.py` 中定义节点的 Input/Output
2. 在 `src/graphs/nodes/` 中创建节点文件
3. 在 `src/graphs/graph.py` 中注册节点并添加边

### 添加 Agent 节点
1. 在 `config/` 中创建 LLM 配置文件（参考 model_select_cfg.json）
2. 在节点函数中使用 LLMClient 调用大模型
3. 注册节点时添加 `metadata={"type": "agent", "llm_cfg": "config/xxx.json"}`