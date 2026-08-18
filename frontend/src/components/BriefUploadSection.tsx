import React, { useState, useRef, useEffect } from 'react';
import type { CampaignBrief, BriefValidationResult } from '../types/campaign';
import { SAMPLE_BRIEFS } from '../data/sampleBriefs';

interface BriefUploadSectionProps {
  currentBrief: CampaignBrief;
  currentFilename: string;
  fileSizeBytes: number;
  validation: BriefValidationResult;
  onBriefChange: (brief: CampaignBrief, filename: string, sizeBytes: number) => void;
  onReset: () => void;
}

export const BriefUploadSection: React.FC<BriefUploadSectionProps> = ({
  currentBrief,
  currentFilename,
  fileSizeBytes,
  validation,
  onBriefChange,
  onReset,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isInspectOpen, setIsInspectOpen] = useState(false);
  const [jsonText, setJsonText] = useState('');
  const [jsonSyntaxError, setJsonSyntaxError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync editor text whenever currentBrief changes
  useEffect(() => {
    setJsonText(JSON.stringify(currentBrief, null, 2));
    setJsonSyntaxError(null);
  }, [currentBrief]);

  const handleFile = (file: File) => {
    if (!file.name.endsWith('.json')) {
      alert('Please select a valid .json brief file.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const parsed = JSON.parse(text);
        onBriefChange(parsed, file.name, file.size);
        setJsonText(JSON.stringify(parsed, null, 2));
        setJsonSyntaxError(null);
      } catch (err: any) {
        setJsonSyntaxError(`JSON Parse Error: ${err.message}`);
      }
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleJsonTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setJsonText(text);
    try {
      const parsed = JSON.parse(text);
      setJsonSyntaxError(null);
      onBriefChange(parsed, currentFilename, new Blob([text]).size);
    } catch (err: any) {
      setJsonSyntaxError(err.message);
    }
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(jsonText);
      const formatted = JSON.stringify(parsed, null, 2);
      setJsonText(formatted);
      setJsonSyntaxError(null);
      onBriefChange(parsed, currentFilename, new Blob([formatted]).size);
    } catch (err: any) {
      setJsonSyntaxError(`Cannot format invalid JSON: ${err.message}`);
    }
  };

  const handleSelectSample = (sampleId: string) => {
    const sample = SAMPLE_BRIEFS.find((s) => s.id === sampleId);
    if (sample) {
      const text = JSON.stringify(sample.brief, null, 2);
      onBriefChange(sample.brief, sample.filename, new Blob([text]).size);
      setJsonText(text);
      setJsonSyntaxError(null);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <section className="brief-section" aria-labelledby="brief-heading">
      <div className="section-header-label" id="brief-heading">
        CAMPAIGN BRIEF (JSON)
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        className="sr-only"
        id="brief-file-input"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]);
          }
        }}
      />

      {/* Drag & Drop Area */}
      <div
        className={`dropzone ${isDragging ? 'dropzone--dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="region"
        aria-label="Upload campaign brief dropzone"
      >
        <div className="dropzone-icon" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0072B2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <div className="dropzone-title">Drag &amp; drop brief JSON here</div>
        <div className="dropzone-subtitle">or click to browse files from your computer</div>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => fileInputRef.current?.click()}
          aria-label="Browse JSON file from your computer"
        >
          Browse JSON File
        </button>
      </div>

      {/* Selected File Card */}
      <div className="selected-file-card" role="status" aria-live="polite">
        <div className="file-info-row">
          <div className="badge-json" aria-label="File format JSON">JSON</div>
          <div className="file-meta">
            <div className="file-name">{currentFilename}</div>
            <div className="file-submeta">
              <span>{currentBrief.campaign?.name || 'YETI Campaign'}</span>
              <span className="dot-separator">•</span>
              <span>{formatFileSize(fileSizeBytes)}</span>
              {validation.isValid && (
                <span className="badge-status-ready">Ready to generate</span>
              )}
              {!validation.isValid && (
                <span className="badge-status-error">Invalid brief ({validation.errors.length} errors)</span>
              )}
            </div>
          </div>
          <button
            type="button"
            className="btn-replace"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Replace current campaign JSON file"
          >
            Replace
          </button>
        </div>
      </div>

      {/* Sample Briefs Selector */}
      <div className="sample-briefs-row">
        <span className="sample-label">Sample briefs:</span>
        <div className="sample-buttons">
          {SAMPLE_BRIEFS.map((sample) => (
            <button
              key={sample.id}
              type="button"
              className={`btn-sample ${currentFilename === sample.filename ? 'btn-sample--active' : ''}`}
              onClick={() => handleSelectSample(sample.id)}
            >
              {sample.label}
            </button>
          ))}
        </div>
      </div>

      {/* Collapsible Inspect / Edit JSON */}
      <div className="inspect-panel">
        <button
          type="button"
          className="inspect-toggle"
          onClick={() => setIsInspectOpen(!isInspectOpen)}
          aria-expanded={isInspectOpen}
          aria-controls="json-inspect-content"
        >
          <span className={`toggle-icon ${isInspectOpen ? 'open' : ''}`}>▶</span>
          <span>INSPECT / EDIT JSON</span>
        </button>

        {isInspectOpen && (
          <div id="json-inspect-content" className="inspect-content">
            <div className="editor-toolbar">
              <span className="editor-title">Brief Editor (live sync)</span>
              <div className="editor-actions">
                <button
                  type="button"
                  className="btn-toolbar"
                  onClick={handleFormatJson}
                  title="Format and pretty-print JSON"
                >
                  Format JSON
                </button>
                <button
                  type="button"
                  className="btn-toolbar"
                  onClick={onReset}
                  title="Reset to default original brief"
                >
                  Reset
                </button>
              </div>
            </div>

            {jsonSyntaxError && (
              <div className="syntax-error-banner" role="alert">
                <strong>Syntax Error:</strong> {jsonSyntaxError}
              </div>
            )}

            {validation.errors.length > 0 && (
              <div className="validation-error-banner" role="alert">
                <strong>Validation Errors:</strong>
                <ul>
                  {validation.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            <textarea
              className="json-textarea"
              value={jsonText}
              onChange={handleJsonTextChange}
              spellCheck={false}
              aria-label="Edit campaign JSON content"
              rows={15}
            />
          </div>
        )}
      </div>
    </section>
  );
};
