from uuid import uuid4

from fastapi.testclient import TestClient
from fraudlens.main import app
from fraudlens.schemas import DomainLookup
from pydantic import ValidationError

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
            "/api/v1/intelligence/public",
            "/api/v1/audit",
        ):
            response = client.get(path, headers=HEADERS)
            assert response.status_code == 200, path


def test_public_intelligence_domain_input_is_constrained() -> None:
    assert DomainLookup(domain="example.com").domain == "example.com"
    try:
        DomainLookup(domain="not_a_domain!")
    except ValidationError:
        return
    raise AssertionError("Invalid domain was accepted")


def test_secure_upload_is_processed_and_deduplicated() -> None:
    suffix = uuid4().hex[:8]
    case_id = f"UPLOAD-{suffix}"
    content = f"trusted evidence {suffix}".encode()
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/cases",
            headers=HEADERS,
            json={
                "id": case_id,
                "tenant_id": "demo",
                "subject": "Evidence intake test",
                "case_type": "Document",
            },
        )
        assert created.status_code == 201
        first = client.post(
            f"/api/v1/cases/{case_id}/uploads",
            headers=HEADERS,
            files={"file": (f"evidence-{suffix}.txt", content, "text/plain")},
        )
        assert first.status_code == 201
        payload = first.json()
        assert payload["status"] == "PROCESSED"
        assert payload["scan_status"] == "SKIPPED"
        assert payload["extracted"]["text_excerpt"] == content.decode()

        duplicate = client.post(
            f"/api/v1/cases/{case_id}/uploads",
            headers=HEADERS,
            files={"file": (f"copy-{suffix}.txt", content, "text/plain")},
        )
        assert duplicate.status_code == 201
        assert duplicate.json()["id"] == payload["id"]

        listing = client.get(f"/api/v1/uploads?case_id={case_id}", headers=HEADERS)
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        download = client.get(f"/api/v1/uploads/{payload['id']}/content", headers=HEADERS)
        assert download.status_code == 200
        assert download.content == content
        assert "attachment" in download.headers["content-disposition"]


def test_upload_rejects_unsupported_content() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/cases/FR-29482/uploads",
            headers=HEADERS,
            files={"file": ("payload.exe", b"MZ-not-an-allowed-file", "application/octet-stream")},
        )
        assert response.status_code == 415


def test_case_workflow_settings_and_policy_are_persisted() -> None:
    suffix = uuid4().hex[:8]
    case_id = f"FLOW-{suffix}"
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/v1/cases",
                headers=HEADERS,
                json={
                    "id": case_id,
                    "tenant_id": "demo",
                    "subject": "Workflow test",
                    "case_type": "Email",
                },
            ).status_code
            == 201
        )
        updated = client.patch(
            f"/api/v1/cases/{case_id}",
            headers=HEADERS,
            json={"assignee": "analyst@example.com", "status": "ESCALATED"},
        )
        assert updated.status_code == 200
        assert updated.json()["assignee"] == "analyst@example.com"
        assert (
            client.post(
                f"/api/v1/cases/{case_id}/comments",
                headers=HEADERS,
                json={"body": "Validated sender anomaly."},
            ).status_code
            == 201
        )
        decided = client.patch(
            f"/api/v1/cases/{case_id}",
            headers=HEADERS,
            json={"disposition": "INCONCLUSIVE"},
        )
        assert decided.json()["status"] == "RESOLVED"
        assert len(decided.json()["comments"]) == 1

        settings = client.put(
            "/api/v1/settings",
            headers=HEADERS,
            json={
                "mandatory_human_review": True,
                "llm_narrative_enabled": False,
                "critical_risk_threshold": 85,
                "evidence_retention_days": 365,
            },
        )
        assert settings.status_code == 200
        assert (
            client.get("/api/v1/settings", headers=HEADERS).json()["critical_risk_threshold"] == 85
        )

        policies = client.get("/api/v1/policies", headers=HEADERS).json()
        policy = policies[0]
        changed = client.put(
            f"/api/v1/policies/{policy['id']}",
            headers=HEADERS,
            json={"enabled": False, "threshold": 91},
        )
        assert changed.status_code == 200
        assert changed.json()["threshold"] == 91


def test_reviewer_role_is_required_for_final_disposition() -> None:
    headers = {**HEADERS, "X-Roles": "analyst"}
    with TestClient(app) as client:
        response = client.patch(
            "/api/v1/cases/FR-29482",
            headers=headers,
            json={"disposition": "CONFIRMED_FRAUD"},
        )
        assert response.status_code == 403
