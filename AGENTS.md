## 项目概述
- **名称**: 工作流模板（含并行分支）
- **功能**: 展示 Agent 节点 + 并行 task 节点 + 汇聚的完整工作流模板

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| model_select | `nodes/model_select_node.py` | agent | 调用大模型根据用户名称推荐问候风格 | - | `config/model_select_cfg.json` |
| greeting | `nodes/greeting_node.py` | agent | 调用大模型根据名称和风格生成个性化问候 | - | `config/greeting_cfg.json` |
| task1 | `nodes/task1_node.py` | task | 并行分支1，功能待定义 | - | - |
| task2 | `nodes/task2_node.py` | task | 并行分支2，功能待定义 | - | - |
| process | `nodes/process_node.py` | agent | 调用大模型整合问候和两个分支结果为最终输出 | - | `config/process_cfg.json` |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 并行分支
- `task1` 和 `task2` 为并行分支，在 `greeting` 之后同时执行
- 两者都完成后直接汇聚到 `process` 节点

## 子图清单
暂无子图

## 技能使用
- 节点 `model_select`、`greeting`、`process` 使用大语言模型技能

## 待定义
- `task1` 和 `task2` 的业务逻辑尚未定义，当前为占位节点