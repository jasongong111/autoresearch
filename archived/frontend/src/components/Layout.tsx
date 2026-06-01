import { useState } from "react";
import {
  LayoutDashboard,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  PlayCircle,
  Settings,
  Sun,
} from "lucide-react";
import { useTheme } from "../hooks/useTheme";
import { Link, useLocation } from "react-router-dom";

const NAV = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/runs", label: "Runs", icon: PlayCircle },
  { path: "/runs/new", label: "New Run", icon: Settings },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { isDark, toggle: toggleTheme } = useTheme();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => localStorage.getItem("dashboard-sidebar-collapsed") === "true"
  );
  const location = useLocation();

  const toggleSidebar = () => {
    setSidebarCollapsed((c) => {
      const next = !c;
      localStorage.setItem("dashboard-sidebar-collapsed", String(next));
      return next;
    });
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-brand">
          <img src="/tadreamk_logo.svg" className="sidebar-brand-icon" alt="Logo" style={{ height: 18, width: 18 }} />
          <span className="sidebar-brand-text">Skill Research</span>
        </div>

        <nav className="sidebar-nav">
          {NAV.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path || (path !== "/" && location.pathname.startsWith(path));
            return (
              <Link
                key={path}
                to={path}
                className={`nav-item ${active ? "active" : ""}`}
                title={label}
              >
                <Icon size={16} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="nav-item"
            onClick={toggleTheme}
            title="Toggle theme"
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
            <span>Theme</span>
          </button>
          <button
            type="button"
            className="nav-item"
            onClick={toggleSidebar}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            <span>Collapse</span>
          </button>
        </div>
      </aside>

      <div className="main-area">
        <main className="page-content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
