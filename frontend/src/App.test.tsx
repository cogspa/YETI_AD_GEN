// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { App } from './App';
import * as api from './services/api';


describe('YETI Ad Generator UI', () => {
  it('valid JSON reveals six audiences, three formats, and 18 outputs', () => {
    render(<App />);

    // Check header
    expect(screen.getByText('AD GENERATOR')).toBeInTheDocument();

    // Check formula / summary banner: "6 audiences × 3 formats = 18 outputs"
    expect(screen.getByText(/6 audiences/i)).toBeInTheDocument();
    expect(screen.getByText(/3 formats/i)).toBeInTheDocument();
    expect(screen.getByText(/18 outputs/i)).toBeInTheDocument();

    // Check 3 target formats
    expect(screen.getByText('1:1')).toBeInTheDocument();
    expect(screen.getByText('16:9')).toBeInTheDocument();
    expect(screen.getByText('9:16')).toBeInTheDocument();

    // Check 6 audience personas P01 - P06
    expect(screen.getByText('P01')).toBeInTheDocument();
    expect(screen.getByText('Westwood College Tailgaters')).toBeInTheDocument();

    expect(screen.getByText('P02')).toBeInTheDocument();
    expect(screen.getByText('South Central College Tailgaters')).toBeInTheDocument();

    expect(screen.getByText('P03')).toBeInTheDocument();
    expect(screen.getByText('Westside Recent Graduates')).toBeInTheDocument();

    expect(screen.getByText('P04')).toBeInTheDocument();
    expect(screen.getByText('College Friends Beach Day')).toBeInTheDocument();

    expect(screen.getByText('P05')).toBeInTheDocument();
    expect(screen.getByText('First-Time Family Campers')).toBeInTheDocument();

    expect(screen.getByText('P06')).toBeInTheDocument();
    expect(screen.getByText('Graduate Adventure Campers')).toBeInTheDocument();

    // Check Generate button
    const generateBtn = screen.getByRole('button', { name: /GENERATE ADS/i });
    expect(generateBtn).toBeInTheDocument();
    expect(generateBtn).not.toBeDisabled();
  });

  it('clicking GENERATE ADS opens progress modal', async () => {
    // Mock API call
    vi.spyOn(api, 'generateCampaignAds').mockResolvedValueOnce({
      run_id: 'run-test-001',
      campaign_id: 'yeti-la-go-anywhere-2026',
      campaign_name: 'Go Anywhere with YETI',
      seed: 42,
      status: 'success',
      started_at: '2026-08-18T08:00:00Z',
      completed_at: '2026-08-18T08:00:05Z',
      duration_seconds: 4.2,
      total_concepts: 6,
      total_outputs: 18,
      concepts: [],
      ads: [],
      storage_mode: 'dropbox',
      storage_root: '/yeti-ad-generator',
      provenance_summary: 'All backgrounds reused from approved assets.',
      gemini_used: false,
      gemini_audiences: [],
      warnings: [],
      errors: [],
    });

    render(<App />);

    const generateBtn = screen.getAllByRole('button', { name: /GENERATE ADS/i })[0];
    fireEvent.click(generateBtn);

    // Verify progress modal is opened
    expect(screen.getByText('Generating 18 Ads')).toBeInTheDocument();
  });


  it('inspect / edit JSON panel expands and displays editable JSON', () => {
    render(<App />);

    const toggleBtn = screen.getAllByRole('button', { name: /INSPECT \/ EDIT JSON/i })[0];
    expect(toggleBtn).toBeInTheDocument();

    fireEvent.click(toggleBtn);


    const textarea = screen.getByLabelText(/Edit campaign JSON content/i) as HTMLTextAreaElement;
    expect(textarea).toBeInTheDocument();
    expect(textarea.value).toContain('yeti-la-go-anywhere-2026');
  });
});
