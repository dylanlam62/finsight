import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import { Bot, Settings, Wrench } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import AgentEditor from "./pages/AgentEditor";
import RunView from "./pages/RunView";
import SettingsPage from "./pages/Settings";

function HKTFinSightLogo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" className="w-8 h-8 shrink-0">
      <rect width="32" height="32" rx="7" fill="#004FA3" />
      <rect x="5" y="21" width="5" height="7" rx="1" fill="#FFB800" />
      <rect x="13" y="16" width="5" height="12" rx="1" fill="#FFB800" />
      <rect x="21" y="10" width="5" height="18" rx="1" fill="#FFB800" />
      <polyline
        points="7.5,20 15.5,15 23.5,9"
        stroke="white"
        strokeWidth="1.8"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="23.5" cy="9" r="2" fill="white" />
    </svg>
  );
}

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
      isActive
        ? "bg-brand-500/10 text-brand-600"
        : "text-warm-600 hover:text-warm-900 hover:bg-warm-200"
    }`;

  return (
    <aside className="w-60 shrink-0 border-r border-warm-200 bg-warm-100 flex flex-col">
      {/* Logo */}
      <Link to="/" className="flex items-center gap-3 px-5 py-4 border-b border-warm-200">
        <HKTFinSightLogo />
        <div className="flex flex-col leading-tight">
          <span className="text-[10px] font-semibold tracking-widest text-brand-500 uppercase">HKT</span>
          <span className="font-serif font-bold text-warm-900 tracking-tight leading-none">FinSight</span>
        </div>
      </Link>

      {/* Nav links */}
      <nav className="flex-1 p-3 space-y-0.5">
        <NavLink to="/" end className={linkClass}>
          <Bot className="w-4 h-4 shrink-0" /> Agents
        </NavLink>
        <NavLink to="/tools" className={linkClass}>
          <Wrench className="w-4 h-4 shrink-0" /> Tools
        </NavLink>
        <NavLink to="/settings" className={linkClass}>
          <Settings className="w-4 h-4 shrink-0" /> Settings
        </NavLink>
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-warm-200">
        <p className="text-xs text-warm-400">HKT Internal Finance AI</p>
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden">
        <Nav />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents/:id" element={<AgentEditor />} />
            <Route path="/agents/:id/run" element={<RunView />} />
            <Route path="/tools" element={<ToolLibrary />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

function ToolLibrary() {
  return (
    <div className="p-8">
      <h1 className="font-serif text-2xl font-semibold text-warm-900 mb-1">Tool Library</h1>
      <p className="text-warm-500 text-sm mb-6">Manage built-in and custom tools available to your agents.</p>
      <ToolLibraryContent />
    </div>
  );
}

import ToolLibraryContent from "./components/ToolPicker/ToolLibrary";
