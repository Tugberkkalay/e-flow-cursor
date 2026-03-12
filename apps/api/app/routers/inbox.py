from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.instance import TaskInstance, ApprovalInstance, ProcessInstance
from app.auth import get_current_user
from app.engine.executor import BPMEngine

router = APIRouter(tags=["inbox"])


@router.get("/inbox")
async def get_inbox(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Pending tasks assigned to current user or their role
    tasks_result = await db.execute(
        select(TaskInstance).where(
            TaskInstance.status == "pending",
            or_(
                TaskInstance.assigned_to == current_user.id,
                TaskInstance.assigned_role == current_user.role,
            )
        ).order_by(TaskInstance.created_at.desc())
    )
    tasks = tasks_result.scalars().all()

    # Pending approvals
    approvals_result = await db.execute(
        select(ApprovalInstance).where(
            ApprovalInstance.status == "pending",
            or_(
                ApprovalInstance.approver_id == current_user.id,
                ApprovalInstance.approver_role == current_user.role,
            )
        ).order_by(ApprovalInstance.created_at.desc())
    )
    approvals = approvals_result.scalars().all()

    items = []

    for t in tasks:
        inst_res = await db.execute(select(ProcessInstance).where(ProcessInstance.id == t.process_instance_id))
        inst = inst_res.scalar_one_or_none()
        items.append({
            "id": str(t.id),
            "type": "task",
            "task_type": t.task_type,
            "title": t.title,
            "description": t.description,
            "instance_id": str(t.process_instance_id),
            "instance_title": inst.title if inst else "",
            "node_id": t.node_id,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        })

    for a in approvals:
        inst_res = await db.execute(select(ProcessInstance).where(ProcessInstance.id == a.process_instance_id))
        inst = inst_res.scalar_one_or_none()
        items.append({
            "id": str(a.id),
            "type": "approval",
            "task_type": "approval",
            "title": f"Approval Required - {inst.title if inst else 'Process'}",
            "instance_id": str(a.process_instance_id),
            "instance_title": inst.title if inst else "",
            "node_id": a.node_id,
            "status": a.status,
            "amount": float(a.amount) if a.amount else None,
            "approver_role": a.approver_role,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "due_date": a.due_date.isoformat() if a.due_date else None,
        })

    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return items


class TaskCompleteRequest(BaseModel):
    data: dict = {}
    comment: Optional[str] = None


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: uuid.UUID,
    req: TaskCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskInstance).where(TaskInstance.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    engine = BPMEngine(db)
    instance = await engine.advance(
        instance_id=task.process_instance_id,
        action="complete_task",
        payload={"data": req.data, "comment": req.comment},
        actor_id=current_user.id,
    )
    return {"status": "completed", "instance_status": instance.status}


class ApprovalDecisionRequest(BaseModel):
    decision: str  # approved, rejected, revision_requested
    comment: Optional[str] = None


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: uuid.UUID,
    req: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ApprovalInstance).where(ApprovalInstance.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(404, "Approval not found")

    action_map = {
        "approved": "approve",
        "rejected": "reject",
        "revision_requested": "revision",
    }
    action = action_map.get(req.decision, req.decision)

    engine = BPMEngine(db)
    instance = await engine.advance(
        instance_id=approval.process_instance_id,
        action=action,
        payload={"comment": req.comment},
        actor_id=current_user.id,
    )
    return {"status": "decided", "decision": req.decision, "instance_status": instance.status}
