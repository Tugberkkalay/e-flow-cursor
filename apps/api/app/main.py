from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.engine import append_audit, complete_task, decide_approval, execute_ready_path, instance_context_schema, start_instance, upload_document
from app.expression import resolve_template
from app.models import (
    ApprovalInstance,
    ApprovalLimit,
    AuditEvent,
    Delegation,
    Document,
    FormDefinition,
    NodeInstance,
    ProcessDefinition,
    ProcessInstance,
    ProcessVersion,
    TaskInstance,
    User,
    utcnow,
)
from app.schemas import (
    ApprovalDecisionRequest,
    ApprovalLimitRequest,
    DelegationRequest,
    ExpressionPreviewRequest,
    FlowCreateRequest,
    FlowUpdateRequest,
    FormCreateRequest,
    FormUpdateRequest,
    InstanceActionRequest,
    InstanceStartRequest,
    LoginRequest,
    TaskCompleteRequest,
    TokenResponse,
    UserCreateRequest,
    UserUpdateRequest,
)
from app.seeder import seed_demo_data
from app.security import create_access_token, get_current_user, hash_password, require_roles, verify_password
from app.templates import default_context_sample, template_by_key

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department,
        "cost_center": user.cost_center,
        "manager_id": user.manager_id,
        "is_active": user.is_active,
    }


def serialize_flow(definition: ProcessDefinition, version: ProcessVersion | None = None) -> dict[str, Any]:
    return {
        "id": definition.id,
        "key": definition.key,
        "name": definition.name,
        "description": definition.description,
        "status": definition.status,
        "latest_version": definition.latest_version,
        "is_template": definition.is_template,
        "template_key": definition.template_key,
        "graph_json": version.graph_json if version else None,
        "version_id": version.id if version else None,
        "version_status": version.status if version else None,
        "legacy_adapter": version.legacy_adapter if version else None,
    }


def serialize_form(form: FormDefinition) -> dict[str, Any]:
    return {
        "id": form.id,
        "key": form.key,
        "name": form.name,
        "status": form.status,
        "version": form.version,
        "schema_json": form.schema_json,
    }


def serialize_instance(instance: ProcessInstance, db: Session) -> dict[str, Any]:
    started_by = db.get(User, instance.started_by_id)
    return {
        "id": instance.id,
        "title": instance.title,
        "status": instance.status,
        "current_node_id": instance.current_node_id,
        "variables_json": instance.variables_json,
        "exports_json": instance.exports_json,
        "started_at": instance.started_at,
        "updated_at": instance.updated_at,
        "completed_at": instance.completed_at,
        "requester": serialize_user(started_by) if started_by else None,
        "active_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "assignee_user_id": task.assignee_user_id,
                "assignee_role": task.assignee_role,
                "node_id": task.node_id,
                "created_at": task.created_at,
            }
            for task in db.scalars(
                select(TaskInstance)
                .where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending")
                .order_by(TaskInstance.created_at)
            ).all()
        ],
        "active_approvals": [
            {
                "id": approval.id,
                "status": approval.status,
                "approver_user_id": approval.approver_user_id,
                "approver_role": approval.approver_role,
                "node_id": approval.node_id,
                "created_at": approval.created_at,
            }
            for approval in db.scalars(
                select(ApprovalInstance)
                .where(ApprovalInstance.process_instance_id == instance.id, ApprovalInstance.status == "pending")
                .order_by(ApprovalInstance.created_at)
            ).all()
        ],
    }


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(bind=engine) as db:
        seed_demo_data(db)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user), user=serialize_user(user))


@app.get("/me")
def get_me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return serialize_user(user)


@app.get("/flows")
def get_flows(
    include_graph: bool = Query(default=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    definitions = db.scalars(select(ProcessDefinition).where(ProcessDefinition.org_id == user.org_id).order_by(ProcessDefinition.created_at)).all()
    payload = []
    for definition in definitions:
        version = db.scalar(
            select(ProcessVersion)
            .where(ProcessVersion.definition_id == definition.id, ProcessVersion.version == definition.latest_version)
        )
        payload.append(serialize_flow(definition, version if include_graph else None))
    return payload


@app.post("/flows")
def create_flow(
    payload: FlowCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    graph = payload.graph_json or {"nodes": [], "edges": []}
    if payload.template_key:
        template = template_by_key(payload.template_key)
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        graph = template["graph_json"]
    definition = ProcessDefinition(
        org_id=user.org_id,
        key=payload.key,
        name=payload.name,
        description=payload.description,
        status="draft",
        latest_version=1,
        is_template=False,
    )
    db.add(definition)
    db.flush()
    version = ProcessVersion(
        org_id=user.org_id,
        definition_id=definition.id,
        version=1,
        status="draft",
        graph_json=graph,
        exported_outputs={},
        legacy_adapter={"strategy": "compatibility_stub", "enabled": True},
    )
    db.add(version)
    append_audit(db, org_id=user.org_id, entity_type="flow", entity_id=definition.id, event_type="flow.created", actor_user_id=user.id, payload={"name": payload.name})
    db.commit()
    return serialize_flow(definition, version)


def _ensure_draft_flow_version(db: Session, definition: ProcessDefinition, user: User) -> ProcessVersion:
    latest = db.scalar(
        select(ProcessVersion)
        .where(ProcessVersion.definition_id == definition.id)
        .order_by(ProcessVersion.version.desc())
    )
    if latest and latest.status == "draft":
        return latest
    next_version = (latest.version + 1) if latest else 1
    draft = ProcessVersion(
        org_id=user.org_id,
        definition_id=definition.id,
        version=next_version,
        status="draft",
        graph_json=latest.graph_json if latest else {"nodes": [], "edges": []},
        exported_outputs=latest.exported_outputs if latest else {},
        legacy_adapter={"strategy": "compatibility_stub", "enabled": True},
    )
    db.add(draft)
    db.flush()
    return draft


@app.put("/flows/{flow_id}")
def update_flow(
    flow_id: str,
    payload: FlowUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    definition = db.get(ProcessDefinition, flow_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Flow not found")
    version = _ensure_draft_flow_version(db, definition, user)
    if payload.name is not None:
        definition.name = payload.name
    if payload.description is not None:
        definition.description = payload.description
    if payload.graph_json is not None:
        version.graph_json = payload.graph_json
    definition.updated_at = utcnow()
    db.commit()
    return serialize_flow(definition, version)


@app.post("/flows/{flow_id}/publish")
def publish_flow(
    flow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    definition = db.get(ProcessDefinition, flow_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Flow not found")
    version = _ensure_draft_flow_version(db, definition, user)
    version.status = "published"
    definition.status = "published"
    definition.latest_version = version.version
    definition.updated_at = utcnow()
    append_audit(db, org_id=user.org_id, entity_type="flow", entity_id=definition.id, event_type="flow.published", actor_user_id=user.id, payload={"version": version.version})
    db.commit()
    return serialize_flow(definition, version)


@app.get("/flows/{flow_id}/versions")
def get_flow_versions(
    flow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    definition = db.get(ProcessDefinition, flow_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Flow not found")
    versions = db.scalars(select(ProcessVersion).where(ProcessVersion.definition_id == flow_id).order_by(ProcessVersion.version.desc())).all()
    return [serialize_flow(definition, version) for version in versions]


@app.get("/forms")
def get_forms(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    forms = db.scalars(select(FormDefinition).where(FormDefinition.org_id == user.org_id).order_by(FormDefinition.key, FormDefinition.version.desc())).all()
    return [serialize_form(form) for form in forms]


@app.post("/forms")
def create_form(
    payload: FormCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    form = FormDefinition(org_id=user.org_id, key=payload.key, name=payload.name, schema_json=payload.schema_json, status="draft", version=1)
    db.add(form)
    append_audit(db, org_id=user.org_id, entity_type="form", entity_id=form.id, event_type="form.created", actor_user_id=user.id, payload={"name": form.name})
    db.commit()
    db.refresh(form)
    return serialize_form(form)


@app.put("/forms/{form_id}")
def update_form(
    form_id: str,
    payload: FormUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    form = db.get(FormDefinition, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.status != "draft":
        form = FormDefinition(
            org_id=form.org_id,
            key=form.key,
            name=form.name,
            version=form.version + 1,
            status="draft",
            schema_json=form.schema_json,
        )
        db.add(form)
        db.flush()
    if payload.name is not None:
        form.name = payload.name
    if payload.schema_json is not None:
        form.schema_json = payload.schema_json
    form.updated_at = utcnow()
    db.commit()
    return serialize_form(form)


@app.post("/forms/{form_id}/publish")
def publish_form(form_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))) -> dict[str, Any]:
    form = db.get(FormDefinition, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    form.status = "published"
    form.updated_at = utcnow()
    append_audit(db, org_id=user.org_id, entity_type="form", entity_id=form.id, event_type="form.published", actor_user_id=user.id, payload={"version": form.version})
    db.commit()
    return serialize_form(form)


@app.post("/instances/start")
def create_instance(
    payload: InstanceStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    version = db.get(ProcessVersion, payload.flow_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Flow version not found")
    definition = db.get(ProcessDefinition, version.definition_id)
    instance = start_instance(db, version=version, definition_name=definition.name if definition else "Flow", actor=user, initial_inputs=payload.initial_inputs)
    return serialize_instance(instance, db)


@app.get("/instances")
def get_instances(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    stmt = select(ProcessInstance).where(ProcessInstance.org_id == user.org_id).order_by(ProcessInstance.started_at.desc())
    if status_filter:
        stmt = stmt.where(ProcessInstance.status == status_filter)
    instances = db.scalars(stmt).all()
    return [serialize_instance(instance, db) for instance in instances]


@app.get("/instances/{instance_id}")
def get_instance(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    documents = db.scalars(select(Document).where(Document.process_instance_id == instance.id).order_by(Document.created_at.desc())).all()
    timeline = db.scalars(select(AuditEvent).where(AuditEvent.process_instance_id == instance.id).order_by(AuditEvent.created_at.desc())).all()
    tasks = db.scalars(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id).order_by(TaskInstance.created_at.desc())).all()
    approvals = db.scalars(select(ApprovalInstance).where(ApprovalInstance.process_instance_id == instance.id).order_by(ApprovalInstance.created_at.desc())).all()
    payload = serialize_instance(instance, db)
    payload.update(
        {
            "timeline": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "payload_json": event.payload_json,
                    "created_at": event.created_at,
                }
                for event in timeline
            ],
            "documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "version": doc.version,
                    "file_name": doc.file_name,
                    "extracted_json": doc.extracted_json,
                    "metadata_json": doc.metadata_json,
                    "created_at": doc.created_at,
                }
                for doc in documents
            ],
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "outcome": task.outcome,
                    "assignee_user_id": task.assignee_user_id,
                    "comments": task.comments,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                }
                for task in tasks
            ],
            "approvals": [
                {
                    "id": approval.id,
                    "status": approval.status,
                    "decision": approval.decision,
                    "approver_user_id": approval.approver_user_id,
                    "comments": approval.comments,
                    "created_at": approval.created_at,
                    "decided_at": approval.decided_at,
                }
                for approval in approvals
            ],
        }
    )
    return payload


@app.post("/instances/{instance_id}/actions")
def instance_action(
    instance_id: str,
    payload: InstanceActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")

    if payload.action == "cancel":
        instance.status = "cancelled"
        instance.current_node_id = None
        instance.completed_at = utcnow()
        append_audit(db, org_id=user.org_id, entity_type="instance", entity_id=instance.id, event_type="instance.cancelled", actor_user_id=user.id, process_instance_id=instance.id, payload={"comment": payload.comment})
        db.commit()
        return serialize_instance(instance, db)

    if payload.action == "reassign":
        task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending").order_by(TaskInstance.created_at.desc()))
        if task is None:
            raise HTTPException(status_code=404, detail="No pending task to reassign")
        task.assignee_user_id = payload.target_user_id
        append_audit(db, org_id=user.org_id, entity_type="task", entity_id=task.id, event_type="task.reassigned", actor_user_id=user.id, process_instance_id=instance.id, payload={"target_user_id": payload.target_user_id})
        db.commit()
        return serialize_instance(instance, db)

    if payload.action == "retry":
        node_instance = db.scalar(
            select(NodeInstance)
            .where(NodeInstance.process_instance_id == instance.id, NodeInstance.status == "error")
            .order_by(NodeInstance.started_at.desc())
        )
        if node_instance is None:
            raise HTTPException(status_code=404, detail="No failed node to retry")
        instance.status = "running"
        instance.current_node_id = node_instance.node_id
        execute_ready_path(db, instance, user)
        db.commit()
        return serialize_instance(instance, db)

    if payload.action == "skip":
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only action")
        task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending").order_by(TaskInstance.created_at.desc()))
        if task:
            return serialize_instance(complete_task(db, task=task, actor=user, payload=payload.payload, outcome="skipped", comment=payload.comment), db)
        approval = db.scalar(select(ApprovalInstance).where(ApprovalInstance.process_instance_id == instance.id, ApprovalInstance.status == "pending").order_by(ApprovalInstance.created_at.desc()))
        if approval:
            return serialize_instance(decide_approval(db, approval=approval, actor=user, decision="skipped", comment=payload.comment), db)
        raise HTTPException(status_code=404, detail="No pending step to skip")

    if payload.action == "approve":
        approval = db.scalar(select(ApprovalInstance).where(ApprovalInstance.process_instance_id == instance.id, ApprovalInstance.status == "pending").order_by(ApprovalInstance.created_at.desc()))
        if approval is None:
            raise HTTPException(status_code=404, detail="No pending approval found")
        return serialize_instance(decide_approval(db, approval=approval, actor=user, decision="approved", comment=payload.comment), db)

    if payload.action == "reject":
        approval = db.scalar(select(ApprovalInstance).where(ApprovalInstance.process_instance_id == instance.id, ApprovalInstance.status == "pending").order_by(ApprovalInstance.created_at.desc()))
        if approval is not None:
            return serialize_instance(decide_approval(db, approval=approval, actor=user, decision="rejected", comment=payload.comment), db)
        task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending").order_by(TaskInstance.created_at.desc()))
        if task is not None:
            return serialize_instance(complete_task(db, task=task, actor=user, payload=payload.payload, outcome="rejected", comment=payload.comment), db)
        raise HTTPException(status_code=404, detail="No pending step found")

    if payload.action == "complete_task":
        task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending").order_by(TaskInstance.created_at.desc()))
        if task is None:
            raise HTTPException(status_code=404, detail="No pending task found")
        return serialize_instance(complete_task(db, task=task, actor=user, payload=payload.payload, outcome=payload.payload.get("outcome"), comment=payload.comment), db)

    raise HTTPException(status_code=400, detail="Unsupported action")


@app.get("/instances/{instance_id}/timeline")
def get_instance_timeline(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    timeline = db.scalars(select(AuditEvent).where(AuditEvent.process_instance_id == instance_id).order_by(AuditEvent.created_at.desc())).all()
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "payload_json": event.payload_json,
            "created_at": event.created_at,
        }
        for event in timeline
    ]


@app.get("/inbox")
def inbox(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    pending_tasks = db.scalars(
        select(TaskInstance).where(
            TaskInstance.status == "pending",
            or_(TaskInstance.assignee_user_id == user.id, and_(TaskInstance.assignee_user_id.is_(None), TaskInstance.assignee_role == user.role)),
        )
    ).all()
    pending_approvals = db.scalars(
        select(ApprovalInstance).where(
            ApprovalInstance.status == "pending",
            or_(ApprovalInstance.approver_user_id == user.id, and_(ApprovalInstance.approver_user_id.is_(None), ApprovalInstance.approver_role == user.role)),
        )
    ).all()
    return {
        "tasks": [
            {
                "id": task.id,
                "process_instance_id": task.process_instance_id,
                "title": task.title,
                "node_id": task.node_id,
                "created_at": task.created_at,
            }
            for task in pending_tasks
        ],
        "approvals": [
            {
                "id": approval.id,
                "process_instance_id": approval.process_instance_id,
                "node_id": approval.node_id,
                "approver_role": approval.approver_role,
                "created_at": approval.created_at,
            }
            for approval in pending_approvals
        ],
    }


@app.post("/tasks/{task_id}/complete")
def complete_task_endpoint(
    task_id: str,
    payload: TaskCompleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    task = db.get(TaskInstance, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    instance = complete_task(db, task=task, actor=user, payload=payload.payload, outcome=payload.outcome, comment=payload.comment)
    return serialize_instance(instance, db)


@app.post("/approvals/{approval_id}/decide")
def approval_decide_endpoint(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    approval = db.get(ApprovalInstance, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    instance = decide_approval(db, approval=approval, actor=user, decision=payload.decision, comment=payload.comment)
    return serialize_instance(instance, db)


@app.post("/instances/{instance_id}/documents")
def upload_instance_document(
    instance_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    document = upload_document(db, instance=instance, actor=user, file=file, document_type=document_type)
    db.commit()
    db.refresh(document)
    return {
        "id": document.id,
        "document_type": document.document_type,
        "version": document.version,
        "file_name": document.file_name,
        "extracted_json": document.extracted_json,
    }


@app.get("/instances/{instance_id}/documents")
def get_instance_documents(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    documents = db.scalars(select(Document).where(Document.process_instance_id == instance_id).order_by(Document.created_at.desc())).all()
    return [
        {
            "id": document.id,
            "document_type": document.document_type,
            "version": document.version,
            "file_name": document.file_name,
            "storage_path": document.storage_path,
            "extracted_json": document.extracted_json,
            "metadata_json": document.metadata_json,
            "created_at": document.created_at,
        }
        for document in documents
    ]


@app.post("/documents/{document_id}/new-version")
def new_document_version(
    document_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    previous = db.get(Document, document_id)
    if previous is None:
        raise HTTPException(status_code=404, detail="Document not found")
    instance = db.get(ProcessInstance, previous.process_instance_id)
    document = upload_document(db, instance=instance, actor=user, file=file, document_type=previous.document_type, metadata=previous.metadata_json)
    db.commit()
    return {
        "id": document.id,
        "document_type": document.document_type,
        "version": document.version,
        "file_name": document.file_name,
        "extracted_json": document.extracted_json,
    }


@app.get("/context/schema")
def get_context_schema(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return instance_context_schema()


@app.post("/expressions/preview")
def expression_preview(
    payload: ExpressionPreviewRequest,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    context = payload.context_sample or default_context_sample()
    return {"result": resolve_template(payload.expr, context)}


@app.get("/audit")
def get_audit(
    instance_id: str | None = None,
    user_id: str | None = None,
    flow_id: str | None = None,
    form_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    stmt = select(AuditEvent).where(AuditEvent.org_id == user.org_id).order_by(AuditEvent.created_at.desc())
    if instance_id:
        stmt = stmt.where(AuditEvent.process_instance_id == instance_id)
    if user_id:
        stmt = stmt.where(AuditEvent.actor_user_id == user_id)
    if flow_id:
        stmt = stmt.where(and_(AuditEvent.entity_type == "flow", AuditEvent.entity_id == flow_id))
    if form_id:
        stmt = stmt.where(and_(AuditEvent.entity_type == "form", AuditEvent.entity_id == form_id))
    events = db.scalars(stmt).all()
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "actor_user_id": event.actor_user_id,
            "process_instance_id": event.process_instance_id,
            "payload_json": event.payload_json,
            "created_at": event.created_at,
        }
        for event in events
    ]


@app.get("/admin/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))) -> list[dict[str, Any]]:
    users = db.scalars(select(User).where(User.org_id == user.org_id).order_by(User.created_at)).all()
    return [serialize_user(item) for item in users]


@app.post("/admin/users")
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))) -> dict[str, Any]:
    item = User(
        org_id=user.org_id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department=payload.department,
        cost_center=payload.cost_center,
        manager_id=payload.manager_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_user(item)


@app.put("/admin/users/{user_id}")
def update_user(user_id: str, payload: UserUpdateRequest, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> dict[str, Any]:
    item = db.get(User, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    return serialize_user(item)


@app.delete("/admin/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> dict[str, bool]:
    item = db.get(User, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@app.get("/admin/delegations")
def list_delegations(db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> list[dict[str, Any]]:
    delegations = db.scalars(select(Delegation).where(Delegation.org_id == admin.org_id).order_by(Delegation.created_at.desc())).all()
    return [
        {
            "id": item.id,
            "delegator_id": item.delegator_id,
            "delegate_id": item.delegate_id,
            "role_scope": item.role_scope,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "is_active": item.is_active,
        }
        for item in delegations
    ]


@app.post("/admin/delegations")
def create_delegation(payload: DelegationRequest, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> dict[str, Any]:
    item = Delegation(org_id=admin.org_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "delegator_id": item.delegator_id,
        "delegate_id": item.delegate_id,
        "role_scope": item.role_scope,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "is_active": item.is_active,
    }


@app.put("/admin/delegations/{delegation_id}")
def update_delegation(
    delegation_id: str,
    payload: DelegationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    item = db.get(Delegation, delegation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Delegation not found")
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    return {
        "id": item.id,
        "delegator_id": item.delegator_id,
        "delegate_id": item.delegate_id,
        "role_scope": item.role_scope,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "is_active": item.is_active,
    }


@app.delete("/admin/delegations/{delegation_id}")
def delete_delegation(delegation_id: str, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> dict[str, bool]:
    item = db.get(Delegation, delegation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Delegation not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@app.get("/admin/approval-limits")
def list_approval_limits(db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> list[dict[str, Any]]:
    items = db.scalars(select(ApprovalLimit).where(ApprovalLimit.org_id == admin.org_id).order_by(ApprovalLimit.min_amount)).all()
    return [
        {
            "id": item.id,
            "department": item.department,
            "budget_type": item.budget_type,
            "currency": item.currency,
            "min_amount": item.min_amount,
            "max_amount": item.max_amount,
            "approver_role": item.approver_role,
            "approver_user_id": item.approver_user_id,
        }
        for item in items
    ]


@app.post("/admin/approval-limits")
def create_approval_limit(payload: ApprovalLimitRequest, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> dict[str, Any]:
    item = ApprovalLimit(org_id=admin.org_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "department": item.department,
        "budget_type": item.budget_type,
        "currency": item.currency,
        "min_amount": item.min_amount,
        "max_amount": item.max_amount,
        "approver_role": item.approver_role,
        "approver_user_id": item.approver_user_id,
    }


@app.put("/admin/approval-limits/{limit_id}")
def update_approval_limit(
    limit_id: str,
    payload: ApprovalLimitRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    item = db.get(ApprovalLimit, limit_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Approval limit not found")
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    return {
        "id": item.id,
        "department": item.department,
        "budget_type": item.budget_type,
        "currency": item.currency,
        "min_amount": item.min_amount,
        "max_amount": item.max_amount,
        "approver_role": item.approver_role,
        "approver_user_id": item.approver_user_id,
    }


@app.delete("/admin/approval-limits/{limit_id}")
def delete_approval_limit(limit_id: str, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))) -> dict[str, bool]:
    item = db.get(ApprovalLimit, limit_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Approval limit not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
