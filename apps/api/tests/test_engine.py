from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.engine import complete_task, decide_approval, start_instance
from app.expression import resolve_template
from app.models import ApprovalInstance, ProcessDefinition, ProcessVersion, TaskInstance, User
from app.seeder import seed_demo_data


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    seed_demo_data(session)
    return session


def test_expression_resolves_arithmetic_and_boolean() -> None:
    context = {
        "form": {"amount": 150, "currency": "TRY"},
        "calc": {"tax": 30},
    }
    assert resolve_template("{{ form.amount + calc.tax }}", context) == 180
    assert resolve_template("{{ form.amount >= 100 and form.currency == 'TRY' }}", context) is True


def test_lazy_engine_executes_step_by_step() -> None:
    db = build_session()
    actor = db.scalar(select(User).where(User.email == "admin@eflow.local"))
    definition = db.scalar(select(ProcessDefinition).where(ProcessDefinition.template_key == "purchase_request"))
    version = db.scalar(select(ProcessVersion).where(ProcessVersion.definition_id == definition.id))

    instance = start_instance(
        db,
        version=version,
        definition_name=definition.name,
        actor=actor,
        initial_inputs={"department": "Operations", "budget_type": "default", "currency": "TRY", "vat_rate": 0},
    )

    pending_task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending"))
    assert pending_task is not None
    assert instance.status == "waiting_task"
    assert pending_task.node_id == "fill_pr"

    instance = complete_task(
        db,
        task=pending_task,
        actor=actor,
        payload={
            "request_title": "Laptop Request",
            "request_type": "Standart",
            "department": "Operations",
            "budget_type": "default",
            "currency": "TRY",
            "vat_rate": 0,
            "line_items": [{"item_name": "Laptop", "quantity": 1, "unit_price": 12000}],
        },
        outcome="submitted",
    )

    assert instance.status == "completed"
    assert instance.exports_json["total_amount"] == 12000.0
    assert instance.exports_json["offers_count"] == 0


def test_approval_limit_routes_to_finance_for_mid_band() -> None:
    db = build_session()
    actor = db.scalar(select(User).where(User.email == "admin@eflow.local"))
    finance = db.scalar(select(User).where(User.email == "finance@eflow.local"))
    definition = db.scalar(select(ProcessDefinition).where(ProcessDefinition.template_key == "purchase_to_pay"))
    version = db.scalar(select(ProcessVersion).where(ProcessVersion.definition_id == definition.id))

    instance = start_instance(
        db,
        version=version,
        definition_name=definition.name,
        actor=actor,
        initial_inputs={
            "department": "Operations",
            "budget_type": "default",
            "currency": "TRY",
            "total_amount": 60000,
        },
    )
    upload_task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending"))
    assert upload_task.node_id == "collect_offers"

    instance = complete_task(db, task=upload_task, actor=actor, payload={"offers_count": 2}, outcome="uploaded")
    vendor_task = db.scalar(select(TaskInstance).where(TaskInstance.process_instance_id == instance.id, TaskInstance.status == "pending"))
    assert vendor_task.node_id == "vendor_selection"

    instance = complete_task(
        db,
        task=vendor_task,
        actor=actor,
        payload={"supplier_vkn": "1234567890", "expected_amount": 60000},
        outcome="selected",
    )

    approval = db.scalar(select(ApprovalInstance).where(ApprovalInstance.process_instance_id == instance.id, ApprovalInstance.status == "pending"))
    assert approval is not None
    assert approval.approver_user_id == finance.id

    instance = decide_approval(db, approval=approval, actor=finance, decision="approved")
    assert instance.status == "completed"
    assert instance.exports_json["po_no"].startswith("PO-")
