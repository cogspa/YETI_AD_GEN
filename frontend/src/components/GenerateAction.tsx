import React, { useState } from 'react';

interface GenerateActionProps {
  isValid: boolean;
  totalOutputs: number;
  onGenerateClick?: () => void;
}

export const GenerateAction: React.FC<GenerateActionProps> = ({
  isValid,
  totalOutputs,
  onGenerateClick,
}) => {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleClick = () => {
    if (!isValid) return;
    setStatusMessage('UI ready — connect pipeline next.');
    if (onGenerateClick) {
      onGenerateClick();
    }
  };

  return (
    <section className="generate-action-section" aria-label="Campaign generation trigger">
      <button
        type="button"
        className="btn-generate"
        disabled={!isValid}
        onClick={handleClick}
        aria-describedby="generate-subtext"
      >
        <span className="btn-generate-main">GENERATE {totalOutputs} ADS</span>
        <span id="generate-subtext" className="btn-generate-sub">
          Six concepts adapted to three formats
        </span>
      </button>

      {statusMessage && (
        <div className="status-announcement" role="status" aria-live="polite">
          <div className="announcement-badge">Info</div>
          <span>{statusMessage}</span>
        </div>
      )}
    </section>
  );
};
