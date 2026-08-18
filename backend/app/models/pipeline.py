"""Pydantic models for Pipeline Execution, Contact Sheet, and Run Artifacts."""

from typing import List, Dict, Optional, Tuple, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from backend.app.models.plan import AudienceConcept, FormatRenderPlan


class GeneratedAdArtifact(BaseModel):
    """Metadata and paths for a single rendered ad format."""
    artifact_id: str
    concept_id: str
    audience_id: str
    audience_name: str
    activity: str
    territory: str
    age_band: str
    product_color: str
    aspect_ratio: Literal["1:1", "16:9", "9:16"]
    dimensions: Tuple[int, int]
    filename: str
    local_path: str
    preview_url: str
    storage_path: Optional[str] = None
    filesize_bytes: int = 0
    background_source: str  # "approved_asset", "gemini_generated", "mock_generated"
    human_review_required: bool = False


class PipelineStageEvent(BaseModel):
    """Event emitted during pipeline execution stages."""
    stage: str
    progress_pct: int
    completed_items: int = 0
    total_items: int = 18
    message: str


class CampaignRunResult(BaseModel):
    """Full end-to-end campaign run result."""
    run_id: str
    campaign_id: str
    campaign_name: str
    seed: int
    status: Literal["success", "failed", "partial"]
    started_at: str
    completed_at: str
    duration_seconds: float
    total_concepts: int = 6
    total_outputs: int = 18
    concepts: List[AudienceConcept]
    render_plans: List[FormatRenderPlan]
    ads: List[GeneratedAdArtifact]
    contact_sheet_local_path: Optional[str] = None
    contact_sheet_preview_url: Optional[str] = None
    zip_bundle_local_path: Optional[str] = None
    zip_bundle_download_url: Optional[str] = None
    storage_mode: str  # "dropbox" or "local"
    storage_root: str
    dropbox_folder_path: Optional[str] = None
    dropbox_shared_link: Optional[str] = None
    provenance_summary: str
    gemini_used: bool = False
    gemini_audiences: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
