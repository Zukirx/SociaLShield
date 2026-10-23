import React, { useState } from 'react';

const SourceBreakdown = ({ verification }) => {
  if (!verification || !verification.analyzed_sources) return null;

  const [filterType, setFilterType] = useState('ALL');

  const stanceStyle = (stance) => {
    switch (stance) {
      case 'SUPPORTS': return 'bg-emerald-100 text-emerald-800 border border-emerald-300';
      case 'REFUTES': return 'bg-rose-100 text-rose-800 border border-rose-300';
      default: return 'bg-slate-100 text-slate-700 border border-slate-300';
    }
  };

  const stanceIcon = (stance) => {
    switch (stance) {
      case 'SUPPORTS': return '✓';
      case 'REFUTES': return '✗';
      default: return '~';
    }
  };

  const sourceTypeBadge = (type) => {
    switch (type) {
      case 'Fact-Checking Agency':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'Regional / Local Press':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'National / Global Outlet':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const sources = verification.analyzed_sources;

  const regionalCount = sources.filter(s => s.source_type === 'Regional / Local Press').length;
  const nationalCount = sources.filter(s => s.source_type === 'National / Global Outlet').length;
  const factCheckCount = sources.filter(s => s.source_type === 'Fact-Checking Agency').length;

  const filteredSources = filterType === 'ALL'
    ? sources
    : sources.filter(s => s.source_type === filterType);

  return (
    <div className="p-6 bg-white rounded-2xl shadow-xl border border-[#d2b48c]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[#f0e4d0]">
        <div>
          <h3 className="text-xl font-bold text-[#8b4513] flex items-center gap-2">
            <span>🔎 Corroboration & Fact-Checking Sources</span>
            <span className="text-xs bg-[#faf5ed] text-[#8b4513] border border-[#d2b48c] px-2 py-0.5 rounded-full font-semibold">
              {sources.length} Total
            </span>
          </h3>
          <p className="text-xs text-[#8b6540] mt-0.5">
            Cross-referenced against verified national newsrooms, regional vernacular press, and certified fact-checkers
          </p>
        </div>

        {/* Source distribution pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setFilterType('ALL')}
            className={`text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all cursor-pointer ${
              filterType === 'ALL' ? 'bg-[#8b4513] text-white' : 'bg-[#faf5ed] text-[#5c4033] border border-[#d2b48c]'
            }`}
          >
            All ({sources.length})
          </button>
          {factCheckCount > 0 && (
            <button
              onClick={() => setFilterType('Fact-Checking Agency')}
              className={`text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                filterType === 'Fact-Checking Agency' ? 'bg-purple-700 text-white' : 'bg-purple-50 text-purple-800 border border-purple-200'
              }`}
            >
              Fact-Checkers ({factCheckCount})
            </button>
          )}
          {regionalCount > 0 && (
            <button
              onClick={() => setFilterType('Regional / Local Press')}
              className={`text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                filterType === 'Regional / Local Press' ? 'bg-amber-700 text-white' : 'bg-amber-50 text-amber-800 border border-amber-200'
              }`}
            >
              Regional/Local ({regionalCount})
            </button>
          )}
          {nationalCount > 0 && (
            <button
              onClick={() => setFilterType('National / Global Outlet')}
              className={`text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                filterType === 'National / Global Outlet' ? 'bg-blue-700 text-white' : 'bg-blue-50 text-blue-800 border border-blue-200'
              }`}
            >
              National ({nationalCount})
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3.5">
        {filteredSources.length === 0 && (
          <p className="text-[#8b6540] italic text-sm py-4 text-center">
            No sources found in this category.
          </p>
        )}
        {filteredSources.map((source, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl bg-[#faf5ed] border border-[#d2b48c] hover:border-[#8b4513] transition-colors"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <a
                  href={source.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-bold text-[#8b4513] hover:text-[#5c4033] hover:underline text-sm leading-snug line-clamp-2 block"
                >
                  {source.title || "Untitled Source"}
                </a>
                <div className="text-xs text-[#8b6540] mt-1.5 flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-[#5c4033]">📰 {source.source}</span>
                  {source.source_type && (
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${sourceTypeBadge(source.source_type)}`}>
                      {source.source_type}
                    </span>
                  )}
                  {source.category && (
                    <span className="bg-[#e8d5b7] text-[#5c4033] px-1.5 py-0.5 rounded text-[10px] font-semibold">
                      {source.category}
                    </span>
                  )}
                  {source.credibility_weight >= 1.0 && (
                    <span className="text-emerald-700 font-semibold text-[11px] flex items-center gap-0.5">
                      ✓ Verified Outlet
                    </span>
                  )}
                </div>
              </div>
              <span className={`px-2.5 py-1 text-xs font-bold rounded-full whitespace-nowrap flex-shrink-0 flex items-center gap-1 ${stanceStyle(source.stance)}`}>
                <span>{stanceIcon(source.stance)}</span>
                <span>{source.stance}</span>
              </span>
            </div>
            <p className="text-xs text-[#5c4033] line-clamp-3 leading-relaxed mt-2 bg-white/60 p-2.5 rounded-lg border border-[#e8d5b7]">
              {source.snippet}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourceBreakdown;
