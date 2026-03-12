from __future__ import annotations

from datetime import date, datetime, timezone
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.models import (
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
)
from app.schemas.schemas import (
    ApprovalDecisionRequest,
    ApprovalLimitCreate,
    DelegationCreate,
    ExpressionPreviewRequest,
    ExpressionPreviewResponse,
    FlowCreate,
    FlowResponse,
    FlowUpdate,
    FormCreate,
    FormResponse,
    FormUpdate,
    InstanceActionRequest,
    InstanceResponse,
    LoginRequest,
    MeResponse,
    ProcessVersionResponse,
    StartInstanceRequest,
    TaskCompleteRequest,
    TimelineEvent,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.bpm_engine import BPMEngine
from app.services.expression_engine import resolve_expression

router = APIRouter()


def _get_latest_version(db: Session, definition_id: str) -> ProcessVersion | None:
    return db.execute(
        select(ProcessVersion)
        .where(ProcessVersion.process_definition_id == definition_id)
        .order_by(desc(ProcessVersion.version_no))
        .limit(1)
    ).scalar_one_or_none()


@router.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.execute(select(User).where(User.email == payload.email, User.is_active == True)).scalar_one_or_none()  # noqa: E712
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(subject=user.id, extra={"role": user.role, "org_id": user.org_id})
    return Token(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse.model_validate(user)


@router.get("/flows", response_model=list[FlowResponse])
def list_flows(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[FlowResponse]:
    flows = db.execute(select(ProcessDefinition).where(ProcessDefinition.org_id == user.org_id)).scalars().all()
    result: list[FlowResponse] = []
    for flow in flows:
        latest = _get_latest_version(db, flow.id)
        result.append(
            FlowResponse(
                id=flow.id,
                code=flow.code,
                name=flow.name,
                description=flow.description,
                latest_version=latest.version_no if latest else None,
                latest_status=latest.status if latest else None,
            )
        )
    return result


@router.post("/flows", response_model=FlowResponse)
def create_flow(payload: FlowCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> FlowResponse:
    existing = db.execute(select(ProcessDefinition).where(ProcessDefinition.code == payload.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Flow code already exists")
    flow = ProcessDefinition(
        org_id=user.org_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        created_by=user.id,
    )
    db.add(flow)
    db.flush()
    version = ProcessVersion(
        org_id=user.org_id,
        process_definition_id=flow.id,
        version_no=1,
        status="draft",
        graph_json=payload.graph_json,
    )
    db.add(version)
    db.add(
        AuditEvent(
            org_id=user.org_id,
            flow_id=flow.id,
            user_id=user.id,
            event_type="flow.created",
            payload_json={"code": payload.code},
        )
    )
    db.commit()
    return FlowResponse(id=flow.id, code=flow.code, name=flow.name, description=flow.description, latest_version=1, latest_status="draft")


@router.put("/flows/{flow_id}", response_model=FlowResponse)
def update_flow(flow_id: str, payload: FlowUpdate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> FlowResponse:
    flow = db.get(ProcessDefinition, flow_id)
    if not flow or flow.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Flow not found")
    latest = _get_latest_version(db, flow.id)
    if not latest:
        raise HTTPException(status_code=404, detail="No flow version found")
    if payload.name is not None:
        flow.name = payload.name
    if payload.description is not None:
        flow.description = payload.description
    if payload.graph_json is not None:
        next_version = ProcessVersion(
            org_id=user.org_id,
            process_definition_id=flow.id,
            version_no=latest.version_no + 1,
            status="draft",
            graph_json=payload.graph_json,
        )
        db.add(next_version)
        latest = next_version
    db.add(
        AuditEvent(
            org_id=user.org_id,
            flow_id=flow.id,
            user_id=user.id,
            event_type="flow.updated",
            payload_json={"version": latest.version_no},
        )
    )
    db.commit()
    return FlowResponse(
        id=flow.id,
        code=flow.code,
        name=flow.name,
        description=flow.description,
        latest_version=latest.version_no,
        latest_status=latest.status,
    )


@router.post("/flows/{flow_id}/publish")
def publish_flow(flow_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> dict[str, Any]:
    flow = db.get(ProcessDefinition, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    latest = _get_latest_version(db, flow_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No versions")
    latest.status = "published"
    latest.published_at = datetime.now(timezone.utc)
    db.add(AuditEvent(org_id=user.org_id, flow_id=flow_id, user_id=user.id, event_type="flow.published", payload_json={"version": latest.version_no}))
    db.commit()
    return {"ok": True, "version_id": latest.id, "version_no": latest.version_no}


@router.get("/flows/{flow_id}/versions", response_model=list[ProcessVersionResponse])
def flow_versions(flow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ProcessVersionResponse]:
    versions = (
        db.execute(select(ProcessVersion).where(ProcessVersion.process_definition_id == flow_id).order_by(desc(ProcessVersion.version_no)))
        .scalars()
        .all()
    )
    return [ProcessVersionResponse.model_validate(v) for v in versions]


@router.get("/forms", response_model=list[FormResponse])
def list_forms(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[FormResponse]:
    forms = db.execute(select(FormDefinition).where(FormDefinition.org_id == user.org_id)).scalars().all()
    return [FormResponse.model_validate(item) for item in forms]


@router.post("/forms", response_model=FormResponse)
def create_form(payload: FormCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> FormResponse:
    existing = db.execute(select(FormDefinition).where(FormDefinition.code == payload.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Form code exists")
    form = FormDefinition(
        org_id=user.org_id,
        code=payload.code,
        name=payload.name,
        schema_json=payload.form_schema,
        status="draft",
        version_no=1,
    )
    db.add(form)
    db.add(AuditEvent(org_id=user.org_id, form_id=form.id, user_id=user.id, event_type="form.created", payload_json={}))
    db.commit()
    db.refresh(form)
    return FormResponse.model_validate(form)


@router.put("/forms/{form_id}", response_model=FormResponse)
def update_form(form_id: str, payload: FormUpdate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> FormResponse:
    form = db.get(FormDefinition, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if payload.name is not None:
        form.name = payload.name
    if payload.form_schema is not None:
        form.schema_json = payload.form_schema
        form.version_no += 1
        form.status = "draft"
    db.add(AuditEvent(org_id=user.org_id, form_id=form.id, user_id=user.id, event_type="form.updated", payload_json={"version": form.version_no}))
    db.commit()
    db.refresh(form)
    return FormResponse.model_validate(form)


@router.post("/forms/{form_id}/publish")
def publish_form(form_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> dict[str, Any]:
    form = db.get(FormDefinition, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    form.status = "published"
    db.add(AuditEvent(org_id=user.org_id, form_id=form.id, user_id=user.id, event_type="form.published", payload_json={"version": form.version_no}))
    db.commit()
    return {"ok": True}


@router.post("/instances/start", response_model=InstanceResponse)
def start_instance(payload: StartInstanceRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> InstanceResponse:
    version = db.get(ProcessVersion, payload.flow_version_id)
    if not version or version.status != "published":
        raise HTTPException(status_code=400, detail="Published flow version not found")
    nodes = version.graph_json.get("nodes", [])
    start_node = next((n for n in nodes if (n.get("data", {}).get("engineType", n.get("type", "")).lower()) in {"start", "manualstart"}), None)
    if not start_node:
        raise HTTPException(status_code=400, detail="Start node missing")
    instance = ProcessInstance(
        org_id=user.org_id,
        process_version_id=version.id,
        title=payload.title,
        requester_id=user.id,
        status="running",
        current_node_id=start_node["id"],
        variables_json={
            "form": payload.initial_inputs,
            "system": {
                "requester": user.full_name,
                "roles": [user.role],
                "org": user.org_id,
                "department": user.department,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
    db.add(instance)
    db.flush()
    db.add(
        AuditEvent(
            org_id=user.org_id,
            process_instance_id=instance.id,
            user_id=user.id,
            flow_id=version.process_definition_id,
            event_type="instance.started",
            payload_json={"flow_version_id": version.id},
        )
    )
    BPMEngine(db).run_until_wait(instance, actor=user)
    db.commit()
    db.refresh(instance)
    return InstanceResponse.model_validate(instance)


@router.get("/instances", response_model=list[InstanceResponse])
def list_instances(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[InstanceResponse]:
    stmt = select(ProcessInstance).where(ProcessInstance.org_id == user.org_id)
    if status_filter:
        stmt = stmt.where(ProcessInstance.status == status_filter)
    instances = db.execute(stmt.order_by(desc(ProcessInstance.started_at))).scalars().all()
    return [InstanceResponse.model_validate(item) for item in instances]


@router.get("/instances/{instance_id}", response_model=InstanceResponse)
def get_instance(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> InstanceResponse:
    instance = db.get(ProcessInstance, instance_id)
    if not instance or instance.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Instance not found")
    return InstanceResponse.model_validate(instance)


@router.get("/instances/{instance_id}/timeline", response_model=list[TimelineEvent])
def instance_timeline(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[TimelineEvent]:
    events = (
        db.execute(
            select(AuditEvent).where(AuditEvent.process_instance_id == instance_id, AuditEvent.org_id == user.org_id).order_by(AuditEvent.created_at)
        )
        .scalars()
        .all()
    )
    return [TimelineEvent.model_validate(ev) for ev in events]


@router.post("/instances/{instance_id}/actions")
def instance_actions(
    instance_id: str,
    payload: InstanceActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    instance = db.get(ProcessInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    engine = BPMEngine(db)
    action = payload.action
    if action == "cancel_instance":
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can cancel")
        instance.status = "cancelled"
        instance.finished_at = datetime.now(timezone.utc)
    elif action == "retry":
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can retry")
        instance.status = "running"
        engine.run_until_wait(instance, actor=user)
    elif action == "skip_step":
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can skip")
        version = db.get(ProcessVersion, instance.process_version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        edges = [e for e in version.graph_json.get("edges", []) if e.get("source") == instance.current_node_id]
        if not edges:
            raise HTTPException(status_code=400, detail="No edge to skip")
        instance.current_node_id = edges[0]["target"]
        instance.status = "running"
        engine.run_until_wait(instance, actor=user)
    elif action == "reassign":
        task_id = payload.payload.get("task_id")
        assignee_id = payload.payload.get("assignee_id")
        task = db.get(TaskInstance, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.assignee_id = assignee_id
    elif action in {"approve", "reject"}:
        approval_id = payload.payload.get("approval_id")
        approval = db.get(ApprovalInstance, approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        engine.decide_approval(approval, user, decision=action, comment=payload.payload.get("comment"))
    elif action == "complete_task":
        task_id = payload.payload.get("task_id")
        task = db.get(TaskInstance, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        engine.complete_task(task, user, payload.payload.get("output", {}))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    db.add(
        AuditEvent(
            org_id=user.org_id,
            process_instance_id=instance_id,
            user_id=user.id,
            event_type=f"instance.action.{action}",
            payload_json=payload.payload,
        )
    )
    db.commit()
    return {"ok": True}


@router.get("/inbox")
def inbox(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    today = date.today()
    delegate_from = db.execute(
        select(Delegation.from_user_id).where(
            Delegation.to_user_id == user.id,
            Delegation.is_active == True,  # noqa: E712
            Delegation.start_date <= today,
            Delegation.end_date >= today,
        )
    ).scalars().all()
    assignable_user_ids = [user.id, *delegate_from]
    pending_tasks = (
        db.execute(
            select(TaskInstance).where(
                TaskInstance.org_id == user.org_id,
                TaskInstance.status == "pending",
                or_(TaskInstance.assignee_id.in_(assignable_user_ids), TaskInstance.assignee_role == user.role),
            )
        )
        .scalars()
        .all()
    )
    pending_approvals = (
        db.execute(
            select(ApprovalInstance).where(
                ApprovalInstance.org_id == user.org_id,
                ApprovalInstance.status == "pending",
                or_(ApprovalInstance.assignee_id.in_(assignable_user_ids), ApprovalInstance.assignee_role == user.role),
            )
        )
        .scalars()
        .all()
    )
    return {
        "tasks": [
            {"id": t.id, "instance_id": t.process_instance_id, "title": t.title, "status": t.status, "assignee_role": t.assignee_role}
            for t in pending_tasks
        ],
        "approvals": [
            {"id": a.id, "instance_id": a.process_instance_id, "status": a.status, "assignee_role": a.assignee_role} for a in pending_approvals
        ],
    }


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: str, payload: TaskCompleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    task = db.get(TaskInstance, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    BPMEngine(db).complete_task(task, user, payload.output)
    db.commit()
    return {"ok": True}


@router.post("/approvals/{approval_id}/decide")
def decide_approval(
    approval_id: str, payload: ApprovalDecisionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, Any]:
    approval = db.get(ApprovalInstance, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    BPMEngine(db).decide_approval(approval, user, payload.decision, payload.comment)
    db.commit()
    return {"ok": True}


def _stub_extract(file_name: str) -> dict[str, Any]:
    lower = file_name.lower()
    if "invoice" in lower:
        return {"doc_type": "invoice", "supplier_vkn": "1234567890", "amount": 12000, "currency": "TRY"}
    if "contract" in lower:
        return {"doc_type": "contract", "start_date": "2026-01-01", "end_date": "2026-12-31", "amount": 500000}
    if "offer" in lower:
        return {"doc_type": "offer", "supplier_vkn": "9988776655", "amount": 45000}
    return {"doc_type": "generic", "quality": "stub"}


@router.post("/instances/{instance_id}/documents")
async def upload_document(
    instance_id: str,
    document_type: str = "generic",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    instance = db.get(ProcessInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    extracted = _stub_extract(file.filename)
    document = Document(
        org_id=user.org_id,
        process_instance_id=instance_id,
        document_type=document_type,
        file_name=file.filename,
        storage_uri=f"s3://stub/{instance_id}/{file.filename}",
        extracted_json=extracted,
        uploaded_by=user.id,
        version_no=1,
    )
    db.add(document)
    vars_json = instance.variables_json or {}
    vars_json.setdefault("docs", {})
    vars_json["docs"].setdefault("list", []).append({"id": document.id, "type": document_type, "file_name": file.filename})
    vars_json["docs"]["offers_count"] = len([d for d in vars_json["docs"].get("list", []) if d["type"] in {"offer", "offers"}])
    vars_json.setdefault("extract", {})[document_type] = extracted
    instance.variables_json = vars_json
    db.add(AuditEvent(org_id=user.org_id, process_instance_id=instance_id, user_id=user.id, event_type="document.uploaded", payload_json={"name": file.filename}))
    db.commit()
    return {"ok": True, "document_id": document.id, "extracted_json": extracted}


@router.get("/instances/{instance_id}/documents")
def list_documents(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    docs = db.execute(select(Document).where(Document.process_instance_id == instance_id, Document.org_id == user.org_id)).scalars().all()
    return [
        {
            "id": d.id,
            "document_type": d.document_type,
            "file_name": d.file_name,
            "version_no": d.version_no,
            "storage_uri": d.storage_uri,
            "extracted_json": d.extracted_json,
        }
        for d in docs
    ]


@router.post("/documents/{document_id}/new-version")
def new_document_version(
    document_id: str,
    file_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    latest = (
        db.execute(
            select(Document)
            .where(
                and_(
                    Document.org_id == doc.org_id,
                    Document.process_instance_id == doc.process_instance_id,
                    or_(Document.id == doc.id, Document.parent_document_id == doc.id),
                )
            )
            .order_by(desc(Document.version_no))
            .limit(1)
        )
        .scalar_one_or_none()
    )
    next_ver = (latest.version_no if latest else doc.version_no) + 1
    new_doc = Document(
        org_id=doc.org_id,
        process_instance_id=doc.process_instance_id,
        parent_document_id=doc.parent_document_id or doc.id,
        document_type=doc.document_type,
        file_name=file_name,
        storage_uri=f"s3://stub/{doc.process_instance_id}/{file_name}",
        version_no=next_ver,
        extracted_json=_stub_extract(file_name),
        uploaded_by=user.id,
    )
    db.add(new_doc)
    db.commit()
    return {"ok": True, "document_id": new_doc.id, "version_no": next_ver}


@router.get("/context/schema")
def context_schema() -> dict[str, Any]:
    return {
        "namespaces": {
            "form": ["request_type", "department", "total_amount", "currency", "line_items"],
            "docs": ["list", "offers_count"],
            "extract": ["invoice", "contract", "offer"],
            "selection": ["supplier_vkn", "match_status"],
            "approval": ["decision", "comment"],
            "gen": ["po_no", "payment_result", "signed_url", "archive_id"],
            "calc": ["total", "kdv", "rate"],
            "flags": ["policy", "mismatch"],
            "system": ["requester", "roles", "org", "now", "department"],
            "exports": ["po_no", "payment_status", "contract_id"],
        }
    }


@router.post("/expressions/preview", response_model=ExpressionPreviewResponse)
def expression_preview(payload: ExpressionPreviewRequest) -> ExpressionPreviewResponse:
    return ExpressionPreviewResponse(result=resolve_expression(payload.expr, payload.sample_context))


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> list[UserResponse]:
    users = db.execute(select(User).where(User.org_id == user.org_id)).scalars().all()
    return [UserResponse.model_validate(item) for item in users]


@router.post("/users", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> UserResponse:
    db_user = User(
        org_id=user.org_id,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        department=payload.department,
        cost_center=payload.cost_center,
        manager_id=payload.manager_id,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.model_validate(db_user)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> UserResponse:
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(target, key, value)
    db.commit()
    db.refresh(target)
    return UserResponse.model_validate(target)


@router.get("/delegations")
def list_delegations(db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> list[dict[str, Any]]:
    rows = db.execute(select(Delegation).where(Delegation.org_id == user.org_id)).scalars().all()
    return [
        {
            "id": row.id,
            "from_user_id": row.from_user_id,
            "to_user_id": row.to_user_id,
            "role_scope": row.role_scope,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "is_active": row.is_active,
        }
        for row in rows
    ]


@router.post("/delegations")
def create_delegation(payload: DelegationCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> dict[str, Any]:
    row = Delegation(org_id=user.org_id, **payload.model_dump())
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id}


@router.get("/approval-limits")
def list_approval_limits(db: Session = Depends(get_db), user: User = Depends(require_role("admin"))) -> list[dict[str, Any]]:
    rows = db.execute(select(ApprovalLimit).where(ApprovalLimit.org_id == user.org_id)).scalars().all()
    return [
        {
            "id": row.id,
            "department": row.department,
            "budget_type": row.budget_type,
            "currency": row.currency,
            "min_amount": row.min_amount,
            "max_amount": row.max_amount,
            "approver_role": row.approver_role,
        }
        for row in rows
    ]


@router.post("/approval-limits")
def create_approval_limit(
    payload: ApprovalLimitCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
) -> dict[str, Any]:
    row = ApprovalLimit(org_id=user.org_id, **payload.model_dump())
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id}


@router.get("/audit")
def audit_events(
    instance_id: str | None = None,
    user_id: str | None = None,
    flow_id: str | None = None,
    form_id: str | None = None,
    export_csv: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "viewer", "approver", "procurement", "finance", "legal")),
):
    stmt = select(AuditEvent).where(AuditEvent.org_id == user.org_id)
    if instance_id:
        stmt = stmt.where(AuditEvent.process_instance_id == instance_id)
    if user_id:
        stmt = stmt.where(AuditEvent.user_id == user_id)
    if flow_id:
        stmt = stmt.where(AuditEvent.flow_id == flow_id)
    if form_id:
        stmt = stmt.where(AuditEvent.form_id == form_id)
    events = db.execute(stmt.order_by(desc(AuditEvent.created_at))).scalars().all()

    if not export_csv:
        return [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "user_id": ev.user_id,
                "instance_id": ev.process_instance_id,
                "created_at": ev.created_at,
                "payload_json": ev.payload_json,
            }
            for ev in events
        ]

    buffer = StringIO()
    buffer.write("id,event_type,user_id,instance_id,created_at,payload\n")
    for ev in events:
        buffer.write(
            f"{ev.id},{ev.event_type},{ev.user_id or ''},{ev.process_instance_id or ''},{ev.created_at.isoformat()},{str(ev.payload_json).replace(',', ';')}\n"
        )
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="audit.csv"'})
