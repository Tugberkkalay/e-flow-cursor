"""Seed database with demo users, approval limits, and 4 domain flow templates."""
import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.config import settings
from app.database import Base
from app.models.user import User, ApprovalLimit
from app.models.flow import ProcessDefinition, ProcessVersion
from app.models.form import FormDefinition, FormVersion
from app.auth import hash_password

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# ──────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────
USERS = [
    {
        "email": "admin@eflow.com",
        "full_name": "Ali Admin",
        "password": "admin123",
        "role": "admin",
        "department": "IT",
        "cost_center": "IT-001",
        "avatar_initials": "AA",
    },
    {
        "email": "procurement@eflow.com",
        "full_name": "Priya Procurement",
        "password": "proc123",
        "role": "procurement",
        "department": "Satın Alma",
        "cost_center": "SA-001",
        "avatar_initials": "PP",
    },
    {
        "email": "finance@eflow.com",
        "full_name": "Fatih Finance",
        "password": "fin123",
        "role": "finance",
        "department": "Finans",
        "cost_center": "FN-001",
        "avatar_initials": "FF",
    },
    {
        "email": "legal@eflow.com",
        "full_name": "Leyla Legal",
        "password": "leg123",
        "role": "legal",
        "department": "Hukuk",
        "cost_center": "HK-001",
        "avatar_initials": "LL",
    },
    {
        "email": "manager@eflow.com",
        "full_name": "Mert Manager",
        "password": "mgr123",
        "role": "approver",
        "department": "Satın Alma",
        "cost_center": "SA-001",
        "avatar_initials": "MM",
    },
    {
        "email": "director@eflow.com",
        "full_name": "Diana Director",
        "password": "dir123",
        "role": "approver",
        "department": "Yönetim",
        "cost_center": "YN-001",
        "avatar_initials": "DD",
    },
    {
        "email": "cfo@eflow.com",
        "full_name": "Carlos CFO",
        "password": "cfo123",
        "role": "approver",
        "department": "Finans",
        "cost_center": "FN-001",
        "avatar_initials": "CC",
    },
]


# ──────────────────────────────────────────────
# PR FORM
# ──────────────────────────────────────────────
PR_FORM_FIELDS = [
    {"id": "title", "key": "title", "label": "Talep Başlığı", "type": "text", "required": True},
    {"id": "request_type", "key": "request_type", "label": "Talep Tipi", "type": "dropdown",
     "options": ["Mal Alımı", "Hizmet Alımı", "Abonelik", "Danışmanlık"], "required": True},
    {"id": "description", "key": "description", "label": "Açıklama", "type": "textarea", "required": True},
    {"id": "vendor_name", "key": "vendor_name", "label": "Tedarikçi Adı", "type": "text"},
    {"id": "total_amount", "key": "total_amount", "label": "Toplam Tutar", "type": "money", "required": True},
    {"id": "currency", "key": "currency", "label": "Para Birimi", "type": "dropdown",
     "options": ["TRY", "USD", "EUR"], "default": "TRY", "required": True},
    {"id": "requester_department", "key": "requester_department", "label": "Talep Eden Birim", "type": "text"},
    {"id": "needed_date", "key": "needed_date", "label": "İhtiyaç Tarihi", "type": "date"},
    {"id": "items", "key": "items", "label": "Kalemler", "type": "line_items",
     "columns": [
         {"key": "item_name", "label": "Kalem Adı", "type": "text"},
         {"key": "quantity", "label": "Miktar", "type": "number"},
         {"key": "unit_price", "label": "Birim Fiyat", "type": "money"},
         {"key": "total", "label": "Toplam", "type": "money", "calculated": True, "formula": "quantity * unit_price"},
     ]},
    {"id": "justification", "key": "justification", "label": "İhtiyaç Gerekçesi", "type": "textarea"},
]


# ──────────────────────────────────────────────
# FLOW GRAPH HELPERS
# ──────────────────────────────────────────────
def node(id: str, type: str, engine_type: str, label: str, x: float, y: float, config: dict = None, category: str = "triggers") -> dict:
    return {
        "id": id,
        "type": "eflowNode",
        "position": {"x": x, "y": y},
        "data": {
            "label": label,
            "engineType": engine_type,
            "category": category,
            "config": config or {},
        },
    }


def edge(id: str, source: str, target: str, label: str = "", source_handle: str = None) -> dict:
    e = {
        "id": id,
        "source": source,
        "target": target,
        "type": "smoothstep",
        "animated": False,
    }
    if label:
        e["label"] = label
    if source_handle:
        e["sourceHandle"] = source_handle
    return e


# ──────────────────────────────────────────────
# TEMPLATE 1: Satın Alma Talebi (PR)
# ──────────────────────────────────────────────
PR_GRAPH = {
    "nodes": [
        node("start", "eflowNode", "FormSubmitTrigger", "Form Gönder", 100, 50, {}, "triggers"),
        node("form_fill", "eflowNode", "FormFill", "PR Formu Doldur", 100, 180, {
            "title": "Satın Alma Talep Formu",
            "assignee_role": "viewer",
        }, "human"),
        node("calculate", "eflowNode", "Calculate", "Toplamları Hesapla", 100, 310, {
            "calculations": [
                {"output_field": "calc.vat_amount", "expression": "{{ form.total_amount }} * 0.20"},
                {"output_field": "calc.total_with_vat", "expression": "{{ form.total_amount }} * 1.20"},
            ]
        }, "data"),
        node("check_threshold", "eflowNode", "IF", "Eşik Kontrolü", 100, 440, {
            "branches": [
                {
                    "label": "Evet",
                    "handle": "true",
                    "condition": {
                        "or": [
                            {"field": "form.total_amount", "op": ">=", "value": 50000},
                            {"field": "form.request_type", "op": "==", "value": "Abonelik"},
                        ]
                    }
                },
                {"label": "Hayır", "handle": "false", "condition": {}},
            ]
        }, "logic"),
        node("doc_upload", "eflowNode", "DocumentUpload", "Teklif Belgesi Yükle (min 2)", 350, 570, {
            "title": "En az 2 teklif belgesi yükleyin",
            "doc_type": "offer",
            "min_count": 2,
            "assignee_role": "viewer",
        }, "human"),
        node("ai_extract", "eflowNode", "ScriptTask", "Teklif Çıkarımı (Stub)", 350, 700, {
            "engineType": "ScriptTask",
            "mappings": [
                {"target": "docs.offer.amount", "source": "{{ form.total_amount }}"},
                {"target": "docs.offer.vendor_name", "source": "{{ form.vendor_name }}"},
            ]
        }, "data"),
        node("normalize", "eflowNode", "NormalizeMoney", "Tutarı Normalize Et", 350, 830, {
            "amount_field": "form.total_amount",
            "currency_field": "form.currency",
            "output_field": "calc.normalized_amount",
        }, "data"),
        node("policy_check", "eflowNode", "PolicyCheck", "Politika Kontrolü", 100, 960, {
            "rules": [
                {
                    "name": "high_value_without_justification",
                    "severity": "warning",
                    "condition": {
                        "and": [
                            {"field": "form.total_amount", "op": ">=", "value": 100000},
                            {"field": "form.justification", "op": "is_empty", "value": None},
                        ]
                    }
                }
            ]
        }, "compliance"),
        node("end", "eflowNode", "End", "Talep Tamamlandı", 100, 1090, {
            "status": "completed",
            "exports": [
                {"key": "pr_id", "expression": "{{ system.instance_id }}"},
                {"key": "total_amount", "expression": "{{ form.total_amount }}"},
                {"key": "flags", "expression": "{{ flags.policy_flags }}"},
            ]
        }, "events"),
    ],
    "edges": [
        edge("e1", "start", "form_fill"),
        edge("e2", "form_fill", "calculate"),
        edge("e3", "calculate", "check_threshold"),
        edge("e4", "check_threshold", "doc_upload", "Evet (≥50K veya Abonelik)", "true"),
        edge("e5", "check_threshold", "policy_check", "Hayır", "false"),
        edge("e6", "doc_upload", "ai_extract"),
        edge("e7", "ai_extract", "normalize"),
        edge("e8", "normalize", "policy_check"),
        edge("e9", "policy_check", "end"),
    ],
}

# ──────────────────────────────────────────────
# TEMPLATE 2: Satın Alma Süreci (P2P)
# ──────────────────────────────────────────────
P2P_GRAPH = {
    "nodes": [
        node("start", "eflowNode", "ManualStart", "Süreç Başlat", 100, 50, {}, "triggers"),
        node("check_offers", "eflowNode", "IF", "Teklif ≥2?", 100, 180, {
            "branches": [
                {"label": "Evet", "handle": "true", "condition": {"field": "form.offers_count", "op": ">=", "value": 2}},
                {"label": "Hayır", "handle": "false", "condition": {}},
            ]
        }, "logic"),
        node("doc_upload_p2p", "eflowNode", "DocumentUpload", "Teklif Yükle", 400, 310, {
            "title": "Teklif belgelerini yükleyin",
            "doc_type": "offer",
            "min_count": 2,
            "assignee_role": "procurement",
        }, "human"),
        node("extract_p2p", "eflowNode", "ScriptTask", "Teklif Çıkarımı", 400, 440, {
            "mappings": [{"target": "docs.offer.extracted", "source": "true"}]
        }, "data"),
        node("vendor_selection", "eflowNode", "VendorSelection", "Tedarikçi Seçimi", 100, 570, {
            "title": "Tedarikçi ve teklif seçimi yapın",
            "assignee_role": "procurement",
        }, "human"),
        node("approval_limit", "eflowNode", "ApprovalByLimitMatrix", "Limit Matrisine Göre Onay", 100, 700, {
            "amount_expr": "{{ form.total_amount }}",
        }, "approval"),
        node("check_approved", "eflowNode", "IF", "Onaylandı mı?", 100, 830, {
            "branches": [
                {"label": "Evet", "handle": "approved", "condition": {"field": "approval.last_decision", "op": "==", "value": "approved"}},
                {"label": "Hayır", "handle": "rejected", "condition": {}},
            ]
        }, "logic"),
        node("gen_po", "eflowNode", "ScriptTask", "PO No Üret", 100, 960, {
            "mappings": [{"target": "gen.po_no", "source": "PO-{{ system.started_at }}"}]
        }, "data"),
        node("erp_call", "eflowNode", "HTTPRequest", "ERP Entegrasyonu (Mock)", 100, 1090, {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "mock": True,
            "mock_response": {"status": "PO_CREATED", "po_id": "ERP-12345"},
            "output_key": "gen.erp_response",
        }, "integrations"),
        node("email_send", "eflowNode", "EmailSend", "Onay E-postası Gönder", 100, 1220, {
            "to": "{{ form.vendor_email }}",
            "subject": "PO Onaylandı - {{ gen.po_no }}",
            "body": "Satın alma siparişiniz onaylanmıştır.",
            "mock": True,
        }, "integrations"),
        node("end_approved", "eflowNode", "End", "Süreç Tamamlandı", 100, 1350, {
            "status": "completed",
            "exports": [
                {"key": "po_no", "expression": "{{ gen.po_no }}"},
                {"key": "supplier_vkn", "expression": "{{ form.vendor_vkn }}"},
                {"key": "approval_summary", "expression": "{{ approval.last_decision }}"},
            ]
        }, "events"),
        node("end_rejected", "eflowNode", "End", "Reddedildi", 400, 960, {
            "status": "rejected",
            "exports": [{"key": "rejection_reason", "expression": "{{ approval.last_comment }}"}]
        }, "events"),
    ],
    "edges": [
        edge("e1", "start", "check_offers"),
        edge("e2", "check_offers", "vendor_selection", "Evet", "true"),
        edge("e3", "check_offers", "doc_upload_p2p", "Hayır", "false"),
        edge("e4", "doc_upload_p2p", "extract_p2p"),
        edge("e5", "extract_p2p", "vendor_selection"),
        edge("e6", "vendor_selection", "approval_limit"),
        edge("e7", "approval_limit", "check_approved"),
        edge("e8", "check_approved", "gen_po", "Evet", "approved"),
        edge("e9", "check_approved", "end_rejected", "Hayır", "rejected"),
        edge("e10", "gen_po", "erp_call"),
        edge("e11", "erp_call", "email_send"),
        edge("e12", "email_send", "end_approved"),
    ],
}

# ──────────────────────────────────────────────
# TEMPLATE 3: Sözleşme Süreci
# ──────────────────────────────────────────────
CONTRACT_GRAPH = {
    "nodes": [
        node("start", "eflowNode", "ManualStart", "Süreç Başlat", 100, 50, {}, "triggers"),
        node("upload_draft", "eflowNode", "DocumentUpload", "Sözleşme Taslağı Yükle", 100, 180, {
            "title": "Sözleşme taslak belgesi",
            "doc_type": "contract_draft",
            "assignee_role": "viewer",
        }, "human"),
        node("ai_extract_contract", "eflowNode", "ScriptTask", "Sözleşme Çıkarımı (Stub)", 100, 310, {
            "mappings": [
                {"target": "docs.contract.parties", "source": "TARAF A & TARAF B"},
                {"target": "docs.contract.amount", "source": "{{ form.total_amount }}"},
                {"target": "docs.contract.start_date", "source": "{{ form.contract_start }}"},
                {"target": "docs.contract.end_date", "source": "{{ form.contract_end }}"},
            ]
        }, "data"),
        node("review_legal", "eflowNode", "ReviewComment", "Hukuki İnceleme", 100, 440, {
            "title": "Sözleşme taslağını inceleyin",
            "assignee_role": "legal",
            "options": ["approve", "revision", "reject"],
            "revision_target_node": "upload_draft",
        }, "human"),
        node("check_legal", "eflowNode", "IF", "Hukuki Karar?", 100, 570, {
            "branches": [
                {"label": "Onaylandı", "handle": "approved", "condition": {"field": "approval.last_decision", "op": "==", "value": "approved"}},
                {"label": "Reddedildi", "handle": "rejected", "condition": {"field": "approval.last_decision", "op": "==", "value": "rejected"}},
                {"label": "Revizyon", "handle": "revision_requested", "condition": {}},
            ]
        }, "logic"),
        node("approval_finance", "eflowNode", "ApprovalTask", "Finans Onayı", 100, 700, {
            "title": "Sözleşme finansal onayı",
            "approver_role": "finance",
        }, "approval"),
        node("esign", "eflowNode", "ServiceTask", "E-İmza (DocuSeal Stub)", 100, 830, {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "mock": True,
            "mock_response": {"signed_url": "https://docs.example.com/signed/contract.pdf", "status": "signed"},
            "output_key": "gen.esign_response",
        }, "integrations"),
        node("archive", "eflowNode", "ServiceTask", "Arşivle", 100, 960, {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "mock": True,
            "mock_response": {"archived": True, "archive_id": "ARC-001"},
            "output_key": "gen.archive_response",
        }, "integrations"),
        node("end_approved", "eflowNode", "End", "Sözleşme İmzalandı", 100, 1090, {
            "status": "completed",
            "exports": [
                {"key": "contract_id", "expression": "{{ system.instance_id }}"},
                {"key": "signed_url", "expression": "{{ gen.esign_response.signed_url }}"},
                {"key": "amount", "expression": "{{ docs.contract.amount }}"},
            ]
        }, "events"),
        node("end_rejected", "eflowNode", "End", "Sözleşme Reddedildi", 400, 570, {
            "status": "rejected",
        }, "events"),
        node("upload_v2", "eflowNode", "DocumentUpload", "Revize Sözleşme Yükle", 400, 440, {
            "title": "Revize edilmiş sözleşme taslağı",
            "doc_type": "contract_draft_v2",
            "assignee_role": "viewer",
        }, "human"),
    ],
    "edges": [
        edge("e1", "start", "upload_draft"),
        edge("e2", "upload_draft", "ai_extract_contract"),
        edge("e3", "ai_extract_contract", "review_legal"),
        edge("e4", "review_legal", "check_legal"),
        edge("e5", "check_legal", "approval_finance", "Onaylandı", "approved"),
        edge("e6", "check_legal", "end_rejected", "Reddedildi", "rejected"),
        edge("e7", "check_legal", "upload_v2", "Revizyon", "revision_requested"),
        edge("e8", "upload_v2", "review_legal"),
        edge("e9", "approval_finance", "esign"),
        edge("e10", "esign", "archive"),
        edge("e11", "archive", "end_approved"),
    ],
}

# ──────────────────────────────────────────────
# TEMPLATE 4: Sipariş/Fatura/Ödeme
# ──────────────────────────────────────────────
INVOICE_GRAPH = {
    "nodes": [
        node("start", "eflowNode", "ManualStart", "Süreç Başlat", 100, 50, {}, "triggers"),
        node("delivery", "eflowNode", "DeliveryAcceptance", "Teslimat Kabulü (Opsiyonel)", 100, 180, {
            "title": "Teslimatı kontrol edin ve onaylayın",
            "assignee_role": "procurement",
        }, "human"),
        node("upload_invoice", "eflowNode", "DocumentUpload", "Fatura Yükle", 100, 310, {
            "title": "Fatura belgesini yükleyin",
            "doc_type": "invoice",
            "assignee_role": "finance",
        }, "human"),
        node("ai_extract_inv", "eflowNode", "ScriptTask", "Fatura Çıkarımı (Stub)", 100, 440, {
            "mappings": [
                {"target": "docs.invoice.amount", "source": "{{ form.invoice_amount }}"},
                {"target": "docs.invoice.vendor_vkn", "source": "{{ form.vendor_vkn }}"},
                {"target": "docs.invoice.date", "source": "{{ form.invoice_date }}"},
                {"target": "docs.invoice.invoice_no", "source": "{{ form.invoice_no }}"},
            ]
        }, "data"),
        node("match", "eflowNode", "ThreeWayMatch", "3-Yön Eşleştirme", 100, 570, {
            "po_amount": "{{ gen.po.amount }}",
            "invoice_amount": "{{ form.invoice_amount }}",
            "tolerance_pct": 5,
        }, "data"),
        node("switch_match", "eflowNode", "Switch", "Eşleşme Durumu", 100, 700, {
            "branches": [
                {"label": "Eşleşti", "handle": "matched", "condition": {"field": "flags.match_status", "op": "==", "value": "matched"}},
                {"label": "Uyuşmazlık", "handle": "mismatch", "condition": {}},
            ]
        }, "logic"),
        node("payment_approval", "eflowNode", "ApprovalTask", "Ödeme Onayı", 100, 830, {
            "title": "Fatura ödemesi için onay",
            "approver_role": "finance",
            "amount_field": "form.invoice_amount",
        }, "approval"),
        node("payment_http", "eflowNode", "HTTPRequest", "Ödeme Sistemi (Mock)", 100, 960, {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "mock": True,
            "mock_response": {"payment_status": "PROCESSED", "reference": "PAY-99999"},
            "output_key": "gen.payment_response",
        }, "integrations"),
        node("dispute_task", "eflowNode", "ReworkTask", "Uyuşmazlık Görevi (Finans)", 400, 830, {
            "title": "Fatura uyuşmazlığını çözün",
            "assignee_role": "finance",
        }, "human"),
        node("end_matched", "eflowNode", "End", "Ödeme Tamamlandı", 100, 1090, {
            "status": "completed",
            "exports": [
                {"key": "invoice_id", "expression": "{{ system.instance_id }}"},
                {"key": "match_status", "expression": "{{ flags.match_status }}"},
                {"key": "payment_status", "expression": "{{ gen.payment_response.payment_status }}"},
            ]
        }, "events"),
        node("end_rejected", "eflowNode", "End", "Fatura Reddedildi", 400, 960, {
            "status": "rejected",
            "exports": [
                {"key": "invoice_id", "expression": "{{ system.instance_id }}"},
                {"key": "match_status", "expression": "{{ flags.match_status }}"},
                {"key": "mismatch_flags", "expression": "{{ flags.policy_flags }}"},
            ]
        }, "events"),
    ],
    "edges": [
        edge("e1", "start", "delivery"),
        edge("e2", "delivery", "upload_invoice"),
        edge("e3", "upload_invoice", "ai_extract_inv"),
        edge("e4", "ai_extract_inv", "match"),
        edge("e5", "match", "switch_match"),
        edge("e6", "switch_match", "payment_approval", "Eşleşti", "matched"),
        edge("e7", "switch_match", "dispute_task", "Uyuşmazlık", "mismatch"),
        edge("e8", "payment_approval", "payment_http"),
        edge("e9", "payment_http", "end_matched"),
        edge("e10", "dispute_task", "end_rejected"),
    ],
}

TEMPLATES = [
    {
        "name": "Satın Alma Talebi (PR)",
        "description": "Satın alma talebi oluşturma, teklif toplama ve politika kontrolü süreci.",
        "category": "procurement",
        "template_key": "pr_request",
        "graph": PR_GRAPH,
    },
    {
        "name": "Satın Alma Süreci (P2P)",
        "description": "Tedarikçi seçimi, onay matrisli PO oluşturma ve ERP entegrasyonu.",
        "category": "procurement",
        "template_key": "p2p_process",
        "graph": P2P_GRAPH,
    },
    {
        "name": "Sözleşme Süreci",
        "description": "Sözleşme taslağı, hukuki inceleme, revizyon döngüsü ve e-imza.",
        "category": "legal",
        "template_key": "contract_process",
        "graph": CONTRACT_GRAPH,
    },
    {
        "name": "Sipariş/Fatura/Ödeme",
        "description": "Fatura çıkarımı, 3-yön eşleştirme, uyuşmazlık yönetimi ve ödeme.",
        "category": "finance",
        "template_key": "invoice_payment",
        "graph": INVOICE_GRAPH,
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding users...")
        user_map = {}
        for u_data in USERS:
            result = await db.execute(select(User).where(User.email == u_data["email"]))
            existing = result.scalar_one_or_none()
            if not existing:
                user = User(
                    org_id="default",
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    hashed_password=hash_password(u_data["password"]),
                    role=u_data["role"],
                    department=u_data["department"],
                    cost_center=u_data["cost_center"],
                    avatar_initials=u_data.get("avatar_initials", u_data["full_name"][:2].upper()),
                )
                db.add(user)
                await db.flush()
                user_map[u_data["email"]] = user.id
                print(f"  ✓ Created user: {u_data['email']}")
            else:
                user_map[u_data["email"]] = existing.id
                print(f"  ℹ Exists: {u_data['email']}")

        await db.commit()

        # Re-fetch IDs
        for email in ["manager@eflow.com", "director@eflow.com", "cfo@eflow.com"]:
            result = await db.execute(select(User).where(User.email == email))
            u = result.scalar_one_or_none()
            if u:
                user_map[email] = u.id

        print("🌱 Seeding approval limits...")
        limits_data = [
            {"min_amount": 0, "max_amount": 50000, "approver_email": "manager@eflow.com",
             "approver_role": "Departman Müdürü"},
            {"min_amount": 50000, "max_amount": 250000, "approver_email": "director@eflow.com",
             "approver_role": "Direktör"},
            {"min_amount": 250000, "max_amount": None, "approver_email": "cfo@eflow.com",
             "approver_role": "CFO"},
        ]

        for lim in limits_data:
            approver_id = user_map.get(lim["approver_email"])
            if not approver_id:
                continue
            # Check existing
            existing_result = await db.execute(
                select(ApprovalLimit).where(
                    ApprovalLimit.org_id == "default",
                    ApprovalLimit.min_amount == lim["min_amount"],
                )
            )
            if not existing_result.scalar_one_or_none():
                limit = ApprovalLimit(
                    org_id="default",
                    min_amount=lim["min_amount"],
                    max_amount=lim["max_amount"],
                    approver_id=approver_id,
                    approver_role=lim["approver_role"],
                    currency="TRY",
                )
                db.add(limit)
                print(f"  ✓ Limit: {lim['min_amount']} - {lim['max_amount']} → {lim['approver_email']}")

        await db.commit()

        print("🌱 Seeding flow templates...")
        for tmpl in TEMPLATES:
            result = await db.execute(
                select(ProcessDefinition).where(
                    ProcessDefinition.template_key == tmpl["template_key"],
                    ProcessDefinition.org_id == "default",
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  ℹ Exists: {tmpl['name']}")
                continue

            admin_result = await db.execute(select(User).where(User.email == "admin@eflow.com"))
            admin = admin_result.scalar_one_or_none()

            definition = ProcessDefinition(
                org_id="default",
                name=tmpl["name"],
                description=tmpl["description"],
                category=tmpl["category"],
                tags=[tmpl["category"], "template"],
                is_template=True,
                template_key=tmpl["template_key"],
                created_by=admin.id if admin else None,
            )
            db.add(definition)
            await db.flush()

            version = ProcessVersion(
                org_id="default",
                definition_id=definition.id,
                version_number=1,
                status="published",
                graph_json=tmpl["graph"],
                published_at=datetime.utcnow(),
                published_by=admin.id if admin else None,
            )
            db.add(version)
            print(f"  ✓ Template: {tmpl['name']}")

        await db.commit()
        print("✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
