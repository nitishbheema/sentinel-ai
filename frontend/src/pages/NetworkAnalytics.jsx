import React, { useState, useEffect } from 'react';
import { Network, Activity, Globe, Shield, RefreshCw } from 'lucide-react';
import { Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';
import api from '../services/api';
import StatCard from '../components/StatCard';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

const NetworkAnalytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchNetwork = async () => {
    try {
      const res = await api.get('/analytics/network');
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNetwork();
  }, []);

  const topPortsData = {
    labels: data?.top_dest_ports?.map((p) => `Port ${p.port}`) || ['Port 443', 'Port 80', 'Port 22', 'Port 53', 'Port 8080'],
    datasets: [
      {
        label: 'Flow Count',
        data: data?.top_dest_ports?.map((p) => p.count) || [45, 32, 18, 12, 8],
        backgroundColor: '#06b6d4',
        borderRadius: 6,
      },
    ],
  };

  const topIpsData = {
    labels: data?.top_source_ips?.map((i) => i.ip) || ['192.168.1.105', '203.0.113.88', '198.51.100.45'],
    datasets: [
      {
        label: 'Inbound Packets',
        data: data?.top_source_ips?.map((i) => i.count) || [42, 28, 25],
        backgroundColor: '#8b5cf6',
        borderRadius: 6,
      },
    ],
  };

  const protocolData = {
    labels: Object.keys(data?.protocols_breakdown || { TCP: 140, UDP: 35, ICMP: 6, DNS: 22 }),
    datasets: [
      {
        data: Object.values(data?.protocols_breakdown || { TCP: 140, UDP: 35, ICMP: 6, DNS: 22 }),
        backgroundColor: ['#06b6d4', '#3b82f6', '#f59e0b', '#10b981'],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            <span>Network Traffic & Sensor Telemetry Analytics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Protocol breakdowns, high-frequency ports, bandwidth metrics, and perimeter talkers
          </p>
        </div>
        <button
          onClick={fetchNetwork}
          className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Monitored Flows"
          value={data?.total_connections ?? '...'}
          icon={Activity}
          change="Real-time"
          trend="up"
          color="cyan"
        />
        <StatCard
          title="Inbound Volume"
          value={`${data?.bandwidth_usage?.inbound_mb || 428.5} MB`}
          icon={Globe}
          color="blue"
        />
        <StatCard
          title="Outbound Volume"
          value={`${data?.bandwidth_usage?.outbound_mb || 112.3} MB`}
          icon={Globe}
          color="purple"
        />
        <StatCard
          title="Peak Throughput"
          value={`${data?.bandwidth_usage?.peak_mbps || 18.4} Mbps`}
          icon={Shield}
          color="emerald"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4">
            Targeted Destination Ports
          </h2>
          <div className="h-60">
            <Bar
              data={topPortsData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { grid: { color: '#1a2333' }, ticks: { color: '#64748b', font: { size: 10 } } },
                  y: { grid: { color: '#1a2333' }, ticks: { color: '#64748b' } },
                },
              }}
            />
          </div>
        </div>

        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4">
            Top Perimeter Talkers (Source IPs)
          </h2>
          <div className="h-60">
            <Bar
              data={topIpsData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { grid: { color: '#1a2333' }, ticks: { color: '#64748b', font: { size: 10 } } },
                  y: { grid: { color: '#1a2333' }, ticks: { color: '#64748b' } },
                },
              }}
            />
          </div>
        </div>

        <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4">
            Protocol Breakdown
          </h2>
          <div className="h-60 flex items-center justify-center">
            <Pie
              data={protocolData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } } },
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkAnalytics;
