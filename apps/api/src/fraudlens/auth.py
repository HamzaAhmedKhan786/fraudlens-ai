from hmac import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from fraudlens.config import get_settings


class Principal(BaseModel):
    subject: str
    tenant_id: str
    roles: frozenset[str]


async def require_principal(
    x_api_key: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str, Header()] = "demo",
    x_actor: Annotated[str, Header()] = "local-analyst",
    x_roles: Annotated[str, Header()] = "analyst,reviewer,admin",
) -> Principal:
    expected = get_settings().api_key
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
