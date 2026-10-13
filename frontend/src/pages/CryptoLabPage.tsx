import React, { useState } from 'react';
import {
  Lock,
  Unlock,
  Key,
  Hash,
  FileCheck,
  CheckCircle2,
  Copy,
  AlertCircle,
  ShieldAlert
} from 'lucide-react';
import { api } from '../lib/api';

export const CryptoLabPage: React.FC = () => {
  // Key Generation
  const [activeKey, setActiveKey] = useState<string>('');

  // Text Encryption State
  const [plaintext, setPlaintext] = useState<string>('Antigravity Zero-Knowledge Security Directive');
  const [encryptResult, setEncryptResult] = useState<any>(null);

  // Decryption State
  const [decryptNonce, setDecryptNonce] = useState<string>('');
  const [decryptCiphertext, setDecryptCiphertext] = useState<string>('');
  const [decryptTag, setDecryptTag] = useState<string>('');
  const [decryptedPlaintext, setDecryptedPlaintext] = useState<string | null>(null);
  const [decryptError, setDecryptError] = useState<string | null>(null);

  // Hash State
  const [hashInput, setHashInput] = useState<string>('Cybersecurity Architecture 2026');
  const [expectedHash, setExpectedHash] = useState<string>('');
  const [hashResult, setHashResult] = useState<any>(null);

  const handleGenerateKey = async () => {
    try {
      const res = await api.crypto.generateKey();
      setActiveKey(res.key_hex);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleEncryptText = async () => {
    try {
      const res = await api.crypto.encryptText(plaintext, activeKey || undefined);
      setEncryptResult(res);
      setDecryptNonce(res.nonce_hex);
      setDecryptCiphertext(res.ciphertext_hex);
      setDecryptTag(res.tag_hex);
      setDecryptedPlaintext(null);
      setDecryptError(null);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDecryptText = async () => {
    try {
      setDecryptError(null);
      const res = await api.crypto.decryptText(
        decryptNonce,
        decryptCiphertext,
        decryptTag,
        activeKey || undefined
      );
      setDecryptedPlaintext(res.plaintext);
    } catch (err: any) {
      setDecryptError(err.message);
    }
  };

  const handleComputeHash = async () => {
    try {
      const res = await api.crypto.hash(hashInput, expectedHash || undefined);
      setHashResult(res);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Lock className="w-6 h-6 text-cyan-400" />
          Cryptography Lab
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          AES-256-GCM authenticated encryption, isolated nonce generation, tag verification, and SHA-256/512 integrity
        </p>
      </div>

      {/* KMS Key Generation Bar */}
      <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Key className="w-5 h-5 text-cyan-400 shrink-0" />
          <div>
            <div className="text-xs font-semibold text-slate-200">KMS Key Management (AES-256)</div>
            <div className="text-[11px] font-mono text-slate-400 truncate max-w-md">
              {activeKey ? `Active Key: ${activeKey}` : 'Using default master key (Version 1)'}
            </div>
          </div>
        </div>
        <button
          onClick={handleGenerateKey}
          className="px-3 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 text-xs font-mono transition"
        >
          Generate Fresh 256-Bit Key
        </button>
      </div>

      {/* Grid: Encrypt & Decrypt */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Encrypt Card */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            AES-256-GCM Encryption
          </span>

          <div>
            <label className="text-xs text-slate-400">Plaintext to Encrypt</label>
            <textarea
              rows={3}
              value={plaintext}
              onChange={(e) => setPlaintext(e.target.value)}
              className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <button
            onClick={handleEncryptText}
            className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white transition glow-cyan"
          >
            Encrypt with Unique Nonce
          </button>

          {encryptResult && (
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs font-mono">
              <div className="text-slate-400 text-[11px]">
                Algorithm: <strong className="text-cyan-400">{encryptResult.algorithm}</strong>
              </div>
              <div>
                <span className="text-slate-500 text-[10px]">Nonce (96-bit):</span>
                <div className="text-cyan-300 break-all">{encryptResult.nonce_hex}</div>
              </div>
              <div>
                <span className="text-slate-500 text-[10px]">Ciphertext:</span>
                <div className="text-slate-200 break-all">{encryptResult.ciphertext_hex}</div>
              </div>
              <div>
                <span className="text-slate-500 text-[10px]">Authentication Tag (128-bit):</span>
                <div className="text-emerald-400 break-all">{encryptResult.tag_hex}</div>
              </div>
            </div>
          )}
        </div>

        {/* Decrypt Card */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Unlock className="w-4 h-4 text-emerald-400" />
            Authenticated Decryption & Tamper Check
          </span>

          <div className="space-y-2 text-xs font-mono">
            <div>
              <label className="text-slate-400 text-[11px]">Nonce Hex</label>
              <input
                type="text"
                value={decryptNonce}
                onChange={(e) => setDecryptNonce(e.target.value)}
                className="w-full rounded bg-slate-900 border border-slate-800 p-2 text-slate-200"
              />
            </div>
            <div>
              <label className="text-slate-400 text-[11px]">Ciphertext Hex</label>
              <input
                type="text"
                value={decryptCiphertext}
                onChange={(e) => setDecryptCiphertext(e.target.value)}
                className="w-full rounded bg-slate-900 border border-slate-800 p-2 text-slate-200"
              />
            </div>
            <div>
              <label className="text-slate-400 text-[11px]">Authentication Tag Hex</label>
              <input
                type="text"
                value={decryptTag}
                onChange={(e) => setDecryptTag(e.target.value)}
                className="w-full rounded bg-slate-900 border border-slate-800 p-2 text-slate-200"
              />
            </div>
          </div>

          <button
            onClick={handleDecryptText}
            className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-xs text-white transition glow-emerald"
          >
            Verify Tag & Decrypt Plaintext
          </button>

          {decryptedPlaintext && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 space-y-1 text-xs">
              <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Authentication Tag Validated!
              </div>
              <div className="font-mono text-slate-100 bg-slate-950 p-2 rounded mt-1">
                {decryptedPlaintext}
              </div>
            </div>
          )}

          {decryptError && (
            <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{decryptError}</span>
            </div>
          )}
        </div>
      </div>

      {/* Hashing & Integrity Verification */}
      <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
        <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Hash className="w-4 h-4 text-purple-400" />
          Cryptographic Hashing & File Integrity (SHA-256 / SHA-512)
        </span>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400">Input Data</label>
            <input
              type="text"
              value={hashInput}
              onChange={(e) => setHashInput(e.target.value)}
              className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs font-mono text-slate-200"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400">Expected SHA-256 (Optional check)</label>
            <input
              type="text"
              placeholder="Paste SHA-256 to verify integrity..."
              value={expectedHash}
              onChange={(e) => setExpectedHash(e.target.value)}
              className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs font-mono text-slate-200"
            />
          </div>
        </div>

        <button
          onClick={handleComputeHash}
          className="py-2 px-5 rounded-lg bg-purple-600 hover:bg-purple-500 font-semibold text-xs text-white transition glow-purple"
        >
          Compute & Verify Hashes
        </button>

        {hashResult && (
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs font-mono">
            <div>
              <span className="text-slate-500 text-[10px]">SHA-256 Digest:</span>
              <div className="text-purple-300 break-all">{hashResult.sha256}</div>
            </div>
            <div>
              <span className="text-slate-500 text-[10px]">SHA-512 Digest:</span>
              <div className="text-slate-400 break-all text-[11px]">{hashResult.sha512}</div>
            </div>
            {hashResult.verified !== null && (
              <div
                className={`p-2 rounded text-xs font-sans font-semibold flex items-center gap-2 ${
                  hashResult.verified
                    ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                    : 'bg-rose-950/60 text-rose-400 border border-rose-800'
                }`}
              >
                {hashResult.verified ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" /> Integrity Verified: SHA-256 matches perfectly!
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4" /> Integrity Violation: Digest does not match expected hash!
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
