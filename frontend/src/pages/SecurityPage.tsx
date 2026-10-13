import React, { useState, useEffect } from 'react';
import {
  Activity,
  Shield,
  Lock,
  AlertTriangle,
  CheckCircle2,
  Filter,
  RefreshCw
} from 'lucide-react';
import { api } from '../lib/api';

export const SecurityPage: React.FC = () => {
  const [gatewayStatus, setGatewayStatus] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [status, evs] = await Promise.all([
        api.security.getGatewayStatus(),
        api.security.getEvents(severityFilter || undefined),
      ]);
      setGatewayStatus(status);
      setEvents(evs);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [severityFilter]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Activity className="w-6 h-6 text-cyan-400" />
            Web & API Security Gateway
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Application-layer request monitoring, sliding-window rate limiting, injection telemetry, and security headers
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Gateway Telemetry Cards */}
      {gatewayStatus && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Rate Limiting */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3 text-xs">
            <span className="font-semibold text-slate-200 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              Sliding-Window Rate Limiting
            </span>
            <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1 font-mono text-[11px]">
              <div>Window Duration: {gatewayStatus.rate_limit_policy.default_window_seconds}s</div>
              <div>Max API Traffic: {gatewayStatus.rate_limit_policy.api_max_requests_per_minute} req/min</div>
              <div>Auth Burst Cap: {gatewayStatus.rate_limit_policy.auth_max_requests_per_minute} req/min</div>
              <div>Auto Block Penalty: {gatewayStatus.rate_limit_policy.temporary_block_duration_seconds}s</div>
            </div>
          </div>

          {/* Active WAF Inspection Rules */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3 text-xs">
            <span className="font-semibold text-slate-200 flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              Active Inspection Filters
            </span>
            <div className="space-y-1.5">
              {gatewayStatus.waf_rules_active.map((rule: string) => (
                <div
                  key={rule}
                  className="p-2 rounded bg-slate-900 border border-slate-800 font-mono text-[11px] text-cyan-300 flex items-center gap-2"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  {rule}
                </div>
              ))}
            </div>
          </div>

          {/* Hardened Headers */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3 text-xs">
            <span className="font-semibold text-slate-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-purple-400" />
              Hardened Security Headers
            </span>
            <div className="space-y-1">
              {gatewayStatus.security_headers_enforced.map((h: string) => (
                <div key={h} className="text-[11px] font-mono text-slate-300 truncate">
                  • {h}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Security Events Explorer */}
      <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-slate-300 font-mono">
            GATEWAY NORMALIZED EVENT STREAM ({events.length})
          </div>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-200"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical Only</option>
            <option value="high">High Only</option>
            <option value="medium">Medium Only</option>
            <option value="low">Low Only</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                <th className="pb-2">Event Type</th>
                <th className="pb-2">Actor Pseudonym</th>
                <th className="pb-2">Severity</th>
                <th className="pb-2">Client IP Token</th>
                <th className="pb-2">Source</th>
                <th className="pb-2">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {events.map((ev) => (
                <tr key={ev.id} className="hover:bg-slate-800/40">
                  <td className="py-2.5 font-sans font-medium text-slate-200">{ev.event_type}</td>
                  <td className="py-2.5 text-cyan-400">{ev.actor_pseudonym}</td>
                  <td className="py-2.5">
                    <span
                      className={`px-1.5 py-0.5 rounded uppercase font-bold text-[10px] ${
                        ev.severity === 'critical'
                          ? 'bg-rose-950 text-rose-300'
                          : ev.severity === 'high'
                          ? 'bg-amber-950 text-amber-300'
                          : 'bg-emerald-950 text-emerald-300'
                      }`}
                    >
                      {ev.severity}
                    </span>
                  </td>
                  <td className="py-2.5 text-slate-400">
                    {ev.network_meta?.ip_token || '127.0.0.1'}
                  </td>
                  <td className="py-2.5 text-slate-400 capitalize">{ev.source}</td>
                  <td className="py-2.5 text-slate-500 font-sans">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
