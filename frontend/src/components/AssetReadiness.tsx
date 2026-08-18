import React from 'react';

export interface AssetStatusItem {
  category: 'Products' | 'Backgrounds' | 'Taglines' | 'Brand & Typography';
  name: string;
  location: string;
  status: 'Local' | 'Dropbox' | 'Missing' | 'Gemini fallback available';
  isReady: boolean;
}

export const ASSET_CHECKLIST: AssetStatusItem[] = [
  { category: 'Products', name: 'Roadie / Tundra (Orange)', location: 'assets/products/cooler_orange.png', status: 'Local', isReady: true },
  { category: 'Products', name: 'Roadie / Tundra (White)', location: 'assets/products/cooler_white.png', status: 'Local', isReady: true },
  { category: 'Backgrounds', name: 'Beach Environment', location: 'assets/backgrounds/Beach.jpg', status: 'Local', isReady: true },
  { category: 'Backgrounds', name: 'Camping Environment', location: 'assets/backgrounds/Camping.jpg', status: 'Local', isReady: true },
  { category: 'Backgrounds', name: 'Tailgate Environment', location: 'assets/backgrounds/Tailgate.jpg', status: 'Local', isReady: true },
  { category: 'Taglines', name: 'Tagline Overlay (Black)', location: 'assets/taglines/TAGLINE_black.png', status: 'Local', isReady: true },
  { category: 'Taglines', name: 'Tagline Overlay (White)', location: 'assets/taglines/TAGLINE_white.png', status: 'Local', isReady: true },
  { category: 'Brand & Typography', name: 'Official YETI Vector Logo', location: 'assets/brand/Yeti_Logo_1.png', status: 'Local', isReady: true },
  { category: 'Brand & Typography', name: 'DejaVuSans-Bold Font', location: 'assets/fonts/DejaVuSans-Bold.ttf', status: 'Local', isReady: true },
];

export const AssetReadiness: React.FC = () => {
  return (
    <section className="asset-readiness-section" aria-labelledby="assets-heading">
      <div className="section-header-label" id="assets-heading">
        ASSET READINESS CHECK
      </div>

      <div className="asset-checklist-panel">
        <div className="asset-grid">
          {ASSET_CHECKLIST.map((item, idx) => (
            <div key={idx} className="asset-item-card">
              <div className="asset-item-header">
                <span className="asset-category-pill">{item.category}</span>
                <span className={`asset-status-pill status-${item.status.toLowerCase().replace(/\s+/g, '-')}`}>
                  <span className="status-dot" />
                  {item.status}
                </span>
              </div>
              <div className="asset-item-name">{item.name}</div>
              <div className="asset-item-path" title={item.location}>{item.location}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
