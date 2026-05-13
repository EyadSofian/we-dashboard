"""APScheduler-based polling: every N minutes, fetch all active accounts."""
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from .config import get_settings
from .db import SessionLocal
from .models import Account, Snapshot
from .we_client import fetch_with_retry, WEAuthError
from .security import decrypt
from .alerts import evaluate_and_fire

logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = AsyncIOScheduler()


async def poll_account(account_id: int) -> None:
    async with SessionLocal() as db:
        acc = await db.get(Account, account_id)
        if not acc or not acc.is_active:
            return
        try:
            password = decrypt(acc.password_enc)
            snap = await fetch_with_retry(acc.landline, password)
        except WEAuthError as e:
            logger.error("Auth error on account %s: %s. Disabling.", acc.landline, e)
            acc.is_active = False
            await db.commit()
            return
        except Exception as e:
            logger.error("Poll failed for account %s: %s", acc.landline, e)
            return

        snapshot = Snapshot(
            account_id=acc.id,
            customer_name=snap.customer_name,
            offer_name=snap.offer_name,
            total_gb=snap.total_gb,
            used_gb=snap.used_gb,
            remain_gb=snap.remain_gb,
            usage_pct=snap.usage_pct,
            effective_time_ms=snap.effective_time_ms,
            expire_time_ms=snap.expire_time_ms,
            taken_at=datetime.utcnow(),
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)

        # Refresh account in same session for relationships
        await evaluate_and_fire(db, acc, snapshot)


async def poll_all() -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(Account).where(Account.is_active.is_(True)))
        ids = [row.id for row in result.scalars().all()]
    for aid in ids:
        try:
            await poll_account(aid)
        except Exception as e:
            logger.exception("Unexpected error polling %s: %s", aid, e)


def start_scheduler():
    scheduler.add_job(
        poll_all,
        "interval",
        minutes=settings.POLL_INTERVAL_MINUTES,
        id="poll_all",
        coalesce=True,
        max_instances=1,
        next_run_time=datetime.utcnow(),  # run immediately on startup
    )
    scheduler.start()
    logger.info("Scheduler started, polling every %d minutes", settings.POLL_INTERVAL_MINUTES)


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
