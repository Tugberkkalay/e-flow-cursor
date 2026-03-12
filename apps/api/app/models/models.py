from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id() -> str:
    return uuid4().hex


class RoleEnum(str, Enum):
    admin = "admin"
    approver = "approver"
    viewer = "viewer"
    procurement = "procurement"
    finance = "finance"
    legal = "legal"


class User(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=RoleEnum.viewer.value)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manager_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Delegation(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    from_user_id: Mapped[str] = mapped_column(String(32), ForeignKey("user.id"))
    to_user_id: Mapped[str] = mapped_column(String(32), ForeignKey("user.id"))
    role_scope: Mapped[str] = mapped_column(String(64), default="approver")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ApprovalLimit(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str] = mapped_column(String(128))
    budget_type: Mapped[str] = mapped_column(String(64), default="capex")
    currency: Mapped[str] = mapped_column(String(8), default="TRY")
    min_amount: Mapped[float] = mapped_column(Float, default=0)
    max_amount: Mapped[float] = mapped_column(Float, default=999999999)
    approver_role: Mapped[str] = mapped_column(String(64))


class ProcessDefinition(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    versions: Mapped[list[ProcessVersion]] = relationship(back_populates="definition")


class ProcessVersion(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_definition_id: Mapped[str] = mapped_column(String(32), ForeignKey("processdefinition.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    graph_json: Mapped[dict] = mapped_column(JSON, default=dict)
    form_contract_json: Mapped[dict] = mapped_column(JSON, default=dict)
    exported_outputs_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    definition: Mapped[ProcessDefinition] = relationship(back_populates="versions")


class FormDefinition(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessInstance(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_version_id: Mapped[str] = mapped_column(String(32), ForeignKey("processversion.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    requester_id: Mapped[str] = mapped_column(String(32), ForeignKey("user.id"))
    status: Mapped[str] = mapped_column(String(32), default="running")
    current_node_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    variables_json: Mapped[dict] = mapped_column(JSON, default=dict)
    exports_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NodeInstance(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_instance_id: Mapped[str] = mapped_column(String(32), ForeignKey("processinstance.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(128))
    node_type: Mapped[str] = mapped_column(String(64))
    node_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class TaskInstance(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_instance_id: Mapped[str] = mapped_column(String(32), ForeignKey("processinstance.id"), index=True)
    node_instance_id: Mapped[str] = mapped_column(String(32), ForeignKey("nodeinstance.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(64), default="human")
    title: Mapped[str] = mapped_column(String(255))
    assignee_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assignee_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    completed_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApprovalInstance(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_instance_id: Mapped[str] = mapped_column(String(32), ForeignKey("processinstance.id"), index=True)
    node_instance_id: Mapped[str] = mapped_column(String(32), ForeignKey("nodeinstance.id"), index=True)
    strategy: Mapped[str] = mapped_column(String(32), default="single")
    assignee_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assignee_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_instance_id: Mapped[str] = mapped_column(String(32), ForeignKey("processinstance.id"), index=True)
    parent_document_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), default="generic")
    file_name: Mapped[str] = mapped_column(String(255))
    storage_uri: Mapped[str] = mapped_column(String(512))
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    extracted_json: Mapped[dict] = mapped_column(JSON, default=dict)
    uploaded_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    process_instance_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    flow_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    form_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_type: Mapped[str] = mapped_column(String(128))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
