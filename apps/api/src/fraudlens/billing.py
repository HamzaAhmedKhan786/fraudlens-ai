import hashlib
import hmac
import json
import time

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fraudlens.auth import Principal, require_role
from fraudlens.config import get_settings
from fraudlens.database import AuditRecord, SubscriptionRecord
from fraudlens.schemas import BillingAction, SubscriptionSelection


def verify_signature(body: bytes, header: str, secret: str, tolerance: int = 300) -> dict:
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    timestamp = int(parts.get("t", "0"))
    signature = parts.get("v1", "")
    if abs(int(time.time()) - timestamp) > tolerance:
        raise HTTPException(400, "Expired Stripe signature")
    expected = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(400, "Invalid Stripe signature")
    return json.loads(body)


async def checkout(
    session: AsyncSession, principal: Principal, payload: SubscriptionSelection
) -> BillingAction:
    require_role(principal, "admin")
    settings = get_settings()
    if not settings.stripe_enabled:
        return BillingAction(
            url=None, configured=False, detail="Stripe test mode is not configured"
        )
    attr = f"stripe_price_{payload.plan_code}_{payload.billing_interval}"
    price = getattr(settings, attr, None)
    if not price:
        raise HTTPException(503, "Selected plan price is not configured")
    data = {
        "mode": "subscription",
        "line_items[0][price]": price,
        "line_items[0][quantity]": "1",
        "subscription_data[trial_period_days]": str(settings.subscription_trial_days),
        "success_url": settings.billing_return_url + "?checkout=success",
        "cancel_url": settings.billing_return_url + "?checkout=cancelled",
        "metadata[tenant_id]": principal.tenant_id,
        "metadata[plan_code]": payload.plan_code,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            data=data,
            auth=(settings.stripe_secret_key, ""),
        )
    if r.status_code >= 400:
        raise HTTPException(502, "Stripe test checkout request failed")
    result = r.json()
    session.add(
        AuditRecord(
            tenant_id=principal.tenant_id,
            actor=principal.subject,
            action="billing.checkout_created",
            resource_id=principal.tenant_id,
            payload={"plan": payload.plan_code},
        )
    )
    await session.commit()
    return BillingAction(
        url=result.get("url"), configured=True, detail="Stripe test checkout created"
    )


async def portal(session: AsyncSession, principal: Principal) -> BillingAction:
    require_role(principal, "admin")
    settings = get_settings()
    row = await session.get(SubscriptionRecord, principal.tenant_id)
    if not settings.stripe_enabled:
        return BillingAction(
            url=None, configured=False, detail="Stripe test mode is not configured"
        )
    if not row or not row.provider_customer_id:
        raise HTTPException(409, "No Stripe test customer is linked")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.stripe.com/v1/billing_portal/sessions",
            data={"customer": row.provider_customer_id, "return_url": settings.billing_return_url},
            auth=(settings.stripe_secret_key, ""),
        )
    if r.status_code >= 400:
        raise HTTPException(502, "Stripe test portal request failed")
    return BillingAction(
        url=r.json().get("url"), configured=True, detail="Stripe test portal created"
    )
