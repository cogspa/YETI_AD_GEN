/** Typed API client for YETI Ad Generator backend */

import type { BriefValidationResult } from '../types/campaign';

export interface ResolvedAssetInfo {
  role: string;
  logical_id: string;
  resolved_path: string;
  status: 'local' | 'cached_from_dropbox' | 'dropbox_available' | 'missing_gemini_eligible' | 'missing_blocking';
  format_type?: string;
  dimensions?: [number, number];
  has_alpha: boolean;
  size_bytes: number;
  sha256_hash?: string;
  is_blocking: boolean;
  error_message?: string;
}

export interface AssetReadinessReport {
  is_ready_to_generate: boolean;
  blocking_missing_count: number;
  gemini_eligible_missing_count: number;
  assets: Record<string, ResolvedAssetInfo>;
  summary_messages: string[];
}

export async function fetchAssetReadiness(): Promise<AssetReadinessReport | null> {
  try {
    const baseUrl = typeof window !== 'undefined' && window.location?.origin ? '' : 'http://localhost:8000';
    const res = await fetch(`${baseUrl}/api/assets/readiness`);
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function validateBriefWithBackend(briefData: any): Promise<BriefValidationResult | null> {
  try {
    const res = await fetch('/api/brief/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(briefData),
    });
    if (!res.ok) {
      throw new Error(`Server error: HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.warn('Backend validation API unreachable, using client validator:', err);
    return null;
  }
}
