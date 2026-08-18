"""Pydantic models for Concept Planning and Format Render Plans."""

from typing import List, Dict, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from backend.app.models.layout import RatioLayoutConfig


class AudienceConcept(BaseModel):
    """Immutable concept selected for a single audience group."""
    concept_id: str
    audience_id: str
    audience_name: str
    age_band: Literal["younger", "older"]
    activity: str
    territory: str
    product_role: str
    product_asset_path: str
    background_pool_id: str
    selected_background_path: str
    tagline_pool_id: str
    selected_tagline_text: str
    selected_tagline_asset_path: str
    tagline_color_hex: str
    logo_asset_path: str
    seed_used: int


class FormatRenderPlan(BaseModel):
    """Deterministic render specification for a specific aspect ratio adaptation."""
    plan_id: str
    concept_id: str
    audience_id: str
    aspect_ratio: Literal["1:1", "16:9", "9:16"]
    output_dimensions: Tuple[int, int]
    target_filename: str
    product_asset_path: str
    background_asset_path: str
    tagline_asset_path: str
    tagline_text: str
    tagline_color_hex: str
    logo_asset_path: str
    layout_config: RatioLayoutConfig


class CampaignPlanResult(BaseModel):
    """Top-level plan result containing 6 audience concepts and 18 format render plans."""
    campaign_id: str
    seed: int
    total_audiences: int = 6
    total_concepts: int = 6
    total_render_plans: int = 18
    concepts: List[AudienceConcept]
    render_plans: List[FormatRenderPlan]
    warnings: List[str] = Field(default_factory=list)
