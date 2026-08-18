import React, { useState, useMemo, useEffect } from 'react';
import { Header } from './components/Header';
import { BriefUploadSection } from './components/BriefUploadSection';
import { CampaignSummary } from './components/CampaignSummary';
import { AssetReadiness } from './components/AssetReadiness';
import { IntegrationStatus } from './components/IntegrationStatus';
import { GenerateAction } from './components/GenerateAction';
import { GenerationProgressModal } from './components/GenerationProgressModal';
import { CampaignResultsView } from './components/CampaignResultsView';
import { LightboxModal } from './components/LightboxModal';
import { ContactSheetModal } from './components/ContactSheetModal';
import { QualityReportModal } from './components/QualityReportModal';
import { YETI_GO_ANYWHERE_2026_BRIEF, SAMPLE_BRIEFS } from './data/sampleBriefs';

import { validateBrief } from './utils/validation';
import {
  generateCampaignAds,
  type CampaignBrief,
  type CampaignRunResult,
  type GeneratedAdArtifact,
} from './services/api';

export const App: React.FC = () => {
  const [currentBrief, setCurrentBrief] = useState<CampaignBrief>(YETI_GO_ANYWHERE_2026_BRIEF);
  const [currentFilename, setCurrentFilename] = useState<string>('yeti-la-go-anywhere-2026.json');
  const [fileSizeBytes, setFileSizeBytes] = useState<number>(() => {
    return new Blob([JSON.stringify(YETI_GO_ANYWHERE_2026_BRIEF)]).size;
  });

  // Generation State
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [showProgressModal, setShowProgressModal] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<string>('Validating JSON');
  const [progressPct, setProgressPct] = useState<number>(0);
  const [completedItems, setCompletedItems] = useState<number>(0);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Results State
  const [campaignResult, setCampaignResult] = useState<CampaignRunResult | null>(null);
  const [selectedLightboxAd, setSelectedLightboxAd] = useState<GeneratedAdArtifact | null>(null);
  const [isContactSheetOpen, setIsContactSheetOpen] = useState<boolean>(false);
  const [isQualityReportOpen, setIsQualityReportOpen] = useState<boolean>(false);


  const validation = useMemo(() => {
    return validateBrief(currentBrief);
  }, [currentBrief]);

  const handleBriefChange = (newBrief: CampaignBrief, filename: string, sizeBytes: number) => {
    setCurrentBrief(newBrief);
    setCurrentFilename(filename);
    setFileSizeBytes(sizeBytes);
    // Reset prior results when brief changes
    setCampaignResult(null);
  };

  const handleReset = () => {
    const defaultSample = SAMPLE_BRIEFS[0];
    const size = new Blob([JSON.stringify(defaultSample.brief)]).size;
    setCurrentBrief(defaultSample.brief);
    setCurrentFilename(defaultSample.filename);
    setFileSizeBytes(size);
    setCampaignResult(null);
  };

  const handleGenerateClick = async () => {
    if (!validation.isValid) return;

    setIsGenerating(true);
    setShowProgressModal(true);
    setGenerationError(null);
    setProgressPct(5);
    setCurrentStage('Validating JSON');
    setCompletedItems(0);

    try {
      // Simulate live progressive stage updates during API processing
      const timer1 = setTimeout(() => {
        setCurrentStage('Resolving controlled assets');
        setProgressPct(18);
      }, 300);

      const timer2 = setTimeout(() => {
        setCurrentStage('Reading repeat history');
        setProgressPct(28);
      }, 600);

      const timer3 = setTimeout(() => {
        setCurrentStage('Selecting six concepts');
        setProgressPct(38);
      }, 900);

      const timer4 = setTimeout(() => {
        setCurrentStage('Generating missing backgrounds if needed');
        setProgressPct(48);
      }, 1200);

      const timer5 = setTimeout(() => {
        setCurrentStage('Rendering 18 adaptations');
        setProgressPct(60);
        setCompletedItems(6);
      }, 1600);

      const timer6 = setTimeout(() => {
        setCompletedItems(12);
        setProgressPct(75);
      }, 2100);

      const timer7 = setTimeout(() => {
        setCompletedItems(18);
        setCurrentStage('Running checks');
        setProgressPct(88);
      }, 2600);

      const timer8 = setTimeout(() => {
        setCurrentStage('Uploading to Dropbox');
        setProgressPct(94);
      }, 3000);

      // Call live backend endpoint
      const result = await generateCampaignAds(currentBrief);

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      clearTimeout(timer5);
      clearTimeout(timer6);
      clearTimeout(timer7);
      clearTimeout(timer8);

      setCurrentStage('Complete');
      setProgressPct(100);
      setCompletedItems(18);
      setCampaignResult(result);
    } catch (err: any) {
      setGenerationError(err.message || 'Generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="app-viewport">
      <div className={`app-column ${campaignResult ? 'results-mode' : ''}`}>
        {/* 1. Brand Header */}
        <Header />

        {/* 2. If results are active, show Campaign Results view */}
        {campaignResult ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#070C12', padding: '14px 20px', borderRadius: '10px', border: '1px solid #182533' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#00D2FF', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 'bold' }}>VIEWING ACTIVE CAMPAIGN:</span>
                <span style={{ color: '#FFFFFF', fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 'bold' }}>{campaignResult.campaign_name}</span>
              </div>
              <button
                onClick={() => setCampaignResult(null)}
                className="btn-contact-sheet-action"
                style={{ padding: '6px 14px', fontSize: '11px' }}
              >
                ← Back to Brief Config
              </button>
            </div>

            <CampaignResultsView
              result={campaignResult}
              onOpenLightbox={(ad) => setSelectedLightboxAd(ad)}
              onOpenContactSheet={() => setIsContactSheetOpen(true)}
              onOpenQualityReport={() => setIsQualityReportOpen(true)}
              onReRun={handleGenerateClick}
            />
          </div>
        ) : (
          /* Otherwise show Brief Configuration & Readiness view */
          <div className="space-y-6">
            {/* Campaign Brief (JSON) */}
            <BriefUploadSection
              currentBrief={currentBrief}
              currentFilename={currentFilename}
              fileSizeBytes={fileSizeBytes}
              validation={validation}
              onBriefChange={handleBriefChange}
              onReset={handleReset}
            />

            {/* Campaign Summary (6 audiences × 3 formats = 18 outputs) */}
            <CampaignSummary brief={currentBrief} />

            {/* Asset Readiness */}
            <AssetReadiness />

            {/* Integration Status */}
            <IntegrationStatus />

            {/* Generate Action Button */}
            <GenerateAction
              isValid={validation.isValid}
              totalOutputs={validation.totalOutputs}
              isGenerating={isGenerating}
              onGenerateClick={handleGenerateClick}
            />
          </div>
        )}

        {/* Live Generation Progress Modal */}
        <GenerationProgressModal
          isOpen={showProgressModal}
          currentStage={currentStage}
          progressPct={progressPct}
          completedItems={completedItems}
          totalItems={18}
          error={generationError}
          onClose={() => setShowProgressModal(false)}
        />

        {/* Lightbox Preview Modal */}
        <LightboxModal
          ad={selectedLightboxAd}
          onClose={() => setSelectedLightboxAd(null)}
        />

        {/* Contact Sheet Fullscreen Modal */}
        <ContactSheetModal
          isOpen={isContactSheetOpen}
          contactSheetUrl={campaignResult?.contact_sheet_preview_url || null}
          campaignName={campaignResult?.campaign_name || 'YETI Campaign'}
          runId={campaignResult?.run_id || 'active'}
          onClose={() => setIsContactSheetOpen(false)}
        />

        {/* Quality Report Modal */}
        <QualityReportModal
          isOpen={isQualityReportOpen}
          report={campaignResult?.quality_report || null}
          reportUrl={campaignResult?.report_download_url}
          logUrl={campaignResult?.pipeline_log_url}
          onClose={() => setIsQualityReportOpen(false)}
        />
      </div>
    </main>
  );
};


export default App;
