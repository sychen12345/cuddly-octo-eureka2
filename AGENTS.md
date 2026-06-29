## 项目概述
- **名称**: 工作流模板
- **功能**: 提供一个基础的工作流模板，展示如何定义状态、创建节点、编排工作流

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| greeting | `nodes/greeting_node.py` | task | 根据用户名称生成问候消息 | - | - |
| process | `nodes/process_node.py` | task | 处理问候消息生成最终结果 | - | - |

**类型说明**: task(任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
暂无子图

## 技能使用
暂无技能使用

## 快速开始
1. 查看状态定义：`src/graphs/state.py`
2. 查看节点实现：`src/graphs/nodes/`
3. 查看工作流编排：`src/graphs/graph.py`
4. 运行测试：修改 GraphInput 参数后执行 test_run

## 扩展指南
### 添加新节点
1. 在 `src/graphs/state.py` 中定义节点的 Input/Output
2. 在 `src/graphs/nodes/` 中创建节点文件
3. 在 `src/graphs/graph.py` 中注册节点并添加边

### 添加 Agent 节点
1. 在 `config/` 中创建 LLM 配置文件（参考工程规范）
2. 在节点函数中读取配置并调用大模型
3. 注册节点时添加 `metadata={"type": "agent", "llm_cfg": "config/xxx.json"}`