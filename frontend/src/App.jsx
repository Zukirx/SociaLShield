import React, { useState, useEffect } from 'react';
import RiskBadge from './components/RiskBadge';
import SourceBreakdown from './components/SourceBreakdown';
import AuthorProfile from './components/AuthorProfile';
import SpreadForecast from './components/SpreadForecast';

const API = 'http://localhost:8000';

const CATEGORIES = [
  { key: 'all', label: 'All News', icon: '🌐' },
  { key: 'Indian English', label: 'Indian English', icon: '🇮🇳' },
  { key: 'Hindi (हिन्दी)', label: 'Hindi (हिन्दी)', icon: '🇮🇳' },
  { key: 'Malayalam (മലയാളം)', label: 'Malayalam (മലയാളം)', icon: '🌴' },
  { key: 'Tamil (தமிழ்)', label: 'Tamil (தமிழ்)', icon: '🛕' },
  { key: 'Global', label: 'Global', icon: '🌍' },
];

const PLATFORMS = [
  { id: 'instagram', label: 'Instagram', icon: '📸', color: 'from-pink-500 to-purple-600', placeholder: 'Paste Instagram post / reel URL, caption, or neighborhood reel claim...' },
  { id: 'twitter', label: 'X (Twitter)', icon: '𝕏', color: 'from-slate-800 to-black', placeholder: 'Paste X / Twitter post URL (e.g. https://x.com/user/status/...) or tweet text...' },
  { id: 'facebook', label: 'Facebook', icon: '👥', color: 'from-blue-600 to-blue-800', placeholder: 'Paste Facebook post / community group URL or forwarded citizen post...' },
  { id: 'news', label: 'Web & News', icon: '🌐', color: 'from-[#8b4513] to-[#5c4033]', placeholder: 'Paste a news headline, web article URL, or general claim...' },
];

const PRESETS = [
  {
    title: '📸 Local Water Panic (Instagram)',
    platform: 'instagram',
    author: '@city_residents_network',
    text: 'URGENT WARNING! Toxic chemical water supply contamination confirmed at district civil hospital ward 4. 8 critical, municipality ordering total water cut across town wards. Do NOT drink tap water!',
    likes: 4200,
    shares: 1100,
    views: 65000,
    comments: 320,
    followers: 24000,
    verified: false,
  },
  {
    title: '👥 Child-Lifter Hoax (Facebook)',
    platform: 'facebook',
    author: 'District Citizens Alert Forum',
    text: 'ALERT TO ALL PARENTS: Gang of 5 child kidnappers disguised as municipal survey workers caught roaming near town primary school. Police station has sounded emergency siren. Forward to every local group immediately!',
    likes: 1850,
    shares: 890,
    views: 28000,
    comments: 215,
    followers: 12000,
    verified: false,
  },
  {
    title: '𝕏 Bank Note Rumor (X/Twitter)',
    platform: 'twitter',
    author: '@fin_leaks_insider',
    text: 'BREAKING: Central Bank preparing emergency demonetization circular to discontinue 500 currency notes starting this Friday midnight. Commercial banks notified secretly.',
    likes: 18500,
    shares: 6200,
    views: 450000,
    comments: 1420,
    followers: 85000,
    verified: true,
  },
  {
    title: '🌴 Regional Strike Alert (Malayalam/Kerala)',
    platform: 'facebook',
    author: 'Kochi Live Updates',
    text: 'അടിയന്തര മുന്നറിയിപ്പ്: നാളെ ജില്ലയിൽ പെട്ടെന്നുള്ള ഹർത്താൽ പ്രഖ്യാപിച്ചു. കെഎസ്ആർടിസി ബസുകളും കടകളും അടച്ചിടും. അടിയന്തര ചികിൽസ ഒഴിച്ച് ആരും പുറത്തിറങ്ങരുത്.',
    likes: 2100,
    shares: 950,
    views: 34000,
    comments: 180,
    followers: 18000,
    verified: false,
  }
];

function NewsFeed({ onFactCheck }) {
  const [headlines, setHeadlines] = useState([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [newsError, setNewsError] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');

  const fetchNews = async (cat = activeCategory) => {
    setLoadingNews(true);
    setNewsError(null);
    try {
      const url = cat === 'all'
        ? `${API}/news?limit=60`
        : `${API}/news?limit=60&category=${encodeURIComponent(cat)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch news');
      const data = await res.json();
      setHeadlines(data.headlines || []);
    } catch (err) {
      setNewsError(err.message);
    } finally {
      setLoadingNews(false);
    }
  };

  useEffect(() => {
    fetchNews(activeCategory);
  }, [activeCategory]);

  const grouped = headlines.reduce((acc, h) => {
    if (!acc[h.source]) acc[h.source] = [];
    acc[h.source].push(h);
    return acc;
  }, {});

  return (
    <div className="bg-white p-6 rounded-2xl shadow-xl border border-[#d2b48c]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-xl font-bold text-[#8b4513] flex items-center gap-2">
            <span>📡 Live Regional & National Headlines</span>
            <span className="text-xs bg-[#faf5ed] text-[#8b4513] border border-[#d2b48c] px-2 py-0.5 rounded-full font-semibold">
              Multi-Language Feeds
            </span>
          </h2>
          <p className="text-sm text-[#8b6540] mt-0.5">
            Real-time wire from {Object.keys(grouped).length} outlets across English, Hindi, Malayalam, Tamil & Global newsrooms
          </p>
        </div>
        <button
          onClick={() => fetchNews(activeCategory)}
          disabled={loadingNews}
          className="text-xs px-3.5 py-2 border border-[#d2b48c] text-[#8b4513] rounded-lg hover:bg-[#faf5ed] transition-colors disabled:opacity-50 font-medium flex items-center gap-1.5 self-start md:self-auto cursor-pointer"
        >
          {loadingNews ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Refreshing...</span>
            </>
          ) : (
            <>↻ Refresh Live Wire</>
          )}
        </button>
      </div>

      {/* Category Pills Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto pb-3 mb-5 border-b border-[#f0e4d0]">
        {CATEGORIES.map((cat) => {
          const isActive = activeCategory === cat.key;
          return (
            <button
              key={cat.key}
              onClick={() => setActiveCategory(cat.key)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                isActive
                  ? 'bg-[#8b4513] text-white shadow-sm'
                  : 'bg-[#faf5ed] text-[#5c4033] border border-[#e8d5b7] hover:bg-[#f0e4d0]'
              }`}
            >
              <span>{cat.icon}</span>
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      {loadingNews && (
        <div className="flex items-center justify-center py-12 text-[#8b6540]">
          <svg className="animate-spin mr-3 h-5 w-5 text-[#8b4513]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Fetching live headlines from {activeCategory === 'all' ? 'all regional & global channels' : activeCategory}...
        </div>
      )}

      {newsError && (
        <div className="p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm mb-4">
          {newsError} — Make sure the backend is running.
        </div>
      )}

      {!loadingNews && !newsError && Object.keys(grouped).length === 0 && (
        <p className="text-[#8b6540] italic text-sm py-6 text-center">
          No headlines found for this category right now.
        </p>
      )}

      {!loadingNews && Object.entries(grouped).map(([source, items]) => {
        const categoryTag = items[0]?.category;
        return (
          <div key={source} className="mb-6 last:mb-0">
            <h3 className="text-sm font-bold text-[#5c4033] uppercase tracking-wider mb-2.5 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#8b4513] inline-block"></span>
              <span>{source}</span>
              {categoryTag && (
                <span className="text-[11px] font-normal normal-case bg-[#faf5ed] text-[#8b6540] border border-[#e8d5b7] px-2 py-0.5 rounded-full">
                  {categoryTag}
                </span>
              )}
              <span className="text-xs font-normal text-[#b89576] ml-auto">
                {items.length} item{items.length !== 1 ? 's' : ''}
              </span>
            </h3>
            <div className="space-y-2">
              {items.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-start justify-between gap-3 p-3.5 rounded-lg bg-[#faf5ed] border border-[#e8d5b7] hover:border-[#8b4513] transition-all group"
                >
                  <div className="flex-1 min-w-0">
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-[#5c4033] group-hover:text-[#8b4513] hover:underline line-clamp-2 leading-snug"
                    >
                      {item.title}
                    </a>
                    <div className="flex items-center gap-2 mt-1">
                      {item.published && (
                        <span className="text-xs text-[#b89576]">
                          {new Date(item.published).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => onFactCheck(item.title, 'news')}
                    className="text-xs whitespace-nowrap px-3 py-1.5 bg-[#8b4513] text-white rounded-md hover:bg-[#5c4033] transition-colors flex-shrink-0 opacity-80 group-hover:opacity-100 font-semibold cursor-pointer shadow-sm"
                    title="Run fact-check and spread prediction on this headline"
                  >
                    Fact-Check & Predict ↗
                  </button>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function App() {
  const [selectedPlatform, setSelectedPlatform] = useState('instagram');
  const [inputText, setInputText] = useState('');
  const [authorUsername, setAuthorUsername] = useState('@city_alerts');
  const [likes, setLikes] = useState(3200);
  const [shares, setShares] = useState(850);
  const [views, setViews] = useState(25000);
  const [comments, setComments] = useState(140);
  const [followers, setFollowers] = useState(15000);
  const [isVerified, setIsVerified] = useState(false);

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractMsg, setExtractMsg] = useState(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showNewsFeed, setShowNewsFeed] = useState(false);

  // Auto-detect social URL when text changes
  const handleTextChange = async (val) => {
    setInputText(val);
    setExtractMsg(null);

    // If user pasted a URL
    const urlMatch = val.match(/https?:\/\/[^\s]+/);
    if (urlMatch) {
      const url = urlMatch[0];
      let detectedPlat = selectedPlatform;
      if (url.includes('twitter.com') || url.includes('x.com')) {
        detectedPlat = 'twitter';
      } else if (url.includes('instagram.com')) {
        detectedPlat = 'instagram';
      } else if (url.includes('facebook.com') || url.includes('fb.watch')) {
        detectedPlat = 'facebook';
      }
      setSelectedPlatform(detectedPlat);
    }
  };

  // Extract metadata directly from pasted link
  const handleExtractFromUrl = async () => {
    const urlMatch = inputText.match(/https?:\/\/[^\s]+/);
    const target = urlMatch ? urlMatch[0] : inputText;
    if (!target) return;

    setIsExtracting(true);
    setExtractMsg(null);
    try {
      const res = await fetch(`${API}/extract-social`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: target })
      });
      if (!res.ok) throw new Error('Extraction failed');
      const data = await res.json();
      if (data.success) {
        if (data.text) setInputText(data.text);
        if (data.platform) setSelectedPlatform(data.platform);
        if (data.author_username) setAuthorUsername(data.author_username);
        if (data.likes) setLikes(data.likes);
        if (data.shares) setShares(data.shares);
        if (data.views) setViews(data.views);
        if (data.comments) setComments(data.comments);
        if (data.followers) setFollowers(data.followers);
        if (data.verified !== undefined) setIsVerified(data.verified);
        setExtractMsg(`✓ Successfully resolved ${data.platform.toUpperCase()} post data!`);
      }
    } catch (e) {
      setExtractMsg(`Could not auto-fetch: ${e.message}. You can enter caption text directly.`);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleApplyPreset = (preset) => {
    setSelectedPlatform(preset.platform);
    setInputText(preset.text);
    setAuthorUsername(preset.author);
    setLikes(preset.likes);
    setShares(preset.shares);
    setViews(preset.views);
    setComments(preset.comments);
    setFollowers(preset.followers);
    setIsVerified(preset.verified);
    setExtractMsg(`Loaded preset: ${preset.title}`);
  };

  const handleAnalyze = async (overrideText, overridePlatform) => {
    const textToAnalyze = overrideText || inputText;
    if (!textToAnalyze) return;

    setLoading(true);
    setError(null);
    setResult(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
      const payload = {
        text: textToAnalyze,
        platform: overridePlatform || selectedPlatform,
        author_username: authorUsername,
        likes: Number(likes) || 0,
        shares: Number(shares) || 0,
        views: Number(views) || 0,
        comments: Number(comments) || 0,
        followers: Number(followers) || 0,
        verified: Boolean(isVerified),
      };

      const response = await fetch(`${API}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || 'Failed to analyze post');
      }

      const data = await response.json();
      setResult(data);
      setShowNewsFeed(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const activePlatObj = PLATFORMS.find(p => p.id === selectedPlatform) || PLATFORMS[0];

  return (
    <div className="min-h-screen bg-[#fdfaf6] text-[#5c4033] p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex flex-col items-center justify-center space-y-3 py-6 text-center">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-tr from-[#8b4513] to-amber-600 rounded-xl flex items-center justify-center shadow-lg text-white text-2xl font-black">
              🛡️
            </div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight text-[#8b4513]">
              SocialShield <span className="text-amber-600 text-2xl md:text-3xl font-light">AI</span>
            </h1>
          </div>
          <p className="text-sm md:text-base text-[#8b6540] max-w-2xl leading-relaxed">
            Multi-Platform Fact-Checking & Spillover Prediction Engine for{' '}
            <span className="font-semibold text-[#5c4033]">Instagram, X, Facebook & Web News</span>.
            Identifies misinformation and forecasts how rapidly it infiltrates{' '}
            <span className="font-bold underline decoration-amber-500">small local newsrooms</span> vs{' '}
            <span className="font-semibold text-[#5c4033]">national broadcast channels</span>.
          </p>
        </header>

        {/* Input & Ingestion Card */}
        <div className="bg-white p-6 md:p-8 rounded-2xl shadow-xl border border-[#d2b48c] space-y-5">
          {/* Platform Selector Tabs */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#8b4513] mb-2 flex items-center justify-between">
              <span>Select Social Media Origin:</span>
              <span className="text-[11px] font-normal text-[#8b6540]">Auto-detects from pasted link</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {PLATFORMS.map((plat) => {
                const isActive = selectedPlatform === plat.id;
                return (
                  <button
                    key={plat.id}
                    onClick={() => setSelectedPlatform(plat.id)}
                    className={`p-3 rounded-xl border flex items-center justify-center gap-2 text-sm font-bold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#8b4513] text-white border-[#8b4513] shadow-md transform scale-[1.02]'
                        : 'bg-[#faf5ed] text-[#5c4033] border-[#e8d5b7] hover:border-[#8b4513] hover:bg-[#f5ede0]'
                    }`}
                  >
                    <span className="text-lg">{plat.icon}</span>
                    <span>{plat.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick-test Presets */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#8b6540] mb-2">
              ⚡ Quick Scenarios (Click to test):
            </div>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleApplyPreset(p)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-[#faf5ed] border border-[#d2b48c] text-[#5c4033] hover:bg-[#8b4513] hover:text-white transition-all cursor-pointer font-medium"
                >
                  {p.title}
                </button>
              ))}
            </div>
          </div>

          {/* Text/URL Input Area */}
          <div className="space-y-2">
            <div className="relative">
              <textarea
                className="w-full bg-[#faf5ed] border border-[#d2b48c] rounded-xl p-4 text-[#5c4033] placeholder-[#b89576] focus:outline-none focus:ring-2 focus:ring-[#8b4513] transition-all resize-none text-sm leading-relaxed"
                rows="4"
                placeholder={activePlatObj.placeholder}
                value={inputText}
                onChange={(e) => handleTextChange(e.target.value)}
                id="main-input"
              />
              {inputText.match(/https?:\/\/[^\s]+/) && (
                <button
                  onClick={handleExtractFromUrl}
                  disabled={isExtracting}
                  className="absolute right-3 bottom-3 text-xs px-2.5 py-1.5 bg-[#8b4513] text-white rounded-lg hover:bg-[#5c4033] transition-all flex items-center gap-1 shadow-sm font-semibold cursor-pointer disabled:opacity-50"
                  title="Auto-fetch post caption and engagement metrics from link"
                >
                  {isExtracting ? (
                    <>
                      <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <span>Fetching...</span>
                    </>
                  ) : (
                    <>⚡ Extract Post Data</>
                  )}
                </button>
              )}
            </div>

            {extractMsg && (
              <div className="text-xs text-[#8b4513] bg-[#faf5ed] border border-[#e8d5b7] p-2 rounded-lg font-medium">
                {extractMsg}
              </div>
            )}
          </div>

          {/* Expandable Engagement & Virality Settings */}
          <div>
            <button
              onClick={() => setShowAdvanced(v => !v)}
              className="text-xs font-bold text-[#8b4513] hover:text-[#5c4033] flex items-center gap-1.5 cursor-pointer"
            >
              <span>{showAdvanced ? '▼' : '▶'}</span>
              <span>{showAdvanced ? 'Hide' : 'Customize'} Social Engagement & Author Parameters</span>
              <span className="text-[10px] bg-[#faf5ed] border border-[#d2b48c] px-2 py-0.5 rounded-full font-normal">
                Likes, shares, followers
              </span>
            </button>

            {showAdvanced && (
              <div className="mt-3 p-4 bg-[#faf5ed] border border-[#e8d5b7] rounded-xl grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs">
                <div>
                  <label className="block text-[#8b6540] font-medium mb-1">Author Handle</label>
                  <input
                    type="text"
                    value={authorUsername}
                    onChange={(e) => setAuthorUsername(e.target.value)}
                    className="w-full p-2 bg-white border border-[#d2b48c] rounded-lg text-[#5c4033] font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[#8b6540] font-medium mb-1">Likes</label>
                  <input
                    type="number"
                    value={likes}
                    onChange={(e) => setLikes(e.target.value)}
                    className="w-full p-2 bg-white border border-[#d2b48c] rounded-lg text-[#5c4033] font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[#8b6540] font-medium mb-1">Shares / Reposts</label>
                  <input
                    type="number"
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    className="w-full p-2 bg-white border border-[#d2b48c] rounded-lg text-[#5c4033] font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[#8b6540] font-medium mb-1">Views</label>
                  <input
                    type="number"
                    value={views}
                    onChange={(e) => setViews(e.target.value)}
                    className="w-full p-2 bg-white border border-[#d2b48c] rounded-lg text-[#5c4033] font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[#8b6540] font-medium mb-1">Followers</label>
                  <input
                    type="number"
                    value={followers}
                    onChange={(e) => setFollowers(e.target.value)}
                    className="w-full p-2 bg-white border border-[#d2b48c] rounded-lg text-[#5c4033] font-mono"
                  />
                </div>
                <div className="flex flex-col justify-end">
                  <label className="flex items-center gap-2 p-2 bg-white border border-[#d2b48c] rounded-lg cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isVerified}
                      onChange={(e) => setIsVerified(e.target.checked)}
                      className="rounded text-[#8b4513] focus:ring-[#8b4513]"
                    />
                    <span className="font-semibold text-[#5c4033]">Verified ✓</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Action Row */}
          <div className="flex justify-between items-center pt-2 flex-wrap gap-3 border-t border-[#f0e4d0]">
            <button
              onClick={() => { setShowNewsFeed(v => !v); setResult(null); setError(null); }}
              className="text-xs font-bold text-indigo-700 hover:text-indigo-900 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span>{showNewsFeed ? '✕ Hide' : '📰 Browse'} Live News Headlines</span>
            </button>

            <button
              onClick={() => handleAnalyze()}
              disabled={loading || !inputText}
              className="px-6 py-3 bg-[#8b4513] hover:bg-[#5c4033] disabled:bg-[#e0d4c8] disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-[#8b4513]/25 transition-all transform active:scale-95 flex items-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Verifying & Modeling Spread...</span>
                </>
              ) : (
                <>
                  <span>🔎 Fact Check & Predict Spread</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-xl text-center text-sm shadow-sm">
            {error}
          </div>
        )}

        {/* Results Dashboard */}
        {result && (
          <div className="space-y-6">
            {/* Top Navigation */}
            <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-[#d2b48c] shadow-sm">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#8b4513]">Analysis Result for:</span>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#faf5ed] border border-[#d2b48c] text-[#5c4033] capitalize">
                  {result.post.platform} Post
                </span>
                <span className="text-xs font-mono text-[#8b6540]">
                  by {result.post.author_username}
                </span>
              </div>
              <button
                onClick={() => { setResult(null); setInputText(''); }}
                className="text-xs text-[#8b4513] hover:underline font-bold cursor-pointer"
              >
                ← Clear / New Verification
              </button>
            </div>

            {/* Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main Column */}
              <div className="lg:col-span-2 space-y-6">
                <RiskBadge
                  assessment={result.risk_assessment}
                  explanation={result.explanation}
                />
                <SpreadForecast
                  diffusion={result.diffusion}
                  diffusion_risk={result.diffusion_risk}
                />
                <SourceBreakdown
                  verification={result.verification}
                />
              </div>

              {/* Sidebar Column */}
              <div className="space-y-6">
                <AuthorProfile
                  post={result.post}
                  credibility_score={result.credibility_score}
                  verification={result.verification}
                />
                <button
                  onClick={() => { setResult(null); setShowNewsFeed(true); }}
                  className="w-full text-xs text-[#8b6540] hover:text-[#5c4033] font-semibold py-2.5 bg-white border border-[#d2b48c] rounded-xl shadow-sm transition-colors cursor-pointer"
                >
                  📰 Compare with Live News Wire
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Live News Feed */}
        {showNewsFeed && !result && (
          <NewsFeed onFactCheck={(title) => {
            setInputText(title);
            setSelectedPlatform('news');
            handleAnalyze(title, 'news');
          }} />
        )}

      </div>
    </div>
  );
}

export default App;
