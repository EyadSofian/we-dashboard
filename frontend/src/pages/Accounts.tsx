import { FormEvent, useEffect, useState } from "react";
import { api, Account } from "../api/client";
import { Plus, Trash2, Pause, Play, Loader2 } from "lucide-react";

export default function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [open, setOpen] = useState(false);

  const load = async () => {
    const r = await api.get<Account[]>("/api/accounts");
    setAccounts(r.data);
  };

  useEffect(() => {
    load();
  }, []);

  const toggle = async (a: Account) => {
    await api.patch(`/api/accounts/${a.id}`, { is_active: !a.is_active });
    load();
  };

  const remove = async (a: Account) => {
    if (!confirm(`Delete ${a.label || a.landline}? This wipes its history too.`)) return;
    await api.delete(`/api/accounts/${a.id}`);
    load();
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Accounts</h1>
          <p className="text-sm text-slate-400">Manage WE landlines tracked by the dashboard</p>
        </div>
        <button className="btn-primary" onClick={() => setOpen(true)}>
          <Plus className="w-4 h-4" /> Add account
        </button>
      </header>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase tracking-wider text-slate-500 bg-panel2/50">
            <tr>
              <th className="px-4 py-3">Label</th>
              <th className="px-4 py-3">Landline</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Added</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id} className="border-t border-border">
                <td className="px-4 py-3 font-medium">{a.label || "—"}</td>
                <td className="px-4 py-3 font-mono text-slate-300">{a.landline}</td>
                <td className="px-4 py-3">
                  {a.is_active ? (
                    <span className="text-good text-xs">● Active</span>
                  ) : (
                    <span className="text-slate-500 text-xs">● Paused</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-400">
                  {new Date(a.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right space-x-2">
                  <button className="btn" onClick={() => toggle(a)}>
                    {a.is_active ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                    {a.is_active ? "Pause" : "Resume"}
                  </button>
                  <button className="btn-danger" onClick={() => remove(a)}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
            {!accounts.length && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-400">
                  No accounts yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {open && <AddDialog onClose={() => setOpen(false)} onCreated={load} />}
    </div>
  );
}

function AddDialog({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [landline, setLandline] = useState("");
  const [password, setPassword] = useState("");
  const [label, setLabel] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      await api.post("/api/accounts", { landline, password, label });
      onCreated();
      onClose();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur grid place-items-center z-50 p-4">
      <form onSubmit={submit} className="card p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-1">Add WE account</h2>
        <p className="text-xs text-slate-400 mb-5">
          Credentials are verified against WE before saving and encrypted at rest.
        </p>

        <label className="text-xs text-slate-400">Landline (with leading 0)</label>
        <input
          className="input w-full mb-3 mt-1"
          placeholder="0234567891"
          value={landline}
          onChange={(e) => setLandline(e.target.value)}
          required
        />

        <label className="text-xs text-slate-400">Password</label>
        <input
          type="password"
          className="input w-full mb-3 mt-1"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <label className="text-xs text-slate-400">Label (optional)</label>
        <input
          className="input w-full mb-3 mt-1"
          placeholder="Home / Office / Mom's line"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />

        {err && <div className="text-xs text-bad mb-3">{err}</div>}

        <div className="flex justify-end gap-2 mt-2">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button disabled={loading} className="btn-primary">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {loading ? "Verifying with WE…" : "Add account"}
          </button>
        </div>
      </form>
    </div>
  );
}
