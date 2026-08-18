import React from 'react';
import type { GeneratedAdArtifact } from '../services/api';

interface LightboxModalProps {
  ad: GeneratedAdArtifact | null;
  onClose: () => void;
}

export const LightboxModal: React.FC<LightboxModalProps> = ({ ad, onClose }) => {
  if (!ad) return null;

  return (
    <div className="modal-overlay-bg" onClick={onClose}>
      <div
        className="modal-dialog-box"
        style={{ maxWidth: '960px', padding: '24px', display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: '24px' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="modal-close-btn"
          style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10 }}
        >
          ✕
        </button>

        {/* Image Preview Container */}
        <div style={{ flex: '1 1 400px', backgroundColor: '#05090E', borderRadius: '8px', border: '1px solid #14202C', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '340px' }}>
          <img
            src={ad.preview_url}
            alt={ad.filename}
            style={{ maxHeight: '65vh', maxWidth: '100%', objectFit: 'contain', borderRadius: '4px', boxShadow: '0 8px 30px rgba(0, 0, 0, 0.8)' }}
          />
        </div>

        {/* Ad Details & Download Sidebar */}
        <div style={{ flex: '0 0 300px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span className="badge-run-id">{ad.audience_id}</span>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#7E93A7' }}>
                {ad.aspect_ratio} ({ad.dimensions[0]}×{ad.dimensions[1]})
              </span>
            </div>

            <h3 style={{ color: '#FFFFFF', fontSize: '18px', fontWeight: '800', marginBottom: '4px' }}>{ad.audience_name}</h3>
            <p style={{ fontSize: '11px', color: '#5E7387', fontFamily: 'var(--font-mono)', marginBottom: '16px' }}>{ad.filename}</p>

            <div style={{ backgroundColor: '#0E1721', border: '1px solid #1C2B3A', borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#CAD6E2' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#5E7387' }}>Activity:</span>
                <span style={{ color: '#00D2FF', textTransform: 'capitalize' }}>{ad.activity}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#5E7387' }}>Territory:</span>
                <span>{ad.territory}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#5E7387' }}>Age Band:</span>
                <span style={{ textTransform: 'uppercase' }}>{ad.age_band}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#5E7387' }}>Product:</span>
                <span style={{ textTransform: 'capitalize' }}>{ad.product_color} Cooler</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#5E7387' }}>File Size:</span>
                <span>{Math.round(ad.filesize_bytes / 1024)} KB</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#5E7387' }}>Background:</span>
                <span style={{ color: ad.background_source === 'approved_asset' ? '#31C48D' : '#FDBA74' }}>
                  {ad.background_source === 'approved_asset' ? 'Approved Asset' : 'AI Generated'}
                </span>
              </div>
            </div>

            {ad.human_review_required && (
              <div style={{ marginTop: '12px', padding: '10px', backgroundColor: 'rgba(234, 88, 12, 0.15)', border: '1px solid #EA580C', borderRadius: '8px', color: '#FDBA74', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                ⚠️ <strong>Human Review Required:</strong> AI scene background variant.
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '16px' }}>
            <a
              href={ad.preview_url}
              download={ad.filename}
              className="btn-zip-download"
              style={{ justifyContent: 'center' }}
            >
              <span>📥 Download PNG</span>
            </a>
            <button onClick={onClose} className="modal-close-btn" style={{ width: '100%', padding: '10px' }}>
              Close Preview
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
