// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { NaturalLanguageBrief } from './NaturalLanguageBrief';
import { CampaignSummary } from './CampaignSummary';
import * as api from '../services/api';
import { YETI_GO_ANYWHERE_2026_BRIEF } from '../data/sampleBriefs';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

const result: api.BriefConversionResult = {
  brief: YETI_GO_ANYWHERE_2026_BRIEF,
  assumptions: ['Used all three formats.'],
  warnings: ['Review generated backgrounds.'],
  summary: { audienceCount: 6, formatCount: 3, totalOutputs: 18 },
};

describe('Natural-language brief intake', () => {
  it('shows an exact count without presenting a full-matrix multiplication', () => {
    render(<CampaignSummary brief={{ ...YETI_GO_ANYWHERE_2026_BRIEF,
      audiences: [YETI_GO_ANYWHERE_2026_BRIEF.audiences[0]],
      generation: { conceptsPerAudience: 7, exactOutputCount: 20, totalOutputsPerRun: 21 },
    }} />);
    expect(screen.getByText('20 Target Ads')).toBeInTheDocument();
    expect(screen.queryByText('7 concepts')).not.toBeInTheDocument();
    expect(screen.getByText(/Final concepts may use fewer formats/)).toBeInTheDocument();
  });
  it('requires text and lets users load an example', () => {
    render(<NaturalLanguageBrief onApply={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Convert to JSON' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Use example' }));
    expect((screen.getByLabelText('Describe your campaign') as HTMLTextAreaElement).value).toContain('Create 18 YETI ads');
    expect(screen.getByRole('button', { name: 'Convert to JSON' })).toBeEnabled();
  });

  it('previews a validated draft and only applies on user action', async () => {
    const convert = vi.spyOn(api, 'convertBrief').mockResolvedValue(result);
    const onApply = vi.fn();
    render(<NaturalLanguageBrief onApply={onApply} />);
    fireEvent.change(screen.getByLabelText('Describe your campaign'), { target: { value: 'Create 18 YETI ads for LA.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Convert to JSON' }));
    await screen.findByText('Draft ready:');
    expect(convert).toHaveBeenCalledWith('Create 18 YETI ads for LA.', expect.any(AbortSignal));
    expect(screen.getByText('Used all three formats.')).toBeInTheDocument();
    expect(screen.getByText('Review generated backgrounds.')).toBeInTheDocument();
    expect(onApply).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Use this brief' }));
    expect(onApply).toHaveBeenCalledWith(result.brief, `${result.brief.campaign.id}.json`, expect.any(Number));
    expect(screen.getByRole('button', { name: 'Brief applied' })).toBeDisabled();
  });

  it('shows a conversion failure without replacing the active brief', async () => {
    vi.spyOn(api, 'convertBrief').mockRejectedValue(new Error('Choose a supported age range.'));
    const onApply = vi.fn();
    render(<NaturalLanguageBrief onApply={onApply} />);
    fireEvent.click(screen.getByRole('button', { name: 'Use example' }));
    fireEvent.click(screen.getByRole('button', { name: 'Convert to JSON' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose a supported age range.');
    expect(onApply).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Convert to JSON' })).toBeEnabled();
  });

  it('discards an old draft when the description changes', async () => {
    vi.spyOn(api, 'convertBrief').mockResolvedValue(result);
    render(<NaturalLanguageBrief onApply={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Use example' }));
    fireEvent.click(screen.getByRole('button', { name: 'Convert to JSON' }));
    await screen.findByText('Draft ready:');
    fireEvent.change(screen.getByLabelText('Describe your campaign'), { target: { value: 'Create 36 ads instead.' } });
    expect(screen.queryByRole('button', { name: 'Use this brief' })).not.toBeInTheDocument();
  });
});
