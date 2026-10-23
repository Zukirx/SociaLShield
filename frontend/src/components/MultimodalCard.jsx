import React, { useState } from 'react';

/**
 * MultimodalCard
 * Displays extracted multimodal intelligence signals returned by the backend:
 *   - 🎙️ Whisper audio transcript (speech-to-text)
 *   - 🔍 OCR screen text (chyrons, banners, meme overlays)
 *   - 🖼️ Sensational overlay alerts detected on-screen
 *   - 🎬 YouTube video metadata (title, channel, duration)
 *   - 📊 Unified synthesized claim used for fact-checking
 */
const MultimodalCard = ({ multimodal_context }) => {
  const [expandTranscript, setExpandTranscript] = useState(false);
  const [expandOcr, setExpandOcr] = useState(false);

  if (!multimodal_context || !multimodal_context.has_media_analysis) {
    return null;
  }

  const {
    audio_transcript = '',
    ocr_text = '',
    sensational_overlays = [],
    youtube = {},
    synthesis = {},
    transcription_engine = 'none',
    ocr_engine = 'none',
  } = multimodal_context;

  const hasYoutube = youtube && (youtube.video_id || youtube.title);
  const hasTranscript = audio_transcript && audio_transcript.trim().length > 0;
  const hasOcr = ocr_text && ocr_text.trim().length > 0;
  const hasSensational = sensational_overlays && sensational_overlays.length > 0;
  const hasSynthesis = synthesis && synthesis.synthesized_claim;

  if (!hasYoutube && !hasTranscript && !hasOcr && !hasSynthesis) return null;

  const engineBadge = (label, engine) => engine && engine !== 'none' ? (
    <span className="text-[10px] px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded-full font-mono border border-violet-200">
      {engine}
    </span>
  ) : null;

  const formatDuration = (sec) => {
    if (!sec) return '';
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-violet-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center text-xl">
            🧠
          </div>
          <div>
            <h3 className="text-white font-bold text-base tracking-tight">Multimodal Media Analysis</h3>
            <p className="text-violet-200 text-xs mt-0.5">
              OCR · Whisper ASR · YouTube Intelligence · Claim Synthesis
            </p>
          </div>
        </div>
        {synthesis.is_multimodal && (
          <span className="text-xs px-2.5 py-1 bg-white/20 text-white rounded-full font-semibold border border-white/30">
            {synthesis.sources_used?.length || 0} Sources Merged
          </span>
        )}
      </div>

      <div className="p-6 space-y-5">

        {/* YouTube Video Metadata */}
        {hasYoutube && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex gap-4">
            {youtube.thumbnail_url && (
              <img
                src={youtube.thumbnail_url}
                alt="Video thumbnail"
                className="w-28 h-16 object-cover rounded-lg flex-shrink-0 shadow-sm"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-red-600 text-lg">▶️</span>
                <span className="text-xs font-bold text-red-700 uppercase tracking-wide">
                  YouTube {youtube.is_short ? 'Short' : 'Video'}
                </span>
                {youtube.source && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-red-100 text-red-600 rounded-full border border-red-200">
                    {youtube.source}
                  </span>
                )}
              </div>
              {youtube.title && (
                <p className="text-sm font-semibold text-slate-800 line-clamp-2 leading-snug">
                  {youtube.title}
                </p>
              )}
              <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                {youtube.channel && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    👤 {youtube.channel}
                  </span>
                )}
                {youtube.views > 0 && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    👁️ {youtube.views.toLocaleString()} views
                  </span>
                )}
                {youtube.likes > 0 && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    👍 {youtube.likes.toLocaleString()}
                  </span>
                )}
                {youtube.duration_sec > 0 && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    ⏱️ {formatDuration(youtube.duration_sec)}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Sensational On-Screen Overlays Detected */}
        {hasSensational && (
          <div className="p-3 bg-orange-50 border border-orange-300 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-orange-600 text-sm">⚠️</span>
              <span className="text-xs font-bold text-orange-800 uppercase tracking-wide">
                Sensational On-Screen Overlays Detected
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {sensational_overlays.map((overlay, i) => (
                <span
                  key={i}
                  className="text-xs font-bold px-2.5 py-1 bg-orange-200 text-orange-800 rounded-full border border-orange-300 animate-pulse"
                >
                  🚨 {overlay}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Audio Transcript (Whisper) */}
        {hasTranscript && (
          <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-indigo-600">🎙️</span>
                <span className="text-xs font-bold text-indigo-800 uppercase tracking-wide">
                  Audio Transcript
                </span>
                {engineBadge('engine', transcription_engine)}
              </div>
              <button
                onClick={() => setExpandTranscript(v => !v)}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
              >
                {expandTranscript ? '▲ Collapse' : '▼ Expand'}
              </button>
            </div>
            <p className={`text-sm text-slate-700 leading-relaxed ${expandTranscript ? '' : 'line-clamp-3'}`}>
              {audio_transcript}
            </p>
          </div>
        )}

        {/* OCR Screen Text */}
        {hasOcr && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-emerald-600">🔍</span>
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wide">
                  OCR Screen Text
                </span>
                {engineBadge('engine', ocr_engine)}
              </div>
              <button
                onClick={() => setExpandOcr(v => !v)}
                className="text-xs text-emerald-600 hover:text-emerald-800 font-semibold cursor-pointer"
              >
                {expandOcr ? '▲ Collapse' : '▼ Expand'}
              </button>
            </div>
            <p className={`text-sm text-slate-700 font-mono leading-relaxed text-xs ${expandOcr ? '' : 'line-clamp-3'}`}>
              {ocr_text}
            </p>
          </div>
        )}

        {/* Synthesized Claim */}
        {hasSynthesis && (
          <div className="p-4 bg-violet-50 border border-violet-200 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-violet-600">📊</span>
              <span className="text-xs font-bold text-violet-800 uppercase tracking-wide">
                Unified Synthesized Claim
              </span>
              <span className="text-[10px] text-violet-500 ml-auto">
                {synthesis.word_count} words · {synthesis.sources_used?.length || 0} sources
              </span>
            </div>
            {synthesis.sources_used && synthesis.sources_used.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {synthesis.sources_used.map((src, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 bg-violet-100 text-violet-700 rounded-full border border-violet-200 font-medium">
                    {src}
                  </span>
                ))}
              </div>
            )}
            <p className="text-sm text-slate-700 leading-relaxed line-clamp-4 italic border-l-4 border-violet-300 pl-3">
              &ldquo;{synthesis.synthesized_claim}&rdquo;
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MultimodalCard;
