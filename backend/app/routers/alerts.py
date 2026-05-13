from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..deps import require_auth
from ..models import Account, AlertConfig, AlertLog
from ..schemas import AlertConfigIn, AlertConfigOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"], dependencies=[Depends(require_auth)])


@router.get("/{account_id}", response_model=List[AlertConfigOut])
async def list_alerts(account_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(AlertConfig).where(AlertConfig.account_id == account_id).order_by(AlertConfig.threshold_pct.asc())
    )
    return list(r.scalars().all())


@router.post("/{account_id}", response_model=AlertConfigOut, status_code=201)
async def add_alert(account_id: int, body: AlertConfigIn, db: AsyncSession = Depends(get_db)):
    acc = await db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "Account not found")
    cfg = AlertConfig(
        account_id=account_id,
        threshold_pct=body.threshold_pct,
        enabled=body.enabled,
    )
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return cfg


@router.patch("/{alert_id}", response_model=AlertConfigOut)
async def update_alert(alert_id: int, body: AlertConfigIn, db: AsyncSession = Depends(get_db)):
    cfg = await db.get(AlertConfig, alert_id)
    if not cfg:
        raise HTTPException(404, "Not found")
    cfg.threshold_pct = body.threshold_pct
    cfg.enabled = body.enabled
    await db.commit()
    await db.refresh(cfg)
    return cfg


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    cfg = await db.get(AlertConfig, alert_id)
    if not cfg:
        raise HTTPException(404, "Not found")
    await db.delete(cfg)
    await db.commit()


@router.get("/logs/{account_id}")
async def alert_logs(account_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(AlertLog)
        .where(AlertLog.account_id == account_id)
        .order_by(desc(AlertLog.fired_at))
        .limit(50)
    )
    rows = list(r.scalars().all())
    return [
        {
            "id": x.id,
            "threshold_pct": x.threshold_pct,
            "fired_at": x.fired_at.isoformat() + "Z",
            "success": x.success,
            "response": (x.response or "")[:400],
        }
        for x in rows
    ]
