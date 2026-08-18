import React, { useState, useMemo } from 'react';
import type { CampaignRunResult, GeneratedAdArtifact } from '../services/api';

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
    <div className="results-container" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Campaign Run Header Summary Banner */}
      <div className="results-header-card">
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
          <div>
            <div className="results-meta-row">
              <span className="badge-run-id">RUN: {result.run_id}</span>
              <span className="badge-seed">SEED: {result.seed}</span>
              <span className="badge-count">18 ADS GENERATED</span>
              <span className="badge-seed">⏱️ {result.duration_seconds}s</span>
            </div>
            <h2 className="results-title">{result.campaign_name}</h2>
            <p className="results-provenance-text">{result.provenance_summary}</p>
          </div>

          {/* Action Buttons */}
          <div className="results-action-group">
            {result.zip_bundle_download_url && (
              <a href={result.zip_bundle_download_url} download className="btn-zip-download">
                <span>📥</span>
                <span>DOWNLOAD ALL 18 ADS (ZIP)</span>
              </a>
            )}

            {result.contact_sheet_preview_url && (
              <button onClick={onOpenContactSheet} className="btn-contact-sheet-action">
                <span>🖼️</span>
                <span>VIEW CONTACT SHEET</span>
              </button>
            )}

            <button
              onClick={onReRun}
              className="btn-contact-sheet-action"
              style={{ color: '#00D2FF', borderColor: 'rgba(0, 210, 255, 0.4)' }}
            >
              <span>🔄</span>
              <span>RUN NEW BATCH</span>
            </button>
          </div>
        </div>

        {/* Dropbox Storage / Provenance Status Bar */}
        <div className="results-storage-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: '#00D2FF', fontWeight: 'bold' }}>Storage:</span>
            <span style={{ color: '#FFFFFF', textTransform: 'capitalize' }}>{result.storage_mode}</span>
            {result.dropbox_folder_path && (
              <span style={{ color: '#5E7387' }}>({result.dropbox_folder_path})</span>
            )}
          </div>

          {result.dropbox_shared_link ? (
            <a
              href={result.dropbox_shared_link}
              target="_blank"
              rel="noopener noreferrer"
              className="dropbox-link-btn"
            >
              <span>🔗</span>
              <span>Open in Dropbox Folder</span>
            </a>
          ) : (
            <span style={{ color: '#5E7387' }}>Dropbox App Folder Synced</span>
          )}
        </div>
      </div>

      {/* 2. Filter Controls */}
      <div className="results-filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#00D2FF', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 'bold', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Filter Ads:
          </span>
        </div>

        <div className="filter-group-items">
          {/* Activity Filter */}
          <div className="filter-select-item">
            <span>Activity:</span>
            <select
              value={selectedActivity}
              onChange={(e) => setSelectedActivity(e.target.value)}
              className="filter-dropdown"
            >
              <option value="all">All Activities (6)</option>
              <option value="beach">Beach</option>
              <option value="camping">Camping</option>
              <option value="tailgating">Tailgating</option>
            </select>
          </div>

          {/* Product Color Filter */}
          <div className="filter-select-item">
            <span>Product:</span>
            <select
              value={selectedProductColor}
              onChange={(e) => setSelectedProductColor(e.target.value)}
              className="filter-dropdown"
            >
              <option value="all">All Colors</option>
              <option value="orange">Orange Cooler (Younger 20–24)</option>
              <option value="white">White Cooler (Older 25–30)</option>
            </select>
          </div>

          {/* Format Filter */}
          <div className="filter-select-item">
            <span>Format:</span>
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              className="filter-dropdown"
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {filteredConcepts.map((concept) => {
          const conceptAds = adsByConcept[concept.concept_id] || [];
          const isOrange = concept.product_role.includes('orange');
          const isYounger = concept.age_band === 'younger';
          const bgFilename = concept.selected_background_path.split('/').pop() || '';
          const hasGeminiBg = result.gemini_audiences.includes(concept.audience_id);

          return (
            <div key={concept.concept_id} className="concept-card">
              {/* Concept Metadata Header */}
              <div className="concept-header-row">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="badge-run-id" style={{ fontSize: '13px', padding: '4px 10px' }}>
                    {concept.audience_id}
                  </span>
                  <div>
                    <h3 className="concept-audience-title">{concept.audience_name}</h3>
                    <p className="concept-audience-subtitle">
                      Territory: <span style={{ color: '#E2E8F0' }}>{concept.territory}</span> | Seed: {concept.seed_used}
                    </p>
                  </div>
                </div>

                {/* Concept Badges */}
                <div className="concept-badge-list">
                  <span className={isYounger ? 'badge-age-younger' : 'badge-age-older'}>
                    {isYounger ? 'AGE 20–24 (YOUNGER)' : 'AGE 25–30 (OLDER)'}
                  </span>

                  <span className={isOrange ? 'badge-product-orange' : 'badge-product-white'}>
                    {isOrange ? 'ORANGE COOLER' : 'WHITE COOLER'}
                  </span>

                  <span className="badge-seed" style={{ textTransform: 'uppercase', color: '#00D2FF' }}>
                    {concept.activity}
                  </span>

                  <span className="badge-seed">
                    TAGLINE: {concept.selected_tagline_text} ({concept.tagline_color_hex === '#000000' ? 'BLACK' : 'WHITE'})
                  </span>

                  {hasGeminiBg ? (
                    <span className="badge-gemini-bg">
                      ⚠️ AI BG (REVIEW REQ)
                    </span>
                  ) : (
                    <span className="badge-approved-bg">
                      ✓ APPROVED BG ({bgFilename})
                    </span>
                  )}
                </div>
              </div>

              {/* Nested 3 Format Render Cards */}
              <div className="format-grid-3col">
                {conceptAds.map((ad) => (
                  <div key={ad.artifact_id} className="format-render-card">
                    <div>
                      {/* Format Header */}
                      <div className="format-card-header">
                        <span className="format-ratio-tag">
                          {ad.aspect_ratio === '1:1' ? '1:1 SQUARE' : ad.aspect_ratio === '16:9' ? '16:9 LANDSCAPE' : '9:16 VERTICAL'}
                        </span>
                        <span className="format-dims-tag">
                          {ad.dimensions[0]}×{ad.dimensions[1]}
                        </span>
                      </div>

                      {/* Rendered Ad Thumbnail */}
                      <div
                        className="format-image-preview-box"
                        onClick={() => onOpenLightbox(ad)}
                      >
                        <img
                          src={ad.preview_url}
                          alt={ad.filename}
                          className="format-ad-img"
                        />
                        <div className="format-hover-overlay">
                          <span className="format-hover-badge">
                            🔍 View Large
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Card Actions */}
                    <div className="format-card-footer">
                      <span className="format-filesize-text">
                        {Math.round(ad.filesize_bytes / 1024)} KB
                      </span>
                      <a
                        href={ad.preview_url}
                        download={ad.filename}
                        className="btn-png-download"
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
