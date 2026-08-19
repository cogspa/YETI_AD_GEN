import React from 'react';

interface GenerateActionProps {
  isValid: boolean;
  totalOutputs: number;
  isGenerating?: boolean;
  onGenerateClick?: () => void;
}

export const GenerateAction: React.FC<GenerateActionProps> = ({
  isValid,
  totalOutputs,
  isGenerating = false,
  onGenerateClick,
}) => {
  return (
    <section className="generate-action-section" aria-label="Campaign generation trigger">
      <button
        type="button"
        className="btn-generate"
        disabled={!isValid || isGenerating}
        onClick={onGenerateClick}
        aria-describedby="generate-subtext"
      >
        <span className="btn-generate-main">
          {isGenerating ? 'GENERATING ADS...' : 'GENERATE ADS'}
        </span>
        <span id="generate-subtext" className="btn-generate-sub">
          Deterministic multi-format adaptation across target aspect ratios
        </span>
      </button>
    </section>



  );
};

