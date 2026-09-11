"""Automated Background Contrast Checker & Dynamic Logo Selector."""

from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union
from PIL import Image, ImageStat
from pydantic import BaseModel, Field


class ContrastAnalysisResult(BaseModel):
    """Structured result of background contrast analysis."""
    luminance: float = Field(
        ...,
        description="Average perceptual luminance normalized between 0.0 (pitch black) and 1.0 (pure white).",
        ge=0.0,
        le=1.0,
    )
    is_dark: bool = Field(
        ...,
        description="True if luminance is below the threshold (default 0.50), meaning a light logo is required.",
    )
    classification: Literal["dark", "light"] = Field(
        ...,
        description="Categorization of background brightness.",
    )
    recommended_logo_role: Literal["brand_logo_white", "brand_logo_black"] = Field(
        ...,
        description="Recommended logo asset role ('brand_logo_white' for dark backgrounds, 'brand_logo_black' for light backgrounds).",
    )
    recommended_logo_path: str = Field(
        ...,
        description="Relative file path to the high-contrast logo asset.",
    )
    zone_sampled: str = Field(
        default="top_logo_zone",
        description="Specific canvas zone sampled for contrast analysis (e.g. 'top_logo_zone', 'full_canvas').",
    )
    sample_bounds: Optional[List[float]] = Field(
        default=None,
        description="Normalized bounding box [left_pct, top_pct, right_pct, bottom_pct] of the sampled zone.",
    )


class BackgroundContrastChecker:
    """
    Analyzes images (auto-generated or static backgrounds) to evaluate perceptual
    luminance in the logo placement zone and select the optimal high-contrast logo:
    - Dark background (luminance < 0.50) -> Light Logo (Yeti_Logo_4.png, white wordmark)
    - Light background (luminance >= 0.50) -> Dark Logo (Yeti_Logo_1.png, black wordmark)
    """

    DEFAULT_WHITE_LOGO = "assets/brand/Yeti_Logo_4.png"
    DEFAULT_BLACK_LOGO = "assets/brand/Yeti_Logo_1.png"

    def __init__(
        self,
        white_logo_path: str = DEFAULT_WHITE_LOGO,
        black_logo_path: str = DEFAULT_BLACK_LOGO,
    ):
        self.white_logo_path = white_logo_path
        self.black_logo_path = black_logo_path

    def calculate_luminance(
        self,
        img: Image.Image,
        sample_zone: str = "top_logo_zone",
    ) -> Tuple[float, List[float]]:
        """
        Calculate weighted perceptual luminance (ITU-R BT.601) in a sampled region:
        L = (0.299 * R + 0.587 * G + 0.114 * B) / 255.0
        Returns (luminance, [left_pct, top_pct, right_pct, bottom_pct]).
        """
        w, h = img.size
        if sample_zone == "top_logo_zone":
            # Logo is placed in top region (anchor top-center, Y within top 30%)
            bounds = [0.10, 0.0, 0.90, 0.30]
        else:
            bounds = [0.0, 0.0, 1.0, 1.0]

        crop_box = (
            int(w * bounds[0]),
            int(h * bounds[1]),
            int(w * bounds[2]),
            int(h * bounds[3]),
        )
        cropped = img.crop(crop_box).convert("RGB")
        stat = ImageStat.Stat(cropped)
        mean_r = stat.mean[0]
        mean_g = stat.mean[1]
        mean_b = stat.mean[2]

        luma = (0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b) / 255.0
        return round(float(luma), 4), bounds

    def analyze_background(
        self,
        image_or_path: Union[str, Path, Image.Image],
        sample_zone: str = "top_logo_zone",
        threshold: float = 0.50,
    ) -> ContrastAnalysisResult:
        """
        Evaluate an image and return structured contrast metrics and logo recommendations.
        """
        if isinstance(image_or_path, (str, Path)):
            path = Path(image_or_path)
            if not path.exists():
                raise FileNotFoundError(f"Background image not found at '{path}'")
            with Image.open(path) as im:
                luminance, bounds = self.calculate_luminance(im, sample_zone=sample_zone)
        elif isinstance(image_or_path, Image.Image):
            luminance, bounds = self.calculate_luminance(image_or_path, sample_zone=sample_zone)
        else:
            raise TypeError(f"Expected file path or PIL Image, got {type(image_or_path)}")

        is_dark = luminance < threshold
        classification: Literal["dark", "light"] = "dark" if is_dark else "light"

        if is_dark:
            recommended_role: Literal["brand_logo_white", "brand_logo_black"] = "brand_logo_white"
            recommended_path = self.white_logo_path
        else:
            recommended_role = "brand_logo_black"
            recommended_path = self.black_logo_path

        return ContrastAnalysisResult(
            luminance=luminance,
            is_dark=is_dark,
            classification=classification,
            recommended_logo_role=recommended_role,
            recommended_logo_path=recommended_path,
            zone_sampled=sample_zone,
            sample_bounds=bounds,
        )

    def select_logo_for_background(
        self,
        image_or_path: Union[str, Path, Image.Image],
        sample_zone: str = "top_logo_zone",
        threshold: float = 0.50,
    ) -> Tuple[str, ContrastAnalysisResult]:
        """
        Convenience helper that returns (recommended_logo_path, analysis_result).
        """
        result = self.analyze_background(image_or_path, sample_zone=sample_zone, threshold=threshold)
        return result.recommended_logo_path, result
