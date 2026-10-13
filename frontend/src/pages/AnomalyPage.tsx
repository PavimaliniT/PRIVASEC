import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Play,
  Activity,
  Layers
} from 'lucide-react';
import { api } from '../lib/api';

export const AnomalyPage: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);

  // Feature Vector Simulator State
  const [features, setFeatures] = useState({
    requests_per_minute: 20.0,
    failed_logins_5m: 0,
    time_of_day_deviation: 0.1,
    device_novelty: 0.0,
    endpoint_rarity: 0.1,
    export_volume_kb: 50.0,
    access_denial_frequency: 0.0,
  });

  const [evalResult, setEvalResult] = useState<any>(null);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [m, a] = await Promise.all([
          api.intelligence.getModelMetrics(),
          api.intelligence.getAnomalies(),
        ]);
        setMetrics(m);
        setAnomalies(a);
      } catch (err: any) {
        console.error(err);
      }
    };
    load();
  }, []);

  const handleEvaluate = async () => {
    try {
      setEvaluating(true);
      const res = await api.intelligence.analyzeAnomaly(features);
      setEvalResult(res);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Cpu className="w-6 h-6 text-cyan-400" />
          Isolation Forest Anomaly Detection
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Unsupervised tree-based anomaly scoring normalized to 0-100 with contributing feature attribution
        </p>
      </div>

      {/* Model Metadata Banner */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400">Model Architecture</div>
            <div className="text-sm font-bold text-slate-200 mt-1">{metrics.model_name}</div>
            <div className="text-[10px] text-cyan-400 font-mono mt-0.5">{metrics.version}</div>
          </div>
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400">F1 Score (Validation)</div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
              {(metrics.f1_score * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Precision: {metrics.precision}</div>
          </div>
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400">Contamination Parameter</div>
            <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {(metrics.contamination_parameter * 100).toFixed(2)}%
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Prior expected outlier ratio</div>
          </div>
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400">Training Samples</div>
            <div className="text-xl font-bold font-mono text-slate-200 mt-1">
              {metrics.training_samples}
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Synthetic Benign + Attacks</div>
          </div>
        </div>
      )}

      {/* Interactive Feature Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Live Feature Testing Console
          </span>

          <div className="space-y-3 text-xs">
            {/* Request Rate */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>Requests Per Minute:</span>
                <span className="font-mono text-cyan-400">{features.requests_per_minute}</span>
              </div>
              <input
                type="range"
                min="1"
                max="300"
                value={features.requests_per_minute}
                onChange={(e) =>
                  setFeatures({ ...features, requests_per_minute: parseFloat(e.target.value) })
                }
                className="w-full mt-1"
              />
            </div>

            {/* Failed Logins */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>Failed Logins in 5m:</span>
                <span className="font-mono text-amber-400">{features.failed_logins_5m}</span>
              </div>
              <input
                type="range"
                min="0"
                max="25"
                value={features.failed_logins_5m}
                onChange={(e) =>
                  setFeatures({ ...features, failed_logins_5m: parseInt(e.target.value) })
                }
                className="w-full mt-1"
              />
            </div>

            {/* Time of Day Deviation */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>Off-Hours Schedule Deviation (0.0=Work hours, 1.0=Off-hours):</span>
                <span className="font-mono text-purple-400">
                  {features.time_of_day_deviation.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={features.time_of_day_deviation}
                onChange={(e) =>
                  setFeatures({ ...features, time_of_day_deviation: parseFloat(e.target.value) })
                }
                className="w-full mt-1"
              />
            </div>

            {/* Device Novelty */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>Device Novelty:</span>
                <span className="font-mono text-slate-200">
                  {features.device_novelty === 1 ? 'New Unrecognized Device' : 'Known Device'}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="1"
                value={features.device_novelty}
                onChange={(e) =>
                  setFeatures({ ...features, device_novelty: parseFloat(e.target.value) })
                }
                className="w-full mt-1"
              />
            </div>

            {/* Export Volume */}
            <div>
              <div className="flex justify-between text-slate-300">
                <span>Export Volume (KB):</span>
                <span className="font-mono text-cyan-400">{features.export_volume_kb} KB</span>
              </div>
              <input
                type="range"
                min="0"
                max="25000"
                step="500"
                value={features.export_volume_kb}
                onChange={(e) =>
                  setFeatures({ ...features, export_volume_kb: parseFloat(e.target.value) })
                }
                className="w-full mt-1"
              />
            </div>
          </div>

          <button
            onClick={handleEvaluate}
            disabled={evaluating}
            className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white transition glow-cyan flex items-center justify-center gap-2"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Evaluate with Isolation Forest
          </button>
        </div>

        {/* Evaluation Output */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200">ML Model Decision & Score</span>
          {evalResult ? (
            <div className="space-y-4">
              <div
                className={`p-4 rounded-xl border flex items-center justify-between ${
                  evalResult.is_anomaly
                    ? 'bg-rose-950/50 border-rose-800 text-rose-300 glow-rose'
                    : 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                }`}
              >
                <div>
                  <div className="text-xs uppercase font-mono">Normalized Anomaly Score</div>
                  <div className="text-3xl font-bold font-mono mt-0.5">
                    {evalResult.anomaly_score} / 100
                  </div>
                </div>
                <div className="text-right">
                  <span className="px-2.5 py-1 rounded font-mono text-xs font-bold bg-black/40">
                    {evalResult.is_anomaly ? 'ANOMALY FLAGGED' : 'NOMINAL BEHAVIOR'}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-2">
                <span className="font-semibold text-slate-300">Feature Attribution Reasons:</span>
                <ul className="list-disc list-inside text-slate-400 space-y-1">
                  {evalResult.reasons.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500 text-xs">
              Adjust feature sliders and click "Evaluate with Isolation Forest"
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
