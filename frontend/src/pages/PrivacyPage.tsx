import React, { useState } from 'react';
import {
  EyeOff,
  UploadCloud,
  ShieldCheck,
  Key,
  Sliders,
  FileText,
  Check,
  AlertCircle,
  Copy,
  Lock
} from 'lucide-react';
import { api } from '../lib/api';

export const PrivacyPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'scan' | 'mask' | 'pseudonym' | 'diff_privacy'>('scan');

  // PII Scan State
  const [scanText, setScanText] = useState(
    'Employee Record:\nName: Priya Nair, Email: priya.nair@example.com, Phone: +91 9876543210\n' +
    'Income Tax PAN: ABCDE1234F, Aadhaar Number: 5432 9876 1234\n' +
    'Corporate Card: 4532 0150 9821 1234, IP: 192.168.1.105'
  );
  const [scanResults, setScanResults] = useState<any>(null);
  const [scanning, setScanning] = useState(false);

  // File Upload State
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [fileScanResults, setFileScanResults] = useState<any>(null);

  // Masking State
  const [maskText, setMaskText] = useState(
    'Contact: rahul.sharma@example.com with PAN ABCDE1234F and Card 4532015098211234'
  );
  const [maskStrategy, setMaskStrategy] = useState('PARTIAL');
  const [maskOutput, setMaskOutput] = useState<any>(null);

  // Pseudonym State
  const [pseudoInput, setPseudoInput] = useState('rahul.sharma@example.com');
  const [pseudoOutput, setPseudoOutput] = useState<any>(null);
  const [reidentToken, setReidentToken] = useState('');
  const [reidentOutput, setReidentOutput] = useState<any>(null);

  // Differential Privacy State
  const [dpEpsilon, setDpEpsilon] = useState<number>(1.0);
  const [dpActual, setDpActual] = useState<number>(1250);
  const [dpOutput, setDpOutput] = useState<any>(null);

  // Handlers
  const handleScanText = async () => {
    try {
      setScanning(true);
      const res = await api.privacy.scanText(scanText);
      setScanResults(res);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setScanning(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploadedFile(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      setScanning(true);
      const res = await api.privacy.scanFile(formData);
      setFileScanResults(res);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setScanning(false);
    }
  };

  const handleMask = async () => {
    try {
      const res = await api.privacy.mask(maskText, maskStrategy);
      setMaskOutput(res);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handlePseudonymize = async () => {
    try {
      const res = await api.privacy.pseudonymize(pseudoInput, 'analytics');
      setPseudoOutput(res);
      setReidentToken(res.token);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleReidentify = async () => {
    try {
      const res = await api.privacy.reidentify(reidentToken, 'Analyst investigation demo');
      setReidentOutput(res);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDiffPrivacy = async () => {
    try {
      const res = await api.privacy.diffPrivacyDemo(dpEpsilon, dpActual);
      setDpOutput(res);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <EyeOff className="w-6 h-6 text-emerald-400" />
          Privacy Engineering Center
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Presidio PII recognition (PAN, Aadhaar), format-preserving masking, HMAC pseudonymization vault, and differential privacy
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        {[
          { id: 'scan', label: 'PII Detection & File Scanner' },
          { id: 'mask', label: 'Data Masking' },
          { id: 'pseudonym', label: 'Pseudonymization Vault' },
          { id: 'diff_privacy', label: 'Differential Privacy (Laplace)' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition -mb-px ${
              activeTab === tab.id
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: PII SCANNER */}
      {activeTab === 'scan' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-200">Interactive Text Scanner</span>
              <button
                onClick={() =>
                  setScanText(
                    'Employee Onboarding:\nName: John Doe, Email: john.doe@example.com, Phone: 9876543210\n' +
                    'PAN: ABCDE1234F, Aadhaar: 2345 6789 0123\nCredit Card: 4532 0150 9821 1234'
                  )
                }
                className="text-[11px] text-cyan-400 hover:underline"
              >
                Insert Sample PII
              </button>
            </div>

            <textarea
              rows={6}
              value={scanText}
              onChange={(e) => setScanText(e.target.value)}
              className="w-full rounded-lg bg-slate-900 border border-slate-800 p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
            />

            <button
              onClick={handleScanText}
              disabled={scanning}
              className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-medium text-xs text-white transition flex items-center justify-center gap-2 glow-emerald"
            >
              <ShieldCheck className="w-4 h-4" />
              {scanning ? 'Analyzing with Presidio...' : 'Run PII Inspection'}
            </button>

            {/* File Upload Section */}
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-300">File Inspection (TXT, CSV, JSON, PDF)</span>
              <label className="flex flex-col items-center justify-center p-4 border-2 border-dashed border-slate-700 hover:border-emerald-500 rounded-lg cursor-pointer bg-slate-900/50 transition">
                <UploadCloud className="w-6 h-6 text-slate-400 mb-1" />
                <span className="text-xs text-slate-300">
                  {uploadedFile ? uploadedFile.name : 'Select or drop a file to scan for sensitive data'}
                </span>
                <span className="text-[10px] text-slate-500 mt-1">Processed in-memory with automatic cleanup</span>
                <input
                  type="file"
                  accept=".txt,.csv,.json,.pdf,.log"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          {/* Results Panel */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200">Detection Findings</span>

            {scanResults || fileScanResults ? (
              <div className="space-y-4">
                {/* Summary badges */}
                <div className="flex flex-wrap gap-2">
                  {Object.entries((scanResults || fileScanResults).entity_counts || {}).map(
                    ([k, v]: any) => (
                      <span
                        key={k}
                        className="text-[11px] font-mono px-2.5 py-1 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-800/80"
                      >
                        {k}: <strong>{v}</strong>
                      </span>
                    )
                  )}
                </div>

                {/* Entities List */}
                <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
                  {((scanResults || fileScanResults).findings || []).map((f: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-slate-200 flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-cyan-300">
                            {f.entity_type}
                          </span>
                          <span className="font-mono text-slate-400">"{f.text_sample}"</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1">
                          Offsets: [{f.start}:{f.end}] • Confidence: {Math.round(f.confidence * 100)}%
                        </div>
                      </div>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                        {f.recommended_action}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
                <EyeOff className="w-8 h-8 opacity-40" />
                <span>Execute a text scan or upload a document to view detected PII candidates</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: DATA MASKING */}
      {activeTab === 'mask' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200">Masking Policy Configuration</span>
            
            <div>
              <label className="text-xs text-slate-400">Masking Strategy</label>
              <select
                value={maskStrategy}
                onChange={(e) => setMaskStrategy(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="PARTIAL">Partial Format-Preserving (e.g. XXXXX1234X)</option>
                <option value="FULL">Full Masking (e.g. **********)</option>
                <option value="REDACT">Redaction Token (e.g. [REDACTED_PAN])</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400">Original Content</label>
              <textarea
                rows={5}
                value={maskText}
                onChange={(e) => setMaskText(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              onClick={handleMask}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-medium text-xs text-white transition glow-cyan"
            >
              Apply Transformation
            </button>
          </div>

          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200">Transformed Output Preview</span>
            {maskOutput ? (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs text-emerald-400 whitespace-pre-wrap">
                  {maskOutput.masked_text}
                </div>
                <div className="text-xs text-slate-400">
                  Entities masked: <strong className="text-slate-200">{maskOutput.entities_transformed}</strong>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
                Select strategy and click "Apply Transformation"
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: PSEUDONYMIZATION VAULT */}
      {activeTab === 'pseudonym' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pseudonymize */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Key className="w-4 h-4 text-cyan-400" />
              HMAC-SHA256 Tokenization
            </span>
            <p className="text-xs text-slate-400">
              Generates consistent deterministic pseudonyms with organization-domain separation, storing AES-256-GCM encrypted mappings in an access-controlled vault.
            </p>

            <div>
              <label className="text-xs text-slate-400">Raw Identifier</label>
              <input
                type="text"
                value={pseudoInput}
                onChange={(e) => setPseudoInput(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              onClick={handlePseudonymize}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-medium text-xs text-white transition glow-cyan"
            >
              Generate Controlled Pseudonym
            </button>

            {pseudoOutput && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs">
                <div className="text-slate-400">Generated Token:</div>
                <div className="font-mono text-cyan-400 font-bold bg-slate-950 p-2 rounded border border-slate-800">
                  {pseudoOutput.token}
                </div>
                <div className="text-[11px] text-slate-500">
                  Vault Key Version: {pseudoOutput.key_version} • Purpose: {pseudoOutput.purpose}
                </div>
              </div>
            )}
          </div>

          {/* Re-identification */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Lock className="w-4 h-4 text-amber-400" />
              Authorized Re-identification
            </span>
            <p className="text-xs text-slate-400">
              Restricted to Privacy Officers & Super Admins. Every retrieval decrypts the vault entry and logs to the immutable audit ledger.
            </p>

            <div>
              <label className="text-xs text-slate-400">Token to Re-identify</label>
              <input
                type="text"
                value={reidentToken}
                onChange={(e) => setReidentToken(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-amber-500"
              />
            </div>

            <button
              onClick={handleReidentify}
              className="w-full py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 font-medium text-xs text-white transition glow-amber"
            >
              Verify & Re-identify Identifier
            </button>

            {reidentOutput && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs">
                <div className="text-slate-400">Decrypted Identity:</div>
                <div className="font-mono text-emerald-400 font-bold bg-slate-950 p-2 rounded border border-slate-800">
                  {reidentOutput.original_identifier}
                </div>
                <div className="text-[11px] text-emerald-500 font-medium">
                  ✓ Operation recorded to immutable hash chain audit trail
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: DIFFERENTIAL PRIVACY */}
      {activeTab === 'diff_privacy' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-purple-400" />
              Laplace Mechanism Calibration
            </span>
            <p className="text-xs text-slate-400">
              Injects calibrated noise from Laplace(0, Sensitivity / ε) to guarantee ε-differential privacy for aggregate queries.
            </p>

            <div>
              <div className="flex justify-between text-xs text-slate-300">
                <span>Privacy Budget (ε - Epsilon):</span>
                <span className="font-mono font-bold text-purple-400">{dpEpsilon.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="3.0"
                step="0.1"
                value={dpEpsilon}
                onChange={(e) => setDpEpsilon(parseFloat(e.target.value))}
                className="w-full mt-2"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>High Privacy (ε=0.1)</span>
                <span>Balanced (ε=1.0)</span>
                <span>Low Privacy (ε=3.0)</span>
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400">Actual Raw Count</label>
              <input
                type="number"
                value={dpActual}
                onChange={(e) => setDpActual(parseInt(e.target.value) || 0)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs font-mono text-slate-200"
              />
            </div>

            <button
              onClick={handleDiffPrivacy}
              className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 font-medium text-xs text-white transition glow-purple"
            >
              Compute Noisy Private Aggregate
            </button>
          </div>

          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200">Differential Privacy Guarantee</span>
            {dpOutput ? (
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <div className="text-slate-400 text-[11px]">True Value</div>
                    <div className="text-xl font-bold font-mono text-slate-200 mt-1">
                      {dpOutput.actual_value}
                    </div>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-purple-800/60 glow-purple">
                    <div className="text-purple-300 text-[11px]">Differentially Private Value</div>
                    <div className="text-xl font-bold font-mono text-purple-400 mt-1">
                      {dpOutput.noisy_value}
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1.5 text-[11px] font-mono">
                  <div>Laplace Noise Scale (1 / ε): <span className="text-cyan-400">{dpOutput.laplace_scale}</span></div>
                  <div>Noise Injected: <span className="text-amber-400">{dpOutput.noise_added}</span></div>
                  <div>95% Confidence Interval: <span className="text-slate-300">{dpOutput.confidence_interval_95_pct}</span></div>
                  <div className="text-emerald-400 mt-2 font-sans font-medium">
                    ✓ Guarantee: {dpOutput.privacy_guarantee}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
                Adjust epsilon and click "Compute Noisy Private Aggregate"
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
