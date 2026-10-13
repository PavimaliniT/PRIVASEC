import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Lock,
  EyeOff,
  Activity,
  CheckCircle2,
  RefreshCw,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { api } from '../lib/api';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.dashboard.overview();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load SOC overview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 15000); // Polling every 15s
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 gap-3">
        <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
        <span>Connecting to PRIVASEC Telemetry Stream...</span>
      </div>
    );
  }

  const metrics = data?.metrics || {};
  const riskDist = data?.risk_distribution || [];
  const threatTrend = data?.threat_trend || [];
  const recentAlerts = data?.recent_alerts || [];
  const health = data?.system_health || {};

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2.5">
            Security Operations Center (SOC)
            <span className="text-xs font-mono font-normal px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Monitoring
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time telemetry, behavioral baseline deviations, and automated defense decisions
          </p>
        </div>
        <button
          onClick={fetchOverview}
          disabled={loading}
          className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Metrics
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Events */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono font-medium text-slate-400 uppercase">
              Total Security Events
            </div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
              {metrics.total_security_events || 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <Activity className="w-3 h-3 text-cyan-500" /> Normalized telemetry
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Open Incidents */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono font-medium text-slate-400 uppercase">
              Open Incidents
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400 mt-1">
              {metrics.open_incidents || 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <ShieldAlert className="w-3 h-3 text-rose-500" /> Automated triage
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-rose-950/60 border border-rose-800/60 flex items-center justify-center text-rose-400 glow-rose">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>

        {/* High Risk Detections */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono font-medium text-slate-400 uppercase">
              High / Critical Threats
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
              {metrics.high_risk_alerts || 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-amber-500" /> Risk score ≥ 60
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-950/60 border border-amber-800/60 flex items-center justify-center text-amber-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        {/* PII Entities Protected */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono font-medium text-slate-400 uppercase">
              PII Entities Protected
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
              {metrics.total_pii_detected || 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <EyeOff className="w-3 h-3 text-emerald-500" /> PAN, Aadhaar, Cards
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
            <EyeOff className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Middle Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Threat Trend Area Chart */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#111827] border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                Live Security Telemetry Velocity & Severity
              </div>
              <div className="text-[11px] text-slate-400">
                Threat event velocity and computed severity intensity over time
              </div>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={threatTrend}>
                <defs>
                  <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} />
                <YAxis stroke="#475569" fontSize={10} tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="severity_score"
                  name="Severity Score"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#cyanGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Bar Chart */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 flex flex-col">
          <div className="mb-4">
            <div className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Risk Level Distribution
            </div>
            <div className="text-[11px] text-slate-400">Assessments by risk category</div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDist} layout="vertical">
                <XAxis type="number" stroke="#475569" fontSize={10} tickLine={false} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#475569"
                  fontSize={10}
                  tickLine={false}
                  width={90}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {riskDist.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row: Recent Alerts + System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Alerts Feed */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#111827] border border-slate-800">
          <div className="text-sm font-semibold text-slate-100 mb-3 flex items-center justify-between">
            <span>Recent Security Detections</span>
            <span className="text-[11px] font-mono text-slate-400">Normalized Event Stream</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                  <th className="pb-2">Event Type</th>
                  <th className="pb-2">Actor</th>
                  <th className="pb-2">Severity</th>
                  <th className="pb-2">Risk Score</th>
                  <th className="pb-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {recentAlerts.map((alert: any) => {
                  const isCrit = alert.severity === 'critical';
                  const isHigh = alert.severity === 'high';
                  const badgeColor = isCrit
                    ? 'bg-rose-950 text-rose-300 border-rose-800'
                    : isHigh
                    ? 'bg-amber-950 text-amber-300 border-amber-800'
                    : 'bg-emerald-950 text-emerald-300 border-emerald-800';

                  return (
                    <tr key={alert.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 font-sans font-medium text-slate-200">
                        {alert.event_type}
                      </td>
                      <td className="py-2.5 text-cyan-400">{alert.actor_pseudonym}</td>
                      <td className="py-2.5">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded border ${badgeColor}`}
                        >
                          {alert.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2.5 font-bold text-slate-200">{alert.risk_score}</td>
                      <td className="py-2.5 text-slate-400 text-[11px] font-sans">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Health Telemetry */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <div className="text-sm font-semibold text-slate-100 flex items-center justify-between">
            <span>SOC Node Telemetry</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>

          <div className="space-y-2 text-xs">
            {Object.entries(health).map(([key, val]) => (
              <div
                key={key}
                className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800"
              >
                <span className="text-slate-400 capitalize font-mono text-[11px]">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-mono font-semibold text-emerald-400 text-[11px]">
                  {String(val)}
                </span>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-800/60 text-[11px] text-cyan-300">
            <strong>KMS Key Version:</strong> v1 (AES-256-GCM) with authenticated encryption active.
          </div>
        </div>
      </div>
    </div>
  );
};
