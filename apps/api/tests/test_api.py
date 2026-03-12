"""Smoke tests for API endpoints using httpx."""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.main import app
from app.database import Base, get_db
from app.auth import hash_password
from app.models.user import User


TEST_DB_URL = "postgresql+asyncpg://eflow:eflow_secret@localhost:5432/eflow"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_token(client):
    """Get admin auth token."""
    response = await client.post("/auth/login", json={
        "email": "admin@eflow.com",
        "password": "admin123",
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture
def auth_headers(auth_token):
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.mark.asyncio
class TestAuth:
    async def test_login_success(self, client):
        response = await client.post("/auth/login", json={
            "email": "admin@eflow.com",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@eflow.com"
        assert data["user"]["role"] == "admin"

    async def test_login_invalid_credentials(self, client):
        response = await client.post("/auth/login", json={
            "email": "admin@eflow.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    async def test_me_endpoint(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@eflow.com"

    async def test_me_unauthorized(self, client):
        response = await client.get("/auth/me")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestFlows:
    async def test_list_flows(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get("/flows", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_flows_has_templates(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get("/flows", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        flows = response.json()
        template_keys = [f["template_key"] for f in flows if f.get("template_key")]
        assert "pr_request" in template_keys
        assert "p2p_process" in template_keys
        assert "contract_process" in template_keys
        assert "invoice_payment" in template_keys

    async def test_create_flow(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.post(
            "/flows",
            json={"name": "Test Flow", "description": "A test flow"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Flow"
        assert data["latest_version"]["status"] == "draft"

    async def test_update_flow(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        # Create first
        create_resp = await client.post(
            "/flows",
            json={"name": "Flow To Update"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        flow_id = create_resp.json()["id"]

        # Update
        update_resp = await client.put(
            f"/flows/{flow_id}",
            json={"name": "Updated Flow Name", "graph_json": {"nodes": [], "edges": []}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Flow Name"

    async def test_publish_flow(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        create_resp = await client.post(
            "/flows",
            json={"name": "Flow To Publish"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        flow_id = create_resp.json()["id"]

        pub_resp = await client.post(
            f"/flows/{flow_id}/publish",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert pub_resp.status_code == 200
        assert pub_resp.json()["latest_version"]["status"] == "published"


@pytest.mark.asyncio
class TestInstances:
    async def test_list_instances(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get("/instances", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_start_instance_from_template(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")

        # Get PR template version
        flows_resp = await client.get("/flows", headers={"Authorization": f"Bearer {auth_token}"})
        flows = flows_resp.json()
        pr_flow = next((f for f in flows if f.get("template_key") == "pr_request"), None)
        if not pr_flow:
            pytest.skip("PR template not found")

        version_id = pr_flow["latest_version"]["id"]

        start_resp = await client.post(
            "/instances/start",
            json={
                "flow_version_id": version_id,
                "title": "Test PR Instance",
                "initial_inputs": {
                    "total_amount": 30000,
                    "currency": "TRY",
                    "request_type": "Mal Alımı",
                    "vendor_name": "Test Vendor",
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert start_resp.status_code == 200
        data = start_resp.json()
        assert data["title"] == "Test PR Instance"
        assert data["status"] in ["running", "completed"]
        return data["id"]

    async def test_instance_timeline(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")

        # Start an instance first
        flows_resp = await client.get("/flows", headers={"Authorization": f"Bearer {auth_token}"})
        flows = flows_resp.json()
        pr_flow = next((f for f in flows if f.get("template_key") == "pr_request"), None)
        if not pr_flow:
            pytest.skip("PR template not found")

        version_id = pr_flow["latest_version"]["id"]
        start_resp = await client.post(
            "/instances/start",
            json={
                "flow_version_id": version_id,
                "title": "Timeline Test Instance",
                "initial_inputs": {"total_amount": 10000}
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert start_resp.status_code == 200
        instance_id = start_resp.json()["id"]

        timeline_resp = await client.get(
            f"/instances/{instance_id}/timeline",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert timeline_resp.status_code == 200
        events = timeline_resp.json()
        assert len(events) > 0
        event_types = [e["event_type"] for e in events]
        assert "instance.started" in event_types


@pytest.mark.asyncio
class TestExpressions:
    async def test_preview_expression(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.post(
            "/expressions/preview",
            json={
                "expression": "{{ form.total_amount * 1.20 }}",
                "context": {"form": {"total_amount": 100000}}
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == pytest.approx(120000.0)
        assert data["error"] is None

    async def test_context_schema(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get(
            "/expressions/context/schema",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        schema = response.json()
        assert isinstance(schema, list)
        keys = [s["key"] for s in schema]
        assert any("form" in k for k in keys)


@pytest.mark.asyncio
class TestUsers:
    async def test_list_users(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get("/users", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 4  # We seeded 7 users

    async def test_approval_limits(self, client, auth_token):
        if not auth_token:
            pytest.skip("No auth token")
        response = await client.get("/users/approval-limits", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        limits = response.json()
        assert len(limits) >= 3  # We seeded 3 limits

    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
