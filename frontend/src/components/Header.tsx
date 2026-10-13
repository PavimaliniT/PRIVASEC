import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Play, Shield, User, Terminal, Bell } from 'lucide-react';
import { useAuthStore } from '../lib/store';

export const Header: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-[#0d121d]/90 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-20">
      {/* Left indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span>ORG:</span>
          <span className="font-semibold text-slate-100">
            {user?.organization_name || 'Acme Cyber Defense'}
          </span>
        </div>
        <div className="h-4 w-px bg-slate-800"></div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span>Actor Pseudonym:</span>
          <span className="font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60 text-[11px]">
            {user?.pseudonym || 'usr_7f3a'}
          </span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Quick Simulator Button */}
        <button
          onClick={() => navigate('/simulation')}
          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-800/80 transition-all glow-rose"
        >
          <Terminal className="w-3.5 h-3.5" />
          Attack Simulator
        </button>

        {/* User Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="text-right">
            <div className="text-xs font-medium text-slate-200">{user?.email || 'analyst@privasec.io'}</div>
            <div className="text-[10px] font-mono text-slate-400 capitalize">{user?.role || 'Analyst'}</div>
          </div>
          <div className="w-8 h-8 rounded bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <User className="w-4 h-4" />
          </div>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          title="Sign out"
          className="p-1.5 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-all"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
