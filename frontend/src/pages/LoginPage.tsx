import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyRound, Shield, Lock, AlertCircle, ArrowRight, UserCheck } from 'lucide-react';
import { api } from '../lib/api';
import { useAuthStore } from '../lib/store';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('admin@privasec.io');
  const [password, setPassword] = useState('Password123!');
  const [totpCode, setTotpCode] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setUser, setSession } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await api.auth.login({
        email,
        password,
        totp_code: totpCode || undefined,
      });

      if (res.mfa_required) {
        setMfaRequired(true);
        return;
      }

      if (res.token) {
        localStorage.setItem('privasec_token', res.token);
      }

      setUser(res.user);
      setSession(res.session);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword('Password123!');
    setMfaRequired(false);
    setTotpCode('');
    // Auto submit
    setTimeout(() => {
      api.auth
        .login({ email: roleEmail, password: 'Password123!' })
        .then((res) => {
          if (res.token) localStorage.setItem('privasec_token', res.token);
          setUser(res.user);
          setSession(res.session);
          navigate('/dashboard');
        })
        .catch((err) => setError(err.message));
    }, 100);
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-cyan-950 border border-cyan-500/40 mx-auto flex items-center justify-center text-cyan-400 glow-cyan">
            <KeyRound className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-wider text-slate-100">
            PRIVASEC <span className="text-cyan-400">SOC</span>
          </h1>
          <p className="text-xs text-slate-400">
            Privacy-Preserving Intelligent Cyber Defense Platform
          </p>
        </div>

        {/* Login Box */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full mt-1 rounded-lg bg-slate-900 border border-slate-800 p-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full mt-1 rounded-lg bg-slate-900 border border-slate-800 p-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {mfaRequired && (
              <div className="space-y-1 p-3 rounded-lg bg-cyan-950/40 border border-cyan-800/80">
                <label className="text-xs font-semibold text-cyan-300">
                  TOTP 6-Digit MFA Verification Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="000000"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  className="w-full mt-1 rounded bg-slate-950 border border-slate-800 p-2 text-center font-mono text-base font-bold text-emerald-400 tracking-widest focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white transition glow-cyan flex items-center justify-center gap-2"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to SOC Console'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Logins */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider text-center">
              Quick Role Switcher (Seeded Demo Accounts)
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@privasec.io')}
                className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-left transition"
              >
                <div className="font-semibold text-cyan-400 text-[11px]">Super Admin</div>
                <div className="text-[10px] text-slate-500 truncate">admin@privasec.io</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('analyst@privasec.io')}
                className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-left transition"
              >
                <div className="font-semibold text-emerald-400 text-[11px]">Security Analyst</div>
                <div className="text-[10px] text-slate-500 truncate">analyst@privasec.io</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('privacy@privasec.io')}
                className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-left transition"
              >
                <div className="font-semibold text-purple-400 text-[11px]">Privacy Officer</div>
                <div className="text-[10px] text-slate-500 truncate">privacy@privasec.io</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('user@privasec.io')}
                className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-left transition"
              >
                <div className="font-semibold text-amber-400 text-[11px]">Standard User</div>
                <div className="text-[10px] text-slate-500 truncate">user@privasec.io</div>
              </button>
            </div>
          </div>
        </div>

        {/* Security Footer Notice */}
        <div className="text-center text-[11px] text-slate-500">
          Argon2id Password Hashing • AES-256-GCM Sensitive Encryption • SHA-256 Audit Trail
        </div>
      </div>
    </div>
  );
};
