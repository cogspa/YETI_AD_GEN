import React, { useEffect, useState } from 'react';
import { fetchIntegrationStatus, type IntegrationStatusResponse } from '../services/api';

export const IntegrationStatus: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [status, setStatus] = useState<IntegrationStatusResponse | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchIntegrationStatus().then((data) => {
      if (isMounted && data) {
        setStatus(data);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const isGeminiActive = status?.gemini?.configured;
  const isDropboxActive = status?.storage?.mode === 'dropbox' && status.storage.configured;

  return (
    <section className="integration-section" aria-labelledby="integrations-heading">
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="section-header-label" id="integrations-heading" style={{ marginBottom: 0 }}>
            SYSTEM &amp; AI INTEGRATIONS
          </div>
          <span style={{ fontSize: '11px', color: isGeminiActive ? '#00E599' : '#8A9CAE' }}>
            {isGeminiActive ? '● Gemini Imagen 3 Connected' : '○ Gemini Standby (Procedural Fallback)'}
          </span>
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
                  <span className="integration-name">Storage Provider</span>
                </div>
                <span className={isDropboxActive ? "badge-connected" : "badge-connected"}>
                  {isDropboxActive ? "Active (Dropbox App Folder)" : "Active (Local Storage)"}
                </span>
              </div>
              <div className="integration-desc">
                {isDropboxActive ? (
                  <>Artifacts, contact sheets, and reports sync directly to Dropbox path <code>{status?.storage?.root || '/yeti-ad-generator'}</code>.</>
                ) : (
                  <>Source assets are verified from local storage. Output directory configured to <code>{status?.storage?.root || '/outputs'}</code>.</>
                )}
              </div>
            </div>

            {/* Gemini AI status */}
            <div className="integration-card">
              <div className="integration-card-top">
                <div className="integration-title-group">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                  </svg>
                  <span className="integration-name">Google Gemini Scene Provider ({status?.gemini?.model || 'imagen-3.0-generate-002'})</span>
                </div>
                <span className={isGeminiActive ? "badge-connected" : "badge-standby"}>
                  {isGeminiActive ? "Active (AI Ready)" : "Standby (Procedural Fallback)"}
                </span>
              </div>
              <div className="integration-desc">
                {isGeminiActive ? (
                  <>Gemini Imagen is connected. If any audience demographic has an activity or territory without an existing background image, Gemini will automatically generate a photorealistic, guardrailed outdoor landscape on the fly.</>
                ) : (
                  <>Provide <code>GEMINI_API_KEY</code> in your <code>.env</code> file to enable Google Imagen background synthesis. When unconfigured, missing backgrounds use high-quality deterministic procedural lighting.</>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};


