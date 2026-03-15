"""批量测试相关的请求/响应模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BatchTestCreate(BaseModel):
    """发起批量测试。"""

    agent_version_id: UUID = Field(description="待测 Agent 版本 ID")
    concurrency: int = Field(default=3, ge=1, le=20, description="并发数，1-20")
    test_case_ids: list[UUID] | None = Field(default=None, description="选取的测试用例 ID 列表（空=全部）")
    checklist_item_ids: list[UUID] | None = Field(default=None, description="选取的 Checklist 项 ID 列表（空=全部）")
    eval_dimension_ids: list[UUID] | None = Field(default=None, description="选取的评判维度 ID 列表（空=全部）")
    pass_threshold: float | None = Field(default=None, ge=1.0, le=3.0, description="及格阈值（覆盖裁判配置），1.0-3.0")


class BatchTestResponse(BaseModel):
    """批量测试概览。"""

    id: UUID = Field(description="批测 ID")
    project_id: UUID = Field(description="所属项目 ID")
    agent_version_id: UUID | None = Field(description="测试的 Agent 版本 ID")
    agent_version_name: str | None = Field(default=None, description="Agent 版本名称")
    status: str = Field(description="批测状态：pending / running / completed / failed")
    concurrency: int = Field(description="并发数")
    total_cases: int = Field(description="总用例数")
    passed_cases: int = Field(description="通过用例数")
    completed_cases: int = Field(description="已完成用例数")
    created_at: datetime = Field(description="发起时间")
    completed_at: datetime | None = Field(description="完成时间")
    config_snapshot: dict | None = Field(default=None, description="发起时的配置快照")

    model_config = {"from_attributes": True}


class BatchTestProgress(BaseModel):
    """批量测试实时进度。"""

    status: str = Field(description="批测状态")
    total_cases: int = Field(description="总用例数")
    completed_cases: int = Field(description="已完成用例数")
    passed_cases: int = Field(description="通过用例数")


class TestResultResponse(BaseModel):
    """单条用例的测试结果。"""

    id: UUID = Field(description="结果 ID")
    batch_test_id: UUID = Field(description="所属批测 ID")
    test_case_id: UUID | None = Field(description="测试用例 ID")
    test_case_name: str | None = Field(default=None, description="测试用例名称")
    status: str = Field(description="状态：pending / running / completed / error")
    conversation: list[dict] | None = Field(description="对话记录（role + content）")
    termination_reason: str | None = Field(description="对话终止原因")
    actual_rounds: int | None = Field(description="实际对话轮次")
    checklist_results: list[dict] | None = Field(description="Checklist 检查结果")
    eval_scores: list[dict] | None = Field(description="维度评分结果")
    judge_summary: str | None = Field(description="裁判总结")
    passed: bool | None = Field(description="是否通过")
    error_message: str | None = Field(description="错误信息")
    sparring_prompt_snapshot: str | None = Field(default=None, description="对练机器人 Prompt 快照")
    judge_prompt_snapshot: str | None = Field(default=None, description="裁判机器人 Prompt 快照")

    model_config = {"from_attributes": True}


class BatchTestDetail(BatchTestResponse):
    """批量测试详情（含所有用例结果）。"""

    test_results: list[TestResultResponse] = Field(description="各用例测试结果")
