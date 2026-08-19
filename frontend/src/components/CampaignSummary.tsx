import React, { useState } from 'react';
import type { CampaignBrief } from '../types/campaign';

interface CampaignSummaryProps {
  brief: CampaignBrief;
}

export const CampaignSummary: React.FC<CampaignSummaryProps> = ({ brief }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const audiences = brief.audiences || [];
  const formats = brief.outputFormats || [];
  const conceptsPerAudience = brief.generation?.conceptsPerAudience || 1;
  const totalOutputs = brief.generation?.totalOutputsPerRun || (audiences.length * formats.length * conceptsPerAudience);

  return (
    <section className="campaign-summary-section" aria-labelledby="summary-heading">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none',
          marginBottom: isExpanded ? '12px' : '0px',
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-header-label" id="summary-heading" style={{ marginBottom: 0 }}>
          TARGET AUDIENCES &amp; CREATIVE MATRIX
        </div>
        <button
          type="button"
          className="btn-toggle-json"
          style={{ padding: '4px 12px', fontSize: '11px', backgroundColor: '#0B131B', border: '1px solid #1C2D3D', borderRadius: '4px', color: '#00D2FF', cursor: 'pointer' }}
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
        >
          {isExpanded ? '▲ Collapse' : '▼ Expand'}
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="summary-banner">

        <div className="summary-formula-box">
          <div className="summary-formula-main">
            <span className="formula-part highlight">{audiences.length} audiences</span>
            {conceptsPerAudience > 1 && (
              <>
                <span className="formula-operator">×</span>
                <span className="formula-part highlight">{conceptsPerAudience} concepts</span>
              </>
            )}
            <span className="formula-operator">×</span>
            <span className="formula-part highlight">{formats.length} formats</span>
            <span className="formula-operator">=</span>
            <span className="formula-total">{totalOutputs} Target Ads</span>
          </div>
          <div className="summary-formula-note">
            Configured Campaign Matrix • {conceptsPerAudience} concept{conceptsPerAudience > 1 ? 's' : ''} per audience mapped across all {formats.length} aspect ratios
          </div>
        </div>



        {/* Aspect Ratio Formats Pills */}
        <div className="formats-strip">
          <span className="strip-title">Target Formats:</span>
          {formats.map((fmt) => (
            <div key={fmt.id || fmt.aspectRatio} className="format-badge">
              <span className="format-ratio">{fmt.aspectRatio}</span>
              <span className="format-dim">{fmt.width}×{fmt.height}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Audience Group Cards Grid */}
      <div className="audience-grid" role="list" aria-label="Audience persona segments">
        {audiences.map((aud, index) => {
          const isOrange = aud.productColor === 'orange' || aud.age.maximum <= 24;
          const isBeach = aud.activity === 'beach';
          return (
            <div key={aud.id || index} className="audience-card" role="listitem">
              <div className="audience-card-header">
                <span className="audience-id-pill">{aud.id}</span>
                <span className="audience-name">{aud.name}</span>
              </div>
              <div className="audience-details">
                <div className="detail-row">
                  <span className="detail-key">Age Band:</span>
                  <span className="detail-val">{aud.age.minimum}–{aud.age.maximum} yrs ({aud.age.band || (isOrange ? 'younger' : 'older')})</span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Activity:</span>
                  <span className="detail-val capitalize">{aud.activity}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Territory:</span>
                  <span className="detail-val">{aud.territory}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Product:</span>
                  <span className="detail-val">
                    <span className={`product-swatch ${isOrange ? 'swatch-orange' : 'swatch-white'}`} />
                    {isOrange ? 'Orange Cooler' : 'White Cooler'} ({aud.productModel})
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Tagline:</span>
                  <span className="detail-val">
                    <span className={`tagline-swatch ${isBeach ? 'swatch-black-text' : 'swatch-white-text'}`}>
                      {isBeach ? 'Black copy' : 'White copy'}
                    </span>
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Outputs:</span>
                  <span className="detail-val" style={{ color: '#00D2FF', fontFamily: 'var(--font-mono)', fontWeight: 'bold' }}>
                    {conceptsPerAudience * formats.length} ads {conceptsPerAudience > 1 ? `(${conceptsPerAudience} vars × ${formats.length} formats)` : `(${formats.map((f: any) => f.aspectRatio).join(', ')})`}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
        </>
      )}
    </section>
  );
};

