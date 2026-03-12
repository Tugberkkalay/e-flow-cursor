"""API integration tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.services.auth import hash_password
from app.models.models import User, ProcessDefinition, ProcessVersion
import uuid


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(User).filter(User.id == "test_admin").first() is None:
        admin = User(
            id="test_admin",
            email="test@eflow.io",
            name="Test Admin",
            hashed_password=hash_password("test123"),
            role="admin",
            department="IT",
            org_id="org_1",
        )
        db.add(admin)

        flow_id = str(uuid.uuid4())
        flow = ProcessDefinition(
            id=flow_id,
            name="Test Flow",
            status="published",
            current_version=1,
            org_id="org_1",
        )
        db.add(flow)

        version = ProcessVersion(
            id=str(uuid.uuid4()),
            flow_id=flow_id,
            version=1,
            graph_json={
                "nodes": [
                    {"id": "n1", "type": "customNode", "position": {"x": 0, "y": 0}, "data": {"label": "Start", "nodeType": "manual_start", "engineType": "Event", "config": {}}},
                    {"id": "n2", "type": "customNode", "position": {"x": 0, "y": 120}, "data": {"label": "End", "nodeType": "end", "engineType": "End", "config": {"exports": {"status": "done"}}}},
                ],
                "edges": [
                    {"id": "e1", "source": "n1", "target": "n2", "type": "smartEdge"},
                ],
            },
            status="published",
        )
        db.add(version)
        db.commit()
    db.close()
    yield


client = TestClient(app)


def get_token():
    resp = client.post("/api/auth/login", json={"email": "test@eflow.io", "password": "test123"})
    return resp.json()["access_token"]


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login():
    resp = client.post("/api/auth/login", json={"email": "test@eflow.io", "password": "test123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me():
    token = get_token()
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@eflow.io"


def test_list_flows():
    token = get_token()
    resp = client.get("/api/flows", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_start_instance_and_complete():
    token = get_token()
    flows = client.get("/api/flows", headers={"Authorization": f"Bearer {token}"}).json()
    test_flow = [f for f in flows if f["name"] == "Test Flow"][0]

    resp = client.post(
        "/api/instances/start",
        json={"flow_id": test_flow["id"], "initial_inputs": {"test": True}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    inst = resp.json()
    assert inst["status"] == "completed"
    assert inst["variables"]["exports"]["status"] == "done"


def test_expression_preview():
    resp = client.post(
        "/api/expressions/preview",
        json={"expression": "{{ a + b }}", "context": {"a": 10, "b": 20}},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 30


def test_context_schema():
    resp = client.get("/api/context/schema")
    assert resp.status_code == 200
    assert "form" in resp.json()["namespaces"]
