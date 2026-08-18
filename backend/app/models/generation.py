"""Pydantic models for AI Scene Generation and Provenance Metadata."""

from typing import Optional, Tuple, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class GeneratedBackgroundMetadata(BaseModel):
    """Provenance and review metadata for an AI-generated or mock-generated scene background."""
    background_id: str
    activity: str
    territory: str
    prompt: str
    negative_prompt: str
    model_used: str
    duration_ms: int
    dimensions: Tuple[int, int] = (2048, 2048)
    ai_generated_background: bool = True
    human_review_required: bool = True
    provenance: Literal["google-genai", "mock-generator"] = "google-genai"
    is_mock: bool = False
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    local_path: str
    remote_storage_path: Optional[str] = None


class GenerationRequest(BaseModel):
    """Request payload to generate a missing background variation."""
    activity: Literal["beach", "camping", "tailgating"]
    territory: Optional[str] = None
    aspect_ratio: Literal["1:1", "16:9", "9:16"] = "1:1"
    custom_prompt_suffix: Optional[str] = None
    force_mock: bool = False
