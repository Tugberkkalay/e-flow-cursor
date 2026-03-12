from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.instance import ProcessInstance, NodeInstance, TaskInstance, ApprovalInstance, AuditEvent, Document
from app.models.flow import ProcessVersion, ProcessDefinition
from app.auth import get_current_user
from app.engine.executor import BPMEngine

router = APIRouter(prefix="/instances", tags=["instances"])


class StartInstanceRequest(BaseModel):
    flow_version_id: str
    title: str
    initial_inputs: dict = {}


class ActionRequest(BaseModel):
    action: str  # approve|reject|revision|complete_task|cancel|reassign|retry|skip
    payload: dict = {}
    comment: Optional[str] = None


def _instance_out(inst: ProcessInstance) -> dict:
    return {
        "id": str(inst.id),
        "title": inst.title,
        "status": inst.status,
        "current_node_id": inst.current_node_id,
        "variables": inst.variables,
        "exports": inst.exports,
        "definition_id": str(inst.definition_id),
        "version_id": str(inst.version_id),
        "started_by": str(inst.started_by) if inst.started_by else None,
        "started_at": inst.started_at.isoformat() if inst.started_at else None,
        "completed_at": inst.completed_at.isoformat() if inst.completed_at else None,
        "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
        "due_date": inst.due_date.isoformat() if inst.due_date else None,
    }


@router.post("/start")
async def start_instance(
    req: StartInstanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = BPMEngine(db)
    try:
        instance = await engine.start_instance(
            version_id=uuid.UUID(req.flow_version_id),
            title=req.title,
            initial_inputs=req.initial_inputs,
            started_by_id=current_user.id,
            org_id=current_user.org_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _instance_out(instance)


@router.get("")
async def list_instances(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ProcessInstance).where(ProcessInstance.org_id == current_user.org_id)
    if status and status != "all":
        query = query.where(ProcessInstance.status == status)
    query = query.order_by(ProcessInstance.started_at.desc())
    result = await db.execute(query)
    instances = result.scalars().all()

    out = []
    for inst in instances:
        d = _instance_out(inst)
        # Add definition name
        def_result = await db.execute(select(ProcessDefinition).where(ProcessDefinition.id == inst.definition_id))
        definition = def_result.scalar_one_or_none()
        d["definition_name"] = definition.name if definition else ""

        # Add started_by name
        if inst.started_by:
            from app.models.user import User as UserModel
            user_result = await db.execute(select(UserModel).where(UserModel.id == inst.started_by))
            user = user_result.scalar_one_or_none()
            d["started_by_name"] = user.full_name if user else ""
        else:
            d["started_by_name"] = ""

        out.append(d)
    return out


@router.get("/{instance_id}")
async def get_instance(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProcessInstance).where(ProcessInstance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(404, "Instance not found")

    d = _instance_out(instance)

    # Node instances
    nodes_result = await db.execute(
        select(NodeInstance).where(NodeInstance.process_instance_id == instance_id)
        .order_by(NodeInstance.started_at)
    )
    d["node_instances"] = [
        {
            "id": str(n.id), "node_id": n.node_id, "node_type": n.node_type,
            "node_label": n.node_label, "status": n.status,
            "started_at": n.started_at.isoformat() if n.started_at else None,
            "completed_at": n.completed_at.isoformat() if n.completed_at else None,
            "duration_ms": n.duration_ms, "output_data": n.output_data,
            "error_message": n.error_message,
        }
        for n in nodes_result.scalars().all()
    ]

    # Tasks
    tasks_result = await db.execute(
        select(TaskInstance).where(TaskInstance.process_instance_id == instance_id)
        .order_by(TaskInstance.created_at)
    )
    task_list = []
    for t in tasks_result.scalars().all():
        td = {
            "id": str(t.id), "node_id": t.node_id, "task_type": t.task_type,
            "title": t.title, "description": t.description, "status": t.status,
            "assigned_to": str(t.assigned_to) if t.assigned_to else None,
            "assigned_role": t.assigned_role,
            "form_data": t.form_data, "result_data": t.result_data,
            "comment": t.comment,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        if t.assigned_to:
            from app.models.user import User as UserModel
            u_res = await db.execute(select(UserModel).where(UserModel.id == t.assigned_to))
            u = u_res.scalar_one_or_none()
            td["assigned_to_name"] = u.full_name if u else ""
        task_list.append(td)
    d["tasks"] = task_list

    # Approvals
    approvals_result = await db.execute(
        select(ApprovalInstance).where(ApprovalInstance.process_instance_id == instance_id)
        .order_by(ApprovalInstance.created_at)
    )
    approval_list = []
    for a in approvals_result.scalars().all():
        ad = {
            "id": str(a.id), "node_id": a.node_id, "status": a.status,
            "decision": a.decision, "comment": a.comment,
            "approver_id": str(a.approver_id) if a.approver_id else None,
            "approver_role": a.approver_role,
            "amount": float(a.amount) if a.amount else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "decided_at": a.decided_at.isoformat() if a.decided_at else None,
        }
        if a.approver_id:
            from app.models.user import User as UserModel
            u_res = await db.execute(select(UserModel).where(UserModel.id == a.approver_id))
            u = u_res.scalar_one_or_none()
            ad["approver_name"] = u.full_name if u else ""
        approval_list.append(ad)
    d["approvals"] = approval_list

    # Documents
    docs_result = await db.execute(
        select(Document).where(Document.process_instance_id == instance_id)
        .order_by(Document.created_at)
    )
    d["documents"] = [
        {
            "id": str(doc.id), "doc_type": doc.doc_type,
            "original_filename": doc.original_filename,
            "version_number": doc.version_number,
            "extraction_status": doc.extraction_status,
            "extracted_json": doc.extracted_json,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in docs_result.scalars().all()
    ]

    # Definition name
    def_result = await db.execute(select(ProcessDefinition).where(ProcessDefinition.id == instance.definition_id))
    definition = def_result.scalar_one_or_none()
    d["definition_name"] = definition.name if definition else ""

    return d


@router.post("/{instance_id}/actions")
async def instance_action(
    instance_id: uuid.UUID,
    req: ActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = BPMEngine(db)
    payload = req.payload or {}
    if req.comment:
        payload["comment"] = req.comment

    try:
        instance = await engine.advance(
            instance_id=instance_id,
            action=req.action,
            payload=payload,
            actor_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _instance_out(instance)


@router.get("/{instance_id}/timeline")
async def instance_timeline(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.process_instance_id == instance_id)
        .order_by(AuditEvent.created_at)
    )
    events = result.scalars().all()
    out = []
    for e in events:
        ed = {
            "id": str(e.id),
            "event_type": e.event_type,
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "actor_email": e.actor_email,
            "payload": e.payload,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        if e.actor_id:
            from app.models.user import User as UserModel
            u_res = await db.execute(select(UserModel).where(UserModel.id == e.actor_id))
            u = u_res.scalar_one_or_none()
            ed["actor_name"] = u.full_name if u else ""
        out.append(ed)
    return out


@router.post("/{instance_id}/documents")
async def upload_document(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Stub: real upload would handle multipart
    doc = Document(
        org_id=current_user.org_id,
        process_instance_id=instance_id,
        doc_type="generic",
        original_filename="stub_upload.pdf",
        storage_key=f"stubs/{instance_id}/stub.pdf",
        extraction_status="pending",
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    return {"id": str(doc.id), "message": "Document uploaded (stub)"}


@router.get("/{instance_id}/documents")
async def list_documents(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.process_instance_id == instance_id)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id), "doc_type": d.doc_type,
            "original_filename": d.original_filename,
            "version_number": d.version_number,
            "extraction_status": d.extraction_status,
            "extracted_json": d.extracted_json,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]
