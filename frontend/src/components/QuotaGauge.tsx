import { fmtGB, fmtPct, usageRingColor } from "../lib/format";

interface Props {
  usagePct: number;
  remainGB: number;
  totalGB: number;
}

export default function QuotaGauge({ usagePct, remainGB, totalGB }: Props) {
  const radius = 92;
  const stroke = 14;
  const C = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, usagePct));
  const dash = (clamped / 100) * C;
  const color = usageRingColor(clamped);

  return (
    <div className="relative w-[240px] h-[240px] grid place-items-center">
      <svg width={240} height={240} className="-rotate-90">
        <circle
          cx={120}
          cy={120}
          r={radius}
          stroke="#1f2533"
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          cx={120}
          cy={120}
          r={radius}
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${dash} ${C - dash}`}
          style={{ transition: "stroke-dasharray 600ms ease, stroke 300ms ease" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-[11px] uppercase tracking-widest text-slate-400">Remaining</div>
        <div className="text-3xl font-semibold mt-1">{fmtGB(remainGB)}</div>
        <div className="text-xs text-slate-400 mt-1">
          {fmtPct(clamped)} used of {fmtGB(totalGB)}
        </div>
      </div>
    </div>
  );
}
