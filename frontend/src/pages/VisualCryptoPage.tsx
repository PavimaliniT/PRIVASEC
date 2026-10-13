import React, { useState } from 'react';
import {
  FileKey,
  Upload,
  Layers,
  Sparkles,
  Download,
  AlertCircle,
  Eye,
  RefreshCw
} from 'lucide-react';
import { api } from '../lib/api';

export const VisualCryptoPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [threshold, setThreshold] = useState<number>(128);
  const [splitResult, setSplitResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<'both' | 'share1' | 'share2' | 'overlay'>('both');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSplit = async () => {
    if (!file) {
      // Create a default small test canvas if no file uploaded
      const canvas = document.createElement('canvas');
      canvas.width = 100;
      canvas.height = 100;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, 100, 100);
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 36px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('SOC', 50, 50);
      }
      canvas.toBlob(async (blob) => {
        if (blob) {
          const defaultFile = new File([blob], 'secret_logo.png', { type: 'image/png' });
          await executeSplit(defaultFile);
        }
      });
      return;
    }
    await executeSplit(file);
  };

  const executeSplit = async (targetFile: File) => {
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', targetFile);
      formData.append('threshold', threshold.toString());

      const res = await api.visualCrypto.split(formData);
      setSplitResult(res);
    } catch (err: any) {
      alert(err.message || 'Failed to split image');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <FileKey className="w-6 h-6 text-purple-400" />
          Visual Cryptography Lab
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          2-out-of-2 visual secret sharing (Naor & Shamir). Each share contains zero visual information alone, but stacking them reconstructs the secret image optically.
        </p>
      </div>

      {/* Control Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <span className="text-sm font-semibold text-slate-200">1. Upload Secret Image</span>
          
          <label className="flex flex-col items-center justify-center p-5 border-2 border-dashed border-slate-700 hover:border-purple-500 rounded-lg cursor-pointer bg-slate-900/60 transition">
            <Upload className="w-6 h-6 text-slate-400 mb-1" />
            <span className="text-xs text-slate-300 truncate max-w-xs">
              {file ? file.name : 'Select binary image/logo or use default'}
            </span>
            <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
          </label>

          <div>
            <div className="flex justify-between text-xs text-slate-300">
              <span>Binarization Threshold:</span>
              <span className="font-mono text-purple-400">{threshold}</span>
            </div>
            <input
              type="range"
              min="30"
              max="220"
              value={threshold}
              onChange={(e) => setThreshold(parseInt(e.target.value))}
              className="w-full mt-2"
            />
          </div>

          <button
            onClick={handleSplit}
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 font-semibold text-xs text-white transition glow-purple flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
            Generate Visual Shares
          </button>
        </div>

        {/* Algorithm Principles */}
        <div className="md:col-span-2 p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-3 text-xs text-slate-300">
          <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            2-out-of-2 Visual Secret Sharing Properties
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
              <strong className="text-purple-300">Information-Theoretic Security:</strong>
              <p className="text-[11px] text-slate-400">
                Any individual share consists of uniformly distributed random 2x2 subpixel blocks. Without the complementary share, zero mutual information is leaked.
              </p>
            </div>
            <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
              <strong className="text-cyan-300">Optical Superimposition:</strong>
              <p className="text-[11px] text-slate-400">
                Decryption requires no computer processor: stacking transparencies aligns subpixel patterns. White pixels allow 50% light; black pixels extinguish 100% light.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Results Display */}
      {splitResult && (
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-slate-100">Visual Shares & Optical Overlay</span>
              <div className="text-[11px] text-slate-400">
                Resolution: {splitResult.share_width}x{splitResult.share_height} ({splitResult.expansion_factor})
              </div>
            </div>

            {/* View toggles */}
            <div className="flex rounded-lg bg-slate-900 p-1 border border-slate-800 text-xs gap-1">
              {['both', 'share1', 'share2', 'overlay'].map((v) => (
                <button
                  key={v}
                  onClick={() => setActiveView(v as any)}
                  className={`px-3 py-1 rounded capitalize font-medium transition ${
                    activeView === v ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>

          {/* Shares Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Share 1 */}
            {(activeView === 'both' || activeView === 'share1') && (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center space-y-3">
                <span className="text-xs font-semibold text-slate-300 font-mono">SHARE 1 (NOISE)</span>
                <img
                  src={`data:image/png;base64,${splitResult.share1_png_base64}`}
                  alt="Share 1"
                  className="w-48 h-48 border border-slate-700 bg-white object-contain rounded"
                />
                <a
                  href={`data:image/png;base64,${splitResult.share1_png_base64}`}
                  download="privasec_share_1.png"
                  className="flex items-center gap-1.5 text-xs text-purple-400 hover:underline pt-1"
                >
                  <Download className="w-3.5 h-3.5" /> Download Share 1
                </a>
              </div>
            )}

            {/* Share 2 */}
            {(activeView === 'both' || activeView === 'share2') && (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center space-y-3">
                <span className="text-xs font-semibold text-slate-300 font-mono">SHARE 2 (NOISE)</span>
                <img
                  src={`data:image/png;base64,${splitResult.share2_png_base64}`}
                  alt="Share 2"
                  className="w-48 h-48 border border-slate-700 bg-white object-contain rounded"
                />
                <a
                  href={`data:image/png;base64,${splitResult.share2_png_base64}`}
                  download="privasec_share_2.png"
                  className="flex items-center gap-1.5 text-xs text-purple-400 hover:underline pt-1"
                >
                  <Download className="w-3.5 h-3.5" /> Download Share 2
                </a>
              </div>
            )}

            {/* Superimposed Overlay */}
            {(activeView === 'both' || activeView === 'overlay') && (
              <div className="p-4 rounded-xl bg-slate-900 border border-purple-800/80 glow-purple flex flex-col items-center space-y-3">
                <span className="text-xs font-semibold text-purple-300 font-mono flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5" /> SUPERIMPOSED OVERLAY
                </span>
                <img
                  src={`data:image/png;base64,${splitResult.overlay_preview_base64}`}
                  alt="Reconstructed"
                  className="w-48 h-48 border border-slate-700 bg-white object-contain rounded"
                />
                <span className="text-[11px] text-emerald-400 font-medium pt-1">
                  ✓ Secret optically revealed with 50% contrast!
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
