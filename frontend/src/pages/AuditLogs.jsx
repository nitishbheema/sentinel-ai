import React, { useState, useEffect } from 'react';
import { FileText, Search, Filter, RefreshCw, Terminal, X } from 'lucide-react';
import api from '../services/api';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = async () => {
    try {
      let url = '/audit-logs?limit=100';
      if (actionFilter) url += `&action=${actionFilter}`;
      const res = await api.get(url);
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span>Immutable Platform Audit Logs</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Cryptographically accounted analyst actions, login attempts, rule updates, and containment authorizations
          </p>
        </div>
        <button
          onClick={fetchLogs}
          className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Audit</span>
        </button>
      </div>

      {/* Filter toolbar */}
      <div className="flex items-center gap-2 bg-[#111827] border border-[#1f293d] p-4 rounded-xl shadow-lg">
        <span className="text-xs font-mono text-slate-400">Action Type:</span>
        {['', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'INCIDENT_CREATED', 'RESPONSE_ACTION_APPROVED', 'RULE_UPDATED'].map((act) => (
          <button
            key={act}
            onClick={() => setActionFilter(act)}
            className={`px-3 py-1 rounded text-xs font-mono font-medium transition ${
              actionFilter === act
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'bg-[#162032] text-slate-400 hover:text-slate-200 border border-[#223049]'
            }`}
          >
            {act ? act.replace(/_/g, ' ') : 'ALL'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Timestamp (UTC)</th>
              <th className="py-3 px-4">User</th>
              <th className="py-3 px-4">Action Event</th>
              <th className="py-3 px-4">Target Resource</th>
              <th className="py-3 px-4">Client IP</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-[#141d2d] transition">
                <td className="py-3 px-4 text-slate-400">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="py-3 px-4 font-bold text-cyan-400">
                  @{log.username}
                </td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded bg-[#162032] border border-[#223049] text-slate-200 font-bold">
                    {log.action}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-300">
                  {log.target_type ? `${log.target_type} #${log.target_id || ''}` : 'SYSTEM'}
                </td>
                <td className="py-3 px-4 text-slate-400">{log.ip_address || '127.0.0.1'}</td>
                <td className="py-3 px-4 text-right">
                  {log.details ? (
                    <button
                      onClick={() => setSelectedLog(log)}
                      className="px-2.5 py-1 rounded bg-[#162032] border border-[#233149] text-slate-300 hover:text-cyan-400 text-[11px]"
                    >
                      Inspect
                    </button>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Details Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-md w-full p-6 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#1f293d] mb-4">
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Audit Details: {selectedLog.action}</span>
              </h2>
              <button onClick={() => setSelectedLog(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <pre className="p-4 bg-[#090d16] border border-[#1b2538] rounded-lg text-slate-300 overflow-x-auto text-[11px]">
              {JSON.stringify(selectedLog.details, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;
