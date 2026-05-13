"""Threshold-based alert dispatcher posting to n8n webhook."""
import logging
from datetime import datetime
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings
from .models import Account, AlertConfig, AlertLog, Snapshot

logger = logging.getLogger(__name__)
settings = get_settings()


async def evaluate_and_fire(
    db: AsyncSession,
    account: Account,
    snapshot: Snapshot,
) -> None:
    """Fire any threshold alert that:
       - is enabled
       - has threshold_pct <= snapshot.usage_pct
       - has NOT yet fired for this quota cycle (dedupe via effective_time)
    """
    if not settings.N8N_WEBHOOK_URL:
        return

    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.account_id == account.id,
            AlertConfig.enabled.is_(True),
        )
    )
    configs = result.scalars().all()
    if not configs:
        return

    for cfg in configs:
        if snapshot.usage_pct < cfg.threshold_pct:
            continue
        # Dedupe: skip if already fired for this quota cycle
        if cfg.last_fired_effective_ms == snapshot.effective_time_ms:
            continue

        payload = {
            "event": "we.quota.threshold",
            "account_id": account.id,
            "label": account.label or account.landline,
            "landline": account.landline,
            "customer_name": snapshot.customer_name,
            "offer_name": snapshot.offer_name,
            "threshold_pct": cfg.threshold_pct,
            "usage_pct": round(snapshot.usage_pct, 2),
            "used_gb": snapshot.used_gb,
            "remain_gb": snapshot.remain_gb,
            "total_gb": snapshot.total_gb,
            "expire_time_iso": datetime.utcfromtimestamp(
                snapshot.expire_time_ms / 1000.0
            ).isoformat() + "Z",
            "snapshot_taken_at": snapshot.taken_at.isoformat() + "Z",
        }

        success = True
        response_text = ""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(settings.N8N_WEBHOOK_URL, json=payload)
                response_text = r.text[:1000]
                r.raise_for_status()
        except Exception as e:
            success = False
            response_text = f"{type(e).__name__}: {e}"
            logger.error("Alert webhook failed: %s", e)

        # Update dedupe marker (only on success, so failures retry next poll)
        if success:
            cfg.last_fired_effective_ms = snapshot.effective_time_ms

        db.add(
            AlertLog(
                account_id=account.id,
                threshold_pct=cfg.threshold_pct,
                success=success,
                response=response_text,
            )
        )

    await db.commit()
