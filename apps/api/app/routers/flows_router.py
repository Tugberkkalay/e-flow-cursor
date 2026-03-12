import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import ProcessDefinition, ProcessVersion, User
from app.schemas.schemas import FlowCreate, FlowUpdate, FlowOut, FlowVersionOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/flows", tags=["flows"])


@router.get("", response_model=list[FlowOut])
def list_flows(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flows = db.query(ProcessDefinition).filter(
        ProcessDefinition.org_id == user.org_id
    ).order_by(ProcessDefinition.updated_at.desc()).all()
    return [FlowOut.model_validate(f) for f in flows]


@router.post("", response_model=FlowOut)
def create_flow(req: FlowCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flow = ProcessDefinition(
        id=str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        status="draft",
        current_version=1,
        org_id=user.org_id,
    )
    db.add(flow)

    version = ProcessVersion(
        id=str(uuid.uuid4()),
        flow_id=flow.id,
        version=1,
        graph_json=req.graph_json or {"nodes": [], "edges": []},
        status="draft",
    )
    db.add(version)
    db.commit()
    db.refresh(flow)
    return FlowOut.model_validate(flow)


@router.get("/{flow_id}", response_model=FlowOut)
def get_flow(flow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flow = db.query(ProcessDefinition).get(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return FlowOut.model_validate(flow)


@router.put("/{flow_id}", response_model=FlowOut)
def update_flow(flow_id: str, req: FlowUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flow = db.query(ProcessDefinition).get(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    if req.name is not None:
        flow.name = req.name
    if req.description is not None:
        flow.description = req.description

    if req.graph_json is not None:
        latest_version = db.query(ProcessVersion).filter(
            ProcessVersion.flow_id == flow_id,
            ProcessVersion.status == "draft",
        ).order_by(ProcessVersion.version.desc()).first()

        if latest_version:
            latest_version.graph_json = req.graph_json
        else:
            new_version = ProcessVersion(
                id=str(uuid.uuid4()),
                flow_id=flow_id,
                version=flow.current_version + 1,
                graph_json=req.graph_json,
                status="draft",
            )
            db.add(new_version)
            flow.current_version += 1

    flow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(flow)
    return FlowOut.model_validate(flow)


@router.post("/{flow_id}/publish", response_model=FlowOut)
def publish_flow(flow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flow = db.query(ProcessDefinition).get(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    latest = db.query(ProcessVersion).filter(
        ProcessVersion.flow_id == flow_id,
    ).order_by(ProcessVersion.version.desc()).first()

    if latest:
        latest.status = "published"

    flow.status = "published"
    flow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(flow)
    return FlowOut.model_validate(flow)


@router.get("/{flow_id}/versions", response_model=list[FlowVersionOut])
def list_versions(flow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    versions = db.query(ProcessVersion).filter(
        ProcessVersion.flow_id == flow_id,
    ).order_by(ProcessVersion.version.desc()).all()
    return [FlowVersionOut.model_validate(v) for v in versions]
