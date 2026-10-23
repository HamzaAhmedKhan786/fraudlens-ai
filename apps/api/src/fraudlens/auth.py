from functools import lru_cache
from hmac import compare_digest
from typing import Annotated

import jwt
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from fraudlens.config import get_settings


class Principal(BaseModel):
    subject: str
    tenant_id: str
    roles: frozenset[str]


ALLOWED_ROLES = frozenset({"admin", "analyst", "reviewer", "viewer", "executive"})


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=300)


def _claim_set(value: object) -> frozenset[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        raw = (str(item) for item in value)
    else:
        raw = str(value or "").replace(",", " ").split()
    return frozenset(item.strip().lower() for item in raw if item.strip())


def _decode_oidc_token(token: str) -> Principal:
    settings = get_settings()
    header = jwt.get_unverified_header(token)
    if header.get("alg") != settings.oidc_algorithm:
        raise ValueError("Unexpected signing algorithm")
    signing_key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=[settings.oidc_algorithm],
        audience=settings.oidc_audience,
        issuer=settings.oidc_issuer,
        options={"require": ["exp", "iat", "sub"]},
    )
    tenant = claims.get(settings.oidc_tenant_claim)
    roles = _claim_set(claims.get(settings.oidc_roles_claim, [])) & ALLOWED_ROLES
    if not isinstance(tenant, str) or not tenant.strip() or not roles:
        raise ValueError("Required identity claims missing")
    return Principal(subject=claims["sub"], tenant_id=tenant.strip(), roles=roles)


async def _active_workspace_membership(subject: str, workspace_id: str):
    from sqlalchemy import select

    from fraudlens.database import MembershipRecord, session_factory

    async with session_factory() as session:
        return await session.scalar(
            select(MembershipRecord).where(
                MembershipRecord.tenant_id == workspace_id,
                MembershipRecord.subject == subject,
                MembershipRecord.status == "ACTIVE",
            )
        )


async def require_principal(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str, Header()] = "demo",
    x_actor: Annotated[str, Header()] = "local-analyst",
    x_roles: Annotated[str, Header()] = "analyst,reviewer,admin",
    x_workspace_id: Annotated[str | None, Header()] = None,
) -> Principal:
    settings = get_settings()
    if authorization and authorization.startswith("Bearer "):
        if not settings.oidc_enabled:
            raise HTTPException(status_code=401, detail="OIDC authentication is disabled")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            principal = _decode_oidc_token(token)
            if x_workspace_id and x_workspace_id != principal.tenant_id:
                membership = await _active_workspace_membership(principal.subject, x_workspace_id)
                if not membership:
                    raise HTTPException(status_code=403, detail="Workspace membership required")
                return Principal(
                    subject=principal.subject,
                    tenant_id=x_workspace_id,
                    roles=frozenset({membership.role.lower()}),
                )
            return principal
        except (jwt.PyJWTError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Invalid identity token") from exc
    expected = settings.api_key
    if not x_api_key or not compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    roles = frozenset(role.strip().lower() for role in x_roles.split(",") if role.strip())
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="At least one role is required"
        )
    return Principal(subject=x_actor, tenant_id=x_tenant_id, roles=roles)


def require_role(principal: Principal, *allowed: str) -> None:
    if principal.roles.isdisjoint(allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
