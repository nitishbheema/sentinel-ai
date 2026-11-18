import React, { useState, useEffect } from 'react';
import { GlobeLock, Plus, Shield, Search, X, Trash2, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import RiskBadge from '../components/RiskBadge';

const ThreatIntelligence = () => {
  const [indicators, setIndicators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newValue, setNewValue] = useState('');
  const [newType, setNewType] = useState('IP');
  const [newThreat, setNewThreat] = useState('C2 Infrastructure');
  const [newConfidence, setNewConfidence] = useState(90);

  const fetchIndicators = async () => {
    try {
      const res = await api.get('/threat-intelligence');
      setIndicators(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndicators();
  }, []);

  const handleCreateIndicator = async (e) => {
    e.preventDefault();
    try {
      await api.post('/threat-intelligence/indicators', {
        indicator_type: newType,
        value: newValue,
        threat_type: newThreat,
        severity: 'HIGH',
        confidence: parseInt(newConfidence),
        source: 'SentinelLab IOC Feed',
        is_active: true,
      });
      setShowModal(false);
      setNewValue('');
      fetchIndicators();
    } catch (err) {
      console.error('Error creating indicator:', err);
    }
  };

  const handleDeactivate = async (id) => {
    try {
      await api.delete(`/threat-intelligence/indicators/${id}`);
      fetchIndicators();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <GlobeLock className="w-5 h-5 text-cyan-400" />
            <span>Threat Intelligence Indicators (IOC Hub)</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Locally curated and external threat intelligence indicators with automated telemetry matching
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold text-xs rounded-lg shadow-lg shadow-cyan-600/30 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Threat Indicator</span>
        </button>
      </div>

      {/* Indicators Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Indicator Value</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Threat Type</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4">Source Feed</th>
              <th className="py-3 px-4">Active</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {indicators.map((ind) => (
              <tr key={ind.id} className="hover:bg-[#141d2d] transition">
                <td className="py-3 px-4 font-bold text-slate-100">{ind.value}</td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded bg-[#162032] border border-[#223049] text-cyan-400 font-bold">
                    {ind.indicator_type}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-200">{ind.threat_type}</td>
                <td className="py-3 px-4">
                  <RiskBadge severity={ind.severity} />
                </td>
                <td className="py-3 px-4 font-bold text-emerald-400">{ind.confidence}%</td>
                <td className="py-3 px-4 text-slate-400">{ind.source}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    ind.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/30 text-slate-500'
                  }`}>
                    {ind.is_active ? 'ACTIVE' : 'EXPIRED'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  {ind.is_active && (
                    <button
                      onClick={() => handleDeactivate(ind.id)}
                      className="p-1 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition"
                      title="Deactivate Indicator"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-md w-full p-6 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#1f293d] mb-4">
              <h2 className="text-sm font-bold text-slate-100">Add Threat Indicator</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateIndicator} className="space-y-4">
              <div>
                <label className="block text-slate-400 mb-1">Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                >
                  <option value="IP">IP Address</option>
                  <option value="DOMAIN">Domain Name</option>
                  <option value="HASH">SHA256 File Hash</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Indicator Value</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 198.51.100.99 or bad-domain.com"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Threat Type</label>
                <input
                  type="text"
                  required
                  value={newThreat}
                  onChange={(e) => setNewThreat(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Confidence Score (0-100)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={newConfidence}
                  onChange={(e) => setNewConfidence(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1f293d]">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded bg-[#162032] text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold"
                >
                  Save Indicator
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreatIntelligence;
