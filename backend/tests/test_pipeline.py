"""Tests for CampaignPipelineRunner and End-to-End Generation (Prompt 9)."""

import json
import pytest
from pathlib import Path
from PIL import Image

from backend.app.services.pipeline_runner import CampaignPipelineRunner
from backend.app.services.storage.local import LocalStorageAdapter


@pytest.fixture
def brief_dict():
    with open("yeti_la_random_ad_campaign.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def runner(tmp_path):
    storage = LocalStorageAdapter(root_dir=str(tmp_path / "storage"))
    return CampaignPipelineRunner(
        storage_adapter=storage,
        local_base_dir=str(tmp_path / "outputs"),
    )


def test_full_pipeline_execution(runner, brief_dict):
    """Test full generation of 6 concepts, 18 ads, contact sheet, ZIP bundle, and manifest."""
    events = []
    def on_progress(event):
        events.append(event)

    result = runner.execute_campaign(brief_dict, seed=42, progress_callback=on_progress)

    # 1. Verify counts
    assert result.status == "success"
    assert result.total_concepts == 6
    assert result.total_outputs == 18
    assert len(result.concepts) == 6
    assert len(result.ads) == 18

    # 2. Verify all 18 files exist with correct dimensions
    for ad in result.ads:
        assert Path(ad.local_path).exists()
        assert ad.filesize_bytes > 0
        img = Image.open(ad.local_path)
        assert img.size == ad.dimensions
        if ad.aspect_ratio == "1:1":
            assert ad.dimensions == (1080, 1080)
        elif ad.aspect_ratio == "16:9":
            assert ad.dimensions == (1920, 1080)
        elif ad.aspect_ratio == "9:16":
            assert ad.dimensions == (1080, 1920)

    # 3. Verify Contact Sheet
    assert result.contact_sheet_local_path is not None
    assert Path(result.contact_sheet_local_path).exists()
    cs_img = Image.open(result.contact_sheet_local_path)
    assert cs_img.width > 1000
    assert cs_img.height > 1000

    # 4. Verify ZIP Bundle
    assert result.zip_bundle_local_path is not None
    assert Path(result.zip_bundle_local_path).exists()

    # 5. Verify Honesty / Provenance
    assert result.gemini_used is False
    assert "All backgrounds reused from approved assets." in result.provenance_summary

    # 6. Verify Progress Events
    stages = [e.stage for e in events]
    assert "Validating JSON" in stages
    assert "Resolving controlled assets" in stages
    assert "Selecting six concepts" in stages
    assert "Rendering 18 adaptations" in stages
    assert "Complete" in stages
