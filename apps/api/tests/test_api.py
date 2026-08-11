from uuid import uuid4

from fastapi.testclient import TestClient
from fraudlens.main import app

HEADERS = {
    "X-API-Key": "fraudlens-local-dev-key",
    "X-Tenant-ID": "demo",
    "X-Actor": "test-analyst",
}


def test_health_is_public_and_dashboard_is_protected() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/dashboard").status_code == 401
        assert client.get("/api/v1/dashboard", headers=HEADERS).status_code == 200


def test_persistent_case_workflow_is_tenant_scoped_and_audited() -> None:
    suffix = uuid4().hex[:8]
    case_id = f"TEST-{suffix}"
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/cases",
            headers=HEADERS,
            json={
                "id": case_id,
                "tenant_id": "demo",
                "subject": "Supplier payment request",
                "case_type": "Invoice + email",
            },
        )
        assert created.status_code == 201

        evidence = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            headers=HEADERS,
            json={
                "id": f"{case_id}-email",
                "kind": "email",
                "source": "message.eml",
                "attributes": {"reply_to_mismatch": True, "spf_pass": False},
            },
        )
        assert evidence.status_code == 201

        report = client.post(f"/api/v1/cases/{case_id}/investigate", headers=HEADERS)
        assert report.status_code == 200
        assert report.json()["risk"]["score"] > 0
        assert report.json()["citations"] == [f"{case_id}-email"]

        detail = client.get(f"/api/v1/cases/{case_id}", headers=HEADERS)
        assert detail.status_code == 200
        assert detail.json()["latest_report"]["case_id"] == case_id

        other_tenant = {**HEADERS, "X-Tenant-ID": "other"}
        assert client.get(f"/api/v1/cases/{case_id}", headers=other_tenant).status_code == 404

        audit = client.get("/api/v1/audit", headers=HEADERS)
        actions = {entry["action"] for entry in audit.json() if entry["resource_id"] == case_id}
        assert actions == {"case.created", "evidence.added", "investigation.completed"}


def test_operational_read_models_are_available() -> None:
    with TestClient(app) as client:
        for path in (
            "/api/v1/investigations",
            "/api/v1/graph",
            "/api/v1/agents",
            "/api/v1/policies",
            "/api/v1/models/health",
            "/api/v1/audit",
        ):
            response = client.get(path, headers=HEADERS)
            assert response.status_code == 200, path
