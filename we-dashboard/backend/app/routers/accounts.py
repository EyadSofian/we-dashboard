from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..deps import require_auth
from ..models import Account
from ..schemas import AccountCreate, AccountUpdate, AccountOut
from ..security import encrypt
from ..we_client import WEClient, WEAuthError

router = APIRouter(prefix="/api/accounts", tags=["accounts"], dependencies=[Depends(require_auth)])


@router.get("", response_model=List[AccountOut])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).order_by(Account.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=AccountOut, status_code=201)
async def create_account(body: AccountCreate, db: AsyncSession = Depends(get_db)):
    landline = body.landline.strip()
    # Check duplicate
    existing = await db.execute(select(Account).where(Account.landline == landline))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Landline already exists")

    # Verify credentials before saving (fail fast)
    try:
        await WEClient(landline, body.password).fetch_quota()
    except WEAuthError as e:
        raise HTTPException(status_code=401, detail=f"WE auth failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"WE API error: {e}")

    acc = Account(
        landline=landline,
        password_enc=encrypt(body.password),
        label=body.label or "",
        is_active=True,
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return acc


@router.patch("/{account_id}", response_model=AccountOut)
async def update_account(account_id: int, body: AccountUpdate, db: AsyncSession = Depends(get_db)):
    acc = await db.get(Account, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Not found")
    if body.label is not None:
        acc.label = body.label
    if body.is_active is not None:
        acc.is_active = body.is_active
    if body.password is not None:
        try:
            await WEClient(acc.landline, body.password).fetch_quota()
        except WEAuthError as e:
            raise HTTPException(status_code=401, detail=f"WE auth failed: {e}")
        acc.password_enc = encrypt(body.password)
    await db.commit()
    await db.refresh(acc)
    return acc


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    acc = await db.get(Account, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(acc)
    await db.commit()
