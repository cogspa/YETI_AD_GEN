import React, { useEffect, useState } from 'react';
import { fetchAssetReadiness } from '../services/api';
import type { AssetReadinessReport } from '../services/api';

export interface AssetDisplayItem {
  category: 'Products' | 'Backgrounds' | 'Taglines' | 'Brand & Typography' | 'Layout Reference';
  name: string;
  location: string;
  status: 'local' | 'cached_from_dropbox' | 'dropbox_available' | 'missing_gemini_eligible' | 'missing_blocking';
  dimensions?: string;
  isBlocking: boolean;
  sha256Prefix?: string;
}

const DEFAULT_FALLBACK_ITEMS: AssetDisplayItem[] = [
  { category: 'Products', name: 'Roadie / Tundra (Orange)', location: 'assets/products/cooler_orange.png', status: 'local', dimensions: '1254×1254', isBlocking: true },
  { category: 'Products', name: 'Roadie / Tundra (White)', location: 'assets/products/cooler_white.png', status: 'local', dimensions: '1254×1254', isBlocking: true },
  { category: 'Backgrounds', name: 'Beach Environment', location: 'assets/backgrounds/Beach.jpg', status: 'local', dimensions: '4000×2667', isBlocking: false },
  { category: 'Backgrounds', name: 'Camping Environment', location: 'assets/backgrounds/Camping.jpg', status: 'local', dimensions: '4000×2667', isBlocking: false },
  { category: 'Backgrounds', name: 'Tailgate Environment', location: 'assets/backgrounds/Tailgate.jpg', status: 'local', dimensions: '4000×2667', isBlocking: false },
  { category: 'Taglines', name: 'Tagline Overlay (Black)', location: 'assets/taglines/TAGLINE_black.png', status: 'local', dimensions: '1080×1080', isBlocking: true },
  { category: 'Taglines', name: 'Tagline Overlay (White)', location: 'assets/taglines/TAGLINE_white.png', status: 'local', dimensions: '1080×1080', isBlocking: true },
  { category: 'Brand & Typography', name: 'Official YETI Vector Logo', location: 'assets/brand/Yeti_Logo_1.png', status: 'local', dimensions: '640×180', isBlocking: true },
  { category: 'Brand & Typography', name: 'DejaVuSans-Bold Font', location: 'assets/fonts/DejaVuSans-Bold.ttf', status: 'local', isBlocking: true },
];

export const AssetReadiness: React.FC = () => {
  const [report, setReport] = useState<AssetReadinessReport | null>(null);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    fetchAssetReadiness().then((data) => {
      if (isMounted && data) {
        setReport(data);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'local':
        return 'Local Verified';
      case 'cached_from_dropbox':
        return 'Dropbox Cached';
      case 'dropbox_available':
        return 'Dropbox Available';
      case 'missing_gemini_eligible':
        return 'Gemini Fallback';
      case 'missing_blocking':
        return 'Missing (Blocking)';
      default:
        return status;
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'local':
      case 'cached_from_dropbox':
        return 'status-local';
      case 'dropbox_available':
        return 'status-dropbox';
      case 'missing_gemini_eligible':
        return 'status-gemini-fallback-available';
      case 'missing_blocking':
        return 'status-blocking';
      default:
        return 'status-local';
    }
  };

  const displayItems = report
    ? Object.entries(report.assets).map(([role, info]) => {
        let category: AssetDisplayItem['category'] = 'Products';
        let name = role;
        if (role.startsWith('product_')) {
          category = 'Products';
          name = role === 'product_orange' ? 'Roadie / Tundra (Orange)' : 'Roadie / Tundra (White)';
        } else if (role.startsWith('background_')) {
          category = 'Backgrounds';
          name = role.replace('background_', '').charAt(0).toUpperCase() + role.replace('background_', '').slice(1) + ' Environment';
        } else if (role.startsWith('tagline_')) {
          category = 'Taglines';
          name = 'Tagline Overlay (' + (role.includes('black') ? 'Black' : 'White') + ')';
        } else if (role.startsWith('brand_') || role.startsWith('font_')) {
          category = 'Brand & Typography';
          name = role === 'brand_logo' ? 'Official YETI Vector Logo' : (role === 'font_bold' ? 'DejaVuSans-Bold Font' : 'DejaVuSans Font');
        } else if (role.startsWith('layout_')) {
          category = 'Layout Reference';
          name = 'Layout Reference ' + role.replace('layout_reference_', '');
        }

        return {
          category,
          name,
          location: info.resolved_path,
          status: info.status,
          dimensions: info.dimensions ? `${info.dimensions[0]}×${info.dimensions[1]}` : undefined,
          isBlocking: info.is_blocking,
          sha256Prefix: info.sha256_hash ? info.sha256_hash.substring(0, 8) : undefined,
        };
      }).filter(item => item.category !== 'Layout Reference') // Focus primary asset checklist
    : DEFAULT_FALLBACK_ITEMS;

  return (
    <section className="asset-readiness-section" aria-labelledby="assets-heading">
      <div
        className="section-header-row"
        style={{ cursor: 'pointer', userSelect: 'none', marginBottom: isExpanded ? '14px' : '0px' }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="section-header-label" id="assets-heading" style={{ marginBottom: 0 }}>
            ASSET READINESS &amp; RESOLVER REPORT
          </div>
          {report && (
            <span className="badge-readiness-summary">
              {report.is_ready_to_generate ? '✓ All Assets Ready' : `⚠️ ${report.blocking_missing_count} Blocking Missing`}
            </span>
          )}
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
        <div className="asset-checklist-panel">
          <div className="asset-grid">
            {displayItems.map((item, idx) => (
              <div key={idx} className="asset-item-card">
                <div className="asset-item-header">
                  <span className="asset-category-pill">{item.category}</span>
                  <span className={`asset-status-pill ${getStatusClass(item.status)}`}>
                    <span className="status-dot" />
                    {getStatusLabel(item.status)}
                  </span>
                </div>
                <div className="asset-item-name">{item.name}</div>
                <div className="asset-item-meta-row">
                  <span className="asset-item-path" title={item.location}>{item.location}</span>
                  {item.dimensions && <span className="asset-item-dim">{item.dimensions}</span>}
                </div>
                {item.sha256Prefix && (
                  <div className="asset-item-sha">SHA: {item.sha256Prefix}…</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};
