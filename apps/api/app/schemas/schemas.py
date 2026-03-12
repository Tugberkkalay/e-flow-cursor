from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    department: str | None = None
    org_id: str

    model_config = ConfigDict(from_attributes=True)


class FlowCreate(BaseModel):
    code: str
    name: str
    description: str | None = None
    graph_json: dict[str, Any] = Field(default_factory=dict)


class FlowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    graph_json: dict[str, Any] | None = None


class FlowResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    latest_version: int | None = None
    latest_status: str | None = None


class ProcessVersionResponse(BaseModel):
    id: str
    version_no: int
    status: str
    graph_json: dict[str, Any]
    created_at: datetime
    published_at: datetime | None = None


class FormCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    name: str
    form_schema: dict[str, Any] = Field(alias="schema_json")


class FormUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    form_schema: dict[str, Any] | None = Field(default=None, alias="schema_json")


class FormResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    code: str
    name: str
    version_no: int
    status: str
    form_schema: dict[str, Any] = Field(alias="schema_json")


class StartInstanceRequest(BaseModel):
    flow_version_id: str
    title: str
    initial_inputs: dict[str, Any] = Field(default_factory=dict)


class InstanceActionRequest(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class InstanceResponse(BaseModel):
    id: str
    title: str
    status: str
    current_node_id: str | None = None
    requester_id: str
    started_at: datetime
    finished_at: datetime | None = None
    variables_json: dict[str, Any]
    exports_json: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class TimelineEvent(BaseModel):
    id: str
    event_type: str
    payload_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskCompleteRequest(BaseModel):
    output: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecisionRequest(BaseModel):
    decision: str
    comment: str | None = None


class ExpressionPreviewRequest(BaseModel):
    expr: str
    sample_context: dict[str, Any] = Field(default_factory=dict)


class ExpressionPreviewResponse(BaseModel):
    result: Any


class UserCreate(BaseModel):
    email: str
    full_name: str
    role: str
    password: str
    department: str | None = None
    cost_center: str | None = None
    manager_id: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    department: str | None = None
    cost_center: str | None = None
    manager_id: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    department: str | None = None
    cost_center: str | None = None
    manager_id: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DelegationCreate(BaseModel):
    from_user_id: str
    to_user_id: str
    role_scope: str = "approver"
    start_date: date
    end_date: date
    is_active: bool = True


class ApprovalLimitCreate(BaseModel):
    department: str
    budget_type: str = "capex"
    currency: str = "TRY"
    min_amount: float
    max_amount: float
    approver_role: str
