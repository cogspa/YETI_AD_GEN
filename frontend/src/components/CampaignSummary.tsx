import React from 'react';
import type { CampaignBrief } from '../types/campaign';

interface CampaignSummaryProps {
  brief: CampaignBrief;
}

export const CampaignSummary: React.FC<CampaignSummaryProps> = ({ brief }) => {
  const audiences = brief.audiences || [];
  const formats = brief.outputFormats || [];
  const conceptsPerAudience = brief.generation?.conceptsPerAudience || 1;
  const totalOutputs = brief.generation?.totalOutputsPerRun || (audiences.length * formats.length * conceptsPerAudience);

  return (
    <section className="campaign-summary-section" aria-labelledby="summary-heading">
      <div className="section-header-label" id="summary-heading">
        CAMPAIGN MATRIX &amp; AUDIENCE SEGMENTS
      </div>

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
            <span className="formula-total">{totalOutputs} outputs</span>
          </div>
          <div className="summary-formula-note">
            Fixed deterministic workflow • {conceptsPerAudience} concept{conceptsPerAudience > 1 ? 's' : ''} per audience adapted across all {formats.length} aspect ratios
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
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
