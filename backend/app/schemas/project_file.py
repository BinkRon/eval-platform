"""项目文件相关的响应模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectFileResponse(BaseModel):
    """项目文件详情。"""

    id: UUID = Field(description="文件 ID")
    project_id: UUID = Field(description="所属项目 ID")
    filename: str = Field(description="文件名")
    file_type: str = Field(description="文件类型（MIME type）")
    file_size: int = Field(description="文件大小（字节）")
    created_at: datetime = Field(description="上传时间")
    updated_at: datetime = Field(description="最后更新时间")

    model_config = {"from_attributes": True}
