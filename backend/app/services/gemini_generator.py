"""Gemini Background Generator & Deterministic Mock Provider for Missing Backgrounds."""

import os
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFilter

from backend.app.models.generation import GeneratedBackgroundMetadata, GenerationRequest
from backend.app.services.storage.base import StorageAdapter
from backend.app.services.storage import get_storage_adapter


NEGATIVE_PROMPT_DEFAULT = (
    "YETI, cooler, product, box, container, bottle, cup, text, words, typography, letters, "
    "signage, watermark, logo, brand mark, emblem, UCLA, USC, Bruins, Trojans, university logo, "
    "mascot, sports jersey, team uniform, close-up faces, distorted objects, blurry, low resolution, cluttered foreground"
)

ACTIVITY_PROMPT_TEMPLATES = {
    "beach": (
        "Commercial cinematic photography of the Westside Los Angeles Pacific coastline in Santa Monica and Malibu. "
        "Bright sunny daylight, clear Pacific Ocean horizon, gentle waves meeting clean warm golden sand. "
        "Wide scenic landscape with open sky and vast clean negative space across the middle ground and foreground. "
        "Clean, pristine, uncluttered commercial environment. No coolers, no products, no logos, no text."
    ),
    "camping": (
        "Commercial cinematic photography of the Los Angeles mountain wilderness in the San Gabriel Mountains and Angeles National Forest. "
        "Majestic tall pine trees, mountain ridgelines in soft golden haze, and rugged natural dirt trail foreground. "
        "Clean darker foreground earth providing high-contrast negative space for product packshots. "
        "Atmospheric, serene, high-end outdoor landscape. No tents, no coolers, no products, no logos, no text."
    ),
    "tailgating": (
        "Commercial cinematic photography of an open-air Los Angeles autumn outdoor gathering space in Westwood or South Central. "
        "Warm late-afternoon golden-hour sunlight casting long soft shadows across clean open asphalt and park perimeter grass, "
        "with distant soft-focus stadium architecture in the far background. Uncluttered, expansive central foreground. "
        "No team marks, no college logos, no UCLA or USC mascots, no uniforms, no text, no coolers."
    ),
}


class GeminiMissingBackgroundError(Exception):
    """Raised when a background is missing and Gemini generation is unavailable or unconfigured."""
    pass


class MockBackgroundGenerator:
    """Deterministic, high-quality procedural background generator for offline development and testing."""

    @staticmethod
    def generate_mock_background(
        activity: str,
        dimensions: Tuple[int, int] = (2048, 2048),
    ) -> Image.Image:
        """Procedurally render a rich, atmospheric gradient landscape in PIL."""
        W, H = dimensions
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        act = activity.lower().strip()
        if act == "beach":
            # Golden hour Pacific sky into ocean into warm sand
            for y in range(H):
                ratio = y / H
                if ratio < 0.45:  # Sky
                    r = int(100 + 130 * (ratio / 0.45))
                    g = int(160 + 80 * (ratio / 0.45))
                    b = int(220 + 20 * (ratio / 0.45))
                elif ratio < 0.70:  # Pacific Ocean
                    r = int(20 + 40 * ((ratio - 0.45) / 0.25))
                    g = int(80 + 60 * ((ratio - 0.45) / 0.25))
                    b = int(140 + 40 * ((ratio - 0.45) / 0.25))
                else:  # Sand
                    r = int(220 - 40 * ((ratio - 0.70) / 0.30))
                    g = int(185 - 40 * ((ratio - 0.70) / 0.30))
                    b = int(140 - 30 * ((ratio - 0.70) / 0.30))
                draw.line([(0, y), (W, y)], fill=(r, g, b))

        elif act == "camping":
            # Mountain sky into pine silhouette into dark earth
            for y in range(H):
                ratio = y / H
                if ratio < 0.40:  # Mountain sky
                    r = int(40 + 80 * (ratio / 0.40))
                    g = int(60 + 80 * (ratio / 0.40))
                    b = int(110 + 60 * (ratio / 0.40))
                elif ratio < 0.65:  # Forest ridge
                    r = int(30 + 30 * ((ratio - 0.40) / 0.25))
                    g = int(55 + 30 * ((ratio - 0.40) / 0.25))
                    b = int(45 + 20 * ((ratio - 0.40) / 0.25))
                else:  # Dark soil base
                    r = int(50 - 20 * ((ratio - 0.65) / 0.35))
                    g = int(40 - 20 * ((ratio - 0.65) / 0.35))
                    b = int(35 - 20 * ((ratio - 0.65) / 0.35))
                draw.line([(0, y), (W, y)], fill=(r, g, b))

        else:  # Tailgating
            # Autumn golden hour sky into park asphalt/grass
            for y in range(H):
                ratio = y / H
                if ratio < 0.50:  # Golden sky
                    r = int(240 - 40 * (ratio / 0.50))
                    g = int(170 - 40 * (ratio / 0.50))
                    b = int(110 - 40 * (ratio / 0.50))
                elif ratio < 0.75:  # Distant park
                    r = int(110 - 30 * ((ratio - 0.50) / 0.25))
                    g = int(120 - 30 * ((ratio - 0.50) / 0.25))
                    b = int(80 - 20 * ((ratio - 0.50) / 0.25))
                else:  # Asphalt ground
                    r = int(65 - 15 * ((ratio - 0.75) / 0.25))
                    g = int(65 - 15 * ((ratio - 0.75) / 0.25))
                    b = int(68 - 15 * ((ratio - 0.75) / 0.25))
                draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Apply soft gaussian blur for smooth photographic background
        blurred = img.filter(ImageFilter.GaussianBlur(radius=8))
        return blurred


class GeminiBackgroundGenerator:
    """
    Generates missing background assets with strict guardrails via Google GenAI SDK
    or deterministic MockBackgroundGenerator.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        storage_adapter: Optional[StorageAdapter] = None,
        local_output_dir: str = "outputs/generated-backgrounds",
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_IMAGE_MODEL", "imagen-3.0-generate-002")
        self.enabled = os.getenv("GEMINI_ENABLED", "true").lower() in ("1", "true", "yes")
        self.storage = storage_adapter or get_storage_adapter()
        self.output_dir = Path(local_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        """Return True if Gemini API key is configured and enabled."""
        return bool(self.api_key and self.enabled)

    def build_prompt(
        self,
        activity: str,
        territory: Optional[str] = None,
        custom_suffix: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Construct a strict guardrailed prompt and negative prompt for any activity or territory."""
        act_key = activity.lower().strip()
        if act_key in ACTIVITY_PROMPT_TEMPLATES:
            base_prompt = ACTIVITY_PROMPT_TEMPLATES[act_key]
        else:
            loc_str = territory if territory else "scenic California outdoors"
            base_prompt = (
                f"Commercial cinematic photography of an open-air {activity} outdoor environment in {loc_str}. "
                "Natural daylight, wide atmospheric landscape, beautiful scenery, and vast clean negative space "
                "across the central foreground for commercial product packshot composite integration. "
                "Clean, pristine, uncluttered high-end commercial environment. No coolers, no products, no logos, no text, no people."
            )

        if territory and territory not in base_prompt:
            base_prompt = f"{base_prompt} Location context: {territory}."
        if custom_suffix:
            base_prompt = f"{base_prompt} {custom_suffix.strip()}"

        return base_prompt, NEGATIVE_PROMPT_DEFAULT

    def generate_for_audience(
        self,
        activity: str,
        territory: Optional[str] = None,
        audience_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        run_id: Optional[str] = None,
        custom_prompt_suffix: Optional[str] = None,
        force_mock: bool = False,
    ) -> GeneratedBackgroundMetadata:
        """Generate a tailored background specifically for an audience demographic concept."""
        return self.generate_background(
            activity=activity,
            territory=territory,
            custom_prompt_suffix=custom_prompt_suffix,
            force_mock=force_mock,
        )


    def generate_background(
        self,
        activity: str,
        territory: Optional[str] = None,
        custom_prompt_suffix: Optional[str] = None,
        force_mock: bool = False,
    ) -> GeneratedBackgroundMetadata:
        """
        Generate a master background image (once per audience concept).
        Saves locally and uploads to Dropbox/storage generated-backgrounds/ folder.
        """
        bg_id = f"gen-bg-{activity.lower()}-{uuid.uuid4().hex[:8]}"
        prompt, negative_prompt = self.build_prompt(activity, territory, custom_prompt_suffix)
        local_target = self.output_dir / f"{bg_id}.png"

        start_time = time.time()

        # Branch 1: Forced Mock or Unconfigured Mock Fallback for Testing
        if force_mock or not self.is_configured():
            if not force_mock and not self.is_configured():
                # If Gemini is strictly unconfigured and not in explicit mock mode, warn or use mock
                is_mock = True
            else:
                is_mock = True

            img = MockBackgroundGenerator.generate_mock_background(activity, (2048, 2048))
            img.save(local_target, format="PNG")
            duration_ms = int((time.time() - start_time) * 1000)

            # Upload to storage
            remote_path = f"generated-backgrounds/{bg_id}.png"
            try:
                storage_meta = self.storage.upload(str(local_target), remote_path, overwrite=True)
                remote_storage_path = storage_meta.path
            except Exception:
                remote_storage_path = None

            return GeneratedBackgroundMetadata(
                background_id=bg_id,
                activity=activity,
                territory=territory or "Los Angeles",
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_used="mock-procedural-v1",
                duration_ms=duration_ms,
                dimensions=(2048, 2048),
                ai_generated_background=False,
                human_review_required=True,
                provenance="mock-generator",
                is_mock=True,
                local_path=str(local_target).replace("\\", "/"),
                remote_storage_path=remote_storage_path,
            )

        # Branch 2: Real Google GenAI SDK (Imagen 3 / Gemini Image Models)
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            full_prompt = f"{prompt} Negative constraints: strictly avoid {negative_prompt}."
            img_bytes = None

            # Attempt 1: Imagen 3 model suite via generate_images
            for m_candidate in [self.model_name, "imagen-3.0-generate-002", "imagen-3.0"]:
                try:
                    result = client.models.generate_images(
                        model=m_candidate,
                        prompt=full_prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/png",
                            aspect_ratio="1:1",
                        ),
                    )
                    if result and result.generated_images:
                        img_bytes = result.generated_images[0].image.image_bytes
                        self.model_name = m_candidate
                        break
                except Exception:
                    continue

            # Attempt 2: Gemini Flash Image models via generate_content
            if not img_bytes:
                for m_candidate in ["gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3-pro-image"]:
                    try:
                        res = client.models.generate_content(
                            model=m_candidate,
                            contents=full_prompt,
                        )
                        if res.candidates and res.candidates[0].content and res.candidates[0].content.parts:
                            for part in res.candidates[0].content.parts:
                                if getattr(part, "inline_data", None) and part.inline_data.data:
                                    img_bytes = part.inline_data.data
                                    self.model_name = m_candidate
                                    break
                        if img_bytes:
                            break
                    except Exception:
                        continue

            if not img_bytes:
                # Quota limit or model restricted - use high-quality procedural lighting fallback
                img = MockBackgroundGenerator.generate_mock_background(activity, (2048, 2048))
                img.save(local_target, format="PNG")
                duration_ms = int((time.time() - start_time) * 1000)

                remote_path = f"generated-backgrounds/{bg_id}.png"
                try:
                    storage_meta = self.storage.upload(str(local_target), remote_path, overwrite=True)
                    remote_storage_path = storage_meta.path
                except Exception:
                    remote_storage_path = None

                return GeneratedBackgroundMetadata(
                    background_id=bg_id,
                    activity=activity,
                    territory=territory or "Los Angeles",
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    model_used="procedural-fallback (quota-standby)",
                    duration_ms=duration_ms,
                    dimensions=(2048, 2048),
                    ai_generated_background=False,
                    human_review_required=True,
                    provenance="mock-generator",
                    is_mock=True,
                    local_path=str(local_target).replace("\\", "/"),
                    remote_storage_path=remote_storage_path,
                )

            img = Image.open(BytesIO(img_bytes))
            img.save(local_target, format="PNG")
            duration_ms = int((time.time() - start_time) * 1000)

            # Upload to storage
            remote_path = f"generated-backgrounds/{bg_id}.png"
            try:
                storage_meta = self.storage.upload(str(local_target), remote_path, overwrite=True)
                remote_storage_path = storage_meta.path
            except Exception:
                remote_storage_path = None

            return GeneratedBackgroundMetadata(
                background_id=bg_id,
                activity=activity,
                territory=territory or "Los Angeles",
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_used=self.model_name,
                duration_ms=duration_ms,
                dimensions=img.size,
                ai_generated_background=True,
                human_review_required=True,
                provenance="google-genai",
                is_mock=False,
                local_path=str(local_target).replace("\\", "/"),
                remote_storage_path=remote_storage_path,
            )
        except Exception:
            # Failsafe: Never crash pipeline; produce rich procedural background
            img = MockBackgroundGenerator.generate_mock_background(activity, (2048, 2048))
            img.save(local_target, format="PNG")
            duration_ms = int((time.time() - start_time) * 1000)

            return GeneratedBackgroundMetadata(
                background_id=bg_id,
                activity=activity,
                territory=territory or "Los Angeles",
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_used="procedural-fallback",
                duration_ms=duration_ms,
                dimensions=(2048, 2048),
                ai_generated_background=False,
                human_review_required=True,
                provenance="mock-generator",
                is_mock=True,
                local_path=str(local_target).replace("\\", "/"),
                remote_storage_path=None,
            )

