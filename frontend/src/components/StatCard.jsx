import React from 'react';

const StatCard = ({ title, value, icon: Icon, change, trend = 'up', color = 'cyan' }) => {
  const colorMap = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    red: 'text-red-400 bg-red-500/10 border-red-500/20',
    orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  };

  const selectedColor = colorMap[color] || colorMap.cyan;

  return (
    <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-5 shadow-lg relative overflow-hidden transition-all duration-200 hover:border-[#2e3e5c]">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
          <h3 className="text-2xl font-bold text-slate-100 mt-1">{value}</h3>
          {change && (
            <p className={`text-xs mt-1.5 flex items-center gap-1 ${trend === 'up' ? 'text-red-400' : 'text-emerald-400'}`}>
              <span>{trend === 'up' ? '↑' : '↓'}</span>
              <span>{change}</span>
            </p>
          )}
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg border ${selectedColor}`}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#2e3e5c] to-transparent" />
    </div>
  );
};

export default StatCard;
