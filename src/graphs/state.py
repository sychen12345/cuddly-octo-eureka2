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
    greeting_style: str = Field(default="", description="大模型推荐的问候风格")
    greeting_message: str = Field(default="", description="生成的问候消息")
    task1_result: str = Field(default="", description="并行分支1的处理结果")
    task2_result: str = Field(default="", description="并行分支2的处理结果")
    processed_result: str = Field(default="", description="处理后的最终结果")


# ============= 图的输入输出定义 =============
class GraphInput(BaseModel):
    """工作流的输入参数"""
    user_name: str = Field(..., description="用户输入的名称")


class GraphOutput(BaseModel):
    """工作流的输出结果"""
    processed_result: str = Field(..., description="最终处理结果")


# ============= 节点的输入输出定义 =============
# Agent节点: 模型选取节点
class ModelSelectNodeInput(BaseModel):
    """模型选取节点的输入"""
    user_name: str = Field(..., description="用户名称")


class ModelSelectNodeOutput(BaseModel):
    """模型选取节点的输出"""
    greeting_style: str = Field(..., description="大模型推荐的问候风格")


# Agent节点: 问候生成节点
class GreetingNodeInput(BaseModel):
    """问候生成节点的输入"""
    user_name: str = Field(..., description="用户名称")
    greeting_style: str = Field(..., description="问候风格")


class GreetingNodeOutput(BaseModel):
    """问候生成节点的输出"""
    greeting_message: str = Field(..., description="生成的问候消息")


# 并行分支1 task节点（功能待定义）
class Task1NodeInput(BaseModel):
    """并行分支1的输入"""
    greeting_message: str = Field(..., description="问候消息")


class Task1NodeOutput(BaseModel):
    """并行分支1的输出"""
    task1_result: str = Field(..., description="分支1的处理结果")


# 并行分支2 task节点（功能待定义）
class Task2NodeInput(BaseModel):
    """并行分支2的输入"""
    greeting_message: str = Field(..., description="问候消息")


class Task2NodeOutput(BaseModel):
    """并行分支2的输出"""
    task2_result: str = Field(..., description="分支2的处理结果")


# Agent节点: 结果处理节点
class ProcessNodeInput(BaseModel):
    """结果处理节点的输入"""
    greeting_message: str = Field(..., description="问候消息")
    task1_result: str = Field(..., description="并行分支1的处理结果")
    task2_result: str = Field(..., description="并行分支2的处理结果")


class ProcessNodeOutput(BaseModel):
    """结果处理节点的输出"""
    processed_result: str = Field(..., description="处理后的最终结果")