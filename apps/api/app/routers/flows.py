from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Any
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.flow import ProcessDefinition, ProcessVersion
from app.auth import get_current_user

router = APIRouter(prefix="/flows", tags=["flows"])


class FlowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = []
    graph_json: Optional[dict] = None


class FlowUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    graph_json: Optional[dict] = None
    form_id: Optional[str] = None
    exported_outputs: Optional[list] = None


def _def_out(d: ProcessDefinition, latest_version: ProcessVersion | None = None) -> dict:
    out = {
        "id": str(d.id),
        "name": d.name,
        "description": d.description,
        "category": d.category,
        "tags": d.tags or [],
        "is_template": d.is_template,
        "template_key": d.template_key,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }
    if latest_version:
        out["latest_version"] = {
            "id": str(latest_version.id),
            "version_number": latest_version.version_number,
            "status": latest_version.status,
            "graph_json": latest_version.graph_json,
            "form_id": str(latest_version.form_id) if latest_version.form_id else None,
            "exported_outputs": latest_version.exported_outputs or [],
        }
    return out


@router.get("")
async def list_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProcessDefinition).where(ProcessDefinition.org_id == current_user.org_id)
        .order_by(ProcessDefinition.updated_at.desc())
    )
    definitions = result.scalars().all()

    out = []
    for d in definitions:
        ver_result = await db.execute(
            select(ProcessVersion)
            .where(ProcessVersion.definition_id == d.id)
            .order_by(ProcessVersion.version_number.desc())
            .limit(1)
        )
        latest = ver_result.scalar_one_or_none()
        out.append(_def_out(d, latest))
    return out


@router.post("")
async def create_flow(
    req: FlowCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    definition = ProcessDefinition(
        org_id=current_user.org_id,
        name=req.name,
        description=req.description,
        category=req.category,
        tags=req.tags,
        created_by=current_user.id,
    )
    db.add(definition)
    await db.flush()

    version = ProcessVersion(
        org_id=current_user.org_id,
        definition_id=definition.id,
        version_number=1,
        status="draft",
        graph_json=req.graph_json or {"nodes": [], "edges": []},
    )
    db.add(version)
    await db.commit()
    await db.refresh(definition)
    await db.refresh(version)
    return _def_out(definition, version)


@router.get("/{flow_id}")
async def get_flow(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProcessDefinition).where(ProcessDefinition.id == flow_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(404, "Flow not found")

    ver_result = await db.execute(
        select(ProcessVersion)
        .where(ProcessVersion.definition_id == definition.id)
        .order_by(ProcessVersion.version_number.desc())
        .limit(1)
    )
    latest = ver_result.scalar_one_or_none()
    return _def_out(definition, latest)


@router.put("/{flow_id}")
async def update_flow(
    flow_id: uuid.UUID,
    req: FlowUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProcessDefinition).where(ProcessDefinition.id == flow_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(404, "Flow not found")

    if req.name:
        definition.name = req.name
    if req.description is not None:
        definition.description = req.description
    definition.updated_at = datetime.utcnow()

    # Update latest draft version
    ver_result = await db.execute(
        select(ProcessVersion)
        .where(ProcessVersion.definition_id == definition.id, ProcessVersion.status == "draft")
        .order_by(ProcessVersion.version_number.desc())
        .limit(1)
    )
    version = ver_result.scalar_one_or_none()
    if version:
        if req.graph_json is not None:
            version.graph_json = req.graph_json
        if req.form_id is not None:
            try:
                version.form_id = uuid.UUID(req.form_id)
            except Exception:
                pass
        if req.exported_outputs is not None:
            version.exported_outputs = req.exported_outputs
        version.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(definition)
    return _def_out(definition, version)


@router.post("/{flow_id}/publish")
async def publish_flow(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProcessDefinition).where(ProcessDefinition.id == flow_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(404, "Flow not found")

    # Archive previous published versions
    prev_result = await db.execute(
        select(ProcessVersion)
        .where(ProcessVersion.definition_id == definition.id, ProcessVersion.status == "published")
    )
    for prev in prev_result.scalars().all():
        prev.status = "archived"

    # Publish latest draft
    ver_result = await db.execute(
        select(ProcessVersion)
        .where(ProcessVersion.definition_id == definition.id, ProcessVersion.status == "draft")
        .order_by(ProcessVersion.version_number.desc())
        .limit(1)
    )
    version = ver_result.scalar_one_or_none()
    if not version:
        raise HTTPException(400, "No draft version to publish")

    version.status = "published"
    version.published_at = datetime.utcnow()
    version.published_by = current_user.id
    await db.commit()
    return _def_out(definition, version)


@router.get("/{flow_id}/versions")
async def list_versions(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProcessVersion)
        .where(ProcessVersion.definition_id == flow_id)
        .order_by(ProcessVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "version_number": v.version_number,
            "status": v.status,
            "graph_json": v.graph_json,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
