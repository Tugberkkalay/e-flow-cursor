from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=3)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class FlowCreateRequest(BaseModel):
    name: str
    key: str
    description: str | None = None
    graph_json: dict[str, Any] | None = None
    template_key: str | None = None


class FlowUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    graph_json: dict[str, Any] | None = None


class FormCreateRequest(BaseModel):
    name: str
    key: str
    schema_json: dict[str, Any]


class FormUpdateRequest(BaseModel):
    name: str | None = None
    schema_json: dict[str, Any] | None = None


class InstanceStartRequest(BaseModel):
    flow_version_id: str
    initial_inputs: dict[str, Any] = Field(default_factory=dict)


class InstanceActionRequest(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    target_user_id: str | None = None
    comment: str | None = None


class TaskCompleteRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    outcome: str | None = None
    comment: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: str
    comment: str | None = None


class ExpressionPreviewRequest(BaseModel):
    expr: str
    context_sample: dict[str, Any] = Field(default_factory=dict)


class UserCreateRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: str
    department: str | None = None
    cost_center: str | None = None
    manager_id: str | None = None


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    department: str | None = None
    cost_center: str | None = None
    manager_id: str | None = None
    is_active: bool | None = None


class DelegationRequest(BaseModel):
    delegator_id: str
    delegate_id: str
    role_scope: list[str] = Field(default_factory=list)
    start_date: date
    end_date: date
    is_active: bool = True


class ApprovalLimitRequest(BaseModel):
    department: str
    budget_type: str = "default"
    currency: str = "TRY"
    min_amount: float
    max_amount: float
    approver_role: str
    approver_user_id: str | None = None


class ProcessInstanceResponse(ORMModel):
    id: str
    title: str
    status: str
    current_node_id: str | None
    variables_json: dict[str, Any]
    exports_json: dict[str, Any]
    started_at: datetime
    updated_at: datetime


class AuditEventResponse(ORMModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    payload_json: dict[str, Any]
    created_at: datetime
