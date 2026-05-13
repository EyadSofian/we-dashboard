import { useCallback, useEffect, useState } from "react";
import { api, Account, DashboardPayload, Snapshot } from "../api/client";
import AccountSwitcher from "../components/AccountSwitcher";
import QuotaGauge from "../components/QuotaGauge";
import UsageTrendChart from "../components/UsageTrendChart";
import ForecastCard from "../components/ForecastCard";
import { fmtDate, fmtDateMs, fmtGB, fmtPct, daysBetween, usageColor } from "../lib/format";
import { RefreshCw, Calendar, User, Package, Clock, Pause } from "lucide-react";

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [history, setHistory] = useState<Snapshot[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get<Account[]>("/api/accounts");
        setAccounts(r.data);
        if (r.data.length) setSelectedId(r.data[0].id);
        else setLoading(false);
      } catch (e: any) {
        setError(e?.response?.data?.detail || "Failed to load accounts");
        setLoading(false);
      }
    })();
  }, []);

  const load = useCallback(async (id: number) => {
    setLoading(true);
    setError("");
    try {
      const [d, h] = await Promise.all([
        api.get<DashboardPayload>(`/api/dashboard/${id}`),
        api.get<Snapshot[]>(`/api/history/${id}?days=30`),
      ]);
      setData(d.data);
      setHistory(h.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId != null) load(selectedId);
  }, [selectedId, load]);

  const refresh = async () => {
    if (selectedId == null) return;
    setRefreshing(true);
    try {
      const r = await api.post(`/api/refresh/${selectedId}`);
      if (!r.data.ok) setError(r.data.error || "Refresh failed");
      await load(selectedId);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  };

  if (!accounts.length && !loading) {
    return (
      <div className="card p-10 text-center">
        <h2 className="text-lg font-semibold">No accounts yet</h2>
        <p className="text-sm text-slate-400 mt-2">
          Add a WE landline in <span className="kbd">Accounts</span> to start tracking.
        </p>
      </div>
    );
  }

  const latest = data?.latest;
  const renewalMs = latest?.expire_time_ms ?? null;
  const daysToRenewal = renewalMs
    ? Math.max(0, daysBetween(new Date(), new Date(renewalMs)))
    : null;

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Quota overview</h1>
          <p className="text-sm text-slate-400">
            Live status, history and forecast for your WE landlines
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AccountSwitcher
            accounts={accounts}
            selectedId={selectedId}
            onChange={setSelectedId}
          />
          <button onClick={refresh} disabled={refreshing} className="btn-primary">
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </header>

      {error && (
        <div className="card p-4 border-bad/30 text-bad text-sm">{error}</div>
      )}

      {loading ? (
        <div className="card p-10 text-center text-slate-400">Loading…</div>
      ) : !latest ? (
        <div className="card p-10 text-center">
          <h3 className="font-semibold">No snapshot yet</h3>
          <p className="text-sm text-slate-400 mt-2">
            Hit <span className="kbd">Refresh</span> or wait for the scheduler.
          </p>
        </div>
      ) : (
        <>
          {/* Hero row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="card p-6 flex items-center gap-6 lg:col-span-2">
              <QuotaGauge
                usagePct={latest.usage_pct}
                remainGB={latest.remain_gb}
                totalGB={latest.total_gb}
              />
              <div className="space-y-3 min-w-0 flex-1">
                <Field icon={User} label="Customer" value={latest.customer_name || "—"} />
                <Field icon={Package} label="Plan" value={latest.offer_name || "—"} />
                <Field
                  icon={Calendar}
                  label="Renewed on"
                  value={fmtDateMs(latest.effective_time_ms)}
                />
                <Field
                  icon={Calendar}
                  label="Renews on"
                  value={`${fmtDateMs(renewalMs ?? null)}${
                    daysToRenewal != null ? ` (${daysToRenewal}d)` : ""
                  }`}
                />
                <Field
                  icon={Clock}
                  label="Last update"
                  value={fmtDate(latest.taken_at)}
                />
              </div>
            </div>

            <ForecastCard forecast={data?.forecast || null} expireMs={renewalMs} />
          </div>

          {/* Stat cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Stat label="Used" value={fmtGB(latest.used_gb)} />
            <Stat label="Remaining" value={fmtGB(latest.remain_gb)} />
            <Stat
              label="Usage"
              value={fmtPct(latest.usage_pct)}
              valueClass={usageColor(latest.usage_pct)}
            />
            <Stat label="Total" value={fmtGB(latest.total_gb)} />
          </div>

          {/* Trend chart */}
          {history.length > 1 ? (
            <UsageTrendChart snapshots={history} />
          ) : (
            <div className="card p-6 text-center text-slate-400 text-sm">
              <Pause className="w-4 h-4 inline mr-1" />
              Collecting samples… chart will populate after a few polls.
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="card p-4">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-2xl font-semibold mt-1 ${valueClass}`}>{value}</div>
    </div>
  );
}

function Field({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 min-w-0">
      <div className="w-9 h-9 rounded-lg bg-panel2 border border-border grid place-items-center shrink-0">
        <Icon className="w-4 h-4 text-slate-400" />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
        <div className="text-sm font-medium truncate">{value}</div>
      </div>
    </div>
  );
}
