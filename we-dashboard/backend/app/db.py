import json
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def init_db():
    from . import models  # noqa: F401
    from .models import Account
    from .security import encrypt

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    seed_raw = settings.ACCOUNTS_SEED.strip()
    if not seed_raw:
        return

    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Account))
        if count and count > 0:
            logger.info("Seed skipped — %d account(s) already exist.", count)
            return

        try:
            entries = json.loads(seed_raw)
        except json.JSONDecodeError as e:
            logger.error("ACCOUNTS_SEED is not valid JSON: %s", e)
            return

        seeded = 0
        for entry in entries:
            landline = str(entry.get("landline", "")).strip()
            password = str(entry.get("password", "")).strip()
            label    = str(entry.get("label", "")).strip()
            if not landline or not password:
                logger.warning("Seed entry missing, skipping: %s", entry)
                continue
            session.add(Account(
                landline=landline,
                password_enc=encrypt(password),
                label=label,
                is_active=True,
            ))
            seeded += 1

        await session.commit()
        logger.info("Seeded %d account(s) from ACCOUNTS_SEED.", seeded)
