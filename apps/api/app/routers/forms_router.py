import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import FormDefinition, User
from app.schemas.schemas import FormCreate, FormUpdate, FormOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/forms", tags=["forms"])


@router.get("", response_model=list[FormOut])
def list_forms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    forms = db.query(FormDefinition).filter(
        FormDefinition.org_id == user.org_id
    ).order_by(FormDefinition.updated_at.desc()).all()
    return [FormOut.model_validate(f) for f in forms]


@router.post("", response_model=FormOut)
def create_form(req: FormCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form = FormDefinition(
        id=str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        fields=req.fields or [],
        org_id=user.org_id,
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    return FormOut.model_validate(form)


@router.get("/{form_id}", response_model=FormOut)
def get_form(form_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form = db.query(FormDefinition).get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return FormOut.model_validate(form)


@router.put("/{form_id}", response_model=FormOut)
def update_form(form_id: str, req: FormUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form = db.query(FormDefinition).get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    if req.name is not None:
        form.name = req.name
    if req.description is not None:
        form.description = req.description
    if req.fields is not None:
        form.fields = req.fields

    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    return FormOut.model_validate(form)


@router.post("/{form_id}/publish", response_model=FormOut)
def publish_form(form_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form = db.query(FormDefinition).get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    form.status = "published"
    form.version += 1
    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    return FormOut.model_validate(form)
