import React, { useState, useEffect } from 'react';
import {
  FileCheck2,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Hash,
  Copy,
  Lock
} from 'lucide-react';
import { api } from '../lib/api';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await api.audit.getLogs();
      setLogs(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    try {
      setVerifying(true);
      const res = await api.audit.verifyChain();
      setVerification(res);
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-emerald-400" />
            Audit & Compliance Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable append-only audit trail with cryptographic SHA-256 hash-chain verification
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchLogs}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-xs text-white transition glow-emerald"
          >
            <ShieldCheck className="w-4 h-4" />
            {verifying ? 'Recomputing Hashes...' : 'Verify Hash Chain'}
          </button>
        </div>
      </div>

      {/* Verification Banner */}
      {verification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between ${
            verification.is_valid
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/50 border-rose-800 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-3">
            {verification.is_valid ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0" />
            )}
            <div>
              <div className="font-semibold text-sm">
                Ledger Status: {verification.status} ({verification.total_records} Blocks Verified)
              </div>
              <div className="text-[11px] text-slate-300 font-mono mt-0.5">
                {verification.message}
              </div>
            </div>
          </div>
          <div className="text-right text-xs font-mono">
            <div>Chain Head: {verification.chain_head?.substring(0, 16)}...</div>
          </div>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
        <div className="text-xs font-semibold text-slate-300 font-mono flex items-center justify-between">
          <span>CHAIN-LINKED AUDIT BLOCKS</span>
          <span className="text-slate-500">{logs.length} entries</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                <th className="pb-2.5">Action</th>
                <th className="pb-2.5">Actor</th>
                <th className="pb-2.5">Previous Block Hash</th>
                <th className="pb-2.5">Entry Block Hash</th>
                <th className="pb-2.5">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 font-sans font-semibold text-slate-200">
                    {log.action}
                  </td>
                  <td className="py-2.5 text-cyan-400">{log.actor_id}</td>
                  <td className="py-2.5 text-slate-500 font-mono" title={log.previous_hash}>
                    {log.previous_hash.substring(0, 12)}...
                  </td>
                  <td className="py-2.5 text-emerald-400 font-mono font-bold" title={log.entry_hash}>
                    {log.entry_hash.substring(0, 16)}...
                  </td>
                  <td className="py-2.5 text-slate-400 font-sans">
                    {new Date(log.timestamp).toLocaleString()}
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
