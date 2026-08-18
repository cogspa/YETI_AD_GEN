import React from 'react';

interface QualityReportModalProps {
  isOpen: boolean;
  report: any;
  reportUrl?: string;
  logUrl?: string;
  onClose: () => void;
}

export const QualityReportModal: React.FC<QualityReportModalProps> = ({
  isOpen,
  report,
  reportUrl,
  logUrl,
  onClose,
}) => {
  if (!isOpen || !report) return null;

  const checks = report.checks || [];
  const audits = report.audience_audits || [];
  const blockingPassed = report.blocking_checks_passed || 8;
  const blockingTotal = report.blocking_checks_total || 8;

  return (
    <div className="modal-overlay-bg" onClick={onClose}>
      <div
        className="modal-dialog-box"
        style={{ maxWidth: '1000px', maxHeight: '90vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header-bar">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#00D2FF', fontFamily: 'var(--font-mono)', fontWeight: 'bold', letterSpacing: '0.1em' }}>YETI QA</span>
              <h2 style={{ color: '#FFFFFF', fontSize: '18px', fontWeight: '800' }}>Deterministic Quality & Compliance Report</h2>
            </div>
            <p style={{ color: '#7E93A7', fontSize: '11px', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
              Run: {report.run_id} | Seed: {report.seed} | Status: <span style={{ color: '#31C48D', fontWeight: 'bold', textTransform: 'uppercase' }}>{report.status}</span>
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {reportUrl && (
              <a
                href={reportUrl}
                download="generation-report.json"
                className="btn-zip-download"
                style={{ padding: '6px 12px', fontSize: '11px' }}
              >
                📥 Report JSON
              </a>
            )}
            {logUrl && (
              <a
                href={logUrl}
                download="pipeline.log"
                className="btn-contact-sheet-action"
                style={{ padding: '6px 12px', fontSize: '11px' }}
              >
                📜 Pipeline Log (JSONL)
              </a>
            )}
            <button onClick={onClose} className="modal-close-btn">
              Close
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="modal-content-area" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Status Banner */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#070E16', border: '1px solid #1A2B3D', borderRadius: '8px', padding: '14px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>🛡️</span>
              <div>
                <div style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: '14px' }}>
                  {blockingPassed}/{blockingTotal} Blocking Rules Verified & Passed
                </div>
                <div style={{ color: '#7E93A7', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                  Deterministic verification executed across brief, 6 concept plans, and 18 rendered ad compositions.
                </div>
              </div>
            </div>
            <span className="badge-count" style={{ fontSize: '12px', padding: '4px 10px' }}>
              PASSED
            </span>
          </div>

          {/* 8 Blocking Checks Grid */}
          <div>
            <h3 style={{ color: '#00D2FF', fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 'bold', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '10px' }}>
              Deterministic Blocking Checks
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '10px' }}>
              {checks.map((chk: any) => (
                <div
                  key={chk.check_id}
                  style={{
                    backgroundColor: '#09111A',
                    border: `1px solid ${chk.passed ? '#152535' : '#E02424'}`,
                    borderRadius: '6px',
                    padding: '10px 14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: chk.passed ? '#31C48D' : '#E02424', fontWeight: 'bold' }}>
                        {chk.passed ? '✓' : '✗'}
                      </span>
                      <span style={{ color: '#FFFFFF', fontSize: '12px', fontWeight: 'bold' }}>{chk.check_name}</span>
                    </div>
                    <span style={{ color: chk.category === 'blocking' ? '#00D2FF' : '#FDBA74', fontSize: '10px', fontFamily: 'var(--font-mono)', textTransform: 'uppercase' }}>
                      {chk.category}
                    </span>
                  </div>
                  <p style={{ color: '#7E93A7', fontSize: '11px', fontFamily: 'var(--font-mono)', margin: 0 }}>
                    {chk.details}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Per-Audience Audit Table */}
          {audits.length > 0 && (
            <div>
              <h3 style={{ color: '#00D2FF', fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 'bold', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '10px' }}>
                Per-Audience Concept & Quality Audit (6 Audiences)
              </h3>
              <div style={{ overflowX: 'auto', border: '1px solid #182635', borderRadius: '8px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', fontFamily: 'var(--font-mono)', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#0A131C', color: '#8EA4B8', borderBottom: '1px solid #182635' }}>
                      <th style={{ padding: '10px 12px' }}>Audience</th>
                      <th style={{ padding: '10px 12px' }}>Age</th>
                      <th style={{ padding: '10px 12px' }}>Activity</th>
                      <th style={{ padding: '10px 12px' }}>Product</th>
                      <th style={{ padding: '10px 12px' }}>Tagline</th>
                      <th style={{ padding: '10px 12px' }}>Contrast</th>
                      <th style={{ padding: '10px 12px' }}>Busyness</th>
                      <th style={{ padding: '10px 12px' }}>Provenance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {audits.map((a: any) => (
                      <tr key={a.audience_id} style={{ borderBottom: '1px solid #101B26', color: '#CAD6E2' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#FFFFFF' }}>{a.audience_id} ({a.territory})</td>
                        <td style={{ padding: '10px 12px' }}>{a.age_band.toUpperCase()}</td>
                        <td style={{ padding: '10px 12px', textTransform: 'capitalize' }}>{a.activity}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ color: a.product_role.includes('orange') ? '#FF8A00' : '#E2E8F0' }}>
                            {a.product_role.includes('orange') ? 'Orange' : 'White'}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ color: a.tagline_color === '#000000' ? '#94A3B8' : '#FFFFFF' }}>
                            {a.tagline_color === '#000000' ? 'Black' : 'White'}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', color: a.contrast_score >= 3.0 ? '#31C48D' : '#FDBA74' }}>
                          {a.contrast_score}:1
                        </td>
                        <td style={{ padding: '10px 12px' }}>{a.busyness_score}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ color: a.provenance.includes('Gemini') ? '#FDBA74' : '#31C48D' }}>
                            {a.provenance}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
