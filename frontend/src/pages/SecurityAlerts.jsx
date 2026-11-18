import React, { useState, useEffect } from 'react';
import { AlertTriangle, Filter, Search, Eye, X, CheckCircle, ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import api from '../services/api';
import RiskBadge from '../components/RiskBadge';

const SecurityAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      let url = '/alerts?limit=100';
      if (severityFilter) url += `&severity=${severityFilter}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      const res = await api.get(url);
      setAlerts(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, statusFilter]);

  const updateAlertStatus = async (alertId, newStatus) => {
    try {
      const res = await api.patch(`/alerts/${alertId}`, { status: newStatus });
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? res.data : a)));
      if (selectedAlert && selectedAlert.id === alertId) {
        setSelectedAlert(res.data);
      }
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
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            <span>Security Alerts & Threat Triage</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Explainable AI threat classifications, Sigma-style rule hits, and correlated attack alerts
          </p>
        </div>
      </div>

      {/* Filter toolbar */}
      <div className="flex flex-wrap items-center gap-4 bg-[#111827] border border-[#1f293d] p-4 rounded-xl shadow-lg">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Severity:</span>
          {['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition ${
                severityFilter === sev
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  : 'bg-[#162032] text-slate-400 hover:text-slate-200 border border-[#223049]'
              }`}
            >
              {sev || 'ALL'}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Status:</span>
          {['', 'OPEN', 'TRIAGED', 'RESOLVED', 'SUPPRESSED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition ${
                statusFilter === st
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  : 'bg-[#162032] text-slate-400 hover:text-slate-200 border border-[#223049]'
              }`}
            >
              {st || 'ALL'}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Alert Title</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Detection Source</th>
              <th className="py-3 px-4">MITRE Technique</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Explainability</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-500">
                  No alerts matched criteria
                </td>
              </tr>
            ) : (
              alerts.map((al) => (
                <tr key={al.id} className="hover:bg-[#141d2d] transition">
                  <td className="py-3 px-4 font-semibold text-slate-100 max-w-xs truncate">
                    {al.title}
                  </td>
                  <td className="py-3 px-4">
                    <RiskBadge severity={al.severity} />
                  </td>
                  <td className="py-3 px-4 font-bold text-cyan-400">{al.risk_score} / 100</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-[#162032] border border-[#223049] text-slate-300">
                      {al.source}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-cyan-400 font-semibold">{al.mitre_technique || 'T1046'}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      al.status === 'RESOLVED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                      al.status === 'TRIAGED' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                      al.status === 'SUPPRESSED' ? 'bg-slate-700/30 text-slate-400' :
                      'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                    }`}>
                      {al.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setSelectedAlert(al)}
                      className="px-3 py-1 rounded bg-[#162032] border border-[#233149] hover:bg-cyan-500/20 hover:text-cyan-400 hover:border-cyan-500/40 text-slate-300 transition inline-flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Inspect AI</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Explainable AI Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-[#1f293d] flex items-center justify-between bg-[#111827]">
              <div>
                <div className="flex items-center gap-3">
                  <RiskBadge severity={selectedAlert.severity} score={selectedAlert.risk_score} />
                  <span className="text-xs font-mono text-slate-400">UUID: {selectedAlert.alert_uuid}</span>
                </div>
                <h2 className="text-base font-bold text-slate-100 mt-1">{selectedAlert.title}</h2>
              </div>
              <button onClick={() => setSelectedAlert(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 font-mono text-xs">
              {/* Risk Score Explanation */}
              <div className="bg-[#141d2d] border border-[#1f293d] rounded-xl p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" />
                  <span>Explainable Composite Risk Calculation (0 - 100)</span>
                </h3>
                <p className="text-slate-300 text-xs mb-3">
                  Formula: <strong className="text-cyan-300">Risk = (0.35 × ML) + (0.30 × Rule) + (0.20 × Correlation) + (0.15 × ThreatIntel)</strong>
                </p>
                <div className="grid grid-cols-4 gap-3 text-center">
                  <div className="p-2.5 rounded bg-[#0d131f] border border-[#1b2538]">
                    <span className="text-[10px] text-slate-400">ML Score (35%)</span>
                    <p className="text-sm font-bold text-slate-100 mt-1">
                      {selectedAlert.risk_breakdown?.components?.ml_score ?? 75.0}
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-[#0d131f] border border-[#1b2538]">
                    <span className="text-[10px] text-slate-400">Rule Score (30%)</span>
                    <p className="text-sm font-bold text-slate-100 mt-1">
                      {selectedAlert.risk_breakdown?.components?.rule_score ?? 80.0}
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-[#0d131f] border border-[#1b2538]">
                    <span className="text-[10px] text-slate-400">Correlation (20%)</span>
                    <p className="text-sm font-bold text-slate-100 mt-1">
                      {selectedAlert.risk_breakdown?.components?.correlation_score ?? 70.0}
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-[#0d131f] border border-[#1b2538]">
                    <span className="text-[10px] text-slate-400">Threat Intel (15%)</span>
                    <p className="text-sm font-bold text-slate-100 mt-1">
                      {selectedAlert.risk_breakdown?.components?.threat_intel_score ?? 90.0}
                    </p>
                  </div>
                </div>
              </div>

              {/* Contributing Features / Evidence */}
              <div className="bg-[#141d2d] border border-[#1f293d] rounded-xl p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3">
                  Contributing Evidence & Feature Importances
                </h3>
                <pre className="p-3 bg-[#090d16] rounded-lg text-slate-300 overflow-x-auto text-[11px]">
                  {JSON.stringify(selectedAlert.evidence, null, 2)}
                </pre>
              </div>

              {/* Status Triage Controls */}
              <div className="flex items-center justify-between pt-4 border-t border-[#1a2333]">
                <span className="text-xs text-slate-400">Triage Status:</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateAlertStatus(selectedAlert.id, 'TRIAGED')}
                    className="px-3 py-1.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/40 hover:bg-blue-500/30 transition text-xs"
                  >
                    Mark Triaged
                  </button>
                  <button
                    onClick={() => updateAlertStatus(selectedAlert.id, 'RESOLVED')}
                    className="px-3 py-1.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30 transition text-xs"
                  >
                    Resolve Alert
                  </button>
                  <button
                    onClick={() => updateAlertStatus(selectedAlert.id, 'SUPPRESSED')}
                    className="px-3 py-1.5 rounded bg-slate-700/30 text-slate-400 hover:text-slate-200 transition text-xs"
                  >
                    Suppress
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityAlerts;
