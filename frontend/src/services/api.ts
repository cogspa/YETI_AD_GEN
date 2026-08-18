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

export interface StorageStatus {
  configured: boolean;
  reachable: boolean;
  mode: 'local' | 'dropbox';
  root: string;
  error?: string;
}

export interface GeneratedAdArtifact {
  artifact_id: string;
  concept_id: string;
  audience_id: string;
  audience_name: string;
  activity: string;
  territory: string;
  age_band: string;
  product_color: 'orange' | 'white';
  aspect_ratio: '1:1' | '16:9' | '9:16';
  dimensions: [number, number];
  filename: string;
  local_path: string;
  preview_url: string;
  storage_path?: string;
  filesize_bytes: number;
  background_source: string;
  human_review_required: boolean;
}

export interface AudienceConcept {
  concept_id: string;
  audience_id: string;
  audience_name: string;
  age_band: 'younger' | 'older';
  activity: string;
  territory: string;
  product_role: string;
  product_asset_path: string;
  background_pool_id: string;
  selected_background_path: string;
  tagline_pool_id: string;
  selected_tagline_text: string;
  selected_tagline_asset_path: string;
  tagline_color_hex: string;
  logo_asset_path: string;
  seed_used: number;
}

export interface CampaignRunResult {
  run_id: string;
  campaign_id: string;
  campaign_name: string;
  seed: number;
  status: 'success' | 'failed' | 'partial';
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  total_concepts: number;
  total_outputs: number;
  concepts: AudienceConcept[];
  ads: GeneratedAdArtifact[];
  contact_sheet_local_path?: string;
  contact_sheet_preview_url?: string;
  zip_bundle_local_path?: string;
  zip_bundle_download_url?: string;
  storage_mode: string;
  storage_root?: string;
  dropbox_folder_path?: string;
  dropbox_shared_link?: string;
  quality_report?: any;
  report_download_url?: string;
  pipeline_log_url?: string;
  provenance_summary: string;
  gemini_used: boolean;
  gemini_audiences: string[];
  warnings: string[];
  errors: string[];
}


export async function fetchStorageStatus(): Promise<StorageStatus | null> {
  try {
    const res = await fetch('/api/storage/status');
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function generateCampaignAds(
  briefData: any,
  seed?: number | null,
): Promise<CampaignRunResult> {
  const url = seed !== undefined && seed !== null ? `/api/campaign/generate?seed=${seed}` : '/api/campaign/generate';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(briefData),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}: ${res.statusText}` }));
    throw new Error(errorData.detail || errorData.message || `Generation failed (${res.status})`);
  }

  return await res.json();
}

