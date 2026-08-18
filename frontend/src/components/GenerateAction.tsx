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
          {isGenerating ? 'GENERATING 18 ADS...' : `GENERATE ${totalOutputs} ADS`}
        </span>
        <span id="generate-subtext" className="btn-generate-sub">
          Six concepts adapted to three formats (1:1, 16:9, 9:16)
        </span>
      </button>
    </section>
  );
};

