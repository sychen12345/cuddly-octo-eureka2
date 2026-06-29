"""
工作流状态定义
定义全局状态、图的输入输出、以及各节点的输入输出
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============= 全局状态定义 =============
class GlobalState(BaseModel):
    """全局状态：工作流执行过程中的共享数据"""
    user_name: str = Field(default="", description="用户名称")
    greeting_message: str = Field(default="", description="生成的问候消息")
    processed_result: str = Field(default="", description="处理后的最终结果")


# ============= 图的输入输出定义 =============
class GraphInput(BaseModel):
    """工作流的输入参数"""
    user_name: str = Field(..., description="用户输入的名称")


class GraphOutput(BaseModel):
    """工作流的输出结果"""
    processed_result: str = Field(..., description="最终处理结果")


# ============= 节点的输入输出定义 =============
# 示例节点1: 问候生成节点
class GreetingNodeInput(BaseModel):
    """问候生成节点的输入"""
    user_name: str = Field(..., description="用户名称")


class GreetingNodeOutput(BaseModel):
    """问候生成节点的输出"""
    greeting_message: str = Field(..., description="生成的问候消息")


# 示例节点2: 结果处理节点
class ProcessNodeInput(BaseModel):
    """结果处理节点的输入"""
    greeting_message: str = Field(..., description="问候消息")


class ProcessNodeOutput(BaseModel):
    """结果处理节点的输出"""
    processed_result: str = Field(..., description="处理后的结果")