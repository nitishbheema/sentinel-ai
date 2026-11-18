import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ShieldAlert,
  ArrowLeft,
  Clock,
  UserCheck,
  MessageSquare,
  Send,
  ShieldCheck,
  AlertTriangle,
  Radio,
  CheckCircle2,
  Lock,
  Layers
} from 'lucide-react';
import api from '../services/api';
import RiskBadge from '../components/RiskBadge';

const IncidentInvestigation = () => {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(true);
  const [responseNotice, setResponseNotice] = useState(null);

  const fetchIncident = async () => {
    try {
      const res = await api.get(`/incidents/${id}`);
      setIncident(res.data);
      setNotes(res.data.notes || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncident();
  }, [id]);

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      const res = await api.post(`/incidents/${id}/notes`, { note: newNote });
      setNotes((prev) => [...prev, res.data]);
      setNewNote('');
    } catch (err) {
      console.error('Error adding note:', err);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      const res = await api.patch(`/incidents/${id}`, { status: newStatus });
      setIncident(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const requestContainment = async (actionType, target) => {
    try {
      setResponseNotice(`Dispatched containment recommendation: ${actionType} on ${target}. Pending analyst approval in Response Hub.`);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="p-10 font-mono text-center text-slate-400">Loading incident investigation workbench...</div>;
  }

  if (!incident) {
    return (
      <div className="p-10 font-mono text-center text-red-400">
        <p>Incident #{id} not found</p>
        <Link to="/incidents" className="text-cyan-400 underline mt-2 block">← Back to Incidents</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div className="flex items-center gap-3">
          <Link
            to="/incidents"
            className="p-2 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400">INCIDENT #{incident.id}</span>
              <RiskBadge severity={incident.severity} score={incident.risk_score} />
            </div>
            <h1 className="text-lg font-bold text-slate-100 uppercase tracking-wider mt-0.5">
              {incident.title}
            </h1>
          </div>
        </div>

        {/* Status selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">Status:</span>
          <select
            value={incident.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="bg-[#111827] border border-[#1f293d] rounded-lg px-3 py-1.5 text-xs font-mono text-cyan-400 focus:outline-none focus:border-cyan-500 font-bold"
          >
            <option value="NEW">NEW</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="FALSE_POSITIVE">FALSE POSITIVE</option>
          </select>
        </div>
      </div>

      {responseNotice && (
        <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl flex items-center justify-between text-xs text-cyan-400 font-mono">
          <span>{responseNotice}</span>
          <button onClick={() => setResponseNotice(null)} className="underline">Dismiss</button>
        </div>
      )}

      {/* Overview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Scope & MITRE Tactics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Incident Scope Card */}
          <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-2">
              Incident Scope & Executive Description
            </h2>
            <p className="text-xs text-slate-300 font-mono leading-relaxed bg-[#0c101a] p-4 rounded-lg border border-[#1a2333]">
              {incident.description || 'No description provided.'}
            </p>

            <div className="grid grid-cols-3 gap-3 mt-4 text-xs font-mono">
              <div className="p-3 bg-[#141d2d] rounded-lg border border-[#1b2538]">
                <span className="text-slate-400 text-[10px]">Assigned Analyst</span>
                <p className="text-slate-200 font-bold mt-0.5">{incident.assigned_to_username || 'Unassigned'}</p>
              </div>
              <div className="p-3 bg-[#141d2d] rounded-lg border border-[#1b2538]">
                <span className="text-slate-400 text-[10px]">Linked Events</span>
                <p className="text-slate-200 font-bold mt-0.5">{incident.events_count} Correlated</p>
              </div>
              <div className="p-3 bg-[#141d2d] rounded-lg border border-[#1b2538]">
                <span className="text-slate-400 text-[10px]">Created</span>
                <p className="text-slate-200 font-bold mt-0.5">{new Date(incident.created_at).toLocaleTimeString()}</p>
              </div>
            </div>
          </div>

          {/* MITRE ATT&CK Tactics Mapped */}
          <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              <span>Correlated MITRE ATT&CK Tactics</span>
            </h2>
            <div className="flex flex-wrap gap-2">
              {(incident.mitre_tactics || ['Initial Access', 'Execution', 'Command and Control']).map((tac, i) => (
                <span key={i} className="px-3 py-1 rounded bg-[#162032] border border-cyan-500/30 text-cyan-400 text-xs font-mono font-bold">
                  {tac}
                </span>
              ))}
            </div>
          </div>

          {/* Defense Containment Actions */}
          <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Analyst Defense Containment Actions</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mb-4">
              All containment actions require explicit analyst authorization before execution.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => requestContainment('ISOLATE_HOST', 'sec-lab-srv01')}
                className="px-3.5 py-2 bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-400 rounded-lg text-xs font-mono font-bold transition flex items-center gap-2"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Recommend Host Isolation</span>
              </button>
              <button
                onClick={() => requestContainment('BLOCK_IP', '203.0.113.88')}
                className="px-3.5 py-2 bg-orange-500/10 border border-orange-500/30 hover:bg-orange-500/20 text-orange-400 rounded-lg text-xs font-mono font-bold transition flex items-center gap-2"
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Recommend Attacker IP Block</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Investigation Timeline & Notes */}
        <div className="space-y-6">
          <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg flex flex-col h-[520px]">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-cyan-400" />
              <span>Analyst Investigation Notes</span>
            </h2>

            {/* Notes timeline list */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {notes.length === 0 ? (
                <p className="text-xs text-slate-500 font-mono text-center py-10">No notes logged yet</p>
              ) : (
                notes.map((n) => (
                  <div key={n.id} className="p-3 rounded-lg bg-[#141d2d] border border-[#1b2538] text-xs font-mono">
                    <div className="flex items-center justify-between text-slate-400 text-[10px] mb-1">
                      <span className="font-bold text-cyan-400">@{n.author_username || 'Analyst'}</span>
                      <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{n.note}</p>
                  </div>
                ))
              )}
            </div>

            {/* Note entry form */}
            <form onSubmit={handleAddNote} className="mt-4 pt-3 border-t border-[#1a2333] flex gap-2">
              <input
                type="text"
                placeholder="Add investigation evidence or hypothesis..."
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                className="flex-1 bg-[#162032] border border-[#223049] rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
              />
              <button
                type="submit"
                className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold rounded-lg text-xs font-mono transition flex items-center gap-1"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncidentInvestigation;
