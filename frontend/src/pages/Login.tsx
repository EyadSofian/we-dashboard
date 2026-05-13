import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Wifi } from "lucide-react";

export default function Login() {
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const r = await api.post("/api/auth/login", { password: pw });
      localStorage.setItem("we_token", r.data.access_token);
      navigate("/");
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <form onSubmit={submit} className="card p-8 w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent2 grid place-items-center">
            <Wifi className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-semibold">WE Dashboard</div>
            <div className="text-xs text-slate-400">Sign in to continue</div>
          </div>
        </div>

        <label className="text-xs text-slate-400 mb-1 block">Admin password</label>
        <input
          type="password"
          autoFocus
          value={pw}
          onChange={(e) => setPw(e.target.value)}
          className="input w-full mb-3"
          placeholder="••••••••"
        />
        {err && <div className="text-xs text-bad mb-3">{err}</div>}
        <button disabled={loading} className="btn-primary w-full justify-center">
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
