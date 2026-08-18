"""Tests for GeminiBackgroundGenerator and MockBackgroundGenerator (Prompt 7)."""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image

from backend.app.services.gemini_generator import (
    GeminiBackgroundGenerator,
    MockBackgroundGenerator,
    NEGATIVE_PROMPT_DEFAULT,
)
from backend.app.services.asset_resolver import AssetResolver
from backend.app.services.storage.local import LocalStorageAdapter


@pytest.fixture
def local_storage(tmp_path):
    return LocalStorageAdapter(root_dir=str(tmp_path / "storage"))


@pytest.fixture
def generator(local_storage, tmp_path):
    return GeminiBackgroundGenerator(
        api_key="mock_gemini_key",
        model_name="imagen-3.0-generate-002",
        storage_adapter=local_storage,
        local_output_dir=str(tmp_path / "gen_bg"),
    )


def test_guardrail_prompt_construction(generator):
    """Verify strict negative prompts and clean scenic descriptions without forbidden elements."""
    prompt, neg_prompt = generator.build_prompt(
        activity="tailgating",
        territory="Westwood",
        custom_suffix="Autumn golden sunlight.",
    )

    # Negative prompt guardrails
    assert "YETI" in neg_prompt
    assert "cooler" in neg_prompt
    assert "logo" in neg_prompt
    assert "words" in neg_prompt
    assert "UCLA" in neg_prompt
    assert "USC" in neg_prompt

    # Positive prompt guardrails
    assert "Westwood" in prompt
    assert "Autumn golden sunlight." in prompt
    assert "No coolers" in prompt or "no coolers" in prompt


def test_mock_background_generator_labeling(generator):
    """Confirm Mock provider outputs truthful provenance without claiming GenAI."""
    meta = generator.generate_background(activity="beach", force_mock=True)

    assert meta.ai_generated_background is False
    assert meta.is_mock is True
    assert meta.provenance == "mock-generator"
    assert meta.human_review_required is True
    assert Path(meta.local_path).exists()

    # Check generated image dimensions
    img = Image.open(meta.local_path)
    assert img.size == (2048, 2048)
    assert img.mode == "RGB"


def test_resolver_does_not_call_gemini_for_existing_background():
    """Verify Gemini is NOT called when local/Dropbox approved backgrounds resolve."""
    resolver = AssetResolver()

    # Resolve approved local background
    res = resolver.resolve_role("background_beach")
    assert res.status == "local"
    assert res.is_blocking is False  # Backgrounds are non-blocking (Gemini-eligible if missing)
    assert "Beach.jpg" in res.resolved_path
    assert res.dimensions == (2400, 1866)
    # No Gemini call triggered


@patch("google.genai.Client")
def test_gemini_generation_success_and_storage_upload(mock_client_class, generator, tmp_path):
    """Test full generation workflow with mocked Google GenAI SDK and storage upload."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Create dummy PNG bytes
    dummy_img = Image.new("RGB", (2048, 2048), (100, 150, 200))
    import io
    buf = io.BytesIO()
    dummy_img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # Mock response
    mock_image_obj = MagicMock()
    mock_image_obj.image.image_bytes = png_bytes
    mock_result = MagicMock()
    mock_result.generated_images = [mock_image_obj]
    mock_client.models.generate_images.return_value = mock_result

    meta = generator.generate_background(
        activity="camping",
        territory="Angeles National Forest",
        force_mock=False,
    )

    assert meta.ai_generated_background is True
    assert meta.is_mock is False
    assert meta.provenance == "google-genai"
    assert meta.model_used == "imagen-3.0-generate-002"
    assert meta.human_review_required is True
    assert meta.remote_storage_path is not None
    assert "generated-backgrounds" in meta.remote_storage_path
    assert Path(meta.local_path).exists()
