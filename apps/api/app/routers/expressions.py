from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any

from app.models.user import User
from app.auth import get_current_user
from app.engine.expression import ExpressionEngine

router = APIRouter(prefix="/expressions", tags=["expressions"])


class PreviewRequest(BaseModel):
    expression: str
    context: dict = {}


@router.post("/preview")
async def preview_expression(
    req: PreviewRequest,
    current_user: User = Depends(get_current_user),
):
    engine = ExpressionEngine()
    try:
        result = engine.resolve(req.expression, req.context)
        return {"result": result, "type": type(result).__name__, "error": None}
    except Exception as e:
        return {"result": None, "type": "error", "error": str(e)}


@router.get("/context/schema")
async def get_context_schema(
    current_user: User = Depends(get_current_user),
):
    """Return the standard context schema for autocomplete."""
    sample_context = {
        "form": {
            "title": "string",
            "total_amount": 0.0,
            "currency": "TRY",
            "request_type": "string",
            "requester_department": "string",
            "vendor_name": "string",
            "description": "string",
        },
        "approval": {
            "last_decision": "approved|rejected|revision_requested",
            "last_comment": "string",
        },
        "calc": {
            "normalized_amount": 0.0,
            "vat_amount": 0.0,
            "total_with_vat": 0.0,
        },
        "flags": {
            "match_status": "matched|mismatch|ambiguous",
            "policy_flags": [],
        },
        "gen": {
            "po_no": "string",
        },
        "docs": {
            "invoice": {"amount": 0.0, "date": "string", "vendor_vkn": "string"},
            "offer": {"amount": 0.0, "vendor_name": "string"},
        },
        "system": {
            "started_by": "user_id",
            "started_at": "datetime",
        },
    }
    return ExpressionEngine.get_context_schema(sample_context)
