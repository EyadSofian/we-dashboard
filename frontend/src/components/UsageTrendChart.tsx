import { Snapshot } from "../api/client";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  snapshots: Snapshot[];
}

export default function UsageTrendChart({ snapshots }: Props) {
  const data = snapshots.map((s) => ({
    t: new Date(s.taken_at).getTime(),
    used: Number(s.used_gb.toFixed(2)),
    remain: Number(s.remain_gb.toFixed(2)),
  }));

  return (
    <div className="card p-5">
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold">Usage Trend</h3>
          <p className="text-xs text-slate-400">Last {snapshots.length} samples</p>
        </div>
      </div>

      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 12, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="usedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#7c5cff" stopOpacity={0.6} />
                <stop offset="100%" stopColor="#7c5cff" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="remainGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#232a39" />
            <XAxis
              dataKey="t"
              type="number"
              domain={["dataMin", "dataMax"]}
              scale="time"
              tickFormatter={(v) =>
                new Date(v).toLocaleDateString(undefined, { month: "short", day: "2-digit" })
              }
              stroke="#5b6478"
              fontSize={11}
            />
            <YAxis stroke="#5b6478" fontSize={11} width={50} />
            <Tooltip
              contentStyle={{
                background: "#11141b",
                border: "1px solid #232a39",
                borderRadius: 10,
                color: "#e2e8f0",
                fontSize: 12,
              }}
              labelFormatter={(v) => new Date(v as number).toLocaleString()}
              formatter={(v: number, name: string) => [`${v} GB`, name]}
            />
            <Area
              type="monotone"
              dataKey="used"
              name="Used"
              stroke="#7c5cff"
              fill="url(#usedGrad)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="remain"
              name="Remaining"
              stroke="#22d3ee"
              fill="url(#remainGrad)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
