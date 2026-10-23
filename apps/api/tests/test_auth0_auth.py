from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import fraudlens.auth as auth
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from fraudlens.config import Settings

ISSUER = "https://example.eu.auth0.com/"
AUDIENCE = "https://api.fraudlens.example"
TENANT_CLAIM = "https://fraudlens.example/tenant_id"
ROLES_CLAIM = "https://fraudlens.example/roles"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def settings() -> Settings:
    return Settings(
        oidc_enabled=True,
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        oidc_jwks_url=f"{ISSUER}.well-known/jwks.json",
        oidc_algorithm="RS256",
        oidc_tenant_claim=TENANT_CLAIM,
        oidc_roles_claim=ROLES_CLAIM,
    )


def token(**overrides) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": "auth0|user-1",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        TENANT_CLAIM: "tenant-a",
        ROLES_CLAIM: ["Analyst", "viewer", "unknown-role"],
        **overrides,
    }
    return jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture(autouse=True)
def mock_auth0(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", settings)
    monkeypatch.setattr(
        auth,
        "_jwks_client",
        lambda _url: SimpleNamespace(
            get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=PRIVATE_KEY.public_key())
        ),
    )


@pytest.mark.asyncio
async def test_auth0_token_validates_issuer_audience_algorithm_and_claims():
    principal = await auth.require_principal(authorization=f"Bearer {token()}")
    assert principal.subject == "auth0|user-1"
    assert principal.tenant_id == "tenant-a"
    assert principal.roles == {"analyst", "viewer"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "wrong-audience"},
        {"iss": "https://wrong.example/"},
        {TENANT_CLAIM: ""},
        {ROLES_CLAIM: []},
    ],
)
async def test_auth0_token_rejects_invalid_identity_claims(overrides):
    with pytest.raises(HTTPException) as exc:
        await auth.require_principal(authorization=f"Bearer {token(**overrides)}")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth0_token_rejects_unexpected_signing_algorithm(monkeypatch):
    ec_key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(UTC)
    signed = jwt.encode(
        {
            "sub": "auth0|user-1",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            TENANT_CLAIM: "tenant-a",
            ROLES_CLAIM: ["viewer"],
        },
        ec_key,
        algorithm="ES256",
    )
    with pytest.raises(HTTPException) as exc:
        await auth.require_principal(authorization=f"Bearer {signed}")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_workspace_switch_uses_database_membership_role(monkeypatch):
    async def membership(subject: str, workspace: str):
        assert subject == "auth0|user-1"
        assert workspace == "tenant-b"
        return SimpleNamespace(role="reviewer")

    monkeypatch.setattr(auth, "_active_workspace_membership", membership)
    principal = await auth.require_principal(
        authorization=f"Bearer {token()}", x_workspace_id="tenant-b"
    )
    assert principal.tenant_id == "tenant-b"
    assert principal.roles == {"reviewer"}


@pytest.mark.asyncio
async def test_workspace_switch_rejects_cross_tenant_access(monkeypatch):
    async def no_membership(_subject: str, _workspace: str):
        return None

    monkeypatch.setattr(auth, "_active_workspace_membership", no_membership)
    with pytest.raises(HTTPException) as exc:
        await auth.require_principal(
            authorization=f"Bearer {token()}", x_workspace_id="tenant-secret"
        )
    assert exc.value.status_code == 403
