"""Tests for CampaignPipelineRunner and End-to-End Generation (Prompt 9)."""

import json
import zipfile
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
    """Test full generation of 6 concepts, 18 ads, contact sheet, ZIP bundle, and manifest organized by product and aspect ratio."""
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

    # 2. Verify products/ hierarchy and aspect ratio folders (e.g., products/roadie-24-orange/1x1/...)
    p01_ads = [a for a in result.ads if a.audience_id == "P01"]
    assert len(p01_ads) == 3
    p01_1x1 = next(a for a in p01_ads if a.aspect_ratio == "1:1")
    assert p01_1x1.filename == "P01_westwood-college_roadie-24-orange_1x1.png"
    assert "/products/roadie-24-orange/1x1/" in p01_1x1.local_path
    assert "products/roadie-24-orange/1x1/" in p01_1x1.storage_path

    # 3. Verify all 18 files exist with correct dimensions and are organized by product and aspect ratio
    for ad in result.ads:
        assert Path(ad.local_path).exists()
        assert ad.filesize_bytes > 0
        assert "/products/" in ad.local_path
        clean_ratio = ad.aspect_ratio.replace(":", "x")
        assert f"/{clean_ratio}/" in ad.local_path
        assert f"products/{ad.product_slug}/{clean_ratio}/" in ad.storage_path

        img = Image.open(ad.local_path)
        assert img.size == ad.dimensions
        if ad.aspect_ratio == "1:1":
            assert ad.dimensions == (1080, 1080)
        elif ad.aspect_ratio == "16:9":
            assert ad.dimensions == (1920, 1080)
        elif ad.aspect_ratio == "9:16":
            assert ad.dimensions == (1080, 1920)

    # 4. Verify Contact Sheet
    assert result.contact_sheet_local_path is not None
    assert Path(result.contact_sheet_local_path).exists()
    cs_img = Image.open(result.contact_sheet_local_path)
    assert cs_img.width > 1000
    assert cs_img.height > 1000

    # 5. Verify ZIP Bundle contains products/ hierarchy
    assert result.zip_bundle_local_path is not None
    assert Path(result.zip_bundle_local_path).exists()
    with zipfile.ZipFile(result.zip_bundle_local_path, "r") as zf:
        namelist = zf.namelist()
        assert "contact-sheet.jpg" in namelist
        # Verify product-first paths in zip
        assert any(n.startswith("products/roadie-24-orange/1x1/") for n in namelist)
        assert any(n.startswith("products/roadie-24-orange/16x9/") for n in namelist)
        assert any(n.startswith("products/roadie-24-orange/9x16/") for n in namelist)
        assert any("P01_westwood-college_roadie-24-orange_1x1.png" in n for n in namelist)

    # 6. Verify Honesty / Provenance
    assert result.gemini_used is False
    assert "All backgrounds reused from approved assets." in result.provenance_summary

    # 7. Verify Progress Events
    stages = [e.stage for e in events]
    assert "Validating JSON" in stages
    assert "Resolving controlled assets" in stages
    assert any("Selecting" in s for s in stages)
    assert any("Rendering" in s for s in stages)
    assert "Complete" in stages

