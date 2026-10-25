import { NavLink } from "react-router-dom";
import { Home, Upload, Library, Clock, Bookmark, FolderKanban, Settings, Waves } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Home", icon: Home, end: true },
  { to: "/upload", label: "Upload Document", icon: Upload },
  { to: "/library", label: "Equation Library", icon: Library },
  { to: "/saved", label: "Saved Visualizations", icon: Bookmark },
  { to: "/projects", label: "Projects", icon: FolderKanban },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-base-700/60 bg-base-900/40 h-screen sticky top-0">
      <div className="px-5 py-5 flex items-center gap-2 border-b border-base-700/60">
        <div className="w-8 h-8 rounded-lg bg-accent-500/15 flex items-center justify-center">
          <Waves size={18} className="text-accent-400" />
        </div>
        <div>
          <p className="font-semibold text-slate-100 leading-tight">EquationLens</p>
          <p className="text-[10px] text-slate-500 leading-tight">see what equations do</p>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive ? "bg-accent-500/15 text-accent-400" : "text-slate-400 hover:bg-base-800 hover:text-slate-200"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-3 py-4 border-t border-base-700/60">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              isActive ? "bg-accent-500/15 text-accent-400" : "text-slate-400 hover:bg-base-800 hover:text-slate-200"
            }`
          }
        >
          <Settings size={16} /> Settings
        </NavLink>
      </div>
    </aside>
  );
}
