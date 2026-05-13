import { Forecast } from "../api/client";
import { TrendingDown, Calendar, Activity } from "lucide-react";
import { fmtDate } from "../lib/format";

interface Props {
  forecast: Forecast | null;
  expireMs: number | null;
}

export default function ForecastCard({ forecast, expireMs }: Props) {
  if (!forecast) {
    return (
      <div className="card p-5">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Activity className="w-4 h-4" /> Forecast
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Need at least 2 snapshots in the current cycle. Forecast will appear after
          the scheduler runs a few times.
        </p>
      </div>
    );
  }

  const willHit = forecast.will_exhaust_before_renewal;
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300 text-sm">
          <TrendingDown className="w-4 h-4" /> Forecast
        </div>
        <span
          className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border
          ${forecast.confidence === "high"
              ? "border-good/40 text-good bg-good/10"
              : forecast.confidence === "medium"
                ? "border-warn/40 text-warn bg-warn/10"
                : "border-slate-500/40 text-slate-400 bg-slate-500/10"
            }`}
        >
          {forecast.confidence} confidence
        </span>
      </div>

      <div className="mt-4 space-y-3">
        <Row label="Daily average" value={`${forecast.daily_avg_gb.toFixed(2)} GB / day`} />
        <Row
          label="Days until exhaust"
          value={
            forecast.days_until_exhaust == null
              ? "—"
              : `${forecast.days_until_exhaust.toFixed(1)} days`
          }
        />
        <Row label="Predicted exhaust" value={fmtDate(forecast.exhaust_date_iso)} icon={Calendar} />
        <Row label="Renewal date" value={expireMs ? fmtDate(new Date(expireMs).toISOString()) : "—"} icon={Calendar} />
      </div>

      <div
        className={`mt-4 px-3 py-2 rounded-lg text-xs ${willHit
            ? "bg-bad/10 text-bad border border-bad/30"
            : "bg-good/10 text-good border border-good/30"
          }`}
      >
        {willHit
          ? "⚠ At current rate, the quota will run out before renewal."
          : "✓ At current rate, you'll have leftover quota at renewal."}
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-400 inline-flex items-center gap-2">
        {Icon ? <Icon className="w-3.5 h-3.5" /> : null}
        {label}
      </span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
