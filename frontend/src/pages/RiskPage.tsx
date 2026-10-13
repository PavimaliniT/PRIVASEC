import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Play
} from 'lucide-react';
import { api } from '../lib/api';

export const RiskPage: React.FC = () => {
  const [riskEvents, setRiskEvents] = useState<any[]>([]);

  // 5-Factor Calculator State
  const [authScore, setAuthScore] = useState<number>(20);
  const [behaviorScore, setBehaviorScore] = useState<number>(30);
  const [mlScore, setMlScore] = useState<number>(25);
  const [apiScore, setApiScore] = useState<number>(15);
  const [sensitivityScore, setSensitivityScore] = useState<number>(20);

  // Compute composite client-side preview
  const compositeScore = Math.round(
    (authScore * 0.25) +
    (behaviorScore * 0.20) +
    (mlScore * 0.20) +
    (apiScore * 0.20) +
    (sensitivityScore * 0.15)
  );

  let level = 'low';
  let recAction = 'ALLOW';
  if (compositeScore >= 80) {
    level = 'critical';
    recAction = 'RESTRICT_AND_CREATE_INCIDENT';
  } else if (compositeScore >= 60) {
    level = 'high';
    recAction = 'REQUIRE_MFA_STEP_UP';
  } else if (compositeScore >= 30) {
    level = 'medium';
    recAction = 'MONITOR_OR_STEP_UP';
  }

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const data = await api.intelligence.getRiskEvents();
        setRiskEvents(data);
      } catch (err: any) {
        console.error(err);
      }
    };
    loadEvents();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <AlertOctagon className="w-6 h-6 text-amber-400" />
          Explainable Risk Scoring Engine
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Dynamic 5-factor weighted risk modeling (0-100) combining authentication, behavioral baselines, ML anomaly, API gateway signals, and data sensitivity
        </p>
      </div>

      {/* 5-Factor Interactive Calculator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            5-Factor Calibration Sliders
          </span>

          <div className="space-y-3 text-xs">
            {/* Factor 1: Auth */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>1. Authentication Signals (Weight 25%):</span>
                <span className="font-mono text-cyan-400 font-bold">{authScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={authScore}
                onChange={(e) => setAuthScore(parseInt(e.target.value))}
                className="w-full mt-1"
              />
            </div>

            {/* Factor 2: Behavior */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>2. Behavioral Baseline Deviation (Weight 20%):</span>
                <span className="font-mono text-purple-400 font-bold">{behaviorScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={behaviorScore}
                onChange={(e) => setBehaviorScore(parseInt(e.target.value))}
                className="w-full mt-1"
              />
            </div>

            {/* Factor 3: ML Anomaly */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>3. ML Isolation Forest Anomaly (Weight 20%):</span>
                <span className="font-mono text-emerald-400 font-bold">{mlScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={mlScore}
                onChange={(e) => setMlScore(parseInt(e.target.value))}
                className="w-full mt-1"
              />
            </div>

            {/* Factor 4: API Security */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>4. Web & API Security Signals (Weight 20%):</span>
                <span className="font-mono text-amber-400 font-bold">{apiScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={apiScore}
                onChange={(e) => setApiScore(parseInt(e.target.value))}
                className="w-full mt-1"
              />
            </div>

            {/* Factor 5: Data Sensitivity */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>5. Data Sensitivity Level (Weight 15%):</span>
                <span className="font-mono text-rose-400 font-bold">{sensitivityScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={sensitivityScore}
                onChange={(e) => setSensitivityScore(parseInt(e.target.value))}
                className="w-full mt-1"
              />
            </div>
          </div>
        </div>

        {/* Calculated Result Card */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-5 flex flex-col justify-between">
          <div>
            <span className="text-sm font-semibold text-slate-200">Composite Risk Assessment</span>

            {/* Big Score Box */}
            <div
              className={`mt-4 p-5 rounded-xl border flex items-center justify-between ${
                level === 'critical'
                  ? 'bg-rose-950/60 border-rose-800 text-rose-300 glow-rose'
                  : level === 'high'
                  ? 'bg-amber-950/60 border-amber-800 text-amber-300 glow-amber'
                  : level === 'medium'
                  ? 'bg-amber-950/30 border-amber-900 text-amber-200'
                  : 'bg-emerald-950/40 border-emerald-800 text-emerald-300 glow-emerald'
              }`}
            >
              <div>
                <div className="text-xs font-mono uppercase tracking-wider">Composite Security Risk</div>
                <div className="text-4xl font-extrabold font-mono mt-1">
                  {compositeScore} <span className="text-sm font-normal text-slate-400">/ 100</span>
                </div>
              </div>

              <div className="text-right">
                <span className="text-xs font-mono font-bold uppercase px-3 py-1 rounded-md bg-black/50 border border-white/10">
                  Level: {level}
                </span>
                <div className="text-xs font-mono font-semibold text-cyan-300 mt-2">
                  {recAction}
                </div>
              </div>
            </div>

            {/* Mathematical Breakdown Table */}
            <div className="mt-4 p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono space-y-1.5">
              <div className="text-slate-400 text-[11px] mb-1">Weighted Factor Attributions:</div>
              <div className="flex justify-between">
                <span>Auth ({authScore} × 0.25):</span>
                <span className="text-slate-200">{(authScore * 0.25).toFixed(1)} pts</span>
              </div>
              <div className="flex justify-between">
                <span>Behavior ({behaviorScore} × 0.20):</span>
                <span className="text-slate-200">{(behaviorScore * 0.20).toFixed(1)} pts</span>
              </div>
              <div className="flex justify-between">
                <span>ML Anomaly ({mlScore} × 0.20):</span>
                <span className="text-slate-200">{(mlScore * 0.20).toFixed(1)} pts</span>
              </div>
              <div className="flex justify-between">
                <span>API Gateway ({apiScore} × 0.20):</span>
                <span className="text-slate-200">{(apiScore * 0.20).toFixed(1)} pts</span>
              </div>
              <div className="flex justify-between">
                <span>Sensitivity ({sensitivityScore} × 0.15):</span>
                <span className="text-slate-200">{(sensitivityScore * 0.15).toFixed(1)} pts</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-slate-500">
            Threshold Calibration: Low (0-29) • Medium (30-59) • High (60-79) • Critical (80-100)
          </div>
        </div>
      </div>

      {/* Risk Event Table */}
      <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3">
        <div className="text-xs font-semibold text-slate-300 font-mono">ASSESSED EVENTS HISTORY</div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                <th className="pb-2">Event Type</th>
                <th className="pb-2">Actor</th>
                <th className="pb-2">Score</th>
                <th className="pb-2">Risk Level</th>
                <th className="pb-2">Recommended Policy Action</th>
                <th className="pb-2">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {riskEvents.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40">
                  <td className="py-2.5 font-sans font-medium text-slate-200">{r.event_type}</td>
                  <td className="py-2.5 text-cyan-400">{r.actor_pseudonym}</td>
                  <td className="py-2.5 font-bold text-slate-100">{r.score}</td>
                  <td className="py-2.5">
                    <span className="px-1.5 py-0.5 rounded uppercase font-bold text-[10px] bg-slate-800 text-slate-300">
                      {r.level}
                    </span>
                  </td>
                  <td className="py-2.5 text-emerald-400">{r.recommended_action}</td>
                  <td className="py-2.5 text-slate-500 font-sans">
                    {new Date(r.timestamp).toLocaleTimeString()}
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
