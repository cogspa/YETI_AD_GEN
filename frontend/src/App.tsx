import React, { useState, useMemo } from 'react';
import { Header } from './components/Header';
import { BriefUploadSection } from './components/BriefUploadSection';
import { CampaignSummary } from './components/CampaignSummary';
import { AssetReadiness } from './components/AssetReadiness';
import { IntegrationStatus } from './components/IntegrationStatus';
import { GenerateAction } from './components/GenerateAction';
import { YETI_GO_ANYWHERE_2026_BRIEF, SAMPLE_BRIEFS } from './data/sampleBriefs';
import { validateBrief } from './utils/validation';
import type { CampaignBrief } from './types/campaign';

export const App: React.FC = () => {
  const [currentBrief, setCurrentBrief] = useState<CampaignBrief>(YETI_GO_ANYWHERE_2026_BRIEF);
  const [currentFilename, setCurrentFilename] = useState<string>('yeti-la-go-anywhere-2026.json');
  const [fileSizeBytes, setFileSizeBytes] = useState<number>(() => {
    return new Blob([JSON.stringify(YETI_GO_ANYWHERE_2026_BRIEF)]).size;
  });

  const validation = useMemo(() => {
    return validateBrief(currentBrief);
  }, [currentBrief]);

  const handleBriefChange = (newBrief: CampaignBrief, filename: string, sizeBytes: number) => {
    setCurrentBrief(newBrief);
    setCurrentFilename(filename);
    setFileSizeBytes(sizeBytes);
  };

  const handleReset = () => {
    const defaultSample = SAMPLE_BRIEFS[0];
    const size = new Blob([JSON.stringify(defaultSample.brief)]).size;
    setCurrentBrief(defaultSample.brief);
    setCurrentFilename(defaultSample.filename);
    setFileSizeBytes(size);
  };

  return (
    <main className="app-viewport">
      <div className="app-column">
        {/* 1. Brand Header */}
        <Header />

        {/* 2. Campaign Brief (JSON) */}
        <BriefUploadSection
          currentBrief={currentBrief}
          currentFilename={currentFilename}
          fileSizeBytes={fileSizeBytes}
          validation={validation}
          onBriefChange={handleBriefChange}
          onReset={handleReset}
        />

        {/* 3. Campaign Summary (6 audiences × 3 formats = 18 outputs) */}
        <CampaignSummary brief={currentBrief} />

        {/* 4. Asset Readiness */}
        <AssetReadiness />

        {/* 5. Integration Status */}
        <IntegrationStatus />

        {/* 6. Generate Action Button */}
        <GenerateAction
          isValid={validation.isValid}
          totalOutputs={validation.totalOutputs}
        />
      </div>
    </main>
  );
};

export default App;
