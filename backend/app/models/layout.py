# ==============================================================================
# POSITION RULES: CANONICAL LAYOUT & PLACEMENT DEFINITIONS
# ==============================================================================
# This module defines the core position rules for all visual elements:
# - Logo region (`logo_region`): Wordmark placement, scaling, and anchoring
# - Product region (`product_region`): Hero cooler placement and sizing
# - Tagline region (`tagline_region`): Campaign tagline overlay placement
#
# Position rules use normalized coordinates (0.0 to 1.0) relative to canvas width
# and height. Elements are anchored (left/center/right, top/center/bottom) to ensure
# responsive, balanced composition across Square (1:1), Landscape (16:9), and Vertical (9:16).
# ==============================================================================

from typing import Tuple, Optional, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict, model_validator


class NormalizedAnchor(BaseModel):
    """Normalized position coordinate (0.0 to 1.0) with anchoring behavior."""
    x: float = Field(ge=0.0, le=1.0, description="Normalized X coordinate (0.0 = left edge, 1.0 = right edge)")
    y: float = Field(ge=0.0, le=1.0, description="Normalized Y coordinate (0.0 = top edge, 1.0 = bottom edge)")
    anchor_x: Literal["left", "center", "right"] = "left"
    anchor_y: Literal["top", "center", "bottom"] = "top"


# POSITION RULE SCHEMA: Defines bounding box, anchor point, and max dimension limits
class NormalizedRegion(BaseModel):
    """Normalized bounding region (0.0 to 1.0) on canvas."""
    x: float = Field(ge=0.0, le=1.0, description="Anchor X position (0.0 to 1.0)")
    y: float = Field(ge=0.0, le=1.0, description="Anchor Y position (0.0 to 1.0)")
    max_width_pct: float = Field(gt=0.0, le=1.0, description="Maximum width as % of canvas width")
    max_height_pct: float = Field(gt=0.0, le=1.0, description="Maximum height as % of canvas height")
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


# PYDANTIC RULE (EditableRegion):
# 1. ConfigDict(extra="forbid"): prevents unrecognized positioning keys.
# 2. Model validator (`within_canvas`): computes calculated bounding box based on anchor
#    and raises ValueError if any part of the element would extend outside the canvas (0.0 to 1.0).
class EditableRegion(NormalizedRegion):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def within_canvas(self):
        # Calculate bounding box edges based on anchor point
        x_factor = {"left": 0, "center": .5, "right": 1}[self.anchor_x]
        y_factor = {"top": 0, "center": .5, "bottom": 1}[self.anchor_y]
        left = self.x - self.max_width_pct * x_factor
        top = self.y - self.max_height_pct * y_factor
        # Guard against element overflowing top, left, right, or bottom canvas boundaries
        if left < -1e-7 or top < -1e-7 or left + self.max_width_pct > 1 + 1e-7 or top + self.max_height_pct > 1 + 1e-7:
            raise ValueError("Keep the element's placement region within the canvas.")
        return self


# PYDANTIC RULE (LayoutOverride & LayoutPreviewRequest):
# Strict models with extra="forbid" ensuring user overrides only modify valid placement regions.
class LayoutOverride(BaseModel):
    """Only placement regions can be overridden; canvas dimensions stay fixed."""
    model_config = ConfigDict(extra="forbid")
    logo_region: Optional[EditableRegion] = None
    product_region: Optional[EditableRegion] = None
    tagline_region: Optional[EditableRegion] = None


class LayoutPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aspectRatio: Literal["1:1", "16:9", "9:16"]
    layout: Optional[LayoutOverride] = None
    activity: Literal["beach", "camping", "tailgating"] = "camping"
    productColor: Literal["orange", "white"] = "white"


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


# ==============================================================================
# POSITION RULES: CANONICAL FORMAT SPECIFICATIONS
# ==============================================================================
# 1:1 (Square, 1080x1080):
#   - Logo: Top-centered (x=50%, y=8.5%, max width 43.7%, max height 15.6%)
#   - Product: Center-anchored (x=50%, y=52%, max width 68%, max height 60%)
#   - Tagline: Bottom-centered (x=50%, 65px above bottom edge, max width 84%)
# 16:9 (Landscape, 1920x1080):
#   - Logo: Top-centered (x=50%, y=8.5%, max width 28.1%, max height 15.6%)
#   - Product: Center-anchored (x=50%, y=52%, max width 47.8%, max height 62.6%)
#   - Tagline: Bottom-centered (x=50%, 65px above bottom edge, max width 68.4%)
# 9:16 (Vertical, 1080x1920):
#   - Logo: Top-centered (x=50%, y=8.5%, max width 46.8%, max height 12.5%)
#   - Product: Center-anchored (x=50%, y=48%, max width 68.4%, max height 45%)
#   - Tagline: Lower-centered (x=50%, y=88%, max width 83.4%, max height 15.5%)
# ==============================================================================
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
            max_width_pct=0.437,  # Increased by 30% (0.336 -> 0.437)
            max_height_pct=0.156,  # Increased by 30% (0.120 -> 0.156)
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
            y=(1080 - 65) / 1080,  # Raised by 10px more (65px from bottom edge)
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
            max_width_pct=0.281,  # Increased by 30% (0.216 -> 0.281)
            max_height_pct=0.156,  # Increased by 30% (0.120 -> 0.156)
            anchor_x="center",
            anchor_y="top",
        ),
        product_region=NormalizedRegion(
            x=0.50,
            y=0.52,
            max_width_pct=0.4784,
            max_height_pct=0.6256,
            anchor_x="center",
            anchor_y="center",
        ),
        tagline_region=NormalizedRegion(
            x=0.50,
            y=(1080 - 65) / 1080,  # Raised by 10px more (65px from bottom edge)
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
            max_width_pct=0.468,  # Increased by 30% (0.360 -> 0.468)
            max_height_pct=0.125,  # Increased by 30% (0.096 -> 0.125)
            anchor_x="center",
            anchor_y="top",
        ),
        product_region=NormalizedRegion(
            x=0.50,
            y=0.48,
            max_width_pct=0.684,
            max_height_pct=0.45,
            anchor_x="center",
            anchor_y="center",
        ),
        tagline_region=NormalizedRegion(
            x=0.50,
            y=0.88,
            max_width_pct=0.834,
            max_height_pct=0.155,
            anchor_x="center",
            anchor_y="bottom",
        ),
        min_separation_pct=0.04,
        shadow=ShadowConfig(enabled=True, opacity=0.32, blur_radius=22, offset_y_pct=0.015),
    ),
}


def resolve_layout(aspect_ratio: str, override: Optional[LayoutOverride] = None) -> RatioLayoutConfig:
    if aspect_ratio not in LAYOUT_CONFIGS:
        raise ValueError(f"Unsupported aspect ratio '{aspect_ratio}'.")
    data = LAYOUT_CONFIGS[aspect_ratio].model_dump()
    if override is not None:
        data.update(override.model_dump(exclude_none=True))
    return RatioLayoutConfig.model_validate(data)

