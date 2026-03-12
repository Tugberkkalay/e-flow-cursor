from fastapi import APIRouter
from app.schemas.schemas import ExpressionPreview, ExpressionResult, ContextSchema
from app.engine.expressions import resolve, get_context_keys

router = APIRouter(prefix="/api", tags=["expressions"])


@router.post("/expressions/preview", response_model=ExpressionResult)
def preview_expression(req: ExpressionPreview):
    try:
        result = resolve(req.expression, req.context)
        return ExpressionResult(result=result)
    except Exception as e:
        return ExpressionResult(result=None, error=str(e))


@router.get("/context/schema", response_model=ContextSchema)
def context_schema():
    sample_context = {
        "form": {
            "title": "string",
            "description": "string",
            "request_type": "string",
            "department": "string",
            "quantity": "number",
            "unit_price": "number",
            "vat_rate": "number",
            "total_amount": "number",
            "currency": "string",
            "needed_by": "date",
            "urgent": "boolean",
        },
        "docs": {
            "offers_count": "number",
            "latest": "object",
        },
        "extract": {
            "vendor_name": "string",
            "vendor_vkn": "string",
            "amount": "number",
            "invoice_no": "string",
            "contract_amount": "number",
        },
        "selection": {
            "supplier_vkn": "string",
            "supplier_name": "string",
            "justification": "string",
        },
        "approval": {
            "decision": "string",
            "comment": "string",
            "approver_id": "string",
            "approver_name": "string",
            "amount": "number",
        },
        "gen": {
            "po_no": "string",
            "payment_status": "string",
        },
        "calc": {
            "total_amount": "number",
            "currency_normalized": "boolean",
        },
        "flags": {
            "policy_check": "string",
            "match_status": "string",
            "mismatch": "object",
        },
        "system": {
            "requester_id": "string",
            "requester_name": "string",
            "requester_email": "string",
            "instance_id": "string",
            "now": "datetime",
            "org_id": "string",
            "year": "string",
            "seq": "string",
        },
    }
    return ContextSchema(namespaces=sample_context)
