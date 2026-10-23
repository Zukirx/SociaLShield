import React from 'react';

const AuthorProfile = ({ post, credibility_score, verification }) => {
  if (!post) return null;

  const platform = (post.platform || 'news').toLowerCase();
  const isSocial = ['instagram', 'twitter', 'facebook', 'youtube', 'quora', 'reddit'].includes(platform);
  const metrics = post.metrics || {};
  const authorMeta = post.author_meta || {};

  const getPlatformInfo = (plat) => {
    switch (plat) {
      case 'instagram':
        return { name: 'Instagram', icon: '📸', color: 'from-pink-500 to-purple-600', badge: 'bg-pink-100 text-pink-800 border-pink-200' };
      case 'twitter':
        return { name: 'X (Twitter)', icon: '𝕏', color: 'from-slate-800 to-black', badge: 'bg-slate-100 text-slate-800 border-slate-300' };
      case 'facebook':
        return { name: 'Facebook', icon: '👥', color: 'from-blue-600 to-blue-800', badge: 'bg-blue-100 text-blue-800 border-blue-200' };
      default:
        return { name: 'News Publication', icon: '📰', color: 'from-[#8b4513] to-[#5c4033]', badge: 'bg-[#faf5ed] text-[#8b4513] border-[#d2b48c]' };
    }
  };

  const platInfo = getPlatformInfo(platform);
  const firstSourceLink = verification?.analyzed_sources?.[0]?.link || null;

  return (
    <div className="p-6 bg-white rounded-2xl shadow-xl border border-[#d2b48c]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-[#8b4513]">
          {isSocial ? 'Social Media Profile' : 'Source Profile'}
        </h3>
        <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold border flex items-center gap-1 ${platInfo.badge}`}>
          <span>{platInfo.icon}</span>
          <span>{platInfo.name}</span>
        </span>
      </div>

      <div className="flex items-center space-x-3.5 mb-5 p-3.5 bg-[#faf5ed] rounded-xl border border-[#e8d5b7]">
        <div className={`w-12 h-12 rounded-full bg-gradient-to-tr ${platInfo.color} flex items-center justify-center text-xl font-bold text-white shadow-sm flex-shrink-0`}>
          {post.author_username ? post.author_username.replace('@', '').charAt(0).toUpperCase() : 'U'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center space-x-1.5 flex-wrap">
            <span className="font-bold text-base text-[#5c4033] truncate">
              {post.author_username}
            </span>
            {authorMeta.verified && (
              <svg className="w-4 h-4 text-blue-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <p className="text-xs text-[#8b6540]">
            {isSocial ? 'Content Originator' : 'Publishing Outlet'}
          </p>
        </div>
      </div>

      <div className="space-y-2.5">
        <div className="flex justify-between items-center p-3 bg-[#faf5ed] border border-[#d2b48c] rounded-xl">
          <span className="text-xs text-[#8b6540] font-semibold">Credibility Index</span>
          <span className={`font-mono font-bold text-sm ${credibility_score > 0.7 ? 'text-emerald-700' : credibility_score > 0.4 ? 'text-amber-700' : 'text-rose-700'}`}>
            {(credibility_score * 100).toFixed(1)}%
          </span>
        </div>

        {isSocial && (
          <>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 bg-[#faf5ed] border border-[#e8d5b7] rounded-lg">
                <div className="text-[10px] text-[#8b6540] font-medium">Followers</div>
                <div className="font-mono text-xs font-bold text-[#5c4033] mt-0.5">
                  {(authorMeta.followers || 0).toLocaleString()}
                </div>
              </div>
              <div className="p-2.5 bg-[#faf5ed] border border-[#e8d5b7] rounded-lg">
                <div className="text-[10px] text-[#8b6540] font-medium">Account Status</div>
                <div className="text-xs font-bold text-[#5c4033] mt-0.5">
                  {authorMeta.verified ? 'Verified ✓' : 'Standard'}
                </div>
              </div>
            </div>

            <div className="p-3 bg-[#faf5ed] border border-[#d2b48c] rounded-xl space-y-1.5">
              <div className="text-[11px] font-bold text-[#8b4513] uppercase tracking-wider">
                Post Engagement Recorded
              </div>
              <div className="grid grid-cols-3 gap-1 text-center pt-1">
                <div className="bg-white/80 p-1.5 rounded border border-[#e8d5b7]">
                  <div className="text-[10px] text-[#8b6540]">Likes</div>
                  <div className="font-mono text-xs font-bold text-[#5c4033]">
                    {(metrics.likes || 0).toLocaleString()}
                  </div>
                </div>
                <div className="bg-white/80 p-1.5 rounded border border-[#e8d5b7]">
                  <div className="text-[10px] text-[#8b6540]">Shares/RT</div>
                  <div className="font-mono text-xs font-bold text-[#5c4033]">
                    {(metrics.shares || 0).toLocaleString()}
                  </div>
                </div>
                <div className="bg-white/80 p-1.5 rounded border border-[#e8d5b7]">
                  <div className="text-[10px] text-[#8b6540]">Comments</div>
                  <div className="font-mono text-xs font-bold text-[#5c4033]">
                    {(metrics.comments || 0).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {!isSocial && (
          <div className="flex justify-between items-center p-3 bg-[#faf5ed] border border-[#d2b48c] rounded-xl">
            <span className="text-xs text-[#8b6540] font-semibold">Sources Corroborating</span>
            <span className="font-mono text-[#5c4033] font-bold text-sm">
              {verification?.analyzed_sources?.length || 0}
            </span>
          </div>
        )}

        {firstSourceLink && (
          <a
            href={firstSourceLink}
            target="_blank"
            rel="noopener noreferrer"
            className="block text-center p-2.5 bg-[#8b4513] text-white text-xs font-bold rounded-lg hover:bg-[#5c4033] transition-colors shadow-sm mt-3"
          >
            Read Top Corroborating Report ↗
          </a>
        )}
      </div>
    </div>
  );
};

export default AuthorProfile;
