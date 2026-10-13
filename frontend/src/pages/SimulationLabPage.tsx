import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  ShieldCheck,
  Cpu,
  AlertTriangle,
  Lock,
  CheckCircle2,
  RefreshCw,
  Zap,
  ArrowRight
} from 'lucide-react';
import { api } from '../lib/api';

export const SimulationLabPage: React.FC = () => {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('brute_force');
  const [running, setRunning] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [activeStep, setActiveStep] = useState<number>(0);

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const data = await api.simulation.getScenarios();
        setScenarios(data);
      } catch (err: any) {
        console.error(err);
      }
    };
    loadScenarios();
  }, []);

  const handleRunSimulation = async () => {
    try {
      setRunning(true);
      setExecutionResult(null);
      setActiveStep(1);

      // Simulate step animations
      const stepTimer1 = setTimeout(() => setActiveStep(2), 300);
      const stepTimer2 = setTimeout(() => setActiveStep(3), 600);
      const stepTimer3 = setTimeout(() => setActiveStep(4), 900);

      const res = await api.simulation.runScenario(selectedScenario);

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);

      setActiveStep(5);
      setExecutionResult(res);
    } catch (err: any) {
      alert(err.message || 'Simulation execution failed');
    } finally {
      setRunning(false);
    }
  };

  const pipeRes = executionResult?.pipeline_result;
  const riskInfo = pipeRes?.risk;
  const anomalyInfo = pipeRes?.anomaly;
  const behaviorInfo = pipeRes?.behavior;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Terminal className="w-6 h-6 text-rose-400" />
            Security Simulation Lab
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Safe live execution of synthetic cyber attack scenarios testing all 12 detection and automated response modules
          </p>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded bg-rose-950/60 text-rose-300 border border-rose-800">
          Sandbox Safe Environment
        </span>
      </div>

      {/* Scenarios Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((sc) => {
          const isSelected = selectedScenario === sc.id;
          const isCrit = sc.severity === 'critical';
          const isHigh = sc.severity === 'high';
          const badgeBg = isCrit
            ? 'bg-rose-950 text-rose-300 border-rose-800'
            : isHigh
            ? 'bg-amber-950 text-amber-300 border-amber-800'
            : 'bg-emerald-950 text-emerald-300 border-emerald-800';

          return (
            <div
              key={sc.id}
              onClick={() => setSelectedScenario(sc.id)}
              className={`p-4 rounded-xl cursor-pointer border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-800/80 border-cyan-500 glow-cyan ring-1 ring-cyan-500'
                  : 'bg-[#111827] border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${badgeBg}`}>
                    {sc.severity.toUpperCase()}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">{sc.category}</span>
                </div>
                <h3 className="text-sm font-semibold text-slate-100 mb-1">{sc.name}</h3>
                <p className="text-[11px] text-slate-400 leading-relaxed">{sc.description}</p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/80 text-[10px] text-cyan-400 font-mono flex items-center gap-1">
                <span>Expected:</span>
                <span className="truncate text-slate-400">{sc.expected_outcome}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Launch Control */}
      <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
        <div className="text-xs text-slate-300">
          Ready to execute selected attack simulation through real FastAPI backend pipeline.
        </div>
        <button
          onClick={handleRunSimulation}
          disabled={running}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition glow-rose disabled:opacity-50"
        >
          {running ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> Executing Pipeline...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" /> Launch Attack Scenario
            </>
          )}
        </button>
      </div>

      {/* Pipeline Visualization (When run) */}
      {(running || executionResult) && (
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-6">
          <div className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400" />
            End-to-End Pipeline Execution Trace
          </div>

          {/* Stepper Pipeline */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {[
              { num: 1, title: '1. Ingestion', desc: 'Gateway & IP Hash' },
              { num: 2, title: '2. Baseline', desc: 'Behavioral Dev' },
              { num: 3, title: '3. Isolation Forest', desc: 'ML Anomaly' },
              { num: 4, title: '4. Risk Engine', desc: '5-Factor 0-100' },
              { num: 5, title: '5. Response', desc: 'Contain & Ledger' },
            ].map((st) => (
              <div
                key={st.num}
                className={`p-3 rounded-lg border text-xs transition ${
                  activeStep >= st.num
                    ? 'bg-slate-900 border-cyan-500 text-cyan-300 glow-cyan'
                    : 'bg-slate-950/60 border-slate-800 text-slate-500'
                }`}
              >
                <div className="font-semibold">{st.title}</div>
                <div className="text-[10px] text-slate-400">{st.desc}</div>
              </div>
            ))}
          </div>

          {/* Result Inspection */}
          {executionResult && (
            <div className="space-y-4 pt-4 border-t border-slate-800">
              {/* Risk Banner */}
              <div
                className={`p-4 rounded-lg border flex items-center justify-between ${
                  riskInfo?.level === 'critical'
                    ? 'bg-rose-950/60 border-rose-800'
                    : riskInfo?.level === 'high'
                    ? 'bg-amber-950/60 border-amber-800'
                    : 'bg-emerald-950/60 border-emerald-800'
                }`}
              >
                <div>
                  <div className="text-xs text-slate-300">Composite Risk Score</div>
                  <div className="text-3xl font-bold font-mono text-slate-100 mt-0.5">
                    {riskInfo?.score} / 100
                    <span className="text-xs font-mono font-bold uppercase ml-3 px-2 py-0.5 rounded bg-black/40">
                      Level: {riskInfo?.level}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-slate-300">Policy Recommended Action</div>
                  <div className="text-sm font-bold font-mono text-cyan-300 mt-1">
                    {riskInfo?.recommended_action}
                  </div>
                </div>
              </div>

              {/* Contributing Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                {/* ML Anomaly */}
                <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-slate-400 font-mono text-[11px]">Isolation Forest ML</div>
                  <div className="text-lg font-bold font-mono text-cyan-400">
                    {anomalyInfo?.score} / 100
                  </div>
                  <div className="text-[11px] text-slate-300">
                    Anomaly Flagged: {anomalyInfo?.is_anomaly ? 'YES (Threat)' : 'NO (Normal)'}
                  </div>
                </div>

                {/* Behavioral */}
                <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-slate-400 font-mono text-[11px]">Behavioral Deviation</div>
                  <div className="text-lg font-bold font-mono text-amber-400">
                    {behaviorInfo?.deviation_score} / 100
                  </div>
                  <div className="text-[11px] text-slate-300">
                    Device Novelty: {behaviorInfo?.device_novelty === 1 ? 'New Unseen Device' : 'Known Device'}
                  </div>
                </div>

                {/* Containment Outcome */}
                <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-slate-400 font-mono text-[11px]">Automated Incident</div>
                  <div className="text-lg font-bold font-mono text-rose-400 truncate">
                    {pipeRes?.incident_id ? `INCIDENT CREATED` : 'No Incident Mandated'}
                  </div>
                  <div className="text-[11px] text-slate-400 truncate">
                    ID: {pipeRes?.incident_id || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Attribution Explanations */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
                <span className="font-semibold text-slate-300">Explainability Factors:</span>
                <ul className="list-disc list-inside text-slate-400 text-[11px] space-y-0.5">
                  {(riskInfo?.reasons || []).map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
