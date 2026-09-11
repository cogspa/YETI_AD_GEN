"""Unit and integration tests for BackgroundContrastChecker and Dynamic Logo Selection."""

import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.services.contrast_checker import (
    BackgroundContrastChecker,
    ContrastAnalysisResult,
)
from backend.app.main import app


@pytest.fixture
def contrast_checker():
    return BackgroundContrastChecker()


def test_dark_background_selects_light_logo(contrast_checker, tmp_path):
    """Confirm a dark background (e.g. night campsite) triggers the light/white logo."""
    # Create a dark image (RGB 30, 30, 40)
    dark_img = Image.new("RGB", (800, 800), color=(30, 30, 40))
    img_path = tmp_path / "dark_bg.jpg"
    dark_img.save(img_path)

    result = contrast_checker.analyze_background(img_path)
    assert isinstance(result, ContrastAnalysisResult)
    assert result.is_dark is True
    assert result.classification == "dark"
    assert result.luminance < 0.20
    assert result.recommended_logo_role == "brand_logo_white"
    assert "Yeti_Logo_4.png" in result.recommended_logo_path


def test_light_background_selects_dark_logo(contrast_checker, tmp_path):
    """Confirm a light background (e.g. sunny midday beach/snow) triggers the dark/black logo."""
    # Create a light image (RGB 240, 245, 250)
    light_img = Image.new("RGB", (800, 800), color=(240, 245, 250))
    img_path = tmp_path / "light_bg.jpg"
    light_img.save(img_path)

    result = contrast_checker.analyze_background(img_path)
    assert isinstance(result, ContrastAnalysisResult)
    assert result.is_dark is False
    assert result.classification == "light"
    assert result.luminance > 0.80
    assert result.recommended_logo_role == "brand_logo_black"
    assert "Yeti_Logo_1.png" in result.recommended_logo_path


def test_top_logo_zone_sampling_accuracy(contrast_checker, tmp_path):
    """
    Confirm that sampling 'top_logo_zone' evaluates the actual logo position (top 30%),
    handling split-tone images (e.g. bright sky top + dark forest bottom) correctly.
    """
    # Create an image 800x800: Top 30% is bright sky (240, 240, 240), bottom 70% is dark forest (20, 30, 20)
    img = Image.new("RGB", (800, 800), color=(20, 30, 20))
    for y in range(int(800 * 0.30)):
        for x in range(800):
            img.putpixel((x, y), (240, 240, 240))

    img_path = tmp_path / "split_bg.jpg"
    img.save(img_path)

    # Top logo zone should see the bright sky -> light classification -> black logo
    top_result = contrast_checker.analyze_background(img_path, sample_zone="top_logo_zone")
    assert top_result.is_dark is False
    assert top_result.classification == "light"
    assert top_result.recommended_logo_role == "brand_logo_black"

    # Full canvas sample would be skewed by the large dark bottom area
    full_result = contrast_checker.analyze_background(img_path, sample_zone="full_canvas")
    assert full_result.luminance < top_result.luminance


def test_select_logo_for_background_helper(contrast_checker):
    """Confirm select_logo_for_background returns both path and result directly."""
    img = Image.new("RGB", (200, 200), color=(10, 10, 10))
    logo_path, res = contrast_checker.select_logo_for_background(img)
    assert logo_path == contrast_checker.white_logo_path
    assert res.is_dark is True


def test_fastapi_contrast_analyze_endpoint():
    """Verify POST /api/contrast/analyze endpoint behaves as expected."""
    client = TestClient(app)
    resp = client.post(
        "/api/contrast/analyze",
        json={"image_path": "assets/backgrounds/Beach.jpg", "sample_zone": "top_logo_zone"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "luminance" in data
    assert "is_dark" in data
    assert "classification" in data
    assert "recommended_logo_role" in data
    assert "recommended_logo_path" in data


def test_pipeline_runner_dynamic_contrast_assignment_dark_and_light(tmp_path, monkeypatch):
    """
    Test that CampaignPipelineRunner dynamically inspects auto-generated backgrounds:
    - Dark background -> selects Yeti_Logo_4.png (white logo)
    - Light background -> selects Yeti_Logo_1.png (black logo)
    """
    from unittest.mock import MagicMock
    from backend.app.services import pipeline_runner
    from backend.app.services.storage.local import LocalStorageAdapter
    from backend.app.models.generation import GeneratedBackgroundMetadata
    from backend.app.models.brief_conversion import BriefIntent
    from backend.app.services.brief_converter import compile_brief

    storage = LocalStorageAdapter(root_dir=str(tmp_path / "storage"))
    monkeypatch.setattr(pipeline_runner, "get_storage_adapter", lambda: storage)

    # 1. Test with Dark Background (RGB 15, 20, 25)
    dark_provider = MagicMock()
    def generate_dark(**kwargs):
        target = tmp_path / "gemini_dark_camp_bg.png"
        Image.new("RGB", (1080, 1080), (15, 20, 25)).save(target)
        return GeneratedBackgroundMetadata(
            background_id="dark-bg-1",
            activity=kwargs["activity"],
            territory=kwargs["territory"],
            prompt=kwargs.get("custom_prompt_suffix", ""),
            negative_prompt="",
            model_used="test-provider",
            duration_ms=1,
            dimensions=(1080, 1080),
            local_path=str(target),
            ai_generated_background=True,
            is_mock=False,
            human_review_required=True,
            provenance="google-genai",
        )
    dark_provider.generate_for_audience.side_effect = generate_dark

    brief_dark = compile_brief(BriefIntent(
        name="Night Campaign", market="Joshua Tree", objective=None,
        audiences=[dict(name="Stargazers", minimumAge=21, maximumAge=24,
            lifeStage="Young adults", activity="camping", territory="Joshua Tree",
            visualDirection="Dark starry night", backgroundPoolId=None,
            productModel="YETI Roadie 24")],
        formatIds=["square"], conceptsPerAudience=1, totalOutputs=1, seed=42,
        assumptions=[], questions=[],
    ))["brief"]

    runner_dark = pipeline_runner.CampaignPipelineRunner(
        storage_adapter=storage,
        gemini_generator=dark_provider,
        local_base_dir=str(tmp_path / "out_dark"),
    )
    res_dark = runner_dark.execute_campaign(brief_dark, seed=42)
    assert res_dark.status == "success"
    # Dark background must receive white/light logo
    assert "Yeti_Logo_4.png" in res_dark.concepts[0].logo_asset_path

    # 2. Test with Light Background (RGB 245, 245, 250)
    light_provider = MagicMock()
    def generate_light(**kwargs):
        target = tmp_path / "gemini_light_snow_bg.png"
        Image.new("RGB", (1080, 1080), (245, 245, 250)).save(target)
        return GeneratedBackgroundMetadata(
            background_id="light-bg-1",
            activity=kwargs["activity"],
            territory=kwargs["territory"],
            prompt=kwargs.get("custom_prompt_suffix", ""),
            negative_prompt="",
            model_used="test-provider",
            duration_ms=1,
            dimensions=(1080, 1080),
            local_path=str(target),
            ai_generated_background=True,
            is_mock=False,
            human_review_required=True,
            provenance="google-genai",
        )
    light_provider.generate_for_audience.side_effect = generate_light

    brief_light = compile_brief(BriefIntent(
        name="Snow Peak Campaign", market="Mammoth", objective=None,
        audiences=[dict(name="Snow Explorers", minimumAge=30, maximumAge=45,
            lifeStage="Adult skiers", activity="skiing", territory="Mammoth",
            visualDirection="Blinding bright midday snow slopes", backgroundPoolId=None,
            productModel="YETI Tundra 45")],
        formatIds=["square"], conceptsPerAudience=1, totalOutputs=1, seed=42,
        assumptions=[], questions=[],
    ))["brief"]

    runner_light = pipeline_runner.CampaignPipelineRunner(
        storage_adapter=storage,
        gemini_generator=light_provider,
        local_base_dir=str(tmp_path / "out_light"),
    )
    res_light = runner_light.execute_campaign(brief_light, seed=42)
    assert res_light.status == "success"
    # Light background must receive black/dark logo
    assert "Yeti_Logo_1.png" in res_light.concepts[0].logo_asset_path
