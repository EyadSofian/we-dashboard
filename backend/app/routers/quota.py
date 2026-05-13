from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..deps import require_auth
from ..models import Account, Snapshot
from ..schemas import SnapshotOut, DashboardOut, AccountOut, ManualRefreshOut
from ..security import decrypt
from ..we_client import fetch_with_retry, WEAuthError
from ..forecast import compute_forecast
from ..alerts import evaluate_and_fire

router = APIRouter(prefix="/api", tags=["quota"], dependencies=[Depends(require_auth)])


@router.get("/dashboard/{account_id}", response_model=DashboardOut)
async def dashboard(account_id: int, db: AsyncSession = Depends(get_db)):
    acc = await db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "Account not found")

    # Latest snapshot
    r = await db.execute(
        select(Snapshot)
        .where(Snapshot.account_id == account_id)
        .order_by(desc(Snapshot.taken_at))
        .limit(1)
    )
    latest = r.scalar_one_or_none()

    # Forecast: use last 14 days within current cycle
    cutoff = datetime.utcnow() - timedelta(days=14)
    r2 = await db.execute(
        select(Snapshot)
        .where(Snapshot.account_id == account_id, Snapshot.taken_at >= cutoff)
        .order_by(Snapshot.taken_at.asc())
    )
    snaps = list(r2.scalars().all())
    forecast = compute_forecast(snaps) if snaps else None

    return DashboardOut(
        account=AccountOut.model_validate(acc),
        latest=SnapshotOut.model_validate(latest) if latest else None,
        forecast=forecast,
    )


@router.get("/history/{account_id}", response_model=List[SnapshotOut])
async def history(
    account_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    r = await db.execute(
        select(Snapshot)
        .where(Snapshot.account_id == account_id, Snapshot.taken_at >= cutoff)
        .order_by(Snapshot.taken_at.asc())
    )
    return list(r.scalars().all())


@router.post("/refresh/{account_id}", response_model=ManualRefreshOut)
async def manual_refresh(account_id: int, db: AsyncSession = Depends(get_db)):
    acc = await db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "Account not found")
    try:
        password = decrypt(acc.password_enc)
        snap = await fetch_with_retry(acc.landline, password)
    except WEAuthError as e:
        return ManualRefreshOut(ok=False, snapshot=None, error=f"Auth failed: {e}")
    except Exception as e:
        return ManualRefreshOut(ok=False, snapshot=None, error=str(e))

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
    await evaluate_and_fire(db, acc, snapshot)
    return ManualRefreshOut(ok=True, snapshot=SnapshotOut.model_validate(snapshot))
