import React, { useState } from 'react';
import {
  Fingerprint,
  QrCode,
  ShieldCheck,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Laptop,
  Trash2
} from 'lucide-react';
import { api } from '../lib/api';
import { useAuthStore } from '../lib/store';

export const AuthPage: React.FC = () => {
  const { user, session, checkAuth } = useAuthStore();

  const [mfaData, setMfaData] = useState<any>(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [stepUpCode, setStepUpCode] = useState('');
  const [mfaSuccess, setMfaSuccess] = useState(false);
  const [stepUpSuccess, setStepUpSuccess] = useState(false);

  const handleSetupMfa = async () => {
    try {
      const res = await api.auth.setupMfa();
      setMfaData(res);
      setMfaSuccess(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleVerifyMfa = async () => {
    try {
      await api.auth.verifyMfa(verifyCode);
      setMfaSuccess(true);
      setMfaData(null);
      await checkAuth();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleStepUp = async () => {
    try {
      await api.auth.stepUp(stepUpCode);
      setStepUpSuccess(true);
      await checkAuth();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Fingerprint className="w-6 h-6 text-emerald-400" />
          Adaptive Authentication & Sessions
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          TOTP multifactor authentication enrollment, risk-based step-up verification, and active session controls
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MFA Setup Card */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <QrCode className="w-4 h-4 text-cyan-400" />
            TOTP Multifactor Authentication (MFA)
          </span>

          <div className="text-xs text-slate-400">
            Current MFA Status:{' '}
            <strong className={user?.mfa_enabled ? 'text-emerald-400' : 'text-amber-400'}>
              {user?.mfa_enabled ? 'ENROLLED & ACTIVE' : 'DISABLED'}
            </strong>
          </div>

          {!mfaData && !user?.mfa_enabled && (
            <button
              onClick={handleSetupMfa}
              className="py-2.5 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white transition glow-cyan"
            >
              Configure TOTP Authenticator
            </button>
          )}

          {mfaData && (
            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-4 text-xs">
              <div className="text-slate-300 font-medium">
                Scan this QR code with Google Authenticator or Authy:
              </div>
              <div className="flex justify-center p-3 bg-white rounded-lg w-48 mx-auto">
                <img
                  src={`data:image/png;base64,${mfaData.qr_code_base64}`}
                  alt="MFA QR Code"
                  className="w-40 h-40"
                />
              </div>
              <div className="text-center font-mono text-[11px] text-slate-400">
                Secret: <span className="text-cyan-400 select-all">{mfaData.secret}</span>
              </div>

              <div className="space-y-2">
                <label className="text-slate-400">Enter 6-Digit Code from App</label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="123456"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value)}
                  className="w-full rounded bg-slate-950 border border-slate-800 p-2.5 text-center font-mono text-base font-bold text-emerald-400 tracking-widest focus:outline-none focus:border-emerald-500"
                />
                <button
                  onClick={handleVerifyMfa}
                  className="w-full py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition"
                >
                  Verify & Activate MFA
                </button>
              </div>
            </div>
          )}

          {mfaSuccess && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" /> MFA successfully enrolled on your account!
            </div>
          )}
        </div>

        {/* Step-Up Challenge Card */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-amber-400" />
            Contextual Step-Up Verification Challenge
          </span>

          <p className="text-xs text-slate-400">
            High-risk operations (such as sensitive data export or key rotation) prompt this step-up challenge to ensure session authorization.
          </p>

          <div className="p-3 rounded bg-slate-900 border border-slate-800 text-xs space-y-1">
            <div className="text-slate-400">Current Session State:</div>
            <div className="font-mono text-cyan-300">
              MFA Authenticated:{' '}
              <strong>{session?.is_mfa_authenticated ? 'ELEVATED (YES)' : 'STANDARD'}</strong>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <label className="text-slate-400">Enter TOTP Step-Up Code</label>
            <input
              type="text"
              maxLength={6}
              placeholder="000000"
              value={stepUpCode}
              onChange={(e) => setStepUpCode(e.target.value)}
              className="w-full rounded bg-slate-900 border border-slate-800 p-2.5 text-center font-mono text-base font-bold text-amber-400 tracking-widest focus:outline-none focus:border-amber-500"
            />
            <button
              onClick={handleStepUp}
              className="w-full py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 font-semibold text-xs text-white transition glow-amber"
            >
              Submit Step-Up Authorization
            </button>
          </div>

          {stepUpSuccess && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" /> Step-up verification granted! Session is now elevated.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
