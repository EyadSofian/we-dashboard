import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, Users, Bell, LogOut, Wifi } from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/accounts", label: "Accounts", icon: Users, end: false },
  { to: "/alerts", label: "Alerts", icon: Bell, end: false },
];

export default function Layout() {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem("we_token");
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 shrink-0 border-r border-border bg-panel/60 backdrop-blur p-5 flex flex-col">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-accent2 grid place-items-center">
            <Wifi className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-semibold text-sm">WE Dashboard</div>
            <div className="text-xs text-slate-400">Quota Monitor</div>
          </div>
        </div>

        <nav className="space-y-1 flex-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive
                    ? "bg-accent/15 text-white border border-accent/30"
                    : "text-slate-400 hover:text-white hover:bg-panel2"
                }`
              }
            >
              <n.icon className="w-4 h-4" />
              {n.label}
            </NavLink>
          ))}
        </nav>

        <button onClick={logout} className="btn justify-center">
          <LogOut className="w-4 h-4" /> Logout
        </button>
      </aside>

      <main className="flex-1 p-8 overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  );
}
