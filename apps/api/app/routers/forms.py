from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.form import FormDefinition, FormVersion
from app.auth import get_current_user

router = APIRouter(prefix="/forms", tags=["forms"])


class FormCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    fields_json: list = []
    rules_json: list = []


class FormUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fields_json: Optional[list] = None
    rules_json: Optional[list] = None


def _form_out(d: FormDefinition, latest: FormVersion | None = None) -> dict:
    out = {
        "id": str(d.id),
        "name": d.name,
        "description": d.description,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }
    if latest:
        out["latest_version"] = {
            "id": str(latest.id),
            "version_number": latest.version_number,
            "status": latest.status,
            "fields_json": latest.fields_json or [],
            "rules_json": latest.rules_json or [],
        }
    return out


@router.get("")
async def list_forms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FormDefinition).where(FormDefinition.org_id == current_user.org_id)
        .order_by(FormDefinition.updated_at.desc())
    )
    defs = result.scalars().all()
    out = []
    for d in defs:
        ver_result = await db.execute(
            select(FormVersion).where(FormVersion.definition_id == d.id)
            .order_by(FormVersion.version_number.desc()).limit(1)
        )
        latest = ver_result.scalar_one_or_none()
        out.append(_form_out(d, latest))
    return out


@router.post("")
async def create_form(
    req: FormCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    definition = FormDefinition(
        org_id=current_user.org_id,
        name=req.name,
        description=req.description,
        created_by=current_user.id,
    )
    db.add(definition)
    await db.flush()

    version = FormVersion(
        org_id=current_user.org_id,
        definition_id=definition.id,
        version_number=1,
        status="draft",
        fields_json=req.fields_json,
        rules_json=req.rules_json,
    )
    db.add(version)
    await db.commit()
    await db.refresh(definition)
    return _form_out(definition, version)


@router.get("/{form_id}")
async def get_form(
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(FormDefinition).where(FormDefinition.id == form_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(404, "Form not found")
    ver_result = await db.execute(
        select(FormVersion).where(FormVersion.definition_id == definition.id)
        .order_by(FormVersion.version_number.desc()).limit(1)
    )
    return _form_out(definition, ver_result.scalar_one_or_none())


@router.put("/{form_id}")
async def update_form(
    form_id: uuid.UUID,
    req: FormUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(FormDefinition).where(FormDefinition.id == form_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(404, "Form not found")

    if req.name:
        definition.name = req.name
    if req.description is not None:
        definition.description = req.description
    definition.updated_at = datetime.utcnow()

    ver_result = await db.execute(
        select(FormVersion).where(FormVersion.definition_id == definition.id, FormVersion.status == "draft")
        .order_by(FormVersion.version_number.desc()).limit(1)
    )
    version = ver_result.scalar_one_or_none()
    if version:
        if req.fields_json is not None:
            version.fields_json = req.fields_json
        if req.rules_json is not None:
            version.rules_json = req.rules_json
        version.updated_at = datetime.utcnow()

    await db.commit()
    return _form_out(definition, version)


@router.post("/{form_id}/publish")
async def publish_form(
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(FormDefinition).where(FormDefinition.id == form_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(404, "Form not found")

    ver_result = await db.execute(
        select(FormVersion).where(FormVersion.definition_id == definition.id, FormVersion.status == "draft")
        .order_by(FormVersion.version_number.desc()).limit(1)
    )
    version = ver_result.scalar_one_or_none()
    if not version:
        raise HTTPException(400, "No draft to publish")
    version.status = "published"
    version.published_at = datetime.utcnow()
    await db.commit()
    return _form_out(definition, version)
