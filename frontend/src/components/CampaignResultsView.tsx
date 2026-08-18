import React, { useState, useMemo } from 'react';
import type { CampaignRunResult, GeneratedAdArtifact, AudienceConcept } from '../services/api';

interface CampaignResultsViewProps {
  result: CampaignRunResult;
  onOpenLightbox: (ad: GeneratedAdArtifact) => void;
  onOpenContactSheet: () => void;
  onReRun: () => void;
}

export const CampaignResultsView: React.FC<CampaignResultsViewProps> = ({
  result,
  onOpenLightbox,
  onOpenContactSheet,
  onReRun,
}) => {
  // Filter states
  const [selectedActivity, setSelectedActivity] = useState<string>('all');
  const [selectedProductColor, setSelectedProductColor] = useState<string>('all');
  const [selectedFormat, setSelectedFormat] = useState<string>('all');

  // Filtered concepts and ads
  const filteredConcepts = useMemo(() => {
    return result.concepts.filter((concept) => {
      if (selectedActivity !== 'all' && concept.activity.toLowerCase() !== selectedActivity.toLowerCase()) {
        return false;
      }
      const prodColor = concept.product_role.includes('orange') ? 'orange' : 'white';
      if (selectedProductColor !== 'all' && prodColor !== selectedProductColor) {
        return false;
      }
      return true;
    });
  }, [result.concepts, selectedActivity, selectedProductColor]);

  // Group ads by concept_id
  const adsByConcept = useMemo(() => {
    const map: Record<string, GeneratedAdArtifact[]> = {};
    for (const ad of result.ads) {
      if (!map[ad.concept_id]) map[ad.concept_id] = [];
      if (selectedFormat === 'all' || ad.aspect_ratio === selectedFormat) {
        map[ad.concept_id].push(ad);
      }
    }
    return map;
  }, [result.ads, selectedFormat]);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. Campaign Run Header Summary Banner */}
      <div className="bg-[#0D151E] border border-[#1E2D3D] rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-[#00D2FF]/20 text-[#00D2FF] border border-[#00D2FF]/40">
                RUN: {result.run_id}
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#15222E] text-gray-300 border border-[#1E2D3D]">
                SEED: {result.seed}
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-700/50">
                18 ADS GENERATED
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#15222E] text-gray-400">
                ⏱️ {result.duration_seconds}s
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-wide">
              {result.campaign_name}
            </h2>
            <p className="text-xs text-gray-400 font-mono mt-1">
              {result.provenance_summary}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3">
            {result.zip_bundle_download_url && (
              <a
                href={result.zip_bundle_download_url}
                download
                className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-[#00D2FF] hover:bg-[#38bdf8] text-[#0A1118] font-bold text-xs font-mono transition-all shadow-lg shadow-[#00D2FF]/20 cursor-pointer"
              >
                <span>📥</span>
                <span>DOWNLOAD ALL 18 ADS (ZIP)</span>
              </a>
            )}

            {result.contact_sheet_preview_url && (
              <button
                onClick={onOpenContactSheet}
                className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-[#15222E] hover:bg-[#1E2D3D] text-white border border-[#223548] font-bold text-xs font-mono transition-colors"
              >
                <span>🖼️</span>
                <span>VIEW CONTACT SHEET</span>
              </button>
            )}

            <button
              onClick={onReRun}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-[#15222E] hover:bg-[#1E2D3D] text-[#00D2FF] border border-[#00D2FF]/40 font-bold text-xs font-mono transition-colors"
            >
              <span>🔄</span>
              <span>RUN NEW BATCH</span>
            </button>
          </div>
        </div>

        {/* Dropbox Storage / Provenance Status Bar */}
        <div className="mt-4 pt-4 border-t border-[#182430] flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-gray-400">
          <div className="flex items-center space-x-2">
            <span className="text-[#00D2FF]">Storage Mode:</span>
            <span className="text-white capitalize font-semibold">{result.storage_mode}</span>
            {result.dropbox_folder_path && (
              <span className="text-gray-500">({result.dropbox_folder_path})</span>
            )}
          </div>

          {result.dropbox_shared_link ? (
            <a
              href={result.dropbox_shared_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00D2FF] hover:underline flex items-center space-x-1"
            >
              <span>🔗 Open in Dropbox</span>
            </a>
          ) : (
            <span className="text-gray-500">Dropbox App Folder Synced</span>
          )}
        </div>
      </div>

      {/* 2. Filter Controls */}
      <div className="bg-[#0A1118] border border-[#1E2D3D] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono font-bold text-[#00D2FF] tracking-wider uppercase">Filter Ads:</span>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {/* Activity Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400 font-mono">Activity:</span>
            <select
              value={selectedActivity}
              onChange={(e) => setSelectedActivity(e.target.value)}
              className="bg-[#121B24] border border-[#1E2D3D] rounded px-2.5 py-1 text-xs font-mono text-white focus:outline-none focus:border-[#00D2FF]"
            >
              <option value="all">All Activities (6)</option>
              <option value="beach">Beach</option>
              <option value="camping">Camping</option>
              <option value="tailgating">Tailgating</option>
            </select>
          </div>

          {/* Product Color Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400 font-mono">Product:</span>
            <select
              value={selectedProductColor}
              onChange={(e) => setSelectedProductColor(e.target.value)}
              className="bg-[#121B24] border border-[#1E2D3D] rounded px-2.5 py-1 text-xs font-mono text-white focus:outline-none focus:border-[#00D2FF]"
            >
              <option value="all">All Colors</option>
              <option value="orange">Orange Cooler (Younger 20–24)</option>
              <option value="white">White Cooler (Older 25–30)</option>
            </select>
          </div>

          {/* Format Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400 font-mono">Format:</span>
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              className="bg-[#121B24] border border-[#1E2D3D] rounded px-2.5 py-1 text-xs font-mono text-white focus:outline-none focus:border-[#00D2FF]"
            >
              <option value="all">All 3 Formats (1:1, 16:9, 9:16)</option>
              <option value="1:1">1:1 Square (1080×1080)</option>
              <option value="16:9">16:9 Landscape (1920×1080)</option>
              <option value="9:16">9:16 Vertical (1080×1920)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. Six Concept Cards (One per Audience) */}
      <div className="space-y-8">
        {filteredConcepts.map((concept) => {
          const conceptAds = adsByConcept[concept.concept_id] || [];
          const isOrange = concept.product_role.includes('orange');
          const isYounger = concept.age_band === 'younger';
          const bgFilename = concept.selected_background_path.split('/').pop() || '';
          const hasGeminiBg = result.gemini_audiences.includes(concept.audience_id);

          return (
            <div
              key={concept.concept_id}
              className="bg-[#0D151E] border border-[#1E2D3D] rounded-xl p-6 shadow-xl hover:border-[#2A3E52] transition-colors"
            >
              {/* Concept Metadata Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-5 border-b border-[#182430] gap-3">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-mono font-bold px-3 py-1 rounded bg-[#00D2FF]/20 text-[#00D2FF] border border-[#00D2FF]/40">
                    {concept.audience_id}
                  </span>
                  <div>
                    <h3 className="text-lg font-bold text-white">{concept.audience_name}</h3>
                    <p className="text-xs text-gray-400 font-mono">
                      Territory: <span className="text-gray-200">{concept.territory}</span> | Seed: {concept.seed_used}
                    </p>
                  </div>
                </div>

                {/* Concept Badges */}
                <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                  {/* Age Band */}
                  <span className={`px-2.5 py-1 rounded border ${
                    isYounger
                      ? 'bg-amber-950/40 text-amber-300 border-amber-600/40'
                      : 'bg-indigo-950/40 text-indigo-300 border-indigo-600/40'
                  }`}>
                    {isYounger ? 'AGE 20–24 (YOUNGER)' : 'AGE 25–30 (OLDER)'}
                  </span>

                  {/* Product Color */}
                  <span className={`px-2.5 py-1 rounded border ${
                    isOrange
                      ? 'bg-[#FF8A00]/20 text-[#FF8A00] border-[#FF8A00]/40'
                      : 'bg-blue-950/40 text-blue-200 border-blue-600/40'
                  }`}>
                    {isOrange ? 'ORANGE COOLER' : 'WHITE COOLER'}
                  </span>

                  {/* Activity */}
                  <span className="px-2.5 py-1 rounded bg-[#15222E] text-[#00D2FF] border border-[#1E2D3D] uppercase">
                    {concept.activity}
                  </span>

                  {/* Tagline */}
                  <span className="px-2.5 py-1 rounded bg-[#101820] text-gray-300 border border-[#1E2D3D]">
                    TAGLINE: {concept.selected_tagline_text} ({concept.tagline_color_hex === '#000000' ? 'BLACK' : 'WHITE'})
                  </span>

                  {/* Background Provenance */}
                  {hasGeminiBg ? (
                    <span className="px-2.5 py-1 rounded bg-amber-950/70 text-amber-300 border border-amber-500 animate-pulse">
                      ⚠️ AI BG (REVIEW REQ)
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-600/30">
                      ✓ APPROVED BG ({bgFilename})
                    </span>
                  )}
                </div>
              </div>

              {/* Nested 3 Format Render Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {conceptAds.map((ad) => (
                  <div
                    key={ad.artifact_id}
                    className="bg-[#090E14] border border-[#182430] rounded-lg p-4 flex flex-col justify-between hover:border-[#00D2FF]/50 transition-all group"
                  >
                    <div>
                      {/* Format Header */}
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-mono font-bold text-[#00D2FF]">
                          {ad.aspect_ratio === '1:1' ? '1:1 SQUARE' : ad.aspect_ratio === '16:9' ? '16:9 LANDSCAPE' : '9:16 VERTICAL'}
                        </span>
                        <span className="text-xs font-mono text-gray-500">
                          {ad.dimensions[0]}×{ad.dimensions[1]}
                        </span>
                      </div>

                      {/* Rendered Ad Thumbnail */}
                      <div
                        className="bg-[#05080C] rounded-lg p-2 flex items-center justify-center min-h-[220px] max-h-[280px] overflow-hidden cursor-pointer relative border border-[#121B24]"
                        onClick={() => onOpenLightbox(ad)}
                      >
                        <img
                          src={ad.preview_url}
                          alt={ad.filename}
                          className="max-h-[240px] max-w-full object-contain rounded drop-shadow group-hover:scale-[1.03] transition-transform duration-200"
                        />
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity rounded-lg">
                          <span className="text-xs font-mono font-bold text-white bg-[#00D2FF]/90 text-[#0A1118] px-3 py-1.5 rounded-lg shadow-lg">
                            🔍 View Large
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Card Actions */}
                    <div className="mt-4 pt-3 border-t border-[#121B24] flex items-center justify-between">
                      <span className="text-[11px] font-mono text-gray-500">
                        {Math.round(ad.filesize_bytes / 1024)} KB
                      </span>
                      <a
                        href={ad.preview_url}
                        download={ad.filename}
                        className="text-xs font-mono text-[#00D2FF] hover:text-white flex items-center space-x-1 py-1 px-2.5 rounded bg-[#121B24] hover:bg-[#1E2D3D] transition-colors"
                      >
                        <span>📥</span>
                        <span>PNG</span>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
