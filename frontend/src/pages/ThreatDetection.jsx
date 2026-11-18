import React, { useState, useEffect } from 'react';
import { Flame, Shield, Target, Crosshair, Cpu, AlertTriangle } from 'lucide-react';
import api from '../services/api';

const ThreatDetection = () => {
  const [threatData, setThreatData] = useState(null);

  useEffect(() => {
    const fetchThreats = async () => {
      try {
        const res = await api.get('/analytics/threats');
        setThreatData(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchThreats();
  }, []);

  const mitreTactics = [
    { id: 'TA0043', name: 'Reconnaissance', count: 22, techniques: ['T1046 - Port Scan', 'T1595 - Active Scanning'] },
    { id: 'TA0001', name: 'Initial Access', count: 14, techniques: ['T1078 - Valid Accounts', 'T1190 - Exploit Public-Facing App'] },
    { id: 'TA0002', name: 'Execution', count: 9, techniques: ['T1059 - Command & Scripting', 'T1204 - User Execution'] },
    { id: 'TA0006', name: 'Credential Access', count: 18, techniques: ['T1110.001 - Password Guessing', 'T1003 - OS Credential Dumping'] },
    { id: 'TA0011', name: 'Command & Control', count: 11, techniques: ['T1071.004 - DNS Beaconing', 'T1571 - Non-Standard Port'] },
    { id: 'TA0010', name: 'Exfiltration', count: 4, techniques: ['T1048 - Exfil Over Alt Protocol'] },
    { id: 'TA0040', name: 'Impact', count: 7, techniques: ['T1499 - Endpoint DoS'] },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Flame className="w-5 h-5 text-red-400" />
            <span>Threat Detection & MITRE ATT&CK Matrix</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Mapping automated heuristic detections, rule alerts, and ML models against adversary tradecraft
          </p>
        </div>
      </div>

      {/* Cyber Kill Chain Visualizer */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
          <Target className="w-4 h-4 text-cyan-400" />
          <span>Unified Cyber Kill-Chain Coverage</span>
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {[
            { stage: 'Reconnaissance', coverage: 95, alerts: 22, color: 'border-cyan-500/40 text-cyan-400' },
            { stage: 'Weaponization', coverage: 70, alerts: 6, color: 'border-blue-500/40 text-blue-400' },
            { stage: 'Delivery', coverage: 85, alerts: 14, color: 'border-yellow-500/40 text-yellow-400' },
            { stage: 'Exploitation', coverage: 90, alerts: 11, color: 'border-orange-500/40 text-orange-400' },
            { stage: 'Installation', coverage: 80, alerts: 8, color: 'border-purple-500/40 text-purple-400' },
            { stage: 'C2 Beaconing', coverage: 92, alerts: 12, color: 'border-red-500/40 text-red-400' },
            { stage: 'Action/Exfil', coverage: 88, alerts: 4, color: 'border-rose-500/40 text-rose-400' },
          ].map((item, idx) => (
            <div key={idx} className={`bg-[#141d2d] border ${item.color} rounded-lg p-3 text-center flex flex-col justify-between`}>
              <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">Phase {idx + 1}</span>
              <p className="text-xs font-bold text-slate-200 mt-1">{item.stage}</p>
              <div className="mt-3">
                <span className="text-lg font-black text-slate-100">{item.alerts}</span>
                <p className="text-[10px] font-mono text-slate-400">Hits ({item.coverage}%)</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* MITRE ATT&CK Matrix Grid */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
          <Crosshair className="w-4 h-4 text-orange-400" />
          <span>MITRE ATT&CK Enterprise Matrix (Observed Tactics)</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {mitreTactics.map((tac) => (
            <div key={tac.id} className="bg-[#141c2c] border border-[#1f293d] rounded-lg p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-cyan-400">{tac.id}</span>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/30">
                    {tac.count} Detections
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-200 mt-2">{tac.name}</h3>
                <div className="mt-3 space-y-1.5">
                  {tac.techniques.map((tech, i) => (
                    <div key={i} className="text-xs font-mono p-1.5 rounded bg-[#101726] text-slate-300 border border-[#1b2538]">
                      {tech}
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-[#1a2333] flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Rule + ML Mapped</span>
                <span className="text-emerald-400">Active</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ThreatDetection;
