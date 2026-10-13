import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Lock,
  EyeOff,
  Activity,
  UserCheck,
  AlertOctagon,
  FileKey,
  Image as ImageIcon,
  KeyRound,
  FileCheck2,
  Terminal,
  Cpu,
  Fingerprint
} from 'lucide-react';
import { useAuthStore } from '../lib/store';

interface NavItem {
  name: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navSections = [
  {
    title: 'OPERATIONS',
    items: [
      { name: 'Security Overview', to: '/dashboard', icon: LayoutDashboard },
      { name: 'Incident Center', to: '/incidents', icon: ShieldAlert, badge: 'Live' },
      { name: 'Web & API Gateway', to: '/api-security', icon: Activity },
    ],
  },
  {
    title: 'PRIVACY & DATA',
    items: [
      { name: 'Privacy Center', to: '/privacy', icon: EyeOff },
      { name: 'Audit & Compliance', to: '/audit', icon: FileCheck2 },
    ],
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { name: 'Anomaly Detection', to: '/anomalies', icon: Cpu },
      { name: 'Behavioral Intelligence', to: '/behavior', icon: UserCheck },
      { name: 'Risk Scoring Engine', to: '/risk', icon: AlertOctagon },
    ],
  },
  {
    title: 'CRYPTOGRAPHY',
    items: [
      { name: 'Cryptography Suite', to: '/crypto', icon: Lock },
      { name: 'Visual Cryptography', to: '/visual-crypto', icon: FileKey },
      { name: 'Steganography Lab', to: '/steganography', icon: ImageIcon },
    ],
  },
  {
    title: 'ADAPTIVE DEFENSE',
    items: [
      { name: 'Adaptive Auth & MFA', to: '/authentication', icon: Fingerprint },
      { name: 'Attack Simulation Lab', to: '/simulation', icon: Terminal, badge: 'Demo' },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <aside className="w-64 bg-[#0d121d] border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/80 gap-3">
        <div className="w-9 h-9 rounded-lg bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400 glow-cyan">
          <KeyRound className="w-5 h-5" />
        </div>
        <div>
          <div className="text-base font-bold tracking-wider text-slate-100 flex items-center gap-1.5">
            PRIVASEC
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              SOC
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-medium">Cyber Defense Platform</div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navSections.map((section) => (
          <div key={section.title}>
            <div className="px-3 mb-2 text-[10px] font-mono font-semibold tracking-wider text-slate-400 uppercase">
              {section.title}
            </div>
            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 glow-cyan'
                          : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/50 border border-transparent'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="truncate">{item.name}</span>
                    {item.badge && (
                      <span className="ml-auto text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer System Telemetry Status */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            SOC Node: Active
          </span>
          <span className="font-mono text-cyan-400">TLS 1.3</span>
        </div>
        <div className="text-[10px] text-slate-400 truncate">
          Role: <span className="font-mono text-slate-200 uppercase">{user?.role || 'Guest'}</span>
        </div>
      </div>
    </aside>
  );
};
