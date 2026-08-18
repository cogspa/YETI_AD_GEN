"""Normalized Layout Configuration derived from visual reference ads."""

from typing import Tuple, Optional, Literal, Dict
from pydantic import BaseModel, Field


class NormalizedAnchor(BaseModel):
    """Normalized position coordinate (0.0 to 1.0) with anchoring behavior."""
    x: float = Field(ge=0.0, le=1.0, description="Normalized X coordinate")
    y: float = Field(ge=0.0, le=1.0, description="Normalized Y coordinate")
    anchor_x: Literal["left", "center", "right"] = "left"
    anchor_y: Literal["top", "center", "bottom"] = "top"


class NormalizedRegion(BaseModel):
    """Normalized bounding region (0.0 to 1.0) on canvas."""
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    max_width_pct: float = Field(gt=0.0, le=1.0)
    max_height_pct: float = Field(gt=0.0, le=1.0)
    anchor_x: Literal["left", "center", "right"] = "left"
    anchor_y: Literal["top", "center", "bottom"] = "top"


class ShadowConfig(BaseModel):
    """Optional subtle contact shadow beneath product."""
    enabled: bool = True
    opacity: float = Field(default=0.35, ge=0.0, le=1.0)
    blur_radius: int = 18
    offset_y_pct: float = 0.02
    width_scale: float = 0.85
    height_scale: float = 0.12


class RatioLayoutConfig(BaseModel):
    """Layout rules for a specific aspect ratio."""
    aspect_ratio: Literal["1:1", "16:9", "9:16"]
    canvas_width: int
    canvas_height: int
    safe_margin_x_pct: float
    safe_margin_y_pct: float
    background_focal_point: Tuple[float, float] = (0.5, 0.5)  # (center_x, center_y) for crop
    logo_region: NormalizedRegion
    product_region: NormalizedRegion
    tagline_region: NormalizedRegion
    min_separation_pct: float = 0.03
    shadow: ShadowConfig = ShadowConfig()


# Canonical Layout Definitions (Centered Composition)
LAYOUT_CONFIGS: Dict[str, RatioLayoutConfig] = {
    "1:1": RatioLayoutConfig(
        aspect_ratio="1:1",
        canvas_width=1080,
        canvas_height=1080,
        safe_margin_x_pct=0.065,
        safe_margin_y_pct=0.065,
        background_focal_point=(0.5, 0.5),
        logo_region=NormalizedRegion(
            x=0.50,
            y=0.085,
            max_width_pct=0.28,
            max_height_pct=0.10,
            anchor_x="center",
            anchor_y="top",
        ),
        product_region=NormalizedRegion(
            x=0.50,
            y=0.52,
            max_width_pct=0.68,
            max_height_pct=0.60,
            anchor_x="center",
            anchor_y="center",
        ),
        tagline_region=NormalizedRegion(
            x=0.50,
            y=0.88,
            max_width_pct=0.84,
            max_height_pct=0.18,
            anchor_x="center",
            anchor_y="bottom",
        ),
        min_separation_pct=0.03,
        shadow=ShadowConfig(enabled=True, opacity=0.32, blur_radius=20, offset_y_pct=0.015),
    ),
    "16:9": RatioLayoutConfig(
        aspect_ratio="16:9",
        canvas_width=1920,
        canvas_height=1080,
        safe_margin_x_pct=0.055,
        safe_margin_y_pct=0.07,
        background_focal_point=(0.5, 0.5),
        logo_region=NormalizedRegion(
            x=0.50,
            y=0.085,
            max_width_pct=0.18,
            max_height_pct=0.10,
            anchor_x="center",
            anchor_y="top",
        ),
        product_region=NormalizedRegion(
            x=0.50,
            y=0.52,
            max_width_pct=0.4784,  # Decreased by 8% (0.52 -> 0.4784)
            max_height_pct=0.6256,  # Decreased by 8% (0.68 -> 0.6256)
            anchor_x="center",
            anchor_y="center",
        ),
        tagline_region=NormalizedRegion(
            x=0.50,
            y=0.90,  # Lowered by 10 points (~0.02 of 1080 canvas)
            max_width_pct=0.684,
            max_height_pct=0.19,
            anchor_x="center",
            anchor_y="bottom",
        ),
        min_separation_pct=0.04,
        shadow=ShadowConfig(enabled=True, opacity=0.35, blur_radius=22, offset_y_pct=0.015),
    ),
    "9:16": RatioLayoutConfig(
        aspect_ratio="9:16",
        canvas_width=1080,
        canvas_height=1920,
        safe_margin_x_pct=0.08,
        safe_margin_y_pct=0.09,
        background_focal_point=(0.5, 0.5),
        logo_region=NormalizedRegion(
            x=0.50,
            y=0.085,
            max_width_pct=0.30,
            max_height_pct=0.08,
            anchor_x="center",
            anchor_y="top",
        ),
        product_region=NormalizedRegion(
            x=0.50,
            y=0.48,
            max_width_pct=0.684,  # Decreased by 10% (0.76 -> 0.684)
            max_height_pct=0.45,   # Decreased by 10% (0.50 -> 0.45)
            anchor_x="center",
            anchor_y="center",
        ),
        tagline_region=NormalizedRegion(
            x=0.50,
            y=0.88,
            max_width_pct=0.834,  # Decreased by 3% (0.86 -> 0.834)
            max_height_pct=0.155,  # Decreased by 3% (0.16 -> 0.155)
            anchor_x="center",
            anchor_y="bottom",
        ),
        min_separation_pct=0.04,
        shadow=ShadowConfig(enabled=True, opacity=0.32, blur_radius=22, offset_y_pct=0.015),
    ),
}
