import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { LayoutDashboard, FolderOpen, MessagesSquare, Moon, Sun, FileSearch } from "lucide-react";
import Dashboard from "./pages/Dashboard.jsx";
import Documents from "./pages/Documents.jsx";
import Research from "./pages/Research.jsx";
import { useTheme } from "./hooks/useTheme";

// Change this one line to rename the app in the sidebar.
const APP_NAME = "Research Assistant";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/documents", label: "Documents", icon: FolderOpen },
  { to: "/research", label: "Research", icon: MessagesSquare },
];

function NavItem({ item, mobile }) {
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg text-sm font-medium transition-colors ${mobile ? "flex-1 flex-col gap-1 py-2 text-xs" : "px-3 py-2"} ${
          isActive ? "bg-navy/10 text-navy" : "text-muted hover:bg-paper hover:text-ink"
        }`
      }
    >
      <item.icon className="size-5" aria-hidden="true" />
      {item.label}
    </NavLink>
  );
}

function Brand({ small }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={`flex items-center justify-center rounded-lg bg-navy text-white dark:text-[#0b1020] ${small ? "size-7" : "size-9"}`}>
        <FileSearch className={small ? "size-4" : "size-5"} aria-hidden="true" />
      </span>
      <span className={`font-serif font-bold tracking-tight ${small ? "text-base" : "text-lg"}`}>{APP_NAME}</span>
    </div>
  );
}

export default function App() {
  const [dark, toggle] = useTheme();
  return (
    <div className="flex h-full flex-col md:flex-row">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-surface p-4 md:flex">
        <div className="mb-8 px-2"><Brand /></div>
        <nav className="flex flex-col gap-1" aria-label="Main">{NAV.map((n) => <NavItem key={n.to} item={n} />)}</nav>
        <button onClick={toggle} className="mt-auto flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted hover:bg-paper hover:text-ink" aria-label="Toggle dark mode">
          {dark ? <Sun className="size-5" /> : <Moon className="size-5" />}{dark ? "Light mode" : "Dark mode"}
        </button>
      </aside>

      <header className="flex items-center justify-between border-b border-line bg-surface px-4 py-3 md:hidden">
        <Brand small />
        <button onClick={toggle} className="rounded-md p-2 text-muted" aria-label="Toggle dark mode">{dark ? <Sun className="size-5" /> : <Moon className="size-5" />}</button>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/research" element={<Research />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <nav className="flex border-t border-line bg-surface px-2 md:hidden" aria-label="Main mobile">{NAV.map((n) => <NavItem key={n.to} item={n} mobile />)}</nav>
    </div>
  );
}