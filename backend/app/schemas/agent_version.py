from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AgentVersionCreate(BaseModel):
    name: str
    description: str | None = None
    endpoint: str | None = None
    method: str = "POST"
    auth_type: str | None = None
    auth_token: str | None = None
    request_template: str | None = None
    response_path: str | None = None
    has_end_signal: bool = False
    end_signal_path: str | None = None
    end_signal_value: str | None = None
    response_format: str = "json"


class AgentVersionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    endpoint: str | None = None
    method: str | None = None
    auth_type: str | None = None
    auth_token: str | None = None
    request_template: str | None = None
    response_path: str | None = None
    has_end_signal: bool | None = None
    end_signal_path: str | None = None
    end_signal_value: str | None = None
    response_format: str | None = None


class AgentVersionResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    endpoint: str | None
    method: str
    auth_type: str | None
    auth_token_set: bool = False
    request_template: str | None
    response_path: str | None
    has_end_signal: bool
    end_signal_path: str | None
    end_signal_value: str | None
    response_format: str
    connection_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
