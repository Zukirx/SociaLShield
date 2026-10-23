import React from 'react';

const RiskBadge = ({ assessment, explanation, verdict: propVerdict, verdict_label, verdict_description }) => {
  if (!assessment) return null;

  const { tier, risk_score } = assessment;
  const verdict = propVerdict || explanation?.verdict || (tier === 'Critical' ? 'FAKE' : tier === 'High' ? 'MISLEADING' : 'UNVERIFIED');

  // Verdict banner styling
  const verdictConfigs = {
    FAKE: {
      bg: 'bg-red-600',
      border: 'border-red-700',
      badge: 'bg-red-800 text-white',
      cardBg: 'bg-gradient-to-br from-red-50 to-orange-50/70 border-red-300',
      title: '🚨 FAKE NEWS DETECTED',
      subtitle: verdict_description || 'This claim has been debunked as fabricated or viral misinformation.',
      accent: 'text-red-700',
      barColor: 'bg-red-600',
    },
    MISLEADING: {
      bg: 'bg-orange-500',
      border: 'border-orange-600',
      badge: 'bg-orange-700 text-white',
      cardBg: 'bg-gradient-to-br from-orange-50 to-amber-50/70 border-orange-300',
      title: '⚠️ MISLEADING CLAIM',
      subtitle: verdict_description || 'Contains unsupported assertions, misleading framing, or distorted facts.',
      accent: 'text-orange-700',
      barColor: 'bg-orange-500',
    },
    UNVERIFIED: {
      bg: 'bg-amber-500',
      border: 'border-amber-600',
      badge: 'bg-amber-700 text-white',
      cardBg: 'bg-gradient-to-br from-amber-50 to-yellow-50/70 border-amber-300',
      title: '⚠️ UNVERIFIED HOAX RISK',
      subtitle: verdict_description || 'Sensational claim with ZERO corroboration from any recognized news outlets.',
      accent: 'text-amber-700',
      barColor: 'bg-amber-500',
    },
    VERIFIED: {
      bg: 'bg-emerald-600',
      border: 'border-emerald-700',
      badge: 'bg-emerald-800 text-white',
      cardBg: 'bg-gradient-to-br from-emerald-50 to-teal-50/70 border-emerald-300',
      title: '✅ VERIFIED FACTUAL',
      subtitle: verdict_description || 'Corroborated by independent, high-credibility news organizations.',
      accent: 'text-emerald-700',
      barColor: 'bg-emerald-600',
    },
    DISPUTED: {
      bg: 'bg-amber-600',
      border: 'border-amber-700',
      badge: 'bg-amber-800 text-white',
      cardBg: 'bg-gradient-to-br from-amber-50 to-orange-50/70 border-amber-300',
      title: '🟡 DISPUTED CLAIM',
      subtitle: verdict_description || 'Conflicting reports found across multiple evaluated sources.',
      accent: 'text-amber-700',
      barColor: 'bg-amber-600',
    },
  };

  const currentCfg = verdictConfigs[verdict] || verdictConfigs.FAKE;

  return (
    <div className={`rounded-2xl border-2 shadow-md overflow-hidden transition-all ${currentCfg.cardBg}`}>
      {/* 🚨 Massive Verdict Header Banner */}
      <div className={`${currentCfg.bg} text-white px-6 py-4 flex flex-wrap items-center justify-between gap-3 shadow-inner`}>
        <div className="flex items-center gap-3">
          <div className="w-3.5 h-3.5 rounded-full bg-white animate-pulse" />
          <div>
            <h2 className="text-xl md:text-2xl font-black tracking-tight uppercase flex items-center gap-2">
              {verdict_label || currentCfg.title}
            </h2>
            <p className="text-xs md:text-sm text-white/90 font-medium">
              {currentCfg.subtitle}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-wider font-bold bg-black/25 px-3 py-1.5 rounded-lg border border-white/20">
            {tier} Risk Tier
          </span>
          <div className="text-xl font-mono font-black px-3.5 py-1 bg-white text-gray-900 rounded-lg shadow-sm">
            {(risk_score * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {/* Risk meter progress bar */}
        <div>
          <div className="flex justify-between items-center text-xs font-semibold text-[#8b4513] mb-1.5">
            <span>Misinformation & Spillover Risk Gauge</span>
            <span className="font-mono font-bold">{(risk_score * 100).toFixed(1)}% / 100%</span>
          </div>
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden shadow-inner">
            <div
              className={`h-full ${currentCfg.barColor} transition-all duration-700 ease-out`}
              style={{ width: `${Math.min(100, Math.max(5, risk_score * 100))}%` }}
            />
          </div>
        </div>

        {/* Narrative Analysis Summary */}
        <div className="bg-white/80 p-4 rounded-xl border border-[#d2b48c]/50">
          <strong className="block text-xs uppercase tracking-wider mb-1.5 text-[#8b4513] font-bold">
            Analysis Rationale & Intelligence Findings
          </strong>
          <p className="text-sm md:text-base text-[#4a2e18] leading-relaxed">
            {explanation?.summary || 'Verification completed against cross-source intelligence network.'}
          </p>
        </div>

        {/* Recommended Action */}
        <div className="p-4 bg-white/90 rounded-xl border border-red-200/80 shadow-sm">
          <strong className="block text-xs uppercase tracking-wider mb-1 text-red-800 font-bold flex items-center gap-1.5">
            <span>🛡️ Newsroom & Platform Containment Action</span>
          </strong>
          <span className="text-xs md:text-sm text-red-950 font-semibold leading-relaxed">
            {explanation?.recommended_action || 'Follow standard verification procedures.'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default RiskBadge;
