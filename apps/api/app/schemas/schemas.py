from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "viewer"
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None
    org_id: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class FlowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    graph_json: Optional[dict] = None


class FlowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    graph_json: Optional[dict] = None


class FlowOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    current_version: int
    form_id: Optional[str] = None
    org_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FlowVersionOut(BaseModel):
    id: str
    flow_id: str
    version: int
    graph_json: dict
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Optional[list] = None


class FormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[list] = None


class FormOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    version: int
    fields: list
    org_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstanceStart(BaseModel):
    flow_id: str
    initial_inputs: Optional[dict] = None


class InstanceOut(BaseModel):
    id: str
    flow_id: str
    flow_name: Optional[str] = None
    version_id: str
    status: str
    variables: dict
    current_node_id: Optional[str] = None
    current_node_label: Optional[str] = None
    requester_id: str
    requester_name: Optional[str] = None
    org_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InstanceAction(BaseModel):
    action: str  # approve, reject, complete_task, reassign, retry, skip, cancel, revision
    data: Optional[dict] = None
    comment: Optional[str] = None
    assignee_id: Optional[str] = None


class TaskComplete(BaseModel):
    form_data: Optional[dict] = None
    comment: Optional[str] = None


class ApprovalDecision(BaseModel):
    decision: str  # approved, rejected, revision
    comment: Optional[str] = None


class AuditEventOut(BaseModel):
    id: str
    instance_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    event_type: str
    event_data: dict
    timestamp: datetime
    org_id: str

    class Config:
        from_attributes = True


class InboxItem(BaseModel):
    id: str
    type: str  # task, approval
    title: str
    instance_id: str
    instance_title: Optional[str] = None
    flow_name: Optional[str] = None
    requester: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime


class DelegationCreate(BaseModel):
    from_user_id: str
    to_user_id: str
    start_date: datetime
    end_date: datetime
    role_scope: Optional[str] = None


class DelegationOut(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    start_date: datetime
    end_date: datetime
    role_scope: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True


class ApprovalLimitCreate(BaseModel):
    department: Optional[str] = None
    budget_type: Optional[str] = None
    currency: str = "TRY"
    min_amount: float
    max_amount: float
    approver_role: str


class ApprovalLimitOut(BaseModel):
    id: str
    department: Optional[str] = None
    budget_type: Optional[str] = None
    currency: str
    min_amount: float
    max_amount: float
    approver_role: str
    org_id: str

    class Config:
        from_attributes = True


class ExpressionPreview(BaseModel):
    expression: str
    context: dict


class ExpressionResult(BaseModel):
    result: Any
    error: Optional[str] = None


class ContextSchema(BaseModel):
    namespaces: dict
