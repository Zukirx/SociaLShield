import React from 'react';

const RiskBadge = ({ assessment, explanation }) => {
  if (!assessment) return null;

  const { tier, risk_score } = assessment;
  
  const colors = {
    Low: 'bg-green-500/20 text-green-400 border-green-500/50',
    Medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    High: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    Critical: 'bg-red-500/20 text-red-400 border-red-500/50',
  };

  return (
    <div className={`p-6 rounded-xl border-2 backdrop-blur-md transition-all ${colors[tier] || colors.Low}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold tracking-tight">Risk Assessment: {tier}</h2>
        <div className="text-xl font-mono px-3 py-1 bg-white/50 rounded-lg text-black/70 border border-black/10">
          {(risk_score * 100).toFixed(1)}%
        </div>
      </div>
      <p className="text-lg mb-4 text-[#5c4033]">{explanation.summary}</p>
      <div className="p-4 bg-white/60 rounded-lg border border-[#8b4513]/20">
        <strong className="block text-sm uppercase tracking-wider mb-1 text-[#8b4513]">Recommended Action</strong>
        <span className="text-[#5c4033] font-medium">{explanation.recommended_action}</span>
      </div>
    </div>
  );
};

export default RiskBadge;
