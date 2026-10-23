import React, { useState } from 'react';

const SpreadForecast = ({ diffusion, diffusion_risk }) => {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'cascade' | 'timeline'

  // Normalize data: support both new rich diffusion dict or legacy float
  const isRich = typeof diffusion === 'object' && diffusion !== null;
  const score = isRich ? (diffusion.score ?? 0.5) : (typeof diffusion_risk === 'number' ? diffusion_risk : 0.5);
  const localRisk = isRich ? (diffusion.local_news_risk ?? score) : score;
  const mainRisk = isRich ? (diffusion.mainstream_news_risk ?? (score * 0.6)) : (score * 0.6);
  const smallVsBig = isRich && diffusion.small_vs_big_ratio ? diffusion.small_vs_big_ratio : (localRisk / Math.max(0.05, mainRisk)).toFixed(1);

  const localTier = isRich ? (diffusion.local_news_tier || 'Moderate Local Spread') : (localRisk > 0.6 ? 'Critical Local Outbreak' : 'Moderate Local Spread');
  const mainTier = isRich ? (diffusion.mainstream_news_tier || 'Filtered by National Desks') : (mainRisk > 0.5 ? 'National Wire Scrutiny' : 'Filtered by National Desks');
  const primaryRegion = isRich && diffusion.primary_region ? diffusion.primary_region : 'National / Regional';

  const vulnerableChannels = isRich && diffusion.vulnerable_channels && diffusion.vulnerable_channels.length > 0
    ? diffusion.vulnerable_channels
    : [
        'Hyper-local WhatsApp & Telegram Forwarding Clusters (Family & RWA loops)',
        'District Vernacular News Portals & City Blogs (Low fact-check buffers)',
        'Local Community Facebook Groups & Citizen Grievance Pages',
        'Regional Cable TV & Vernacular YouTube Stringers'
      ];

  const cascadeStages = isRich && diffusion.cascade_stages && diffusion.cascade_stages.length > 0
    ? diffusion.cascade_stages
    : [
        { stage: 'Social Media Origin', level: Math.round(score * 100), status: 'Active Seeding', description: 'Initial post reshares and algorithmic recommendation.' },
        { stage: 'WhatsApp & Dark Social', level: Math.round(localRisk * 95), status: 'High Amplification', description: 'Forwarding across family loops and neighborhood chats.' },
        { stage: 'Small Local News Portals', level: Math.round(localRisk * 85), status: 'Imminent Pickup', description: 'District digital blogs and local stringers.' },
        { stage: 'Mainstream TV & National Press', level: Math.round(mainRisk * 75), status: 'Under Editorial Filter', description: 'National prime time and wire fact-checking.' },
      ];

  const timelineForecast = isRich && diffusion.timeline_forecast && diffusion.timeline_forecast.length > 0
    ? diffusion.timeline_forecast
    : [
        { window: '0 – 2 Hours', stage: 'Social Echo Chamber', channels: 'Instagram / X / Facebook feeds', reach: 'Peer Network' },
        { window: '2 – 6 Hours', stage: 'Dark Social Forwarding', channels: 'WhatsApp status & RWA groups', reach: 'District Level' },
        { window: '6 – 12 Hours', stage: 'Local News Uptake', channels: 'District portals & city blogs', reach: 'Multi-District' },
        { window: '12 – 24+ Hours', stage: 'Regional Press / TV', channels: 'Local cable TV & state print dailies', reach: 'State / National' },
      ];

  const keyTriggers = isRich && diffusion.key_triggers ? diffusion.key_triggers : [];
  const containmentAdvisory = isRich && diffusion.containment_advisory ? diffusion.containment_advisory : 'Issue proactive factual notice through district communication desks to prevent rumor amplification in neighborhood chats.';

  const localPct = Math.round(localRisk * 100);
  const mainPct = Math.round(mainRisk * 100);

  // Local risk coloring
  const getLocalRiskStyle = (pct) => {
    if (pct >= 70) return { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-700', bar: 'bg-red-500', badge: 'bg-red-100 text-red-800' };
    if (pct >= 45) return { bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-700', bar: 'bg-amber-500', badge: 'bg-amber-100 text-amber-800' };
    return { bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-700', bar: 'bg-emerald-500', badge: 'bg-emerald-100 text-emerald-800' };
  };

  const getMainRiskStyle = (pct) => {
    if (pct >= 70) return { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', bar: 'bg-orange-500', badge: 'bg-orange-100 text-orange-800' };
    if (pct >= 40) return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', bar: 'bg-blue-500', badge: 'bg-blue-100 text-blue-800' };
    return { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-600', bar: 'bg-slate-400', badge: 'bg-slate-100 text-slate-700' };
  };

  const localStyle = getLocalRiskStyle(localPct);
  const mainStyle = getMainRiskStyle(mainPct);

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-[#d2b48c] overflow-hidden">
      {/* Component Header */}
      <div className="p-6 pb-4 border-b border-[#f0e4d0]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xl">📡</span>
              <h3 className="text-xl font-bold text-[#8b4513]">Spread & Spillover Forecast</h3>
              <span className="text-xs bg-[#faf5ed] text-[#8b4513] border border-[#d2b48c] px-2.5 py-0.5 rounded-full font-semibold">
                Dual-Tier Engine
              </span>
            </div>
            <p className="text-xs text-[#8b6540] mt-1">
              Predicting virality across <span className="font-semibold text-[#5c4033]">Small Local News & Dark Social</span> vs <span className="font-semibold text-[#5c4033]">Mainstream National Channels</span>
            </p>
          </div>
          {primaryRegion && (
            <span className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-1 rounded-lg font-medium whitespace-nowrap">
              📍 {primaryRegion}
            </span>
          )}
        </div>

        {/* Tab switcher */}
        <div className="flex gap-2 mt-4 pt-2 border-t border-[#f5ede0]">
          <button
            onClick={() => setActiveTab('overview')}
            className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activeTab === 'overview'
                ? 'bg-[#8b4513] text-white shadow-sm'
                : 'text-[#8b6540] hover:bg-[#faf5ed]'
            }`}
          >
            📊 Small vs Big News
          </button>
          <button
            onClick={() => setActiveTab('cascade')}
            className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activeTab === 'cascade'
                ? 'bg-[#8b4513] text-white shadow-sm'
                : 'text-[#8b6540] hover:bg-[#faf5ed]'
            }`}
          >
            🌊 Cascade Stages
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activeTab === 'timeline'
                ? 'bg-[#8b4513] text-white shadow-sm'
                : 'text-[#8b6540] hover:bg-[#faf5ed]'
            }`}
          >
            ⏱ 24h Timeline
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <>
            {/* Dual Spillover Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Small & Local News Card */}
              <div className={`p-4 rounded-xl border ${localStyle.border} ${localStyle.bg} relative overflow-hidden transition-all shadow-sm`}>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-base">🏘</span>
                    <span className="text-xs font-bold uppercase tracking-wider text-[#5c4033]">
                      Small & Local News
                    </span>
                  </div>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${localStyle.badge}`}>
                    {localTier}
                  </span>
                </div>

                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-xs text-[#8b6540]">Regional Spillover Risk</span>
                  <span className={`text-2xl font-mono font-extrabold ${localStyle.text}`}>
                    {localPct}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-white/80 rounded-full h-2.5 overflow-hidden mb-3 border border-black/5">
                  <div
                    className={`h-2.5 rounded-full ${localStyle.bar} transition-all duration-1000 ease-out`}
                    style={{ width: `${localPct}%` }}
                  />
                </div>

                <p className="text-[11px] text-[#5c4033] leading-relaxed">
                  <strong>High vulnerability factors:</strong> District WhatsApp loops, vernacular community portals, and citizen Facebook groups lack formal fact-checking desks and amplify local civic or panic news immediately.
                </p>
              </div>

              {/* Mainstream Big News Channels Card */}
              <div className={`p-4 rounded-xl border ${mainStyle.border} ${mainStyle.bg} relative overflow-hidden transition-all shadow-sm`}>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-base">📺</span>
                    <span className="text-xs font-bold uppercase tracking-wider text-[#5c4033]">
                      Big Mainstream News
                    </span>
                  </div>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${mainStyle.badge}`}>
                    {mainTier}
                  </span>
                </div>

                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-xs text-[#8b6540]">National Broadcast Exposure</span>
                  <span className={`text-2xl font-mono font-extrabold ${mainStyle.text}`}>
                    {mainPct}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-white/80 rounded-full h-2.5 overflow-hidden mb-3 border border-black/5">
                  <div
                    className={`h-2.5 rounded-full ${mainStyle.bar} transition-all duration-1000 ease-out`}
                    style={{ width: `${mainPct}%` }}
                  />
                </div>

                <p className="text-[11px] text-[#5c4033] leading-relaxed">
                  <strong>Editorial filtering:</strong> National TV newsrooms, PTI/ANI wire desks, and major dailies mandate verification before broadcast, slowing national media uptake.
                </p>
              </div>
            </div>

            {/* Spillover Ratio Callout */}
            {Number(smallVsBig) > 1.2 && (
              <div className="p-3.5 bg-amber-50/90 border border-amber-300 rounded-xl flex items-start gap-3">
                <span className="text-xl">⚠️</span>
                <div className="text-xs text-amber-900 leading-snug">
                  <strong className="font-bold text-amber-950">Local News Exposure Alert: </strong>
                  Small local newsrooms and neighborhood WhatsApp networks are{' '}
                  <span className="font-extrabold underline decoration-amber-500">{smallVsBig}x more likely</span> to amplify this claim than national news channels due to proximity urgency and absence of local verification buffers.
                </div>
              </div>
            )}

            {/* Vulnerable Hyperlocal Channels */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#8b4513] mb-2.5 flex items-center gap-1.5">
                <span>🎯</span>
                <span>Hyperlocal Channels Most Vulnerable to Uptake</span>
              </h4>
              <div className="space-y-1.5">
                {vulnerableChannels.map((channel, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 p-2.5 rounded-lg bg-[#faf5ed] border border-[#e8d5b7] text-xs text-[#5c4033]"
                  >
                    <span className="text-amber-700 font-bold">⚡</span>
                    <span className="font-medium">{channel}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Key Triggers Detected */}
            {keyTriggers.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#8b4513] mb-2 flex items-center gap-1.5">
                  <span>🔍</span>
                  <span>Spread Acceleration Triggers Detected</span>
                </h4>
                <div className="flex flex-wrap gap-2">
                  {keyTriggers.map((trig, idx) => (
                    <span
                      key={idx}
                      className="text-[11px] px-2.5 py-1 bg-[#faf5ed] text-[#8b4513] border border-[#d2b48c] rounded-md font-medium"
                    >
                      • {trig}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Containment Advisory */}
            <div className="p-3.5 bg-indigo-50/80 border border-indigo-200 rounded-xl">
              <div className="flex items-center gap-2 text-indigo-900 font-bold text-xs mb-1">
                <span>🛡️</span>
                <span>Recommended Local Media Containment</span>
              </div>
              <p className="text-xs text-indigo-800 leading-relaxed">
                {containmentAdvisory}
              </p>
            </div>
          </>
        )}

        {/* CASCADE STAGES TAB */}
        {activeTab === 'cascade' && (
          <div className="space-y-4">
            <p className="text-xs text-[#8b6540]">
              Simulated propagation cascade across 4 diffusion layers, from social seeding to small news uptake and national scrutiny:
            </p>

            <div className="space-y-3">
              {cascadeStages.map((stage, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-[#faf5ed] border border-[#e8d5b7]">
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-bold text-xs text-[#5c4033] flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-[#8b4513] text-white flex items-center justify-center text-[10px]">
                        {idx + 1}
                      </span>
                      <span>{stage.stage}</span>
                    </span>
                    <span className="text-xs font-mono font-bold text-[#8b4513]">
                      {stage.level}%
                    </span>
                  </div>

                  {/* Level bar */}
                  <div className="w-full bg-[#e8d5b7] rounded-full h-2 overflow-hidden mb-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-1000 ${
                        idx <= 1 ? 'bg-[#8b4513]' : idx === 2 ? 'bg-amber-600' : 'bg-slate-500'
                      }`}
                      style={{ width: `${stage.level}%` }}
                    />
                  </div>

                  <div className="flex items-start justify-between gap-2 text-[11px]">
                    <span className="text-[#8b6540]">{stage.description}</span>
                    <span className="font-semibold text-[#8b4513] whitespace-nowrap bg-white px-2 py-0.5 rounded border border-[#d2b48c] text-[10px]">
                      {stage.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TIMELINE TAB */}
        {activeTab === 'timeline' && (
          <div className="space-y-4">
            <p className="text-xs text-[#8b6540]">
              Projected time window of dissemination before intervention or official fact-checks reach local newsrooms:
            </p>

            <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#d2b48c]">
              {timelineForecast.map((step, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-[#8b4513] border-2 border-white" />
                  <div className="p-3 bg-[#faf5ed] border border-[#e8d5b7] rounded-lg">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-bold text-[#8b4513]">{step.window}</span>
                      <span className="text-[10px] font-semibold bg-white border border-[#d2b48c] text-[#5c4033] px-2 py-0.5 rounded-full">
                        Reach: {step.reach}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-[#5c4033]">{step.stage}</div>
                    <div className="text-[11px] text-[#8b6540] mt-0.5">Primary Channels: {step.channels}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SpreadForecast;
