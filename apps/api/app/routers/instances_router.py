from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.models import (
    ProcessInstance, ProcessDefinition, ProcessVersion, NodeInstance,
    TaskInstance, ApprovalInstance, AuditEvent, User,
)
from app.schemas.schemas import InstanceStart, InstanceOut, InstanceAction, AuditEventOut
from app.services.auth import get_current_user
from app.engine.runtime import BPMRuntime

router = APIRouter(prefix="/api/instances", tags=["instances"])


@router.get("", response_model=list[InstanceOut])
def list_instances(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(ProcessInstance).filter(ProcessInstance.org_id == user.org_id)
    if status:
        query = query.filter(ProcessInstance.status == status)
    instances = query.order_by(ProcessInstance.started_at.desc()).all()
    return [InstanceOut.model_validate(i) for i in instances]


@router.post("/start", response_model=InstanceOut)
def start_instance(req: InstanceStart, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flow = db.query(ProcessDefinition).get(req.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    version = db.query(ProcessVersion).filter(
        ProcessVersion.flow_id == req.flow_id,
        ProcessVersion.status == "published",
    ).order_by(ProcessVersion.version.desc()).first()

    if not version:
        version = db.query(ProcessVersion).filter(
            ProcessVersion.flow_id == req.flow_id,
        ).order_by(ProcessVersion.version.desc()).first()

    if not version:
        raise HTTPException(status_code=400, detail="No version available")

    runtime = BPMRuntime(db)
    instance = runtime.start_instance(
        flow_id=req.flow_id,
        version_id=version.id,
        requester_id=user.id,
        initial_inputs=req.initial_inputs,
    )
    return InstanceOut.model_validate(instance)


@router.get("/{instance_id}", response_model=InstanceOut)
def get_instance(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    instance = db.query(ProcessInstance).get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return InstanceOut.model_validate(instance)


@router.post("/{instance_id}/actions", response_model=InstanceOut)
def instance_action(
    instance_id: str,
    req: InstanceAction,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    instance = db.query(ProcessInstance).get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    runtime = BPMRuntime(db)

    if req.action == "cancel":
        instance = runtime.cancel_instance(instance, user.id)
    elif req.action == "retry":
        node_id = (req.data or {}).get("node_id", instance.current_node_id)
        instance = runtime.retry_node(instance, node_id)
    elif req.action == "skip":
        instance = runtime.skip_node(instance)
    elif req.action == "approve":
        pending = db.query(ApprovalInstance).filter(
            ApprovalInstance.instance_id == instance_id,
            ApprovalInstance.decision == None,
        ).first()
        if pending:
            instance = runtime.decide_approval(pending, "approved", req.comment)
    elif req.action == "reject":
        pending = db.query(ApprovalInstance).filter(
            ApprovalInstance.instance_id == instance_id,
            ApprovalInstance.decision == None,
        ).first()
        if pending:
            instance = runtime.decide_approval(pending, "rejected", req.comment)
    elif req.action == "complete_task":
        pending = db.query(TaskInstance).filter(
            TaskInstance.instance_id == instance_id,
            TaskInstance.status == "pending",
        ).first()
        if pending:
            instance = runtime.complete_task(pending, req.data)

    return InstanceOut.model_validate(instance)


@router.get("/{instance_id}/timeline", response_model=list[AuditEventOut])
def instance_timeline(instance_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    events = db.query(AuditEvent).filter(
        AuditEvent.instance_id == instance_id,
    ).order_by(AuditEvent.timestamp.asc()).all()
    return [AuditEventOut.model_validate(e) for e in events]
