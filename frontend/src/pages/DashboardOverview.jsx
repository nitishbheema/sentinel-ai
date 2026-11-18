import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  AlertTriangle,
  Radio,
  Flame,
  CheckCircle,
  Cpu,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  Brain
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import api from '../services/api';
import StatCard from '../components/StatCard';
import RiskBadge from '../components/RiskBadge';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const DashboardOverview = () => {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [sumRes, alertRes, incRes] = await Promise.all([
        api.get('/analytics/overview'),
        api.get('/alerts?limit=5'),
        api.get('/incidents?limit=5')
      ]);
      setSummary(sumRes.data);
      setAlerts(alertRes.data);
      setIncidents(incRes.data);
    } catch (e) {
      console.error('Error fetching dashboard summary:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const lineChartData = {
    labels: summary?.recent_events_trend?.map((t) => t.timestamp) || ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', 'Now'],
    datasets: [
      {
        label: 'Security Events',
        data: summary?.recent_events_trend?.map((t) => t.events) || [12, 19, 14, 25, 22, 30, 28],
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Threat Alerts',
        data: summary?.recent_events_trend?.map((t) => t.alerts) || [2, 4, 1, 5, 3, 6, 4],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#94a3b8', font: { size: 11 } },
      },
    },
    scales: {
      x: { grid: { color: '#1a2333' }, ticks: { color: '#64748b' } },
      y: { grid: { color: '#1a2333' }, ticks: { color: '#64748b' } },
    },
  };

  const doughnutData = {
    labels: ['Rule Engine', 'ML Intrusion', 'Threat Intel', 'Correlation'],
    datasets: [
      {
        data: [
          summary?.threat_distribution?.RULE || 18,
          summary?.threat_distribution?.ML || 12,
          summary?.threat_distribution?.THREAT_INTEL || 8,
          summary?.threat_distribution?.CORRELATION || 5,
        ],
        backgroundColor: ['#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444'],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <span>SOC Command Center</span>
            <span className="text-xs py-0.5 px-2 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono">
              REAL-TIME
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Autonomous threat correlation, machine learning intrusion classification, and defensive triage
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Telemetry</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Events"
          value={summary?.total_events ?? '...'}
          icon={Radio}
          change="+18% /hr"
          trend="up"
          color="cyan"
        />
        <StatCard
          title="Total Alerts"
          value={summary?.total_alerts ?? '...'}
          icon={AlertTriangle}
          change="+4 new"
          trend="up"
          color="orange"
        />
        <StatCard
          title="Critical Alerts"
          value={summary?.critical_alerts ?? '...'}
          icon={Flame}
          trend="up"
          color="red"
        />
        <StatCard
          title="Active Incidents"
          value={summary?.active_incidents ?? '...'}
          icon={ShieldAlert}
          color="purple"
        />
        <StatCard
          title="Resolved"
          value={summary?.resolved_incidents ?? '...'}
          icon={CheckCircle}
          color="emerald"
        />
        <StatCard
          title="Endpoints"
          value={summary?.monitored_endpoints ?? '...'}
          icon={Cpu}
          color="blue"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Security Telemetry Trend
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Ingested network flows & correlated alert volumes
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400">Sliding Window (6h)</span>
          </div>
          <div className="h-64">
            <Line data={lineChartData} options={chartOptions} />
          </div>
        </div>

        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Detection Sources
              </h2>
              <Brain className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="h-48 relative flex items-center justify-center">
              <Doughnut
                data={doughnutData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 12 } } },
                }}
              />
            </div>
          </div>
          <div className="pt-3 border-t border-[#1a2333] text-center">
            <span className="text-xs font-mono text-slate-400">
              ML Health: <strong className="text-emerald-400">{summary?.ml_health_status || 'OPTIMAL'}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Tables: Latest Alerts & Active Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts table */}
        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              <span>Latest Security Alerts</span>
            </h2>
            <Link to="/alerts" className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-mono">
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-[#1a2333] overflow-hidden">
            {alerts.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center font-mono">No active alerts recorded</p>
            ) : (
              alerts.map((al) => (
                <div key={al.id} className="py-3 flex items-start justify-between gap-4 hover:bg-[#141c2c] px-2 rounded-lg transition">
                  <div>
                    <p className="text-xs font-semibold text-slate-200 line-clamp-1">{al.title}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{al.description}</p>
                    <div className="flex items-center gap-2 mt-1.5 font-mono text-[10px] text-slate-500">
                      <span>Source: <strong className="text-slate-400">{al.source}</strong></span>
                      {al.mitre_technique && (
                        <span>• MITRE: <strong className="text-cyan-400">{al.mitre_technique}</strong></span>
                      )}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <RiskBadge severity={al.severity} score={al.risk_score} />
                    <p className="text-[10px] text-slate-500 font-mono mt-1">
                      {new Date(al.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Incidents table */}
        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <span>Active Incident Queue</span>
            </h2>
            <Link to="/incidents" className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-mono">
              <span>Manage Incidents</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-[#1a2333]">
            {incidents.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center font-mono">No open incidents in queue</p>
            ) : (
              incidents.map((inc) => (
                <Link
                  key={inc.id}
                  to={`/incidents/${inc.id}`}
                  className="py-3 flex items-start justify-between gap-4 hover:bg-[#141c2c] px-2 rounded-lg transition block"
                >
                  <div>
                    <p className="text-xs font-semibold text-slate-200 line-clamp-1">{inc.title}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{inc.description}</p>
                    <div className="flex items-center gap-2 mt-1.5 font-mono text-[10px] text-slate-500">
                      <span>Status: <strong className="text-cyan-400">{inc.status}</strong></span>
                      <span>• Analyst: <strong className="text-slate-300">{inc.assigned_to_username || 'Unassigned'}</strong></span>
                      <span>• Events: <strong className="text-slate-300">{inc.events_count}</strong></span>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <RiskBadge severity={inc.severity} score={inc.risk_score} />
                    <p className="text-[10px] text-cyan-400 hover:underline font-mono mt-1">
                      Investigate →
                    </p>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
