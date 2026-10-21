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
            signing_key = jwt.PyJWKClient(settings.oidc_jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=settings.oidc_audience,
                issuer=settings.oidc_issuer,
            )
            tenant = claims.get(settings.oidc_tenant_claim)
            raw_roles = claims.get(settings.oidc_roles_claim, [])
            roles = frozenset(raw_roles if isinstance(raw_roles, list) else str(raw_roles).split())
            if not tenant or not roles or not claims.get("sub"):
                raise ValueError("Required identity claims missing")
            if x_workspace_id and x_workspace_id != tenant:
                from sqlalchemy import select

                from fraudlens.database import MembershipRecord, session_factory

                async with session_factory() as session:
                    membership = await session.scalar(
                        select(MembershipRecord).where(
                            MembershipRecord.tenant_id == x_workspace_id,
                            MembershipRecord.subject == claims["sub"],
                            MembershipRecord.status == "ACTIVE",
                        )
                    )
                if not membership:
                    raise HTTPException(status_code=403, detail="Workspace membership required")
                tenant = x_workspace_id
                roles = frozenset({membership.role})
            return Principal(subject=claims["sub"], tenant_id=tenant, roles=roles)
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
