from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.db.base import Base
from app.models.models import ApprovalLimit, ApprovalInstance, ProcessDefinition, ProcessInstance, ProcessVersion, TaskInstance, User
from app.services.bpm_engine import BPMEngine
from app.services.expression_engine import resolve_expression


def _db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, future=True)()


def test_expression_preview_resolves_value() -> None:
    context = {"form": {"total_amount": 70000, "request_type": "Abonelik"}}
    result = resolve_expression("{{ form.total_amount >= 50000 or form.request_type == 'Abonelik' }}", context)
    assert result is True


def test_lazy_execution_step_by_step() -> None:
    db = _db()
    user = User(
        org_id="org_default",
        email="admin@test.local",
        full_name="Admin",
        role="admin",
        department="general",
        cost_center="GEN",
        manager_id=None,
        hashed_password=get_password_hash("secret"),
    )
    db.add(user)
    db.flush()

    flow = ProcessDefinition(org_id="org_default", code="flow_a", name="Flow A", description="", created_by=user.id)
    db.add(flow)
    db.flush()
    version = ProcessVersion(
        org_id="org_default",
        process_definition_id=flow.id,
        version_no=1,
        status="published",
        graph_json={
            "nodes": [
                {"id": "start", "type": "start", "data": {"engineType": "start"}},
                {"id": "task", "type": "humanTask", "data": {"engineType": "humanTask", "title": "Enter Data"}},
                {"id": "end", "type": "end", "data": {"engineType": "end", "exportMapping": {"amount": "{{ form.total_amount }}"}}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "task"},
                {"id": "e2", "source": "task", "target": "end"},
            ],
        },
    )
    db.add(version)
    db.flush()

    instance = ProcessInstance(
        org_id="org_default",
        process_version_id=version.id,
        title="Demo",
        requester_id=user.id,
        status="running",
        current_node_id="start",
        variables_json={"form": {}},
    )
    db.add(instance)
    db.flush()

    engine = BPMEngine(db)
    engine.run_until_wait(instance, actor=user)
    db.flush()

    assert instance.status == "waiting_task"
    task = db.query(TaskInstance).filter(TaskInstance.process_instance_id == instance.id).first()
    assert task is not None

    engine.complete_task(task, user, {"total_amount": 12345})
    db.flush()
    assert instance.status == "completed"
    assert instance.exports_json["amount"] == 12345


def test_approval_limit_matrix_route() -> None:
    db = _db()
    user = User(
        org_id="org_default",
        email="requester@test.local",
        full_name="Requester",
        role="viewer",
        department="general",
        cost_center="GEN",
        manager_id=None,
        hashed_password=get_password_hash("secret"),
    )
    db.add(user)
    db.add(
        ApprovalLimit(
            org_id="org_default",
            department="general",
            budget_type="capex",
            currency="TRY",
            min_amount=50000,
            max_amount=250000,
            approver_role="director",
        )
    )
    db.flush()

    flow = ProcessDefinition(org_id="org_default", code="flow_limit", name="Flow Limit", description="", created_by=user.id)
    db.add(flow)
    db.flush()
    version = ProcessVersion(
        org_id="org_default",
        process_definition_id=flow.id,
        version_no=1,
        status="published",
        graph_json={
            "nodes": [
                {"id": "start", "type": "start", "data": {"engineType": "start"}},
                {"id": "approval", "type": "approvalTask", "data": {"engineType": "approval", "byLimitMatrix": True}},
                {"id": "end", "type": "end", "data": {"engineType": "end"}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "approval"},
                {"id": "e2", "source": "approval", "target": "end"},
            ],
        },
    )
    db.add(version)
    db.flush()
    instance = ProcessInstance(
        org_id="org_default",
        process_version_id=version.id,
        title="Limit Case",
        requester_id=user.id,
        status="running",
        current_node_id="start",
        variables_json={"form": {"total_amount": 120000, "department": "general", "currency": "TRY"}, "system": {"department": "general"}},
        started_at=datetime.now(timezone.utc),
    )
    db.add(instance)
    db.flush()
    BPMEngine(db).run_until_wait(instance, actor=user)
    db.flush()
    approval = db.query(ApprovalInstance).filter(ApprovalInstance.process_instance_id == instance.id).first()
    assert approval is not None
    assert approval.assignee_role == "director"
