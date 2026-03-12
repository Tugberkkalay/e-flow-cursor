from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


def _field(
    key: str,
    label: str,
    field_type: str,
    *,
    required: bool = False,
    options: list[str] | None = None,
    calculation: str | None = None,
    rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": field_type,
        "required": required,
        "options": options or [],
        "calculation": calculation,
        "rules": rules or [],
    }


FORM_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "purchase_request",
        "name": "Purchase Request",
        "status": "published",
        "version": 1,
        "schema_json": {
            "title": "Purchase Request Form",
            "fields": [
                _field("request_title", "Request Title", "text", required=True),
                _field("request_type", "Request Type", "dropdown", required=True, options=["Standart", "Abonelik", "Hizmet"]),
                _field("department", "Department", "dropdown", required=True, options=["Operations", "Procurement", "Finance", "Legal"]),
                _field("budget_type", "Budget Type", "dropdown", required=True, options=["default", "capex", "opex"]),
                _field("currency", "Currency", "dropdown", required=True, options=["TRY", "USD", "EUR"]),
                _field("vat_rate", "VAT Rate", "number", required=True),
                _field(
                    "line_items",
                    "Line Items",
                    "line_items_table",
                    required=True,
                    rules=[
                        {"type": "columns", "value": ["item_name", "quantity", "unit_price", "amount"]},
                    ],
                ),
                _field("subtotal", "Subtotal", "money", calculation="{{ sum([item.amount for item in form.line_items]) }}"),
                _field("total_amount", "Total Amount", "money", calculation="{{ calc.total_amount }}"),
            ],
            "rules_builder": {
                "required_if": [
                    {
                        "target": "line_items",
                        "expression": "{{ form.request_type in ['Standart', 'Abonelik', 'Hizmet'] }}",
                    }
                ],
                "visible_if": [],
            },
        },
    },
    {
        "key": "contract_review",
        "name": "Contract Review",
        "status": "published",
        "version": 1,
        "schema_json": {
            "title": "Contract Review Form",
            "fields": [
                _field("contract_title", "Contract Title", "text", required=True),
                _field("supplier_name", "Supplier", "text", required=True),
                _field("contract_amount", "Contract Amount", "money", required=True),
                _field("currency", "Currency", "dropdown", required=True, options=["TRY", "USD", "EUR"]),
                _field("start_date", "Start Date", "date", required=True),
                _field("end_date", "End Date", "date", required=True),
                _field("legal_notes", "Legal Notes", "textarea"),
            ]
        },
    },
    {
        "key": "invoice_intake",
        "name": "Invoice Intake",
        "status": "published",
        "version": 1,
        "schema_json": {
            "title": "Invoice Intake",
            "fields": [
                _field("invoice_no", "Invoice No", "text", required=True),
                _field("supplier_vkn", "Supplier VKN", "text", required=True),
                _field("invoice_amount", "Invoice Amount", "money", required=True),
                _field("currency", "Currency", "dropdown", required=True, options=["TRY", "USD", "EUR"]),
                _field("invoice_date", "Invoice Date", "date", required=True),
                _field("contract_id", "Contract ID", "text"),
            ]
        },
    },
]


def _node(
    node_id: str,
    label: str,
    primitive: str,
    preset: str,
    *,
    category: str,
    config: dict[str, Any] | None = None,
    version: int = 1,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "primitive": primitive,
        "preset": preset,
        "category": category,
        "version": version,
        "config": config or {},
    }


def _edge(source: str, target: str, label: str, condition: str | None = None) -> dict[str, Any]:
    return {
        "id": f"{source}__{target}__{label.lower().replace(' ', '_')}",
        "source": source,
        "target": target,
        "label": label,
        "condition": condition,
    }


FLOW_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "purchase_request_template",
        "name": "Satin Alma Talebi (PR)",
        "description": "PR intake, offer collection, extraction and policy checks.",
        "template_key": "purchase_request",
        "graph_json": {
            "nodes": [
                _node("start", "Form Submit", "Event", "form_submit", category="Triggers", config={"start": True}),
                _node("fill_pr", "Form Fill (PR)", "HumanTask", "form_fill", category="Human Tasks", config={"form_key": "purchase_request", "outcome_namespace": "form"}),
                _node("calculate", "Calculate totals", "ServiceTask", "calculate_totals", category="Data", config={"action": "calculate_pr_totals"}),
                _node("need_offers", "IF amount/request type", "Gateway", "if", category="Logic"),
                _node("upload_offers", "Document Upload", "HumanTask", "document_upload", category="Human Tasks", config={"document_type": "offer", "min_count": 2, "outcome_namespace": "docs"}),
                _node("extract_offers", "AI Extract Offers", "ServiceTask", "ai_extract", category="Document Intelligence", config={"action": "extract_offers"}),
                _node("normalize", "Normalize", "ServiceTask", "normalize", category="Data", config={"action": "normalize_offers"}),
                _node("policy", "Policy Check", "ServiceTask", "policy_check", category="Error & Compliance", config={"action": "policy_check"}),
                _node(
                    "end",
                    "End",
                    "End",
                    "end",
                    category="Events",
                    config={
                        "mappings": {
                            "pr_id": "{{ system.instance_id }}",
                            "total_amount": "{{ calc.total_amount }}",
                            "flags": "{{ flags }}",
                            "offers_count": "{{ docs.offers_count }}",
                        }
                    },
                ),
            ],
            "edges": [
                _edge("start", "fill_pr", "Start"),
                _edge("fill_pr", "calculate", "Next"),
                _edge("calculate", "need_offers", "Evaluate"),
                _edge("need_offers", "upload_offers", "Evet", "{{ calc.total_amount >= 50000 or form.request_type == 'Abonelik' }}"),
                _edge("need_offers", "policy", "Hayir", "{{ not (calc.total_amount >= 50000 or form.request_type == 'Abonelik') }}"),
                _edge("upload_offers", "extract_offers", "Uploaded"),
                _edge("extract_offers", "normalize", "Extracted"),
                _edge("normalize", "policy", "Normalized"),
                _edge("policy", "end", "Complete"),
            ],
        },
    },
    {
        "key": "purchase_to_pay_template",
        "name": "Satin Alma Sureci (P2P)",
        "description": "Offer validation, vendor selection, approvals, PO generation and ERP handoff.",
        "template_key": "purchase_to_pay",
        "graph_json": {
            "nodes": [
                _node("start", "Manual Start", "Event", "manual_start", category="Triggers", config={"start": True}),
                _node("offers_gate", "IF offers >= 2", "Gateway", "if", category="Logic"),
                _node("collect_offers", "Document Upload", "HumanTask", "document_upload", category="Human Tasks", config={"document_type": "offer", "min_count": 2, "outcome_namespace": "docs"}),
                _node("extract_offers", "Extract Offers", "ServiceTask", "ai_extract", category="Document Intelligence", config={"action": "extract_offers"}),
                _node("vendor_selection", "Vendor Selection", "HumanTask", "vendor_selection", category="Human Tasks", config={"assignee_role": "approver", "form_key": "purchase_request", "outcome_namespace": "selection"}),
                _node("limit_approval", "Approval by Limit Matrix", "ApprovalTask", "approval_limit_matrix", category="Approval", config={"strategy": "limit_matrix"}),
                _node("approved_gate", "IF approved?", "Gateway", "if", category="Logic"),
                _node("generate_po", "Generate PO No", "ServiceTask", "generate_po", category="Integrations", config={"action": "generate_po_number"}),
                _node("mock_erp", "HTTP Integration (ERP)", "ServiceTask", "http_request", category="Integrations", config={"action": "mock_http", "endpoint": "mock://erp/purchase-order"}),
                _node("email_notify", "Email Send", "ServiceTask", "email_send", category="Integrations", config={"action": "mock_email"}),
                _node(
                    "end_rejected",
                    "End Rejected",
                    "End",
                    "end",
                    category="Events",
                    config={"status": "rejected", "mappings": {"approval_summary": "{{ approval.summary }}"}},
                ),
                _node(
                    "end_ok",
                    "End",
                    "End",
                    "end",
                    category="Events",
                    config={
                        "mappings": {
                            "po_no": "{{ gen.po_no }}",
                            "supplier_vkn": "{{ selection.supplier_vkn }}",
                            "approval_summary": "{{ approval.summary }}",
                        }
                    },
                ),
            ],
            "edges": [
                _edge("start", "offers_gate", "Check"),
                _edge("offers_gate", "vendor_selection", "Yes", "{{ docs.offers_count >= 2 }}"),
                _edge("offers_gate", "collect_offers", "No", "{{ docs.offers_count < 2 }}"),
                _edge("collect_offers", "extract_offers", "Uploaded"),
                _edge("extract_offers", "vendor_selection", "Ready"),
                _edge("vendor_selection", "limit_approval", "Selected"),
                _edge("limit_approval", "approved_gate", "Decided"),
                _edge("approved_gate", "end_rejected", "NO", "{{ approval.decision != 'approved' }}"),
                _edge("approved_gate", "generate_po", "YES", "{{ approval.decision == 'approved' }}"),
                _edge("generate_po", "mock_erp", "Generated"),
                _edge("mock_erp", "email_notify", "Integrated"),
                _edge("email_notify", "end_ok", "Completed"),
            ],
        },
    },
    {
        "key": "contract_template",
        "name": "Sozlesme Sureci",
        "description": "Contract upload, revision loop, finance approval and signature stub.",
        "template_key": "contract",
        "graph_json": {
            "nodes": [
                _node("start", "Manual Start", "Event", "manual_start", category="Triggers", config={"start": True}),
                _node("upload_contract", "Document Upload ContractDraft v1", "HumanTask", "document_upload", category="Human Tasks", config={"document_type": "contract_draft", "form_key": "contract_review", "outcome_namespace": "docs"}),
                _node("extract_contract", "AI Extract Contract", "ServiceTask", "ai_extract", category="Document Intelligence", config={"action": "extract_contract"}),
                _node("review_legal", "Review Legal", "ApprovalTask", "approval_single", category="Approval", config={"assignee_role": "approver", "target_department": "Legal"}),
                _node("legal_gate", "Legal Decision", "Gateway", "switch", category="Logic"),
                _node("upload_revision", "Upload v2", "HumanTask", "document_upload", category="Human Tasks", config={"document_type": "contract_revision", "form_key": "contract_review", "outcome_namespace": "docs"}),
                _node("approval_finance", "Approval Finance", "ApprovalTask", "approval_single", category="Approval", config={"assignee_role": "approver", "target_department": "Finance"}),
                _node("sign_stub", "Signature", "ServiceTask", "docuseal_stub", category="Integrations", config={"action": "signature_stub"}),
                _node("archive", "Archive Integration", "ServiceTask", "storage", category="Integrations", config={"action": "archive_stub"}),
                _node("timer", "Timer -30d", "Event", "timer", category="Events", config={"kind": "timer", "auto_continue": True}),
                _node(
                    "end_rejected",
                    "End Rejected",
                    "End",
                    "end",
                    category="Events",
                    config={"status": "rejected"},
                ),
                _node(
                    "end",
                    "End",
                    "End",
                    "end",
                    category="Events",
                    config={
                        "mappings": {
                            "contract_id": "{{ system.instance_id }}",
                            "signed_url": "{{ gen.signed_url }}",
                            "dates": "{{ extract.contract_dates }}",
                            "amount": "{{ extract.contract_amount }}",
                        }
                    },
                ),
            ],
            "edges": [
                _edge("start", "upload_contract", "Start"),
                _edge("upload_contract", "extract_contract", "Uploaded"),
                _edge("extract_contract", "review_legal", "Ready"),
                _edge("review_legal", "legal_gate", "Decided"),
                _edge("legal_gate", "upload_revision", "Revision", "{{ approval.decision == 'revision' }}"),
                _edge("legal_gate", "end_rejected", "Reject", "{{ approval.decision == 'rejected' }}"),
                _edge("legal_gate", "approval_finance", "Approve", "{{ approval.decision == 'approved' }}"),
                _edge("upload_revision", "extract_contract", "Loop"),
                _edge("approval_finance", "sign_stub", "Approved"),
                _edge("sign_stub", "archive", "Signed"),
                _edge("archive", "timer", "Archived"),
                _edge("timer", "end", "Reminded"),
            ],
        },
    },
    {
        "key": "invoice_match_template",
        "name": "Siparis / Fatura / Odeme",
        "description": "Invoice intake, extraction, match, dispute and payment handoff.",
        "template_key": "invoice_match",
        "graph_json": {
            "nodes": [
                _node("start", "Manual Start", "Event", "manual_start", category="Triggers", config={"start": True}),
                _node("delivery", "Delivery Acceptance", "HumanTask", "delivery_acceptance", category="Human Tasks", config={"optional": True, "outcome_namespace": "selection"}),
                _node("upload_invoice", "Document Upload Invoice", "HumanTask", "document_upload", category="Human Tasks", config={"document_type": "invoice", "form_key": "invoice_intake", "outcome_namespace": "docs"}),
                _node("extract_invoice", "AI Extract Invoice", "ServiceTask", "ai_extract", category="Document Intelligence", config={"action": "extract_invoice"}),
                _node("match_invoice", "3-Way Match", "ServiceTask", "three_way_match", category="Document Intelligence", config={"action": "match_invoice"}),
                _node("match_gate", "Switch match.status", "Gateway", "switch", category="Logic"),
                _node("payment_approval", "Payment Approval", "ApprovalTask", "approval_single", category="Approval", config={"assignee_role": "approver", "target_department": "Finance"}),
                _node("payment_http", "HTTP Integration Payment", "ServiceTask", "http_request", category="Integrations", config={"action": "mock_payment"}),
                _node("dispute_task", "Dispute Task", "HumanTask", "review_comment", category="Human Tasks", config={"assignee_role": "approver", "target_department": "Finance", "outcome_namespace": "flags"}),
                _node("resume_gate", "Resume or Reject", "Gateway", "if", category="Logic"),
                _node(
                    "end_ok",
                    "End",
                    "End",
                    "end",
                    category="Events",
                    config={
                        "mappings": {
                            "invoice_id": "{{ system.instance_id }}",
                            "match_status": "{{ selection.match_status }}",
                            "mismatch_flags": "{{ flags.mismatch_flags }}",
                            "payment_status": "{{ gen.payment_status }}",
                        }
                    },
                ),
                _node(
                    "end_rejected",
                    "End Rejected",
                    "End",
                    "end",
                    category="Events",
                    config={"status": "rejected", "mappings": {"match_status": "{{ selection.match_status }}"}},
                ),
            ],
            "edges": [
                _edge("start", "delivery", "Start"),
                _edge("delivery", "upload_invoice", "Continue"),
                _edge("upload_invoice", "extract_invoice", "Uploaded"),
                _edge("extract_invoice", "match_invoice", "Extracted"),
                _edge("match_invoice", "match_gate", "Ready"),
                _edge("match_gate", "payment_approval", "matched", "{{ selection.match_status == 'matched' }}"),
                _edge("match_gate", "dispute_task", "mismatch", "{{ selection.match_status in ['mismatch', 'ambiguous'] }}"),
                _edge("payment_approval", "payment_http", "Approved"),
                _edge("payment_http", "end_ok", "Paid"),
                _edge("dispute_task", "resume_gate", "Reviewed"),
                _edge("resume_gate", "match_invoice", "resume", "{{ flags.dispute_outcome == 'resume' }}"),
                _edge("resume_gate", "end_rejected", "reject", "{{ flags.dispute_outcome != 'resume' }}"),
            ],
        },
    },
]


def build_template_catalog() -> list[dict[str, Any]]:
    return deepcopy(FLOW_TEMPLATES)


def build_form_catalog() -> list[dict[str, Any]]:
    return deepcopy(FORM_TEMPLATES)


def template_by_key(key: str) -> dict[str, Any] | None:
    for template in FLOW_TEMPLATES:
        if template["template_key"] == key or template["key"] == key:
            return deepcopy(template)
    return None


def default_context_sample() -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    return {
        "form": {
            "request_type": "Standart",
            "department": "Operations",
            "budget_type": "default",
            "currency": "TRY",
            "line_items": [
                {"item_name": "Laptop", "quantity": 1, "unit_price": 50000, "amount": 50000},
            ],
            "invoice_amount": 12500,
        },
        "docs": {"offers_count": 0, "latest": {"file_name": "demo.pdf"}},
        "extract": {"contract_amount": 250000, "supplier_vkn": "1234567890"},
        "selection": {"supplier_vkn": "1234567890", "match_status": "matched"},
        "approval": {"decision": "approved", "summary": "Demo approval trail"},
        "gen": {"po_no": "PO-2026-0001", "payment_status": "queued"},
        "calc": {"total_amount": 50000, "subtotal": 50000},
        "flags": {"mismatch_flags": []},
        "system": {"now": now, "roles": ["admin"], "requester": {"name": "Demo User"}},
    }
