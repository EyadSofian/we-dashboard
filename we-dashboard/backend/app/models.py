from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, Text
)
from sqlalchemy.orm import relationship
from .db import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    landline = Column(String(32), unique=True, nullable=False, index=True)
    password_enc = Column(Text, nullable=False)  # Fernet-encrypted
    label = Column(String(120), nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    snapshots = relationship("Snapshot", back_populates="account", cascade="all, delete-orphan")
    alerts = relationship("AlertConfig", back_populates="account", cascade="all, delete-orphan")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    customer_name = Column(String(200), nullable=True)
    offer_name = Column(String(200), nullable=True)
    total_gb = Column(Float, nullable=False)
    used_gb = Column(Float, nullable=False)
    remain_gb = Column(Float, nullable=False)
    usage_pct = Column(Float, nullable=False)
    effective_time_ms = Column(Integer, nullable=False)   # epoch ms
    expire_time_ms = Column(Integer, nullable=False)      # epoch ms
    taken_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    account = relationship("Account", back_populates="snapshots")


Index("ix_snapshots_account_taken", Snapshot.account_id, Snapshot.taken_at)


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    threshold_pct = Column(Float, nullable=False)  # e.g. 80, 90, 95
    enabled = Column(Boolean, nullable=False, default=True)
    last_fired_effective_ms = Column(Integer, nullable=True)  # dedupe per quota cycle

    account = relationship("Account", back_populates="alerts")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False)
    threshold_pct = Column(Float, nullable=False)
    fired_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    success = Column(Boolean, nullable=False, default=True)
    response = Column(Text, nullable=True)
