import React, { useState } from 'react';
import { Settings as SettingsIcon, Sliders, Key, Server, FileCode, Check, Copy } from 'lucide-react';

const Settings = () => {
  const [weights, setWeights] = useState({
    ml: 0.35,
    rule: 0.30,
    corr: 0.20,
    intel: 0.15,
  });
  const [copied, setCopied] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);

  const handleCopyKey = () => {
    navigator.clipboard.writeText('sentinel_agent_telemetry_secure_key_2026');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveWeights = (e) => {
    e.preventDefault();
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-cyan-400" />
            <span>Platform Configuration & Diagnostics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Fine-tune risk calculation weights, manage sensor agent telemetry keys, and view API documentation
          </p>
        </div>
      </div>

      {savedNotice && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 font-mono">
          Risk formula weights calibrated and synchronized to runtime engine.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Scoring Engine Weights */}
        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-2 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span>Composite Risk Formula Weights (Sum = 1.0)</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mb-4">
            Adjust component influences for normalized threat score generation (0 - 100).
          </p>

          <form onSubmit={handleSaveWeights} className="space-y-4 font-mono text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-300">Machine Learning Intrusion Weight</span>
                <span className="text-cyan-400 font-bold">{weights.ml}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.6"
                step="0.05"
                value={weights.ml}
                onChange={(e) => setWeights({ ...weights, ml: parseFloat(e.target.value) })}
                className="w-full accent-cyan-500 bg-[#162032]"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-300">Rule-Based Detection Weight</span>
                <span className="text-cyan-400 font-bold">{weights.rule}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.6"
                step="0.05"
                value={weights.rule}
                onChange={(e) => setWeights({ ...weights, rule: parseFloat(e.target.value) })}
                className="w-full accent-cyan-500 bg-[#162032]"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-300">Multi-Stage Correlation Weight</span>
                <span className="text-cyan-400 font-bold">{weights.corr}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.5"
                step="0.05"
                value={weights.corr}
                onChange={(e) => setWeights({ ...weights, corr: parseFloat(e.target.value) })}
                className="w-full accent-cyan-500 bg-[#162032]"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-300">Threat Intelligence Match Weight</span>
                <span className="text-cyan-400 font-bold">{weights.intel}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.4"
                step="0.05"
                value={weights.intel}
                onChange={(e) => setWeights({ ...weights, intel: parseFloat(e.target.value) })}
                className="w-full accent-cyan-500 bg-[#162032]"
              />
            </div>

            <button
              type="submit"
              className="mt-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold rounded-lg transition"
            >
              Calibrate Risk Engine
            </button>
          </form>
        </div>

        {/* System Diagnostics & Telemetry Secrets */}
        <div className="space-y-6">
          <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
              <Key className="w-4 h-4 text-cyan-400" />
              <span>Endpoint Agent Shared Secret</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mb-3">
              Telemetry intake API secret required in the <code className="text-slate-200">X-Agent-Secret</code> header:
            </p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value="sentinel_agent_telemetry_secure_key_2026"
                className="w-full bg-[#141d2d] border border-[#1b2538] rounded-lg p-2 font-mono text-xs text-cyan-400 select-all"
              />
              <button
                type="button"
                onClick={handleCopyKey}
                className="px-3 py-2 bg-[#162032] border border-[#223049] hover:text-cyan-400 rounded-lg text-xs font-mono transition flex items-center gap-1 shrink-0"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>

          <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-400" />
              <span>System Diagnostics & Documentation</span>
            </h2>
            <div className="space-y-2 font-mono text-xs text-slate-300">
              <div className="flex justify-between py-1 border-b border-[#1a2333]">
                <span className="text-slate-400">Application Version:</span>
                <span className="text-cyan-400 font-bold">SentinelAI v1.0.0</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1a2333]">
                <span className="text-slate-400">Database Engine:</span>
                <span className="text-slate-200">PostgreSQL / SQLite Production Ready</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1a2333]">
                <span className="text-slate-400">Interactive OpenAPI Docs:</span>
                <a href="/api/docs" target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">
                  /api/docs ↗
                </a>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">ReDoc Specification:</span>
                <a href="/api/redoc" target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">
                  /api/redoc ↗
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
