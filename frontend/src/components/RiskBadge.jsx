import React from 'react';

const RiskBadge = ({ severity, score }) => {
  const sev = (severity || 'LOW').toUpperCase();

  const getColors = () => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      case 'MEDIUM':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'LOW':
      default:
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40';
    }
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getColors()}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {sev}
      {score !== undefined && <span className="opacity-75">({score})</span>}
    </span>
  );
};

export default RiskBadge;
