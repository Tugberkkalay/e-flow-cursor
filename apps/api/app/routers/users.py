from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user import User, Delegation, ApprovalLimit
from app.auth import get_current_user, hash_password, require_admin

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "viewer"
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    is_active: Optional[bool] = None


class DelegationRequest(BaseModel):
    delegate_id: str
    role_scope: Optional[str] = None
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None


class ApprovalLimitRequest(BaseModel):
    department: Optional[str] = None
    budget_type: Optional[str] = None
    currency: str = "TRY"
    min_amount: float = 0
    max_amount: Optional[float] = None
    approver_id: str
    approver_role: Optional[str] = None
    priority: int = 0


def _user_out(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "department": u.department,
        "cost_center": u.cost_center,
        "manager_id": str(u.manager_id) if u.manager_id else None,
        "is_active": u.is_active,
        "avatar_initials": u.avatar_initials or u.full_name[:2].upper(),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User).where(User.org_id == current_user.org_id).order_by(User.full_name)
    )
    return [_user_out(u) for u in result.scalars().all()]


@router.post("")
async def create_user(
    req: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check email unique
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")

    user = User(
        org_id=current_user.org_id,
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role,
        department=req.department,
        cost_center=req.cost_center,
        manager_id=uuid.UUID(req.manager_id) if req.manager_id else None,
        avatar_initials=req.full_name[:2].upper(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_out(user)


@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    req: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if req.full_name:
        user.full_name = req.full_name
    if req.role:
        user.role = req.role
    if req.department is not None:
        user.department = req.department
    if req.cost_center is not None:
        user.cost_center = req.cost_center
    if req.is_active is not None:
        user.is_active = req.is_active
    user.updated_at = datetime.utcnow()

    await db.commit()
    return _user_out(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = False
    await db.commit()
    return {"status": "deactivated"}


# Delegations
@router.get("/{user_id}/delegations")
async def list_delegations(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Delegation).where(Delegation.delegator_id == user_id)
    )
    return [
        {
            "id": str(d.id), "delegate_id": str(d.delegate_id),
            "role_scope": d.role_scope,
            "start_date": d.start_date.isoformat(), "end_date": d.end_date.isoformat(),
            "is_active": d.is_active, "reason": d.reason,
        }
        for d in result.scalars().all()
    ]


@router.post("/delegations")
async def create_delegation(
    req: DelegationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delegation = Delegation(
        org_id=current_user.org_id,
        delegator_id=current_user.id,
        delegate_id=uuid.UUID(req.delegate_id),
        role_scope=req.role_scope,
        start_date=req.start_date,
        end_date=req.end_date,
        reason=req.reason,
    )
    db.add(delegation)
    await db.commit()
    return {"id": str(delegation.id), "status": "created"}


# Approval Limits
@router.get("/approval-limits")
async def list_approval_limits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApprovalLimit).where(ApprovalLimit.org_id == current_user.org_id)
        .order_by(ApprovalLimit.min_amount)
    )
    items = []
    for lim in result.scalars().all():
        d = {
            "id": str(lim.id),
            "department": lim.department,
            "budget_type": lim.budget_type,
            "currency": lim.currency,
            "min_amount": float(lim.min_amount),
            "max_amount": float(lim.max_amount) if lim.max_amount else None,
            "approver_id": str(lim.approver_id),
            "approver_role": lim.approver_role,
            "priority": lim.priority,
        }
        u_res = await db.execute(select(User).where(User.id == lim.approver_id))
        u = u_res.scalar_one_or_none()
        d["approver_name"] = u.full_name if u else ""
        items.append(d)
    return items


@router.post("/approval-limits")
async def create_approval_limit(
    req: ApprovalLimitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit = ApprovalLimit(
        org_id=current_user.org_id,
        department=req.department,
        budget_type=req.budget_type,
        currency=req.currency,
        min_amount=req.min_amount,
        max_amount=req.max_amount,
        approver_id=uuid.UUID(req.approver_id),
        approver_role=req.approver_role,
        priority=req.priority,
    )
    db.add(limit)
    await db.commit()
    return {"id": str(limit.id), "status": "created"}


@router.delete("/approval-limits/{limit_id}")
async def delete_approval_limit(
    limit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ApprovalLimit).where(ApprovalLimit.id == limit_id))
    limit = result.scalar_one_or_none()
    if not limit:
        raise HTTPException(404, "Limit not found")
    await db.delete(limit)
    await db.commit()
    return {"status": "deleted"}
