"""项目相关的请求/响应模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """创建评测项目。"""

    name: str = Field(max_length=100, description="项目名称", examples=["客服 Agent 评测"])
    description: str | None = Field(default=None, description="项目描述")


class ProjectUpdate(BaseModel):
    """更新项目信息（部分更新）。"""

    name: str | None = Field(default=None, max_length=100, description="项目名称")
    description: str | None = Field(default=None, description="项目描述")


class LatestBatchSummary(BaseModel):
    """项目最近一次批测摘要（用于项目列表卡片展示）。"""

    created_at: datetime = Field(description="批测发起时间")
    agent_version_name: str = Field(description="测试的 Agent 版本名称")
    pass_rate: float = Field(description="通过率（0-1）")
    pass_rate_change: float | None = Field(default=None, description="通过率变化（与上次比）")


class ConfigReadinessItem(BaseModel):
    """单项配置就绪状态。"""

    ready: bool = Field(description="是否就绪")
    message: str = Field(description="状态描述")


class ConfigReadiness(BaseModel):
    """项目配置就绪检查结果。"""

    agent_version: ConfigReadinessItem = Field(description="Agent 版本就绪状态")
    test_case: ConfigReadinessItem = Field(description="测试用例就绪状态")
    judge_config: ConfigReadinessItem = Field(description="裁判配置就绪状态")
    model_config_status: ConfigReadinessItem = Field(description="模型配置就绪状态")
    all_ready: bool = Field(description="是否全部就绪，可发起批测")


class ProjectResponse(BaseModel):
    """项目详情。"""

    id: UUID = Field(description="项目 ID")
    name: str = Field(description="项目名称")
    description: str | None = Field(description="项目描述")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最后更新时间")
    agent_version_count: int = Field(default=0, description="Agent 版本数量")
    test_case_count: int = Field(default=0, description="测试用例数量")
    batch_test_count: int = Field(default=0, description="批测次数")
    latest_batch: LatestBatchSummary | None = Field(default=None, description="最近一次批测摘要")

    model_config = {"from_attributes": True}
