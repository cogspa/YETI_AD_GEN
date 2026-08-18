import React from 'react';

export const IntegrationStatus: React.FC = () => {
  return (
    <section className="integration-section" aria-labelledby="integrations-heading">
      <div className="section-header-label" id="integrations-heading">
        SYSTEM &amp; AI INTEGRATIONS
      </div>

      <div className="integrations-panel">
        <div className="integration-cards">
          {/* Storage / Dropbox status */}
          <div className="integration-card">
            <div className="integration-card-top">
              <div className="integration-title-group">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0072B2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                  <line x1="12" y1="22.08" x2="12" y2="12" />
                </svg>
                <span className="integration-name">Local Storage / Dropbox Adapter</span>
              </div>
              <span className="badge-connected">Active (Local)</span>
            </div>
            <div className="integration-desc">
              Source assets are verified from local storage. Output directory configured to <code>/outputs/yeti-la-go-anywhere-2026</code>.
            </div>
          </div>

          {/* Gemini AI status */}
          <div className="integration-card">
            <div className="integration-card-top">
              <div className="integration-title-group">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
                <span className="integration-name">Gemini AI Scene Provider</span>
              </div>
              <span className="badge-standby">Standby (Fallback)</span>
            </div>
            <div className="integration-desc">
              Gemini GenAI is configured strictly as a fallback provider for missing contextual backgrounds. Required assets exist locally, so a standard run executes with zero external AI calls.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
