import React, { useState, useEffect } from 'react';
import { ShieldCheck, Check, X, RotateCcw, AlertOctagon, Terminal, RefreshCw } from 'lucide-react';
import api from '../services/api';

const ResponseManagement = () => {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAction, setSelectedAction] = useState(null);
  const [notice, setNotice] = useState('');

  const fetchActions = async () => {
    try {
      const res = await api.get('/response/actions');
      setActions(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const handleApprove = async (actionId) => {
    try {
      const res = await api.post(`/response/${actionId}/approve`);
      setActions((prev) => prev.map((a) => (a.id === actionId ? res.data : a)));
      setNotice(`Defensive action #${actionId} approved & executed successfully.`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (actionId) => {
    try {
      const res = await api.post(`/response/${actionId}/reject`);
      setActions((prev) => prev.map((a) => (a.id === actionId ? res.data : a)));
      setNotice(`Action #${actionId} rejected by analyst.`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRollback = async (actionId) => {
    try {
      const res = await api.post(`/response/${actionId}/rollback`);
      setActions((prev) => prev.map((a) => (a.id === actionId ? res.data : a)));
      setNotice(`Action #${actionId} containment lifted & rolled back.`);
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
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Automated Defensive Response & Approval Hub</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Analyst-authorized active defense: simulated lab IP blocking, endpoint network quarantine, and containment rollbacks
          </p>
        </div>
        <button
          onClick={fetchActions}
          className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Actions</span>
        </button>
      </div>

      {notice && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs text-emerald-400 font-mono">
          <span>{notice}</span>
          <button onClick={() => setNotice('')} className="underline">Dismiss</button>
        </div>
      )}

      {/* Security Caution Box */}
      <div className="bg-[#141c2c] border border-cyan-500/30 rounded-xl p-4 flex items-start gap-3">
        <AlertOctagon className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-xs font-mono text-slate-300">
          <p className="font-bold text-slate-100 uppercase">Human-in-the-Loop Security Guardrails Enforced</p>
          <p className="text-slate-400 mt-1">
            Zero automated destructive actions occur without explicit analyst approval. All containment demonstrations execute simulated laboratory commands (<code className="text-cyan-400">iptables DROP</code>, <code className="text-cyan-400">agent quarantine</code>) and maintain complete audit provenance.
          </p>
        </div>
      </div>

      {/* Response Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Action ID</th>
              <th className="py-3 px-4">Defensive Type</th>
              <th className="py-3 px-4">Target Entity</th>
              <th className="py-3 px-4">Current Status</th>
              <th className="py-3 px-4">Rollback Support</th>
              <th className="py-3 px-4">Dispatched At</th>
              <th className="py-3 px-4 text-right">Analyst Authorization</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {actions.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-500 font-mono">
                  No defensive actions currently queued
                </td>
              </tr>
            ) : (
              actions.map((act) => (
                <tr key={act.id} className="hover:bg-[#141d2d] transition">
                  <td className="py-3 px-4 font-bold text-cyan-400">#{act.id}</td>
                  <td className="py-3 px-4">
                    <span className="font-bold text-slate-100">{act.action_type}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-200 font-semibold">{act.target}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      act.status === 'EXECUTED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                      act.status === 'PENDING_APPROVAL' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30 animate-pulse' :
                      act.status === 'ROLLED_BACK' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                      'bg-slate-700/30 text-slate-400'
                    }`}>
                      {act.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">AVAILABLE</td>
                  <td className="py-3 px-4 text-slate-400">
                    {new Date(act.created_at).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {act.status === 'PENDING_APPROVAL' ? (
                        <>
                          <button
                            onClick={() => handleApprove(act.id)}
                            className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30 transition font-bold"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReject(act.id)}
                            className="px-2.5 py-1 rounded bg-red-500/20 text-red-400 border border-red-500/40 hover:bg-red-500/30 transition"
                          >
                            Reject
                          </button>
                        </>
                      ) : act.status === 'EXECUTED' ? (
                        <button
                          onClick={() => handleRollback(act.id)}
                          className="px-2.5 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/40 hover:bg-blue-500/30 transition flex items-center gap-1"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>Rollback</span>
                        </button>
                      ) : (
                        <span className="text-slate-500 text-[10px]">Archived</span>
                      )}

                      {act.execution_result && (
                        <button
                          onClick={() => setSelectedAction(act)}
                          className="p-1 rounded bg-[#162032] border border-[#233149] text-slate-400 hover:text-cyan-400"
                          title="View Execution Log"
                        >
                          <Terminal className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Execution Log Modal */}
      {selectedAction && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-lg w-full p-6 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#1f293d] mb-4">
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Response Execution Audit: #{selectedAction.id}</span>
              </h2>
              <button onClick={() => setSelectedAction(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <pre className="p-4 bg-[#090d16] border border-[#1b2538] rounded-lg text-slate-300 overflow-x-auto text-[11px]">
              {JSON.stringify(selectedAction.execution_result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResponseManagement;
