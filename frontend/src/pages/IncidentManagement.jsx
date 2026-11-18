import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, Plus, Filter, Search, ArrowRight, UserCheck, Clock, X } from 'lucide-react';
import api from '../services/api';
import RiskBadge from '../components/RiskBadge';

const IncidentManagement = () => {
  const [incidents, setIncidents] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSev, setNewSev] = useState('HIGH');

  const fetchIncidents = async () => {
    try {
      let url = '/incidents?limit=50';
      if (statusFilter) url += `&status=${statusFilter}`;
      const res = await api.get(url);
      setIncidents(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter]);

  const handleCreateIncident = async (e) => {
    e.preventDefault();
    try {
      await api.post('/incidents', {
        title: newTitle,
        description: newDesc,
        severity: newSev,
        status: 'NEW',
        risk_score: newSev === 'CRITICAL' ? 85.0 : newSev === 'HIGH' ? 65.0 : 40.0,
      });
      setShowCreateModal(false);
      setNewTitle('');
      setNewDesc('');
      fetchIncidents();
    } catch (err) {
      console.error('Error creating incident:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            <span>Incident Queue & Investigation Management</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Track security incidents through their complete lifecycle: New, Investigating, Confirmed, Resolved, or False Positive
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold text-xs rounded-lg shadow-lg shadow-cyan-600/30 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Create Incident</span>
        </button>
      </div>

      {/* Filter toolbar */}
      <div className="flex items-center gap-2 bg-[#111827] border border-[#1f293d] p-4 rounded-xl shadow-lg">
        <span className="text-xs font-mono text-slate-400">Status:</span>
        {['', 'NEW', 'INVESTIGATING', 'CONFIRMED', 'RESOLVED', 'FALSE_POSITIVE'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1 rounded text-xs font-mono font-medium transition ${
              statusFilter === st
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'bg-[#162032] text-slate-400 hover:text-slate-200 border border-[#223049]'
            }`}
          >
            {st ? st.replace('_', ' ') : 'ALL'}
          </button>
        ))}
      </div>

      {/* Incidents Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Incident Title</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Assigned Analyst</th>
              <th className="py-3 px-4">Linked Evidence</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Workbench</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-500 font-mono">
                  No security incidents recorded in this queue
                </td>
              </tr>
            ) : (
              incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-[#141d2d] transition">
                  <td className="py-3 px-4">
                    <p className="font-bold text-slate-100">{inc.title}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{inc.description}</p>
                  </td>
                  <td className="py-3 px-4">
                    <RiskBadge severity={inc.severity} />
                  </td>
                  <td className="py-3 px-4 font-bold text-cyan-400">{inc.risk_score} / 100</td>
                  <td className="py-3 px-4">
                    <span className="flex items-center gap-1.5 text-slate-300">
                      <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{inc.assigned_to_username || 'Unassigned'}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-[#162032] border border-[#223049]">
                      {inc.events_count} Events
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      inc.status === 'RESOLVED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                      inc.status === 'INVESTIGATING' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' :
                      inc.status === 'CONFIRMED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                      inc.status === 'FALSE_POSITIVE' ? 'bg-slate-700/30 text-slate-400' :
                      'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                    }`}>
                      {inc.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      to={`/incidents/${inc.id}`}
                      className="px-3 py-1 rounded bg-[#162032] border border-[#233149] hover:bg-cyan-500/20 hover:text-cyan-400 hover:border-cyan-500/40 text-slate-300 transition inline-flex items-center gap-1.5"
                    >
                      <span>Investigate</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Incident Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-[#1f293d] mb-4">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-cyan-400" />
                <span>Declare Security Incident</span>
              </h2>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateIncident} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-slate-400 uppercase mb-1">Incident Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Unauthorized Credential Access on DC-01"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 uppercase mb-1">Severity</label>
                <select
                  value={newSev}
                  onChange={(e) => setNewSev(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 uppercase mb-1">Description & Scope</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Describe initial discovery vector, affected entities, and containment urgency..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1f293d]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-2 rounded-lg bg-[#162032] text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold"
                >
                  Create Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentManagement;
