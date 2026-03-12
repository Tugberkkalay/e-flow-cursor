import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class ProcessInstance(Base):
    __tablename__ = "process_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(64), default="default", index=True)
    definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("process_definitions.id"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("process_versions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    # running, completed, rejected, cancelled, failed, waiting
    current_node_id: Mapped[str | None] = mapped_column(String(100))
    variables: Mapped[dict] = mapped_column(JSONB, default=dict)
    exports: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    node_instances: Mapped[list["NodeInstance"]] = relationship("NodeInstance", back_populates="process_instance")
    task_instances: Mapped[list["TaskInstance"]] = relationship("TaskInstance", back_populates="process_instance")
    approval_instances: Mapped[list["ApprovalInstance"]] = relationship("ApprovalInstance", back_populates="process_instance")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="process_instance")
    audit_events: Mapped[list["AuditEvent"]] = relationship("AuditEvent", back_populates="process_instance")


class NodeInstance(Base):
    __tablename__ = "node_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(64), default="default")
    process_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("process_instances.id"), nullable=False)
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[str] = mapped_column(String(100), nullable=False)
    node_label: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending, running, completed, failed, skipped
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    process_instance: Mapped["ProcessInstance"] = relationship("ProcessInstance", back_populates="node_instances")


class TaskInstance(Base):
    __tablename__ = "task_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(64), default="default")
    process_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("process_instances.id"), nullable=False)
    node_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("node_instances.id"), nullable=True)
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending, completed, skipped, cancelled
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_role: Mapped[str | None] = mapped_column(String(100))
    form_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    comment: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    process_instance: Mapped["ProcessInstance"] = relationship("ProcessInstance", back_populates="task_instances")


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(64), default="default")
    process_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("process_instances.id"), nullable=False)
    node_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("node_instances.id"), nullable=True)
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    approver_role: Mapped[str | None] = mapped_column(String(100))
    decision: Mapped[str | None] = mapped_column(String(30))
    # approved, rejected, revision_requested, info_requested
    comment: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    process_instance: Mapped["ProcessInstance"] = relationship("ProcessInstance", back_populates="approval_instances")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(64), default="default")
    process_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("process_instances.id"), nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(100))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    extracted_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    extraction_status: Mapped[str] = mapped_column(String(30), default="pending")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    process_instance: Mapped["ProcessInstance"] = relationship("ProcessInstance", back_populates="documents")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(64), default="default", index=True)
    process_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("process_instances.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    actor_email: Mapped[str | None] = mapped_column(String(255))
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    process_instance: Mapped["ProcessInstance | None"] = relationship("ProcessInstance", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_events_instance_created", "process_instance_id", "created_at"),
    )
