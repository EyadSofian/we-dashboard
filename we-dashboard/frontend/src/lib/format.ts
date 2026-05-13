export const fmtGB = (n: number | null | undefined) => {
  if (n == null) return "—";
  if (n >= 1000) return `${(n / 1000).toFixed(2)} TB`;
  return `${n.toFixed(1)} GB`;
};

export const fmtPct = (n: number | null | undefined) =>
  n == null ? "—" : `${n.toFixed(1)}%`;

export const fmtDate = (iso: string | null | undefined) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric", month: "short", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
};

export const fmtDateMs = (ms: number | null | undefined) => {
  if (!ms) return "—";
  return fmtDate(new Date(ms).toISOString());
};

export const daysBetween = (a: Date, b: Date) =>
  Math.round((b.getTime() - a.getTime()) / 86400000);

export const usageColor = (pct: number) => {
  if (pct >= 90) return "text-bad";
  if (pct >= 75) return "text-warn";
  return "text-good";
};

export const usageRingColor = (pct: number) => {
  if (pct >= 90) return "#ef4444";
  if (pct >= 75) return "#f59e0b";
  return "#22c55e";
};
