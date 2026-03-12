from typing import Any, Literal

from pydantic import BaseModel, Field


class BuilderChatRequest(BaseModel):
    """用户发送给构建助手的聊天请求。"""

    message: str = Field(
        min_length=1,
        description="用户发送给构建助手的消息",
        examples=["请生成 5 条关于理财推荐场景的测试用例"],
    )
    provider: str = Field(
        min_length=1,
        description="LLM 供应商名称，如 openai、dashscope",
    )
    model: str = Field(
        min_length=1,
        description="模型名称，如 gpt-4o、qwen-max",
    )


class BuilderChatResponse(BaseModel):
    """构建助手的聊天响应。包含文本回复和可选的确认卡片数据。"""

    response: str = Field(
        description="助手的文本回复（已移除配置块标签）",
    )
    card_type: str | None = Field(
        default=None,
        description="确认卡片类型。generate_confirm: 生成确认卡片；null: 普通文本回复",
    )
    card_data: dict[str, Any] | None = Field(
        default=None,
        description=(
            "卡片渲染数据。包含 config_type、title、items、impact_message、"
            "existing_count、config_payload 等字段"
        ),
    )


class ApplyConfigRequest(BaseModel):
    """确认写入配置的请求。用户在确认卡片上点击'确认写入'后触发。"""

    config_type: Literal["test_cases", "judge_config"] = Field(
        description="配置类型。test_cases: 对练用例；judge_config: 裁判配置",
    )
    config_payload: dict[str, Any] = Field(
        description="要写入的配置数据，来自 card_data.config_payload",
    )
    mode: Literal["append", "replace"] = Field(
        default="append",
        description="写入模式。append: 追加到现有配置；replace: 替换全部现有配置",
    )


class ApplyConfigResponse(BaseModel):
    """配置写入结果。"""

    success: bool = Field(description="是否写入成功")
    summary: dict[str, Any] = Field(
        description="写入摘要，包含 created/checklist_count/dimension_count 和 mode",
    )
