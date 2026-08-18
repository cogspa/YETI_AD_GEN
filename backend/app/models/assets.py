"""Pydantic models for Asset Catalog and Path Resolution."""

from typing import Optional, Tuple, Literal, List, Dict
from pydantic import BaseModel, Field


AssetRole = Literal[
    "product_orange",
    "product_white",
    "background_beach",
    "background_camping",
    "background_tailgating",
    "tagline_black",
    "tagline_white",
    "brand_logo",
    "font_regular",
    "font_bold",
    "layout_reference_1x1",
    "layout_reference_16x9",
    "layout_reference_9x16",
]

AssetStatus = Literal[
    "local",
    "cached_from_dropbox",
    "dropbox_available",
    "missing_gemini_eligible",
    "missing_blocking",
]


class ResolvedAssetInfo(BaseModel):
    role: str
    logical_id: str
    resolved_path: str
    status: AssetStatus
    format_type: Optional[str] = None  # e.g., "PNG", "JPEG", "TTF", "SVG"
    dimensions: Optional[Tuple[int, int]] = None  # (width, height)
    has_alpha: bool = False
    size_bytes: int = 0
    sha256_hash: Optional[str] = None
    is_blocking: bool = False
    error_message: Optional[str] = None


class AssetReadinessReport(BaseModel):
    is_ready_to_generate: bool
    blocking_missing_count: int
    gemini_eligible_missing_count: int
    assets: Dict[str, ResolvedAssetInfo]
    summary_messages: List[str]
