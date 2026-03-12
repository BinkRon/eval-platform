from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectFileResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
