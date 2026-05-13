"""Usage forecasting based on snapshot history."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .models import Snapshot
from .schemas import ForecastOut


def compute_forecast(snapshots: List[Snapshot]) -> Optional[ForecastOut]:
    """
    Linear forecast from the most recent N snapshots.
    Assumes snapshots are within the same quota cycle (same effective_time).
    Returns None if insufficient data.
    """
    if not snapshots or len(snapshots) < 2:
        return None

    # Sort ascending by taken_at
    snaps = sorted(snapshots, key=lambda s: s.taken_at)
    # Take snapshots from the latest quota cycle only (same effective_time)
    latest_effective = snaps[-1].effective_time_ms
    cycle = [s for s in snaps if s.effective_time_ms == latest_effective]
    if len(cycle) < 2:
        return None

    first, last = cycle[0], cycle[-1]
    elapsed_hours = (last.taken_at - first.taken_at).total_seconds() / 3600.0
    if elapsed_hours <= 0:
        return None

    used_delta = last.used_gb - first.used_gb
    if used_delta < 0:
        # Quota reset within window or anomaly
        return None

    hourly_avg = used_delta / elapsed_hours
    daily_avg = hourly_avg * 24

    if daily_avg <= 0:
        return ForecastOut(
            daily_avg_gb=0.0,
            days_until_exhaust=None,
            exhaust_date_iso=None,
            will_exhaust_before_renewal=False,
            confidence="low",
            sample_days=int(elapsed_hours / 24),
        )

    days_left = last.remain_gb / daily_avg
    exhaust_dt = datetime.now(timezone.utc) + timedelta(days=days_left)
    renewal_dt = datetime.fromtimestamp(last.expire_time_ms / 1000.0, tz=timezone.utc)
    will_exhaust = exhaust_dt < renewal_dt

    # Confidence based on sample size
    sample_days = elapsed_hours / 24
    if sample_days >= 7:
        confidence = "high"
    elif sample_days >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return ForecastOut(
        daily_avg_gb=round(daily_avg, 2),
        days_until_exhaust=round(days_left, 1),
        exhaust_date_iso=exhaust_dt.isoformat(),
        will_exhaust_before_renewal=will_exhaust,
        confidence=confidence,
        sample_days=int(sample_days),
    )
