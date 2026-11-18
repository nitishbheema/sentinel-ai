import React, { useState, useEffect } from 'react';
import { Sliders, Check, X, Shield, Eye, Code, RefreshCw } from 'lucide-react';
import api from '../services/api';
import RiskBadge from '../components/RiskBadge';

const DetectionRules = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRule, setSelectedRule] = useState(null);

  const fetchRules = async () => {
    try {
      const res = await api.get('/detection-rules');
      setRules(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const toggleRule = async (rule) => {
    try {
      const res = await api.patch(`/detection-rules/${rule.id}`, {
        is_enabled: !rule.is_enabled,
      });
      setRules((prev) => prev.map((r) => (r.id === rule.id ? res.data : r)));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            <span>Detection Rule Engine Management</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Configurable Sigma-inspired detection logic, heuristic sliding windows, thresholds, and MITRE ATT&CK mapping
          </p>
        </div>
        <button
          onClick={fetchRules}
          className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reload Rules</span>
        </button>
      </div>

      {/* Rules Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Rule ID</th>
              <th className="py-3 px-4">Rule Name</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Window / Threshold</th>
              <th className="py-3 px-4">MITRE Technique</th>
              <th className="py-3 px-4">Active</th>
              <th className="py-3 px-4 text-right">Condition</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {rules.map((r) => (
              <tr key={r.id} className="hover:bg-[#141d2d] transition">
                <td className="py-3 px-4 font-bold text-cyan-400">{r.rule_id}</td>
                <td className="py-3 px-4">
                  <p className="font-bold text-slate-100">{r.name}</p>
                  <p className="text-[11px] text-slate-400 line-clamp-1">{r.description}</p>
                </td>
                <td className="py-3 px-4 text-slate-300">{r.category}</td>
                <td className="py-3 px-4">
                  <RiskBadge severity={r.severity} />
                </td>
                <td className="py-3 px-4 text-slate-300">
                  <span>{r.time_window_seconds}s</span> / <strong>≥ {r.threshold} hits</strong>
                </td>
                <td className="py-3 px-4 text-cyan-400 font-semibold">{r.mitre_technique_id || 'T1046'}</td>
                <td className="py-3 px-4">
                  <button
                    onClick={() => toggleRule(r)}
                    className={`px-2.5 py-1 rounded text-[10px] font-bold border transition ${
                      r.is_enabled
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/30'
                        : 'bg-slate-800 text-slate-500 border-slate-700 hover:text-slate-300'
                    }`}
                  >
                    {r.is_enabled ? 'ENABLED' : 'DISABLED'}
                  </button>
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => setSelectedRule(r)}
                    className="p-1 rounded bg-[#162032] border border-[#233149] hover:text-cyan-400 transition"
                    title="View YAML Condition"
                  >
                    <Code className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* YAML Condition Modal */}
      {selectedRule && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#1f293d] mb-4">
              <h2 className="text-sm font-bold text-slate-100 font-mono">
                Rule Condition: {selectedRule.rule_id}
              </h2>
              <button onClick={() => setSelectedRule(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <pre className="p-4 bg-[#090d16] border border-[#1b2538] rounded-lg text-slate-300 text-xs font-mono overflow-x-auto">
              {selectedRule.condition_yaml}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetectionRules;
