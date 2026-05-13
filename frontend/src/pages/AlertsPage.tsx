import { FormEvent, useEffect, useState } from "react";
import { api, Account, AlertConfig, AlertLog } from "../api/client";
import { Plus, Trash2, Bell, CheckCircle2, XCircle } from "lucide-react";
import AccountSwitcher from "../components/AccountSwitcher";

export default function AlertsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [alerts, setAlerts] = useState<AlertConfig[]>([]);
  const [logs, setLogs] = useState<AlertLog[]>([]);
  const [threshold, setThreshold] = useState(80);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      const r = await api.get<Account[]>("/api/accounts");
      setAccounts(r.data);
      if (r.data.length) setSelectedId(r.data[0].id);
    })();
  }, []);

  const load = async (id: number) => {
    const [a, l] = await Promise.all([
      api.get<AlertConfig[]>(`/api/alerts/${id}`),
      api.get<AlertLog[]>(`/api/alerts/logs/${id}`),
    ]);
    setAlerts(a.data);
    setLogs(l.data);
  };

  useEffect(() => {
    if (selectedId != null) load(selectedId);
  }, [selectedId]);

  const add = async (e: FormEvent) => {
    e.preventDefault();
    if (selectedId == null) return;
    setErr("");
    try {
      await api.post(`/api/alerts/${selectedId}`, { threshold_pct: threshold, enabled: true });
      load(selectedId);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Failed");
    }
  };

  const toggle = async (a: AlertConfig) => {
    await api.patch(`/api/alerts/${a.id}`, {
      threshold_pct: a.threshold_pct,
      enabled: !a.enabled,
    });
    if (selectedId != null) load(selectedId);
  };

  const remove = async (a: AlertConfig) => {
    await api.delete(`/api/alerts/${a.id}`);
    if (selectedId != null) load(selectedId);
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-sm text-slate-400">
            Threshold-based webhooks sent to your n8n route. One trigger per quota cycle.
          </p>
        </div>
        <AccountSwitcher accounts={accounts} selectedId={selectedId} onChange={setSelectedId} />
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Bell className="w-4 h-4 text-accent" /> Thresholds
          </h3>

          <form onSubmit={add} className="flex items-center gap-2 mb-4">
            <input
              type="number"
              min={1}
              max={100}
              className="input w-28"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
            />
            <span className="text-sm text-slate-400">% usage</span>
            <button className="btn-primary ml-auto">
              <Plus className="w-4 h-4" /> Add
            </button>
          </form>
          {err && <div className="text-xs text-bad mb-2">{err}</div>}

          <ul className="space-y-2">
            {alerts.map((a) => (
              <li
                key={a.id}
                className="flex items-center justify-between bg-panel2 border border-border rounded-lg px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={a.enabled}
                    onChange={() => toggle(a)}
                    className="accent-accent"
                  />
                  <span className="font-medium">{a.threshold_pct}%</span>
                  <span className="text-xs text-slate-400">
                    fires once per quota cycle
                  </span>
                </div>
                <button className="btn-danger" onClick={() => remove(a)}>
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </li>
            ))}
            {!alerts.length && (
              <li className="text-xs text-slate-500 text-center py-6">
                No thresholds yet. Add e.g. 80, 90, 95.
              </li>
            )}
          </ul>
        </div>

        <div className="card p-5">
          <h3 className="font-semibold mb-3">Recent fires</h3>
          <ul className="space-y-2 max-h-[420px] overflow-auto">
            {logs.map((l) => (
              <li
                key={l.id}
                className="flex items-start justify-between bg-panel2 border border-border rounded-lg px-3 py-2 text-sm"
              >
                <div className="flex items-start gap-2">
                  {l.success ? (
                    <CheckCircle2 className="w-4 h-4 text-good mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-bad mt-0.5" />
                  )}
                  <div>
                    <div className="font-medium">{l.threshold_pct}% threshold</div>
                    <div className="text-xs text-slate-400">
                      {new Date(l.fired_at).toLocaleString()}
                    </div>
                    {l.response && (
                      <div className="text-[11px] text-slate-500 mt-1 font-mono break-all">
                        {l.response.slice(0, 120)}
                      </div>
                    )}
                  </div>
                </div>
              </li>
            ))}
            {!logs.length && (
              <li className="text-xs text-slate-500 text-center py-6">
                No fires yet.
              </li>
            )}
          </ul>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-2">Webhook payload schema</h3>
        <p className="text-xs text-slate-400 mb-3">
          Each fire posts JSON to <span className="kbd">N8N_WEBHOOK_URL</span>. Route to
          Telegram/WhatsApp/Email inside n8n.
        </p>
        <pre className="text-[11px] bg-panel2 border border-border rounded-lg p-3 overflow-auto">
{`{
  "event": "we.quota.threshold",
  "account_id": 1,
  "label": "Home",
  "landline": "0234567891",
  "customer_name": "EYAD ...",
  "offer_name": "VDSL 140GB",
  "threshold_pct": 90,
  "usage_pct": 91.42,
  "used_gb": 128.0,
  "remain_gb": 12.0,
  "total_gb": 140.0,
  "expire_time_iso": "2026-06-01T00:00:00Z",
  "snapshot_taken_at": "2026-05-13T18:45:12Z"
}`}
        </pre>
      </div>
    </div>
  );
}
