import React, { useState, useEffect } from 'react';
import {
  UserCheck,
  Clock,
  Laptop,
  Activity,
  Shield,
  EyeOff,
  RefreshCw
} from 'lucide-react';
import { api } from '../lib/api';

export const BehaviorPage: React.FC = () => {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const data = await api.intelligence.getBehaviorProfiles();
      setProfiles(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-cyan-400" />
            Behavioral Intelligence & Baselines
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Rolling statistical profiles aggregated by pseudonymous user identifiers to detect deviations without invasive surveillance
          </p>
        </div>
        <button
          onClick={loadProfiles}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Privacy Notice Banner */}
      <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/60 text-xs text-cyan-300 flex items-center gap-3">
        <EyeOff className="w-5 h-5 text-cyan-400 shrink-0" />
        <div>
          <strong>Privacy By Design Safeguard:</strong> Behavioral profiles track only aggregated statistical metadata (typical hours, request velocity, device tokens). Keystroke logging, invasive desktop monitoring, and raw personally identifiable records are strictly excluded.
        </div>
      </div>

      {/* Profiles Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {profiles.map((p) => {
          const base = p.baseline_features || {};
          const hours = base.typical_hours || [];
          const devices = base.known_devices || [];

          return (
            <div
              key={p.id}
              className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4 text-xs"
            >
              {/* Card Header */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <div className="text-[10px] font-mono text-slate-400">Pseudonymous Actor</div>
                  <div className="text-sm font-bold font-mono text-cyan-400">{p.actor_pseudonym}</div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {base.total_events_observed || 0} Obs
                </span>
              </div>

              {/* Rolling Velocity */}
              <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[11px] flex items-center gap-1">
                  <Activity className="w-3.5 h-3.5 text-emerald-400" /> Rolling Request Velocity
                </div>
                <div className="text-base font-bold font-mono text-slate-100">
                  {base.avg_requests_per_min || 15.0} <span className="text-xs font-normal text-slate-400">req/min</span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                  Std Deviation: ±{base.std_requests_per_min || 4.0} req/min
                </div>
              </div>

              {/* Typical Schedule */}
              <div className="space-y-1.5">
                <div className="text-slate-400 text-[11px] flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-purple-400" /> Typical Active Schedule (UTC)
                </div>
                <div className="flex flex-wrap gap-1">
                  {hours.map((h: number) => (
                    <span
                      key={h}
                      className="px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800 text-[10px] font-mono"
                    >
                      {h}:00
                    </span>
                  ))}
                </div>
              </div>

              {/* Known Device Hashes */}
              <div className="space-y-1.5">
                <div className="text-slate-400 text-[11px] flex items-center gap-1">
                  <Laptop className="w-3.5 h-3.5 text-cyan-400" /> Observed Device Fingerprints
                </div>
                <div className="space-y-1">
                  {devices.map((d: string, idx: number) => (
                    <div
                      key={idx}
                      className="p-1.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-300 truncate"
                    >
                      {d}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
