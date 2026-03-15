"""Agent 版本相关的请求/响应模型。"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AgentVersionCreate(BaseModel):
    """创建 Agent 版本。"""

    name: str = Field(max_length=100, description="版本名称", examples=["v1.0-主流程"])
    description: str | None = Field(default=None, description="版本说明")
    endpoint: str | None = Field(default=None, description="Agent 对话 API 地址", examples=["https://api.example.com/chat"])
    method: Literal["POST", "GET"] = Field(default="POST", description="HTTP 请求方法")
    auth_type: Literal["bearer", "header"] | None = Field(default=None, description="认证方式。bearer: Authorization Bearer；header: 自定义 Header")
    auth_token: str | None = Field(default=None, max_length=500, description="认证凭证（保存后不回显）")
    request_template: str | None = Field(default=None, description="请求体 Jinja2 模板，可用变量：{{ message }}、{{ history }}")
    response_path: str | None = Field(default=None, description="从 JSON 响应中提取回复文本的 JMESPath", examples=["data.reply"])
    has_end_signal: bool = Field(default=False, description="Agent 是否会发送结束信号")
    end_signal_path: str | None = Field(default=None, description="结束信号在响应中的 JMESPath")
    end_signal_value: str | None = Field(default=None, description="结束信号的匹配值")
    response_format: Literal["json", "sse"] = Field(default="json", description="响应格式。json: 标准 JSON；sse: Server-Sent Events 流式")


class AgentVersionUpdate(BaseModel):
    """更新 Agent 版本（部分更新）。"""

    name: str | None = Field(default=None, max_length=100, description="版本名称")
    description: str | None = Field(default=None, description="版本说明")
    endpoint: str | None = Field(default=None, description="Agent 对话 API 地址")
    method: Literal["POST", "GET"] | None = Field(default=None, description="HTTP 请求方法")
    auth_type: Literal["bearer", "header"] | None = Field(default=None, description="认证方式")
    auth_token: str | None = Field(default=None, max_length=500, description="认证凭证（空值表示不更新）")
    request_template: str | None = Field(default=None, description="请求体 Jinja2 模板")
    response_path: str | None = Field(default=None, description="回复文本的 JMESPath")
    has_end_signal: bool | None = Field(default=None, description="是否启用结束信号")
    end_signal_path: str | None = Field(default=None, description="结束信号的 JMESPath")
    end_signal_value: str | None = Field(default=None, description="结束信号匹配值")
    response_format: Literal["json", "sse"] | None = Field(default=None, description="响应格式")


class AgentTestResult(BaseModel):
    """Agent 连通性测试结果。"""

    status: str = Field(description="测试状态：success 或 failed")
    reply: str | None = Field(default=None, description="Agent 回复内容（成功时）")
    error: str | None = Field(default=None, description="错误信息（失败时）")


class AgentVersionResponse(BaseModel):
    """Agent 版本详情。"""

    id: UUID = Field(description="版本 ID")
    project_id: UUID = Field(description="所属项目 ID")
    name: str = Field(description="版本名称")
    description: str | None = Field(description="版本说明")
    endpoint: str | None = Field(description="Agent 对话 API 地址")
    method: str = Field(description="HTTP 请求方法")
    auth_type: str | None = Field(description="认证方式")
    auth_token_set: bool = Field(default=False, description="是否已设置认证凭证（不返回实际值）")
    request_template: str | None = Field(description="请求体模板")
    response_path: str | None = Field(description="回复文本 JMESPath")
    has_end_signal: bool = Field(description="是否启用结束信号")
    end_signal_path: str | None = Field(description="结束信号 JMESPath")
    end_signal_value: str | None = Field(description="结束信号匹配值")
    response_format: str = Field(description="响应格式")
    connection_status: str = Field(description="连通性状态：unknown / success / failed")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最后更新时间")

    model_config = {"from_attributes": True}
