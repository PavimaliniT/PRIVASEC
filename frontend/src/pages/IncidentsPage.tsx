import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  Clock,
  RotateCcw,
  UserX,
  KeyRound,
  Filter,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { api } from '../lib/api';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [resolutionNote, setResolutionNote] = useState('');

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await api.incidents.list(
        statusFilter || undefined,
        severityFilter || undefined
      );
      setIncidents(data);
      if (data.length > 0 && !selectedIncident) {
        loadIncidentDetails(data[0].id);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadIncidentDetails = async (id: string) => {
    try {
      const res = await api.incidents.get(id);
      setSelectedIncident(res.incident);
      setActions(res.actions || []);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [severityFilter, statusFilter]);

  const handleExecuteAction = async (actionType: string) => {
    if (!selectedIncident) return;
    try {
      await api.incidents.respond(selectedIncident.id, actionType, 'Analyst containment mandate');
      await loadIncidentDetails(selectedIncident.id);
      await loadIncidents();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleResolve = async () => {
    if (!selectedIncident) return;
    try {
      await api.incidents.resolve(
        selectedIncident.id,
        resolutionNote || 'Remediated and verified safe.',
        'Resolved'
      );
      setResolutionNote('');
      await loadIncidentDetails(selectedIncident.id);
      await loadIncidents();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleRollback = async (actionId: string) => {
    try {
      await api.incidents.rollback(actionId);
      if (selectedIncident) await loadIncidentDetails(selectedIncident.id);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-rose-400" />
            Automated Incident Response Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Auditable incident lifecycle, automated containment policies, evidence timelines, and analyst rollback controls
          </p>
        </div>
        <button
          onClick={loadIncidents}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Statuses</option>
          <option value="Detected">Detected</option>
          <option value="Triaged">Triaged</option>
          <option value="Contained">Contained</option>
          <option value="Resolved">Resolved</option>
        </select>
      </div>

      {/* Main Grid: List on Left, Details & Actions on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incidents Queue */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 space-y-3">
          <div className="text-xs font-semibold text-slate-300 font-mono flex items-center justify-between">
            <span>INCIDENT QUEUE</span>
            <span className="text-slate-500">{incidents.length} items</span>
          </div>

          <div className="space-y-2 max-h-[550px] overflow-y-auto pr-1">
            {incidents.map((inc) => {
              const isSelected = selectedIncident?.id === inc.id;
              const isCrit = inc.severity === 'critical';
              const isHigh = inc.severity === 'high';
              const badgeBg = isCrit
                ? 'bg-rose-950 text-rose-300 border-rose-800'
                : isHigh
                ? 'bg-amber-950 text-amber-300 border-amber-800'
                : 'bg-emerald-950 text-emerald-300 border-emerald-800';

              return (
                <div
                  key={inc.id}
                  onClick={() => loadIncidentDetails(inc.id)}
                  className={`p-3 rounded-lg cursor-pointer border transition text-xs ${
                    isSelected
                      ? 'bg-slate-800 border-cyan-500 glow-cyan'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${badgeBg}`}>
                      {inc.severity.toUpperCase()}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {inc.status}
                    </span>
                  </div>
                  <div className="font-medium text-slate-200 line-clamp-2">{inc.title}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-1.5 flex items-center justify-between">
                    <span>Score: {inc.risk_score}</span>
                    <span>{new Date(inc.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Incident Details & Containment */}
        {selectedIncident ? (
          <div className="lg:col-span-2 space-y-6">
            {/* Incident Header Info */}
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs font-mono text-cyan-400">Incident ID: {selectedIncident.id}</div>
                  <h2 className="text-base font-bold text-slate-100 mt-1">{selectedIncident.title}</h2>
                  <div className="text-xs text-slate-400 mt-1">
                    Status: <strong className="text-slate-200 uppercase">{selectedIncident.status}</strong> • Risk Score:{' '}
                    <strong className="text-rose-400 font-mono">{selectedIncident.risk_score}/100</strong>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-800 flex flex-wrap gap-2">
                <button
                  onClick={() => handleExecuteAction('REVOKE_SUSPICIOUS_SESSIONS')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800 text-xs font-medium transition"
                >
                  <UserX className="w-3.5 h-3.5" /> Revoke Sessions
                </button>
                <button
                  onClick={() => handleExecuteAction('REQUIRE_MFA_STEP_UP')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-amber-950/60 hover:bg-amber-900 text-amber-300 border border-amber-800 text-xs font-medium transition"
                >
                  <KeyRound className="w-3.5 h-3.5" /> Require MFA Step-Up
                </button>
                <button
                  onClick={() => handleExecuteAction('APPLY_RATE_RESTRICTION')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition"
                >
                  Throttle Requests
                </button>
              </div>
            </div>

            {/* Investigation Timeline */}
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
              <div className="text-xs font-semibold text-slate-300 font-mono flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                INVESTIGATION AUDIT TIMELINE
              </div>

              <div className="space-y-3 relative before:absolute before:inset-0 before:left-3 before:w-0.5 before:bg-slate-800">
                {(selectedIncident.timeline || []).map((tl: any, i: number) => (
                  <div key={i} className="flex items-start gap-4 text-xs relative">
                    <div className="w-6 h-6 rounded-full bg-slate-900 border border-cyan-500/60 flex items-center justify-center shrink-0 text-cyan-400 text-[10px] font-mono z-10">
                      {i + 1}
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{tl.state}</span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(tl.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-slate-300">{tl.message}</div>
                      {tl.actor && (
                        <div className="text-[10px] text-slate-500 font-mono">Actor: {tl.actor}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions Taken & Rollback */}
            {actions.length > 0 && (
              <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3">
                <div className="text-xs font-semibold text-slate-300 font-mono">EXECUTED ACTIONS & ROLLBACK</div>
                <div className="space-y-2">
                  {actions.map((act) => (
                    <div
                      key={act.id}
                      className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="font-semibold text-slate-200 font-mono">{act.action_type}</div>
                        <div className="text-[10px] text-slate-400">
                          Status: <strong className="text-cyan-400">{act.status}</strong> • Approved by:{' '}
                          {act.approved_by || 'Auto Policy'}
                        </div>
                      </div>
                      {act.status === 'EXECUTED' && (
                        <button
                          onClick={() => handleRollback(act.id)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-rose-300 border border-slate-700 text-[11px] transition"
                        >
                          <RotateCcw className="w-3 h-3" /> Rollback
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Resolution Form */}
            {selectedIncident.status !== 'Resolved' && selectedIncident.status !== 'Closed' && (
              <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3">
                <div className="text-xs font-semibold text-slate-300 font-mono">RESOLVE INCIDENT</div>
                <input
                  type="text"
                  placeholder="Resolution summary notes..."
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  className="w-full rounded bg-slate-900 border border-slate-800 p-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
                <button
                  onClick={handleResolve}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-xs text-white transition flex items-center gap-1.5 glow-emerald"
                >
                  <CheckCircle2 className="w-4 h-4" /> Mark Incident as Resolved
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="lg:col-span-2 p-8 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-center text-slate-500 text-xs">
            Select an incident from the queue to investigate timeline and take action.
          </div>
        )}
      </div>
    </div>
  );
};
