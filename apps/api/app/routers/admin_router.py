import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, Delegation, ApprovalLimit, AuditEvent
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserOut,
    DelegationCreate, DelegationOut,
    ApprovalLimitCreate, ApprovalLimitOut,
    AuditEventOut,
)
from app.services.auth import get_current_user, hash_password

router = APIRouter(prefix="/api", tags=["admin"])


# Users CRUD
@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    users = db.query(User).filter(User.org_id == user.org_id).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("/users", response_model=UserOut)
def create_user(req: UserCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        name=req.name,
        hashed_password=hash_password(req.password),
        role=req.role,
        department=req.department,
        cost_center=req.cost_center,
        manager_id=req.manager_id,
        org_id=user.org_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserOut.model_validate(new_user)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, req: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    target = db.query(User).get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if req.name is not None:
        target.name = req.name
    if req.role is not None:
        target.role = req.role
    if req.department is not None:
        target.department = req.department
    if req.cost_center is not None:
        target.cost_center = req.cost_center
    if req.manager_id is not None:
        target.manager_id = req.manager_id

    db.commit()
    db.refresh(target)
    return UserOut.model_validate(target)


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    target = db.query(User).get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(target)
    db.commit()
    return {"ok": True}


# Delegations
@router.get("/delegations", response_model=list[DelegationOut])
def list_delegations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    delegations = db.query(Delegation).filter(Delegation.org_id == user.org_id).all()
    return [DelegationOut.model_validate(d) for d in delegations]


@router.post("/delegations", response_model=DelegationOut)
def create_delegation(req: DelegationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    delegation = Delegation(
        id=str(uuid.uuid4()),
        from_user_id=req.from_user_id,
        to_user_id=req.to_user_id,
        start_date=req.start_date,
        end_date=req.end_date,
        role_scope=req.role_scope,
        org_id=user.org_id,
    )
    db.add(delegation)
    db.commit()
    db.refresh(delegation)
    return DelegationOut.model_validate(delegation)


# Approval Limits
@router.get("/approval-limits", response_model=list[ApprovalLimitOut])
def list_approval_limits(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    limits = db.query(ApprovalLimit).filter(ApprovalLimit.org_id == user.org_id).all()
    return [ApprovalLimitOut.model_validate(l) for l in limits]


@router.post("/approval-limits", response_model=ApprovalLimitOut)
def create_approval_limit(req: ApprovalLimitCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    limit = ApprovalLimit(
        id=str(uuid.uuid4()),
        department=req.department,
        budget_type=req.budget_type,
        currency=req.currency,
        min_amount=req.min_amount,
        max_amount=req.max_amount,
        approver_role=req.approver_role,
        org_id=user.org_id,
    )
    db.add(limit)
    db.commit()
    db.refresh(limit)
    return ApprovalLimitOut.model_validate(limit)


# Audit (read-only, events cannot be deleted)
@router.get("/audit", response_model=list[AuditEventOut])
def list_audit_events(
    instance_id: str = None,
    user_id: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(AuditEvent).filter(AuditEvent.org_id == user.org_id)
    if instance_id:
        query = query.filter(AuditEvent.instance_id == instance_id)
    if user_id:
        query = query.filter(AuditEvent.user_id == user_id)
    events = query.order_by(AuditEvent.timestamp.desc()).limit(500).all()
    return [AuditEventOut.model_validate(e) for e in events]
