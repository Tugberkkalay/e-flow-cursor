from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import TaskInstance, ApprovalInstance, User
from app.schemas.schemas import InboxItem, TaskComplete, ApprovalDecision, InstanceOut
from app.services.auth import get_current_user
from app.engine.runtime import BPMRuntime

router = APIRouter(prefix="/api", tags=["inbox"])


@router.get("/inbox", response_model=list[InboxItem])
def get_inbox(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = []

    tasks = db.query(TaskInstance).filter(
        TaskInstance.assignee_id == user.id,
        TaskInstance.status == "pending",
    ).order_by(TaskInstance.created_at.desc()).all()

    for task in tasks:
        items.append(InboxItem(
            id=task.id,
            type="task",
            title=task.title,
            instance_id=task.instance_id,
            instance_title=task.instance_title,
            flow_name=task.flow_name,
            description=task.description,
            created_at=task.created_at,
        ))

    approvals = db.query(ApprovalInstance).filter(
        ApprovalInstance.approver_id == user.id,
        ApprovalInstance.decision == None,
    ).order_by(ApprovalInstance.created_at.desc()).all()

    for appr in approvals:
        items.append(InboxItem(
            id=appr.id,
            type="approval",
            title=f"Onay: {appr.flow_name or 'Süreç'}",
            instance_id=appr.instance_id,
            instance_title=appr.instance_title,
            flow_name=appr.flow_name,
            amount=appr.amount,
            created_at=appr.created_at,
        ))

    return sorted(items, key=lambda x: x.created_at, reverse=True)


@router.post("/tasks/{task_id}/complete", response_model=InstanceOut)
def complete_task(task_id: str, req: TaskComplete, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(TaskInstance).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")

    runtime = BPMRuntime(db)
    instance = runtime.complete_task(task, req.form_data)
    return InstanceOut.model_validate(instance)


@router.post("/approvals/{approval_id}/decide", response_model=InstanceOut)
def decide_approval(approval_id: str, req: ApprovalDecision, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    approval = db.query(ApprovalInstance).get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.approver_id != user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")

    runtime = BPMRuntime(db)
    instance = runtime.decide_approval(approval, req.decision, req.comment)
    return InstanceOut.model_validate(instance)
