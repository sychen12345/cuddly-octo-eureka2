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
    grok_result: str = Field(default="", description="Grok API 返回结果")
    openai_result: str = Field(default="", description="OpenAI API 返回结果")
    merged_analysis: str = Field(default="", description="合并后的分析结果")
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


# 示例节点1: 问候生成节点
class GreetingNodeInput(BaseModel):
    """问候生成节点的输入"""
    user_name: str = Field(..., description="用户名称")
    greeting_style: str = Field(..., description="问候风格")


class GreetingNodeOutput(BaseModel):
    """问候生成节点的输出"""
    greeting_message: str = Field(..., description="生成的问候消息")


# 并行节点: Grok API 调用
class GrokNodeInput(BaseModel):
    """Grok 节点的输入"""
    greeting_message: str = Field(..., description="问候消息，作为 Grok 分析的输入")


class GrokNodeOutput(BaseModel):
    """Grok 节点的输出"""
    grok_result: str = Field(..., description="Grok API 返回的分析结果")


# 并行节点: OpenAI API 调用
class OpenAINodeInput(BaseModel):
    """OpenAI 节点的输入"""
    greeting_message: str = Field(..., description="问候消息，作为 OpenAI 分析的输入")


class OpenAINodeOutput(BaseModel):
    """OpenAI 节点的输出"""
    openai_result: str = Field(..., description="OpenAI API 返回的分析结果")


# 汇聚节点: 合并分析结果
class MergeNodeInput(BaseModel):
    """合并节点的输入"""
    grok_result: str = Field(..., description="Grok 分析结果")
    openai_result: str = Field(..., description="OpenAI 分析结果")


class MergeNodeOutput(BaseModel):
    """合并节点的输出"""
    merged_analysis: str = Field(..., description="合并后的分析结果")


# 结果处理节点
class ProcessNodeInput(BaseModel):
    """结果处理节点的输入"""
    greeting_message: str = Field(..., description="问候消息")
    merged_analysis: str = Field(..., description="合并后的分析结果")


class ProcessNodeOutput(BaseModel):
    """结果处理节点的输出"""
    processed_result: str = Field(..., description="处理后的最终结果")