"""Seed data for e-Flow Enterprise: users, flows, forms, approval limits."""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.models import (
    User, ProcessDefinition, ProcessVersion, FormDefinition,
    ApprovalLimit, Delegation, AuditEvent,
)
from app.services.auth import hash_password


TEMPLATES = {
    "tpl_purchase_request": {
        "name": "Satın Alma Talebi (PR)",
        "description": "Talep formu, hesaplama, doküman yükleme, politika kontrolü",
        "nodes": [
            {"id": "n1", "type": "customNode", "position": {"x": 400, "y": 0}, "data": {"label": "Form Gönderim", "nodeType": "form_submit", "engineType": "Event", "category": "triggers", "config": {"form_id": "pr_form"}}},
            {"id": "n2", "type": "customNode", "position": {"x": 400, "y": 120}, "data": {"label": "PR Formu Doldur", "nodeType": "form_fill", "engineType": "HumanTask", "category": "human_tasks", "config": {"form_id": "pr_form", "assignee_type": "requester"}}},
            {"id": "n3", "type": "customNode", "position": {"x": 400, "y": 240}, "data": {"label": "Toplam Hesapla", "nodeType": "calculate", "engineType": "ScriptTask", "category": "data", "config": {"expression": "{{ form.quantity * form.unit_price * (1 + form.vat_rate / 100) }}"}}},
            {"id": "n4", "type": "customNode", "position": {"x": 400, "y": 360}, "data": {"label": "Tutar >= 50K?", "nodeType": "if_condition", "engineType": "Gateway", "category": "logic", "config": {"condition": "{{ form.total_amount >= 50000 or form.request_type == 'subscription' }}"}}},
            {"id": "n5", "type": "customNode", "position": {"x": 200, "y": 510}, "data": {"label": "Teklif Yükle (min 2)", "nodeType": "document_upload", "engineType": "HumanTask", "category": "human_tasks", "config": {"doc_type": "offer", "min_count": 2}}},
            {"id": "n6", "type": "customNode", "position": {"x": 200, "y": 640}, "data": {"label": "AI Teklif Çıkarım", "nodeType": "ai_extract", "engineType": "ServiceTask", "category": "document", "config": {"extract_type": "offer"}}},
            {"id": "n7", "type": "customNode", "position": {"x": 200, "y": 760}, "data": {"label": "Para Normalize", "nodeType": "normalize_money", "engineType": "ScriptTask", "category": "data", "config": {"target_currency": "TRY"}}},
            {"id": "n8", "type": "customNode", "position": {"x": 400, "y": 880}, "data": {"label": "Politika Kontrol", "nodeType": "policy_check", "engineType": "ScriptTask", "category": "error", "config": {"policy_type": "procurement"}}},
            {"id": "n9", "type": "customNode", "position": {"x": 400, "y": 1010}, "data": {"label": "Bitiş", "nodeType": "end", "engineType": "End", "category": "logic", "config": {"exports": {"pr_id": "{{ system.instance_id }}", "total_amount": "{{ calc.total_amount }}", "flags": "{{ flags }}", "offers_count": "{{ docs.offers_count }}"}}}},
        ],
        "edges": [
            {"id": "e1-2", "source": "n1", "target": "n2", "type": "smartEdge"},
            {"id": "e2-3", "source": "n2", "target": "n3", "type": "smartEdge"},
            {"id": "e3-4", "source": "n3", "target": "n4", "type": "smartEdge"},
            {"id": "e4-5", "source": "n4", "target": "n5", "sourceHandle": "true", "type": "smartEdge", "label": "Evet"},
            {"id": "e4-8", "source": "n4", "target": "n8", "sourceHandle": "false", "type": "smartEdge", "label": "Hayır"},
            {"id": "e5-6", "source": "n5", "target": "n6", "type": "smartEdge"},
            {"id": "e6-7", "source": "n6", "target": "n7", "type": "smartEdge"},
            {"id": "e7-8", "source": "n7", "target": "n8", "type": "smartEdge"},
            {"id": "e8-9", "source": "n8", "target": "n9", "sourceHandle": "pass", "type": "smartEdge", "label": "Geçti"},
        ],
    },
    "tpl_purchase_process": {
        "name": "Satın Alma Süreci (P2P)",
        "description": "Tedarikçi seçim, onay matrisi, sipariş oluşturma",
        "nodes": [
            {"id": "n1", "type": "customNode", "position": {"x": 400, "y": 0}, "data": {"label": "Başlat", "nodeType": "manual_start", "engineType": "Event", "category": "triggers", "config": {}}},
            {"id": "n2", "type": "customNode", "position": {"x": 400, "y": 120}, "data": {"label": "Teklif >= 2?", "nodeType": "if_condition", "engineType": "Gateway", "category": "logic", "config": {"condition": "{{ docs.offers_count >= 2 }}"}}},
            {"id": "n3", "type": "customNode", "position": {"x": 400, "y": 380}, "data": {"label": "Tedarikçi Seçimi", "nodeType": "vendor_selection", "engineType": "HumanTask", "category": "human_tasks", "config": {"justification_required": True}}},
            {"id": "n4", "type": "customNode", "position": {"x": 400, "y": 500}, "data": {"label": "Limit Matrisli Onay", "nodeType": "approval_limit_matrix", "engineType": "ApprovalTask", "category": "approval", "config": {"amount_field": "form.total_amount"}}},
            {"id": "n5", "type": "customNode", "position": {"x": 300, "y": 770}, "data": {"label": "PO No Oluştur", "nodeType": "set_fields", "engineType": "ScriptTask", "category": "data", "config": {"mappings": [{"key": "gen.po_no", "value": "PO-{{ system.year }}-{{ system.seq }}"}]}}},
            {"id": "n6", "type": "customNode", "position": {"x": 300, "y": 890}, "data": {"label": "ERP Entegrasyon", "nodeType": "http_request", "engineType": "ServiceTask", "category": "integrations", "config": {"url": "https://mock-erp.example.com/po", "method": "POST"}}},
            {"id": "n7", "type": "customNode", "position": {"x": 300, "y": 1010}, "data": {"label": "E-posta Bildirim", "nodeType": "email_send", "engineType": "ServiceTask", "category": "integrations", "config": {"to": "{{ system.requester_email }}", "subject": "PO Oluşturuldu"}}},
            {"id": "n8", "type": "customNode", "position": {"x": 400, "y": 1140}, "data": {"label": "Bitiş", "nodeType": "end", "engineType": "End", "category": "logic", "config": {"exports": {"po_no": "{{ gen.po_no }}", "supplier_vkn": "{{ selection.supplier_vkn }}"}}}},
        ],
        "edges": [
            {"id": "e1-2", "source": "n1", "target": "n2", "type": "smartEdge"},
            {"id": "e2-3", "source": "n2", "target": "n3", "sourceHandle": "true", "type": "smartEdge", "label": "Evet"},
            {"id": "e3-4", "source": "n3", "target": "n4", "type": "smartEdge"},
            {"id": "e4-5", "source": "n4", "target": "n5", "sourceHandle": "approved", "type": "smartEdge", "label": "Onaylandı"},
            {"id": "e5-6", "source": "n5", "target": "n6", "type": "smartEdge"},
            {"id": "e6-7", "source": "n6", "target": "n7", "type": "smartEdge"},
            {"id": "e7-8", "source": "n7", "target": "n8", "type": "smartEdge"},
        ],
    },
    "tpl_contract": {
        "name": "Sözleşme Süreci",
        "description": "Sözleşme yükleme, hukuk inceleme, revizyon döngüsü, imza",
        "nodes": [
            {"id": "n1", "type": "customNode", "position": {"x": 400, "y": 0}, "data": {"label": "Başlat", "nodeType": "manual_start", "engineType": "Event", "category": "triggers", "config": {}}},
            {"id": "n2", "type": "customNode", "position": {"x": 400, "y": 120}, "data": {"label": "Sözleşme Taslağı Yükle", "nodeType": "document_upload", "engineType": "HumanTask", "category": "human_tasks", "config": {"doc_type": "contract_draft", "min_count": 1}}},
            {"id": "n3", "type": "customNode", "position": {"x": 400, "y": 240}, "data": {"label": "AI Sözleşme Çıkarım", "nodeType": "ai_extract", "engineType": "ServiceTask", "category": "document", "config": {"extract_type": "contract"}}},
            {"id": "n4", "type": "customNode", "position": {"x": 400, "y": 360}, "data": {"label": "Hukuk İnceleme", "nodeType": "review_comment", "engineType": "HumanTask", "category": "human_tasks", "config": {"reviewers": ["legal"], "comment_required": True}}},
            {"id": "n5", "type": "customNode", "position": {"x": 400, "y": 480}, "data": {"label": "Finans Onayı", "nodeType": "approval_single", "engineType": "ApprovalTask", "category": "approval", "config": {"approver_type": "role"}}},
            {"id": "n6", "type": "customNode", "position": {"x": 400, "y": 600}, "data": {"label": "E-İmza (DocuSeal)", "nodeType": "http_request", "engineType": "ServiceTask", "category": "integrations", "config": {"url": "https://docuseal-stub.example.com/sign", "method": "POST"}}},
            {"id": "n7", "type": "customNode", "position": {"x": 400, "y": 720}, "data": {"label": "Bitiş", "nodeType": "end", "engineType": "End", "category": "logic", "config": {"exports": {"contract_id": "{{ system.instance_id }}", "amount": "{{ extract.contract_amount }}"}}}},
        ],
        "edges": [
            {"id": "e1-2", "source": "n1", "target": "n2", "type": "smartEdge"},
            {"id": "e2-3", "source": "n2", "target": "n3", "type": "smartEdge"},
            {"id": "e3-4", "source": "n3", "target": "n4", "type": "smartEdge"},
            {"id": "e4-5", "source": "n4", "target": "n5", "type": "smartEdge"},
            {"id": "e5-6", "source": "n5", "target": "n6", "sourceHandle": "approved", "type": "smartEdge", "label": "Onay"},
            {"id": "e6-7", "source": "n6", "target": "n7", "type": "smartEdge"},
        ],
    },
    "tpl_invoice_payment": {
        "name": "Sipariş/Fatura/Ödeme",
        "description": "Teslimat kabul, fatura eşleşme, ödeme onayı",
        "nodes": [
            {"id": "n1", "type": "customNode", "position": {"x": 400, "y": 0}, "data": {"label": "Başlat", "nodeType": "manual_start", "engineType": "Event", "category": "triggers", "config": {}}},
            {"id": "n2", "type": "customNode", "position": {"x": 400, "y": 120}, "data": {"label": "Teslimat Kabul", "nodeType": "delivery_acceptance", "engineType": "HumanTask", "category": "human_tasks", "config": {}}},
            {"id": "n3", "type": "customNode", "position": {"x": 400, "y": 240}, "data": {"label": "Fatura Yükle", "nodeType": "document_upload", "engineType": "HumanTask", "category": "human_tasks", "config": {"doc_type": "invoice", "min_count": 1}}},
            {"id": "n4", "type": "customNode", "position": {"x": 400, "y": 360}, "data": {"label": "AI Fatura Çıkarım", "nodeType": "ai_extract", "engineType": "ServiceTask", "category": "document", "config": {"extract_type": "invoice"}}},
            {"id": "n5", "type": "customNode", "position": {"x": 400, "y": 480}, "data": {"label": "3'lü Eşleşme", "nodeType": "three_way_match", "engineType": "ServiceTask", "category": "document", "config": {"tolerance_pct": 5}}},
            {"id": "n6", "type": "customNode", "position": {"x": 400, "y": 600}, "data": {"label": "Ödeme Onayı", "nodeType": "approval_single", "engineType": "ApprovalTask", "category": "approval", "config": {"approver_type": "role"}}},
            {"id": "n7", "type": "customNode", "position": {"x": 400, "y": 720}, "data": {"label": "Ödeme Entegrasyon", "nodeType": "http_request", "engineType": "ServiceTask", "category": "integrations", "config": {"url": "https://mock-erp.example.com/payment", "method": "POST"}}},
            {"id": "n8", "type": "customNode", "position": {"x": 400, "y": 840}, "data": {"label": "Bitiş", "nodeType": "end", "engineType": "End", "category": "logic", "config": {"exports": {"invoice_id": "{{ extract.invoice_no }}", "match_status": "{{ flags.match_status }}", "payment_status": "{{ gen.payment_status }}"}}}},
        ],
        "edges": [
            {"id": "e1-2", "source": "n1", "target": "n2", "type": "smartEdge"},
            {"id": "e2-3", "source": "n2", "target": "n3", "type": "smartEdge"},
            {"id": "e3-4", "source": "n3", "target": "n4", "type": "smartEdge"},
            {"id": "e4-5", "source": "n4", "target": "n5", "type": "smartEdge"},
            {"id": "e5-6", "source": "n5", "target": "n6", "type": "smartEdge"},
            {"id": "e6-7", "source": "n6", "target": "n7", "sourceHandle": "approved", "type": "smartEdge", "label": "Onay"},
            {"id": "e7-8", "source": "n7", "target": "n8", "type": "smartEdge"},
        ],
    },
}


def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(User).count() > 0:
            print("Database already seeded, skipping.")
            return

        # Users
        admin = User(
            id="user_admin",
            email="admin@eflow.io",
            name="Admin Kullanıcı",
            hashed_password=hash_password("admin123"),
            role="admin",
            department="IT",
            cost_center="CC001",
            org_id="org_1",
        )
        proc_approver = User(
            id="user_procurement",
            email="ahmet@eflow.io",
            name="Ahmet Yılmaz",
            hashed_password=hash_password("pass123"),
            role="approver",
            department="Satın Alma",
            cost_center="CC001",
            manager_id="user_admin",
            org_id="org_1",
        )
        finance_approver = User(
            id="user_finance",
            email="mehmet@eflow.io",
            name="Mehmet Demir",
            hashed_password=hash_password("pass123"),
            role="approver",
            department="Finans",
            cost_center="CC002",
            manager_id="user_admin",
            org_id="org_1",
        )
        legal_user = User(
            id="user_legal",
            email="ayse@eflow.io",
            name="Ayşe Kara",
            hashed_password=hash_password("pass123"),
            role="viewer",
            department="Hukuk",
            cost_center="CC003",
            manager_id="user_admin",
            org_id="org_1",
        )
        db.add_all([admin, proc_approver, finance_approver, legal_user])

        # Approval Limits
        db.add_all([
            ApprovalLimit(id=str(uuid.uuid4()), min_amount=0, max_amount=50000, approver_role="dept_manager", currency="TRY", org_id="org_1"),
            ApprovalLimit(id=str(uuid.uuid4()), min_amount=50000, max_amount=250000, approver_role="director", currency="TRY", org_id="org_1"),
            ApprovalLimit(id=str(uuid.uuid4()), min_amount=250000, max_amount=999999999, approver_role="cfo", currency="TRY", org_id="org_1"),
        ])

        # Delegation
        db.add(Delegation(
            id=str(uuid.uuid4()),
            from_user_id="user_finance",
            to_user_id="user_procurement",
            start_date=datetime(2024, 3, 15),
            end_date=datetime(2024, 3, 22),
            role_scope="approval",
            org_id="org_1",
        ))

        # Flows & Versions
        for tpl_id, tpl_data in TEMPLATES.items():
            flow_id = str(uuid.uuid4())
            flow = ProcessDefinition(
                id=flow_id,
                name=tpl_data["name"],
                description=tpl_data["description"],
                status="published",
                current_version=1,
                org_id="org_1",
            )
            db.add(flow)

            version = ProcessVersion(
                id=str(uuid.uuid4()),
                flow_id=flow_id,
                version=1,
                graph_json={"nodes": tpl_data["nodes"], "edges": tpl_data["edges"]},
                status="published",
            )
            db.add(version)

        # Forms
        pr_form = FormDefinition(
            id="form_pr",
            name="Satın Alma Talep Formu",
            description="PR başvuru formu",
            status="published",
            version=2,
            fields=[
                {"id": "f1", "key": "title", "label": "Talep Başlığı", "type": "text", "required": True, "order": 0},
                {"id": "f2", "key": "description", "label": "Açıklama", "type": "textarea", "required": False, "order": 1},
                {"id": "f3", "key": "request_type", "label": "Talep Türü", "type": "dropdown", "required": True, "options": [{"label": "Mal Alımı", "value": "goods"}, {"label": "Hizmet", "value": "service"}, {"label": "Abonelik", "value": "subscription"}], "order": 2},
                {"id": "f4", "key": "department", "label": "Departman", "type": "dropdown", "required": True, "options": [{"label": "IT", "value": "it"}, {"label": "HR", "value": "hr"}, {"label": "Ops", "value": "ops"}], "order": 3},
                {"id": "f5", "key": "quantity", "label": "Miktar", "type": "number", "required": True, "order": 4},
                {"id": "f6", "key": "unit_price", "label": "Birim Fiyat", "type": "money", "required": True, "order": 5},
                {"id": "f7", "key": "vat_rate", "label": "KDV Oranı (%)", "type": "number", "required": True, "order": 6},
                {"id": "f8", "key": "total_amount", "label": "Toplam Tutar", "type": "money", "required": False, "order": 7},
                {"id": "f9", "key": "currency", "label": "Para Birimi", "type": "dropdown", "required": True, "options": [{"label": "TRY", "value": "TRY"}, {"label": "USD", "value": "USD"}, {"label": "EUR", "value": "EUR"}], "order": 8},
                {"id": "f10", "key": "needed_by", "label": "İhtiyaç Tarihi", "type": "date", "required": False, "order": 9},
                {"id": "f11", "key": "urgent", "label": "Acil mi?", "type": "boolean", "required": False, "order": 10},
                {"id": "f12", "key": "attachments", "label": "Ek Dosyalar", "type": "file_upload", "required": False, "order": 11},
            ],
            org_id="org_1",
        )
        db.add(pr_form)

        db.commit()
        print("Database seeded successfully!")
        print(f"  Users: 4 (admin, procurement, finance, legal)")
        print(f"  Flows: {len(TEMPLATES)} templates")
        print(f"  Forms: 1 (PR form)")
        print(f"  Approval Limits: 3 tiers")
        print(f"  Delegation: 1")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
