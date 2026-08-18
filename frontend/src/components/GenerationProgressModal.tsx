import React from 'react';

interface GenerationProgressModalProps {
  isOpen: boolean;
  currentStage: string;
  progressPct: number;
  completedItems: number;
  totalItems: number;
  error?: string | null;
  onClose?: () => void;
}

const STAGES = [
  'Validating JSON',
  'Resolving controlled assets',
  'Reading repeat history',
  'Selecting six concepts',
  'Generating missing backgrounds if needed',
  'Rendering 18 adaptations',
  'Running checks',
  'Uploading to Dropbox',
  'Complete',
];

export const GenerationProgressModal: React.FC<GenerationProgressModalProps> = ({
  isOpen,
  currentStage,
  progressPct,
  completedItems,
  totalItems = 18,
  error,
  onClose,
}) => {
  if (!isOpen) return null;

  const currentStageIndex = STAGES.indexOf(currentStage);

  return (
    <div className="modal-overlay-bg">
      <div className="modal-dialog-box" style={{ maxWidth: '540px', padding: '24px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#00D2FF', fontFamily: 'var(--font-mono)', fontWeight: 'bold', fontSize: '18px', letterSpacing: '0.1em' }}>YETI</span>
            <span style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: '16px' }}>Generating 18 Ads</span>
          </div>
          {currentStage === 'Complete' && (
            <span className="badge-count" style={{ fontSize: '11px' }}>READY</span>
          )}
        </div>

        {/* Counter */}
        <div style={{ textAlign: 'center', margin: '20px 0' }}>
          <div style={{ fontSize: '36px', fontWeight: '800', fontFamily: 'var(--font-mono)', color: '#FFFFFF', letterSpacing: '0.05em' }}>
            {completedItems} <span style={{ color: '#5E7387', fontSize: '22px' }}>/ {totalItems}</span>
          </div>
          <p style={{ color: '#00D2FF', fontSize: '13px', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
            {error ? 'Generation Encountered an Error' : currentStage}
          </p>
        </div>

        {/* Progress Bar */}
        <div style={{ width: '100%', height: '10px', backgroundColor: '#111D29', borderRadius: '8px', border: '1px solid #1C2E40', overflow: 'hidden', marginBottom: '20px' }}>
          <div
            style={{
              height: '100%',
              width: `${Math.max(5, Math.min(100, progressPct))}%`,
              background: error ? '#E02424' : 'linear-gradient(90deg, #00A3FF, #00D2FF)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>

        {/* Stage Steps List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto', marginBottom: '20px' }}>
          {STAGES.map((stg, idx) => {
            const isDone = currentStageIndex > idx || currentStage === 'Complete';
            const isCurrent = currentStage === stg;

            return (
              <div
                key={stg}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  backgroundColor: isCurrent ? '#142433' : isDone ? '#0E1720' : '#070C12',
                  color: isCurrent ? '#00D2FF' : isDone ? '#CAD6E2' : '#4E6375',
                  border: isCurrent ? '1px solid rgba(0, 210, 255, 0.4)' : '1px solid transparent',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>{isDone ? '✓' : isCurrent ? '▶' : '○'}</span>
                  <span>{stg}</span>
                </div>
                {isCurrent && stg === 'Rendering 18 adaptations' && (
                  <span style={{ color: '#FF8A00', fontWeight: 'bold' }}>{completedItems}/18</span>
                )}
                {isDone && <span style={{ color: '#5E7387' }}>Done</span>}
              </div>
            );
          })}
        </div>

        {/* Error message */}
        {error && (
          <div style={{ backgroundColor: 'rgba(224, 36, 36, 0.15)', border: '1px solid #E02424', color: '#FCA5A5', padding: '10px 14px', borderRadius: '8px', fontSize: '12px', marginBottom: '16px', fontFamily: 'var(--font-mono)' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Action button */}
        {(currentStage === 'Complete' || error) && (
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={onClose}
              className="btn-zip-download"
              style={{ cursor: 'pointer', border: 'none' }}
            >
              {error ? 'Close' : 'View Generated Campaign'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
