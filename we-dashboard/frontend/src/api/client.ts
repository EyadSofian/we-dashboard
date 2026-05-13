import axios from "axios";

export const api = axios.create({
  baseURL: "/",
});

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("we_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("we_token");
      if (location.pathname !== "/login") location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ---- Types ----
export interface Account {
  id: number;
  landline: string;
  label: string;
  is_active: boolean;
  created_at: string;
}

export interface Snapshot {
  id: number;
  account_id: number;
  customer_name: string | null;
  offer_name: string | null;
  total_gb: number;
  used_gb: number;
  remain_gb: number;
  usage_pct: number;
  effective_time_ms: number;
  expire_time_ms: number;
  taken_at: string;
}

export interface Forecast {
  daily_avg_gb: number;
  days_until_exhaust: number | null;
  exhaust_date_iso: string | null;
  will_exhaust_before_renewal: boolean;
  confidence: "low" | "medium" | "high";
  sample_days: number;
}

export interface DashboardPayload {
  account: Account;
  latest: Snapshot | null;
  forecast: Forecast | null;
}

export interface AlertConfig {
  id: number;
  account_id: number;
  threshold_pct: number;
  enabled: boolean;
}

export interface AlertLog {
  id: number;
  threshold_pct: number;
  fired_at: string;
  success: boolean;
  response: string;
}
