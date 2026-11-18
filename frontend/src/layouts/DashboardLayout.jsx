import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  Activity,
  AlertTriangle,
  Flame,
  Radio,
  Network,
  Cpu,
  BrainCircuit,
  Sliders,
  GlobeLock,
  ShieldCheck,
  FileText,
  Users,
  Settings as SettingsIcon,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Bell,
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const DashboardLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Overview', path: '/', icon: Activity },
    { label: 'Live Events', path: '/events', icon: Radio },
    { label: 'Threat Detection', path: '/threats', icon: Flame },
    { label: 'Security Alerts', path: '/alerts', icon: AlertTriangle },
    { label: 'Incidents', path: '/incidents', icon: ShieldAlert },
    { label: 'Network Analytics', path: '/network', icon: Network },
    { label: 'Endpoints', path: '/endpoints', icon: Cpu },
    { label: 'ML Analytics', path: '/ml-analytics', icon: BrainCircuit },
    { label: 'Detection Rules', path: '/rules', icon: Sliders },
    { label: 'Threat Intel', path: '/threat-intel', icon: GlobeLock },
    { label: 'Response', path: '/response', icon: ShieldCheck },
    { label: 'Audit Logs', path: '/audit', icon: FileText },
    ...(isAdmin ? [{ label: 'Users', path: '/users', icon: Users }] : []),
    { label: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  return (
    <div className="flex h-screen bg-[#0a0e17] text-slate-200 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${
          collapsed ? 'w-20' : 'w-64'
        } bg-[#0d131f] border-r border-[#1a2333] flex flex-col transition-all duration-300 z-30 select-none`}
      >
        {/* Brand */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#1a2333]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-extrabold text-sm tracking-widest text-slate-100 uppercase">
                  Sentinel<span className="text-cyan-400">AI</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono tracking-wider">
                  SOC PLATFORM v1.0
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#162032] transition"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto py-3 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2b]'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>

        {/* User bar */}
        <div className="p-3 border-t border-[#1a2333] bg-[#0a0e17]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-cyan-400 shrink-0">
                {user?.username?.slice(0, 2).toUpperCase() || 'SO'}
              </div>
              {!collapsed && (
                <div className="flex flex-col overflow-hidden">
                  <span className="text-xs font-semibold text-slate-200 truncate">{user?.username}</span>
                  <span className="text-[10px] text-cyan-400 uppercase font-mono">{user?.role}</span>
                </div>
              )}
            </div>
            {!collapsed && (
              <button
                onClick={handleLogout}
                title="Sign out"
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-[#162032] transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-[#0d131f] border-b border-[#1a2333] px-6 flex items-center justify-between z-20">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="font-mono text-[11px] font-semibold">SOC ENGINE ONLINE</span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 font-mono">
              <span>Host IP: <strong className="text-slate-200">127.0.0.1:8000</strong></span>
              <span>•</span>
              <span>ML Model: <strong className="text-cyan-400">RandomForest v1.0 (97.2%)</strong></span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#141c2c] border border-[#1f293d] text-xs">
              <span className="text-slate-400">Role:</span>
              <span className="font-semibold text-cyan-400 uppercase">{user?.role || 'ANALYST'}</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-400 text-xs font-medium transition flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        </header>

        {/* Viewport */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0a0e17]">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
