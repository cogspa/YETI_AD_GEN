import { useEffect, useRef, useState } from 'react';
import type { CampaignBrief } from '../types/campaign';
import { convertBrief, type BriefConversionResult } from '../services/api';

interface Props {
  onApply: (brief: CampaignBrief, filename: string, sizeBytes: number) => void;
}

const EXAMPLE = 'Create 18 YETI ads for Los Angeles. Target college tailgaters in Westwood ages 20–24, beachgoers on the Westside ages 25–30, and mountain campers ages 25–30. Use two concepts per audience in square, landscape, and vertical formats. Keep the approved Go Anywhere artwork and cooler color rules.';

export function NaturalLanguageBrief({ onApply }: Props) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<BriefConversionResult | null>(null);
  const [applied, setApplied] = useState(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const updateText = (value: string) => {
    setText(value);
    setDraft(null);
    setError(null);
    setApplied(false);
  };

  const handleConvert = async () => {
    if (busy || text.trim().length < 10) return;
    const request = new AbortController();
    controller.current = request;
    const timeout = window.setTimeout(() => request.abort(), 100000);
    setBusy(true);
    setError(null);
    setDraft(null);
    setApplied(false);
    try {
      const result = await convertBrief(text.trim(), request.signal);
      if (!request.signal.aborted) setDraft(result);
    } catch (err) {
      setError(request.signal.aborted ? 'Conversion timed out. Please try again.' :
        err instanceof Error ? err.message : 'Brief conversion failed. Please try again.');
    } finally {
      window.clearTimeout(timeout);
      setBusy(false);
      controller.current = null;
    }
  };

  const handleApply = () => {
    if (!draft) return;
    const json = JSON.stringify(draft.brief, null, 2);
    onApply(draft.brief, `${draft.brief.campaign.id}.json`, new Blob([json]).size);
    setApplied(true);
  };

  return (
    <div className="natural-brief">
      <label htmlFor="natural-brief-text" className="natural-brief-title">Describe your campaign</label>
      <p id="natural-brief-help">Tell us the audiences, locations, ages, ad count, and formats. New territories get AI-generated backgrounds. We’ll turn your description into a campaign brief you can review.</p>
      <textarea
        id="natural-brief-text"
        className="natural-brief-textarea"
        aria-describedby="natural-brief-help natural-brief-rules"
        placeholder="For example: Create 18 YETI ads for LA beachgoers, campers, and college tailgaters…"
        value={text}
        onChange={(event) => updateText(event.target.value)}
        maxLength={12000}
        rows={5}
        disabled={busy}
      />
      <p id="natural-brief-rules" className="natural-brief-hint">Uses approved GO ANYWHERE artwork. Ages 20–24 use orange coolers; ages 25+ use white. Formats: square, landscape, vertical. Generated scenes are available for review after ad generation.</p>
      <div className="natural-brief-actions">
        <button type="button" className="btn-secondary" disabled={busy || text.trim().length < 10} onClick={handleConvert}>
          {busy ? 'Converting brief…' : 'Convert to JSON'}
        </button>
        <button type="button" className="btn-toolbar" disabled={busy} onClick={() => updateText(EXAMPLE)}>Use example</button>
        <span className="natural-brief-hint">{text.length.toLocaleString()} / 12,000</span>
      </div>
      {busy && <p role="status">Converting and checking campaign rules. This may take a minute.</p>}
      {error && <div className="validation-error-banner natural-brief-error" role="alert">{error}</div>}
      {draft && (
        <div className="natural-brief-draft">
          <p role="status"><strong>Draft ready:</strong> {draft.summary.audienceCount} audiences · {draft.summary.formatCount} formats · {draft.summary.totalOutputs} ads</p>
          <p>{draft.brief.campaign.name}</p>
          {draft.formatCounts && <p>{Object.entries(draft.formatCounts).map(([format, count]) => `${count} ${format}`).join(' · ')}</p>}
          {draft.assumptions.length > 0 && <div><strong>Defaults and assumptions</strong><ul>{draft.assumptions.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
          {draft.warnings.length > 0 && <div><strong>Review notes</strong><ul>{draft.warnings.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
          <details>
            <summary>Preview generated JSON</summary>
            <pre className="natural-brief-json">{JSON.stringify(draft.brief, null, 2)}</pre>
          </details>
          <button type="button" className="btn-secondary" disabled={applied} onClick={handleApply}>{applied ? 'Brief applied' : 'Use this brief'}</button>
          <p className="natural-brief-hint">{applied ? 'The campaign brief below has been updated. Review it, then select Generate Ads.' : 'Your current campaign stays selected until you use this brief.'}</p>
        </div>
      )}
    </div>
  );
}
