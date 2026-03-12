from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import csv
import io
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models.user import User
from app.models.instance import AuditEvent
from app.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_events(
    instance_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AuditEvent).where(AuditEvent.org_id == current_user.org_id)

    if instance_id:
        query = query.where(AuditEvent.process_instance_id == uuid.UUID(instance_id))
    if user_id:
        query = query.where(AuditEvent.actor_id == uuid.UUID(user_id))
    if event_type:
        query = query.where(AuditEvent.event_type.contains(event_type))

    query = query.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    out = []
    for e in events:
        out.append({
            "id": str(e.id),
            "event_type": e.event_type,
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "actor_email": e.actor_email,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "payload": e.payload,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "instance_id": str(e.process_instance_id) if e.process_instance_id else None,
        })
    return out


@router.get("/export")
async def export_audit_csv(
    instance_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AuditEvent).where(AuditEvent.org_id == current_user.org_id)
    if instance_id:
        query = query.where(AuditEvent.process_instance_id == uuid.UUID(instance_id))
    query = query.order_by(AuditEvent.created_at.desc()).limit(5000)

    result = await db.execute(query)
    events = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "event_type", "actor_id", "actor_email", "entity_type", "entity_id", "payload", "created_at"])
    for e in events:
        writer.writerow([
            str(e.id), e.event_type,
            str(e.actor_id) if e.actor_id else "",
            e.actor_email or "",
            e.entity_type or "", e.entity_id or "",
            str(e.payload),
            e.created_at.isoformat() if e.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_events.csv"},
    )
