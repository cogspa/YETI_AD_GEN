import React from 'react';

interface ContactSheetModalProps {
  isOpen: boolean;
  contactSheetUrl: string | null;
  campaignName: string;
  runId: string;
  onClose: () => void;
}

export const ContactSheetModal: React.FC<ContactSheetModalProps> = ({
  isOpen,
  contactSheetUrl,
  campaignName,
  runId,
  onClose,
}) => {
  if (!isOpen || !contactSheetUrl) return null;

  return (
    <div className="modal-overlay-bg" onClick={onClose}>
      <div
        className="modal-dialog-box"
        style={{ maxWidth: '1100px', height: '90vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header-bar">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#00D2FF', fontFamily: 'var(--font-mono)', fontWeight: 'bold', letterSpacing: '0.1em' }}>YETI</span>
              <h2 style={{ color: '#FFFFFF', fontSize: '18px', fontWeight: '800' }}>Campaign Contact Sheet (18 Ads)</h2>
            </div>
            <p style={{ color: '#7E93A7', fontSize: '11px', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
              {campaignName} | Run: {runId} | 6 Audiences × 3 Ratios (1:1, 16:9, 9:16)
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <a
              href={contactSheetUrl}
              download="yeti_campaign_contact_sheet.jpg"
              className="btn-zip-download"
              style={{ padding: '6px 14px', fontSize: '11px' }}
            >
              📥 Download JPG
            </a>
            <button onClick={onClose} className="modal-close-btn">
              Close
            </button>
          </div>
        </div>

        {/* High-res Image Scrollable Area */}
        <div className="modal-content-area" style={{ backgroundColor: '#05090E', display: 'flex', justifyContent: 'center', alignItems: 'flex-start' }}>
          <img
            src={contactSheetUrl}
            alt="YETI Campaign Contact Sheet"
            style={{ maxWidth: '100%', height: 'auto', borderRadius: '6px', boxShadow: '0 10px 40px rgba(0, 0, 0, 0.8)' }}
          />
        </div>
      </div>
    </div>
  );
};
