import React, { useState, useEffect } from 'react';
import { Cpu, Server, ShieldCheck, Lock, Activity, RefreshCw } from 'lucide-react';
import api from '../services/api';
import StatCard from '../components/StatCard';

const EndpointMonitoring = () => {
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEndpoints = async () => {
    try {
      const res = await api.get('/endpoints');
      setEndpoints(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEndpoints();
  }, []);

  const isolatedCount = endpoints.filter((e) => e.isolation_status).length;
  const activeCount = endpoints.filter((e) => e.status === 'ACTIVE').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span>Endpoint Monitoring & Agent Fleet</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Autonomous health, telemetry heartbeat, and network quarantine status of deployed sensor agents
          </p>
        </div>
        <button
          onClick={fetchEndpoints}
          className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Fleet</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Agents"
          value={endpoints.length}
          icon={Server}
          color="cyan"
        />
        <StatCard
          title="Active & Healthy"
          value={activeCount}
          icon={ShieldCheck}
          color="emerald"
        />
        <StatCard
          title="Isolated Hosts"
          value={isolatedCount}
          icon={Lock}
          color={isolatedCount > 0 ? 'red' : 'blue'}
        />
        <StatCard
          title="Agent Protocol"
          value="v1.0.0"
          icon={Activity}
          color="purple"
        />
      </div>

      {/* Fleet Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">Hostname</th>
              <th className="py-3 px-4">IP Address</th>
              <th className="py-3 px-4">Operating System</th>
              <th className="py-3 px-4">Fleet Status</th>
              <th className="py-3 px-4">Network Quarantine</th>
              <th className="py-3 px-4">Agent Version</th>
              <th className="py-3 px-4 text-right">Heartbeat</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {endpoints.map((ep) => (
              <tr key={ep.id} className="hover:bg-[#141d2d] transition">
                <td className="py-3 px-4 font-bold text-slate-100 flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${ep.isolation_status ? 'bg-red-400' : 'bg-emerald-400'}`} />
                  <span>{ep.hostname}</span>
                </td>
                <td className="py-3 px-4 text-cyan-400">{ep.ip_address}</td>
                <td className="py-3 px-4 text-slate-300">{ep.os_version || ep.os_type}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    ep.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                    ep.status === 'ISOLATED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                    'bg-slate-700/30 text-slate-400'
                  }`}>
                    {ep.status}
                  </span>
                </td>
                <td className="py-3 px-4">
                  {ep.isolation_status ? (
                    <span className="text-red-400 font-bold flex items-center gap-1">
                      <Lock className="w-3.5 h-3.5" />
                      <span>ISOLATED (DROP ALL)</span>
                    </span>
                  ) : (
                    <span className="text-emerald-400 font-medium">Standard Route</span>
                  )}
                </td>
                <td className="py-3 px-4 text-slate-400">{ep.agent_version}</td>
                <td className="py-3 px-4 text-right text-slate-400">
                  {new Date(ep.last_seen).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EndpointMonitoring;
