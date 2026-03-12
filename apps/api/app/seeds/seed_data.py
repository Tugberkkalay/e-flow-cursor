from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.models import ApprovalLimit, FormDefinition, ProcessDefinition, ProcessVersion, User

settings = get_settings()


def _upsert_user(db: Session, **payload: str) -> None:
    existing = db.execute(select(User).where(User.email == payload["email"])).scalar_one_or_none()
    if existing:
        return
    db.add(User(org_id=settings.default_org_id, **payload))


def _create_template_flow(db: Session, code: str, name: str, graph_json: dict) -> None:
    existing = db.execute(select(ProcessDefinition).where(ProcessDefinition.code == code)).scalar_one_or_none()
    if existing:
        return
    definition = ProcessDefinition(
        org_id=settings.default_org_id,
        code=code,
        name=name,
        description=f"{name} template",
    )
    db.add(definition)
    db.flush()
    version = ProcessVersion(
        org_id=settings.default_org_id,
        process_definition_id=definition.id,
        version_no=1,
        status="published",
        graph_json=graph_json,
    )
    db.add(version)


def _create_form(db: Session, code: str, name: str, schema_json: dict) -> None:
    existing = db.execute(select(FormDefinition).where(FormDefinition.code == code)).scalar_one_or_none()
    if existing:
        return
    db.add(
        FormDefinition(
            org_id=settings.default_org_id,
            code=code,
            name=name,
            schema_json=schema_json,
            status="published",
            version_no=1,
        )
    )


def seed_all(db: Session) -> None:
    _upsert_user(
        db,
        email="admin@eflow.local",
        full_name="System Admin",
        role="admin",
        department="management",
        cost_center="ADM",
        manager_id=None,
        hashed_password=get_password_hash("admin123"),
    )
    _upsert_user(
        db,
        email="procurement@eflow.local",
        full_name="Procurement Approver",
        role="procurement",
        department="procurement",
        cost_center="PRC",
        manager_id=None,
        hashed_password=get_password_hash("demo123"),
    )
    _upsert_user(
        db,
        email="finance@eflow.local",
        full_name="Finance Approver",
        role="finance",
        department="finance",
        cost_center="FIN",
        manager_id=None,
        hashed_password=get_password_hash("demo123"),
    )
    _upsert_user(
        db,
        email="legal@eflow.local",
        full_name="Legal Reviewer",
        role="legal",
        department="legal",
        cost_center="LGL",
        manager_id=None,
        hashed_password=get_password_hash("demo123"),
    )

    existing_limits = db.execute(select(ApprovalLimit).where(ApprovalLimit.org_id == settings.default_org_id)).scalars().all()
    if not existing_limits:
        db.add_all(
            [
                ApprovalLimit(
                    org_id=settings.default_org_id,
                    department="general",
                    budget_type="capex",
                    currency="TRY",
                    min_amount=0,
                    max_amount=50000,
                    approver_role="manager",
                ),
                ApprovalLimit(
                    org_id=settings.default_org_id,
                    department="general",
                    budget_type="capex",
                    currency="TRY",
                    min_amount=50000,
                    max_amount=250000,
                    approver_role="director",
                ),
                ApprovalLimit(
                    org_id=settings.default_org_id,
                    department="general",
                    budget_type="capex",
                    currency="TRY",
                    min_amount=250000,
                    max_amount=999999999,
                    approver_role="cfo",
                ),
            ]
        )

    _create_form(
        db,
        code="pr_form",
        name="Satın Alma Talebi Formu",
        schema_json={
            "fields": [
                {"key": "request_type", "type": "dropdown", "options": ["Normal", "Abonelik"]},
                {"key": "department", "type": "text"},
                {"key": "total_amount", "type": "money"},
                {"key": "currency", "type": "dropdown", "options": ["TRY", "USD", "EUR"]},
                {"key": "line_items", "type": "line_items"},
            ]
        },
    )

    # 4.1 PR Template
    _create_template_flow(
        db,
        code="tpl_pr_request",
        name="Satın Alma Talebi (PR)",
        graph_json={
            "nodes": [
                {"id": "start", "type": "start", "data": {"engineType": "start"}},
                {"id": "form_fill", "type": "humanTask", "data": {"engineType": "formFill", "title": "Form Fill (PR)"}},
                {"id": "calc", "type": "serviceTask", "data": {"engineType": "calculate", "setContext": {"calc.total": "{{ form.total_amount }}", "flags.needs_offer": "{{ form.total_amount >= 50000 or form.request_type == 'Abonelik' }}"}}},
                {"id": "if_offer", "type": "gateway", "data": {"engineType": "if"}},
                {"id": "doc_upload", "type": "humanTask", "data": {"engineType": "documentUpload", "title": "Upload >=2 Offers"}},
                {"id": "extract", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "extract.offers"}},
                {"id": "policy", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "flags.policy"}},
                {"id": "end", "type": "end", "data": {"engineType": "end", "exportMapping": {"pr_id": "{{ gen.pr_id or 'PR-' + str(len(form)) }}", "total_amount": "{{ form.total_amount }}", "flags": "{{ flags }}", "offers_count": "{{ docs.offers_count or 0 }}"}}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "form_fill"},
                {"id": "e2", "source": "form_fill", "target": "calc"},
                {"id": "e3", "source": "calc", "target": "if_offer"},
                {"id": "e4", "source": "if_offer", "target": "doc_upload", "label": "Evet", "data": {"condition": "flags.needs_offer == True"}},
                {"id": "e5", "source": "if_offer", "target": "policy", "label": "Hayır", "data": {"default": True}},
                {"id": "e6", "source": "doc_upload", "target": "extract"},
                {"id": "e7", "source": "extract", "target": "policy"},
                {"id": "e8", "source": "policy", "target": "end"},
            ],
        },
    )

    # 4.2 PR -> P2P Template
    _create_template_flow(
        db,
        code="tpl_p2p",
        name="Satın Alma Süreci (P2P)",
        graph_json={
            "nodes": [
                {"id": "start", "type": "start", "data": {"engineType": "start"}},
                {"id": "if_offers", "type": "gateway", "data": {"engineType": "if"}},
                {"id": "upload", "type": "humanTask", "data": {"engineType": "documentUpload", "title": "Upload offers"}},
                {"id": "extract", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "extract.offers"}},
                {"id": "selection", "type": "humanTask", "data": {"engineType": "humanTask", "title": "Vendor Selection", "assigneeRole": "procurement"}},
                {"id": "approval", "type": "approvalTask", "data": {"engineType": "approval", "title": "Limit Approval", "byLimitMatrix": True}},
                {"id": "if_approved", "type": "gateway", "data": {"engineType": "if"}},
                {"id": "gen_po", "type": "serviceTask", "data": {"engineType": "setFields", "setContext": {"gen.po_no": "PO-{{ form.department or 'GEN' }}-2026"}}},
                {"id": "erp", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "gen.erp_result"}},
                {"id": "mail", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "gen.email_result"}},
                {"id": "end_rej", "type": "end", "data": {"engineType": "end", "exportMapping": {"status": "{{ 'rejected' }}"}}},
                {"id": "end_ok", "type": "end", "data": {"engineType": "end", "exportMapping": {"po_no": "{{ gen.po_no }}", "supplier_vkn": "{{ selection.supplier_vkn or '' }}", "approval_summary": "{{ approval }}"}}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "if_offers"},
                {"id": "e2", "source": "if_offers", "target": "selection", "data": {"condition": "docs.offers_count >= 2"}},
                {"id": "e3", "source": "if_offers", "target": "upload", "data": {"default": True}},
                {"id": "e4", "source": "upload", "target": "extract"},
                {"id": "e5", "source": "extract", "target": "selection"},
                {"id": "e6", "source": "selection", "target": "approval"},
                {"id": "e7", "source": "approval", "target": "if_approved"},
                {"id": "e8", "source": "if_approved", "target": "end_rej", "label": "Reddedildi", "data": {"condition": "approval.decision == 'reject'"}},
                {"id": "e9", "source": "if_approved", "target": "gen_po", "label": "Onaylandı", "data": {"default": True}},
                {"id": "e10", "source": "gen_po", "target": "erp"},
                {"id": "e11", "source": "erp", "target": "mail"},
                {"id": "e12", "source": "mail", "target": "end_ok"},
            ],
        },
    )

    # 4.3 Contract Template
    _create_template_flow(
        db,
        code="tpl_contract",
        name="Sözleşme Süreci",
        graph_json={
            "nodes": [
                {"id": "start", "type": "start", "data": {"engineType": "start"}},
                {"id": "upload_v1", "type": "humanTask", "data": {"engineType": "documentUpload", "title": "Upload Draft v1"}},
                {"id": "extract", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "extract.contract"}},
                {"id": "review_legal", "type": "approvalTask", "data": {"engineType": "approval", "title": "Review Legal", "assigneeRole": "legal"}},
                {"id": "if_legal", "type": "gateway", "data": {"engineType": "switch", "mode": "switch", "expression": "approval.decision"}},
                {"id": "upload_v2", "type": "humanTask", "data": {"engineType": "documentUpload", "title": "Upload Revision v2"}},
                {"id": "approval_fin", "type": "approvalTask", "data": {"engineType": "approval", "title": "Approval Finance", "assigneeRole": "finance"}},
                {"id": "esign", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "gen.signed_url"}},
                {"id": "archive", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "gen.archive_id"}},
                {"id": "timer", "type": "event", "data": {"engineType": "event"}},
                {"id": "end_reject", "type": "end", "data": {"engineType": "end", "exportMapping": {"status": "{{ 'rejected' }}"}}},
                {"id": "end_ok", "type": "end", "data": {"engineType": "end", "exportMapping": {"contract_id": "{{ gen.archive_id }}", "signed_url": "{{ gen.signed_url }}", "dates": "{{ {'notify': 'end_date-30'} }}", "amount": "{{ form.total_amount or 0 }}"}}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "upload_v1"},
                {"id": "e2", "source": "upload_v1", "target": "extract"},
                {"id": "e3", "source": "extract", "target": "review_legal"},
                {"id": "e4", "source": "review_legal", "target": "if_legal"},
                {"id": "e5", "source": "if_legal", "target": "upload_v2", "data": {"case": "revision"}},
                {"id": "e6", "source": "if_legal", "target": "end_reject", "data": {"case": "reject"}},
                {"id": "e7", "source": "if_legal", "target": "approval_fin", "data": {"default": True}},
                {"id": "e8", "source": "upload_v2", "target": "extract"},
                {"id": "e9", "source": "approval_fin", "target": "esign"},
                {"id": "e10", "source": "esign", "target": "archive"},
                {"id": "e11", "source": "archive", "target": "timer"},
                {"id": "e12", "source": "timer", "target": "end_ok"},
            ],
        },
    )

    # 4.4 Invoice / Payment Template
    _create_template_flow(
        db,
        code="tpl_invoice_payment",
        name="Sipariş/Fatura/Ödeme",
        graph_json={
            "nodes": [
                {"id": "start", "type": "start", "data": {"engineType": "start"}},
                {"id": "acceptance", "type": "humanTask", "data": {"engineType": "humanTask", "title": "Delivery Acceptance"}},
                {"id": "upload_invoice", "type": "humanTask", "data": {"engineType": "documentUpload", "title": "Upload Invoice"}},
                {"id": "extract", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "extract.invoice"}},
                {"id": "match", "type": "serviceTask", "data": {"engineType": "setFields", "setContext": {"selection.match_status": "{{ 'matched' if form.total_amount and form.total_amount < 100000 else 'mismatch' }}"}}},
                {"id": "switch", "type": "gateway", "data": {"engineType": "switch", "mode": "switch", "expression": "selection.match_status"}},
                {"id": "payment_approval", "type": "approvalTask", "data": {"engineType": "approval", "title": "Payment Approval", "assigneeRole": "finance"}},
                {"id": "payment_http", "type": "serviceTask", "data": {"engineType": "service", "outputKey": "gen.payment_result"}},
                {"id": "dispute", "type": "humanTask", "data": {"engineType": "humanTask", "title": "Dispute Task", "assigneeRole": "finance"}},
                {"id": "end", "type": "end", "data": {"engineType": "end", "exportMapping": {"invoice_id": "{{ gen.invoice_id or 'INV-001' }}", "match_status": "{{ selection.match_status }}", "mismatch_flags": "{{ flags }}", "payment_status": "{{ 'paid' if gen.payment_result else 'pending' }}"}}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "acceptance"},
                {"id": "e2", "source": "acceptance", "target": "upload_invoice"},
                {"id": "e3", "source": "upload_invoice", "target": "extract"},
                {"id": "e4", "source": "extract", "target": "match"},
                {"id": "e5", "source": "match", "target": "switch"},
                {"id": "e6", "source": "switch", "target": "payment_approval", "data": {"case": "matched"}},
                {"id": "e7", "source": "switch", "target": "dispute", "data": {"default": True}},
                {"id": "e8", "source": "payment_approval", "target": "payment_http"},
                {"id": "e9", "source": "payment_http", "target": "end"},
                {"id": "e10", "source": "dispute", "target": "end"},
            ],
        },
    )

    db.commit()
