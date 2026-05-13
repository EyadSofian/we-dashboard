import { Account } from "../api/client";
import { ChevronDown } from "lucide-react";

interface Props {
  accounts: Account[];
  selectedId: number | null;
  onChange: (id: number) => void;
}

export default function AccountSwitcher({ accounts, selectedId, onChange }: Props) {
  if (!accounts.length) return null;
  return (
    <div className="relative inline-block">
      <select
        className="input pr-9 appearance-none cursor-pointer min-w-[220px]"
        value={selectedId ?? ""}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        {accounts.map((a) => (
          <option key={a.id} value={a.id}>
            {a.label || a.landline} {a.is_active ? "" : "(paused)"}
          </option>
        ))}
      </select>
      <ChevronDown className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
    </div>
  );
}
