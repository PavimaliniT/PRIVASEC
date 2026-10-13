import React, { useState } from 'react';
import {
  Image as ImageIcon,
  Lock,
  Unlock,
  Upload,
  Download,
  Eye,
  Sliders,
  CheckCircle2,
  RefreshCw,
  GitCompare
} from 'lucide-react';
import { api } from '../lib/api';

export const SteganographyPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'embed' | 'extract' | 'compare'>('embed');

  // Embed State
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [secretMsg, setSecretMsg] = useState('PRIVASEC-CLASSIFIED-PAYLOAD-TOKEN-4491');
  const [embedKey, setEmbedKey] = useState('');
  const [embedResult, setEmbedResult] = useState<any>(null);
  const [embedding, setEmbedding] = useState(false);

  // Extract State
  const [stegoFile, setStegoFile] = useState<File | null>(null);
  const [extractKey, setExtractKey] = useState('');
  const [extractResult, setExtractResult] = useState<any>(null);
  const [extracting, setExtracting] = useState(false);

  // Compare State
  const [compareCover, setCompareCover] = useState<File | null>(null);
  const [compareStego, setCompareStego] = useState<File | null>(null);
  const [compareResult, setCompareResult] = useState<any>(null);

  const handleEmbed = async () => {
    // If no cover image uploaded, generate a default synthetic 128x128 PNG canvas
    let targetFile = coverFile;
    if (!targetFile) {
      const canvas = document.createElement('canvas');
      canvas.width = 128;
      canvas.height = 128;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const grad = ctx.createLinearGradient(0, 0, 128, 128);
        grad.addColorStop(0, '#1e293b');
        grad.addColorStop(1, '#0f172a');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 128, 128);
      }
      const blob: Blob = await new Promise((res) => canvas.toBlob((b) => res(b!), 'image/png'));
      targetFile = new File([blob], 'cover_carrier.png', { type: 'image/png' });
    }

    try {
      setEmbedding(true);
      const formData = new FormData();
      formData.append('cover_image', targetFile);
      formData.append('secret_message', secretMsg);
      if (embedKey) formData.append('key_hex', embedKey);

      const res = await api.steganography.embed(formData);
      setEmbedResult(res);
    } catch (err: any) {
      alert(err.message || 'Embedding failed');
    } finally {
      setEmbedding(false);
    }
  };

  const handleExtract = async () => {
    if (!stegoFile && !embedResult) {
      alert('Please upload a stego PNG image or generate one first in the Embed tab.');
      return;
    }

    try {
      setExtracting(true);
      const formData = new FormData();
      if (stegoFile) {
        formData.append('stego_image', stegoFile);
      } else {
        // Use stego generated in memory
        const byteCharacters = atob(embedResult.stego_png_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const blob = new Blob([new Uint8Array(byteNumbers)], { type: 'image/png' });
        formData.append('stego_image', blob, 'stego_image.png');
      }

      if (extractKey || embedKey) formData.append('key_hex', extractKey || embedKey);

      const res = await api.steganography.extract(formData);
      setExtractResult(res);
    } catch (err: any) {
      alert(err.message || 'Extraction failed');
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <ImageIcon className="w-6 h-6 text-cyan-400" />
          Steganography Lab
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Lossless PNG Least-Significant-Bit (LSB) embedding with authenticated AES-256-GCM encryption, PSNR metrics, and extraction
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        {[
          { id: 'embed', label: 'Embed Encrypted Payload' },
          { id: 'extract', label: 'Extract & Decrypt Message' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition -mb-px ${
              activeTab === tab.id
                ? 'border-cyan-500 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: EMBED */}
      {activeTab === 'embed' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              1. Carrier PNG & Secret Payload
            </span>

            <label className="flex flex-col items-center justify-center p-4 border-2 border-dashed border-slate-700 hover:border-cyan-500 rounded-lg cursor-pointer bg-slate-900/60 transition">
              <Upload className="w-6 h-6 text-slate-400 mb-1" />
              <span className="text-xs text-slate-300 truncate max-w-xs">
                {coverFile ? coverFile.name : 'Upload cover PNG (or default carrier)'}
              </span>
              <input
                type="file"
                accept=".png"
                onChange={(e) => setCoverFile(e.target.files?.[0] || null)}
                className="hidden"
              />
            </label>

            <div>
              <label className="text-xs text-slate-400">Secret Message</label>
              <textarea
                rows={3}
                value={secretMsg}
                onChange={(e) => setSecretMsg(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400">Custom AES Key Hex (Optional)</label>
              <input
                type="text"
                placeholder="Leave blank to use platform KMS master key"
                value={embedKey}
                onChange={(e) => setEmbedKey(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2 text-xs font-mono text-slate-200"
              />
            </div>

            <button
              onClick={handleEmbed}
              disabled={embedding}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white transition glow-cyan flex items-center justify-center gap-2"
            >
              {embedding ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
              Encrypt & Embed into PNG LSBs
            </button>
          </div>

          {/* Embed Result */}
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200">Generated Stego PNG & Quality Metrics</span>

            {embedResult ? (
              <div className="space-y-4">
                <div className="flex items-center gap-6">
                  <img
                    src={`data:image/png;base64,${embedResult.stego_png_base64}`}
                    alt="Stego"
                    className="w-32 h-32 rounded border border-slate-700 bg-slate-950 object-cover"
                  />
                  <div className="space-y-1.5 text-xs font-mono">
                    <div className="text-slate-400">
                      PSNR:{' '}
                      <strong className="text-emerald-400 font-bold text-sm">
                        {embedResult.psnr_db} dB
                      </strong>{' '}
                      ({embedResult.imperceptibility})
                    </div>
                    <div className="text-slate-400">
                      MSE: <strong className="text-slate-200">{embedResult.mse}</strong>
                    </div>
                    <div className="text-slate-400">
                      Modified Bits: <strong className="text-cyan-400">{embedResult.bits_modified}</strong>
                    </div>
                    <div className="text-slate-400">
                      Encryption: <strong className="text-purple-400">{embedResult.encryption_algorithm}</strong>
                    </div>
                  </div>
                </div>

                <div className="pt-2">
                  <a
                    href={`data:image/png;base64,${embedResult.stego_png_base64}`}
                    download="stego_protected_carrier.png"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-xs font-semibold transition"
                  >
                    <Download className="w-4 h-4" /> Download Stego PNG
                  </a>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
                Configure carrier and click "Encrypt & Embed into PNG LSBs"
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: EXTRACT */}
      {activeTab === 'extract' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Unlock className="w-4 h-4 text-emerald-400" />
              Upload Stego Image for Extraction
            </span>

            <label className="flex flex-col items-center justify-center p-5 border-2 border-dashed border-slate-700 hover:border-emerald-500 rounded-lg cursor-pointer bg-slate-900/60 transition">
              <Upload className="w-6 h-6 text-slate-400 mb-1" />
              <span className="text-xs text-slate-300 truncate max-w-xs">
                {stegoFile
                  ? stegoFile.name
                  : embedResult
                  ? 'Using stego PNG generated in session'
                  : 'Select stego PNG file'}
              </span>
              <input
                type="file"
                accept=".png"
                onChange={(e) => setStegoFile(e.target.files?.[0] || null)}
                className="hidden"
              />
            </label>

            <div>
              <label className="text-xs text-slate-400">Decryption Key Hex (Optional)</label>
              <input
                type="text"
                placeholder="Leave blank if encrypted with master key"
                value={extractKey}
                onChange={(e) => setExtractKey(e.target.value)}
                className="w-full mt-1 rounded bg-slate-900 border border-slate-800 p-2 text-xs font-mono text-slate-200"
              />
            </div>

            <button
              onClick={handleExtract}
              disabled={extracting}
              className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-xs text-white transition glow-emerald flex items-center justify-center gap-2"
            >
              {extracting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Unlock className="w-4 h-4" />}
              Extract & Decrypt Payload
            </button>
          </div>

          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            <span className="text-sm font-semibold text-slate-200">Decrypted Secret Message</span>
            {extractResult ? (
              <div className="space-y-3">
                <div className="p-4 rounded-lg bg-emerald-950/40 border border-emerald-800 text-xs">
                  <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Authenticated Decryption Successful!
                  </div>
                  <div className="font-mono text-slate-100 bg-slate-950 p-3 rounded border border-slate-800 break-all text-sm font-bold">
                    {extractResult.secret_message}
                  </div>
                </div>
                <div className="text-[11px] font-mono text-slate-400 space-y-0.5">
                  <div>Nonce: {extractResult.nonce_hex}</div>
                  <div>Tag: {extractResult.tag_hex}</div>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
                Upload stego PNG and click "Extract & Decrypt Payload"
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
