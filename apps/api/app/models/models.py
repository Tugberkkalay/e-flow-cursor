import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="viewer")  # admin, approver, viewer
    department = Column(String)
    cost_center = Column(String)
    manager_id = Column(String, ForeignKey("users.id"), nullable=True)
    org_id = Column(String, nullable=False, default="org_1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Delegation(Base):
    __tablename__ = "delegations"

    id = Column(String, primary_key=True, default=gen_id)
    from_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    role_scope = Column(String)
    active = Column(Boolean, default=True)
    org_id = Column(String, nullable=False, default="org_1")
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovalLimit(Base):
    __tablename__ = "approval_limits"

    id = Column(String, primary_key=True, default=gen_id)
    department = Column(String)
    budget_type = Column(String)
    currency = Column(String, default="TRY")
    min_amount = Column(Float, nullable=False, default=0)
    max_amount = Column(Float, nullable=False)
    approver_role = Column(String, nullable=False)
    org_id = Column(String, nullable=False, default="org_1")
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessDefinition(Base):
    __tablename__ = "process_definitions"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="draft")  # draft, published
    current_version = Column(Integer, default=1)
    form_id = Column(String, ForeignKey("form_definitions.id"), nullable=True)
    org_id = Column(String, nullable=False, default="org_1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("ProcessVersion", back_populates="definition")


class ProcessVersion(Base):
    __tablename__ = "process_versions"

    id = Column(String, primary_key=True, default=gen_id)
    flow_id = Column(String, ForeignKey("process_definitions.id"), nullable=False)
    version = Column(Integer, nullable=False)
    graph_json = Column(JSON, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    definition = relationship("ProcessDefinition", back_populates="versions")


class ProcessInstance(Base):
    __tablename__ = "process_instances"

    id = Column(String, primary_key=True, default=gen_id)
    flow_id = Column(String, ForeignKey("process_definitions.id"), nullable=False)
    flow_name = Column(String)
    version_id = Column(String, ForeignKey("process_versions.id"), nullable=False)
    status = Column(String, default="running")  # running, completed, failed, cancelled, pending
    variables = Column(JSON, default=dict)
    current_node_id = Column(String)
    current_node_label = Column(String)
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    requester_name = Column(String)
    org_id = Column(String, nullable=False, default="org_1")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    node_instances = relationship("NodeInstance", back_populates="instance")


class NodeInstance(Base):
    __tablename__ = "node_instances"

    id = Column(String, primary_key=True, default=gen_id)
    instance_id = Column(String, ForeignKey("process_instances.id"), nullable=False)
    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    node_label = Column(String)
    status = Column(String, default="pending")  # pending, running, completed, failed, skipped
    input_data = Column(JSON)
    output_data = Column(JSON)
    error = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    retry_count = Column(Integer, default=0)
    org_id = Column(String, nullable=False, default="org_1")

    instance = relationship("ProcessInstance", back_populates="node_instances")


class TaskInstance(Base):
    __tablename__ = "task_instances"

    id = Column(String, primary_key=True, default=gen_id)
    instance_id = Column(String, ForeignKey("process_instances.id"), nullable=False)
    node_instance_id = Column(String, ForeignKey("node_instances.id"), nullable=False)
    task_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=False)
    assignee_name = Column(String)
    status = Column(String, default="pending")  # pending, completed, cancelled
    form_data = Column(JSON)
    due_date = Column(DateTime)
    flow_name = Column(String)
    instance_title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    org_id = Column(String, nullable=False, default="org_1")


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"

    id = Column(String, primary_key=True, default=gen_id)
    instance_id = Column(String, ForeignKey("process_instances.id"), nullable=False)
    node_instance_id = Column(String, ForeignKey("node_instances.id"), nullable=False)
    approver_id = Column(String, ForeignKey("users.id"), nullable=False)
    approver_name = Column(String)
    decision = Column(String)  # approved, rejected, revision
    comment = Column(Text)
    amount = Column(Float)
    decided_at = Column(DateTime)
    flow_name = Column(String)
    instance_title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    org_id = Column(String, nullable=False, default="org_1")


class FormDefinition(Base):
    __tablename__ = "form_definitions"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="draft")
    version = Column(Integer, default=1)
    fields = Column(JSON, default=list)
    org_id = Column(String, nullable=False, default="org_1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_id)
    instance_id = Column(String, ForeignKey("process_instances.id"), nullable=False)
    doc_type = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    version = Column(Integer, default=1)
    extracted_json = Column(JSON)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    storage_key = Column(String)
    org_id = Column(String, nullable=False, default="org_1")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=gen_id)
    instance_id = Column(String, ForeignKey("process_instances.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_name = Column(String)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    org_id = Column(String, nullable=False, default="org_1")
