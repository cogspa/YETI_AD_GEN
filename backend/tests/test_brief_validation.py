"""Unit test suite for YETI campaign brief contract validation."""

import json
import pytest
import copy
from backend.app.services.brief_validator import validate_brief_dict, validate_brief_json_file
from backend.app.models.brief import CampaignBriefModel


@pytest.fixture
def valid_brief_data():
    with open("yeti_la_random_ad_campaign.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_campaign_json_passes(valid_brief_data):
    """Confirm the canonical campaign JSON passes all validation rules without errors."""
    is_valid, model, errors = validate_brief_dict(valid_brief_data)
    assert is_valid is True, f"Validation failed with errors: {errors}"
    assert errors == []
    assert model is not None
    assert len(model.audiences) == 6
    assert len(model.outputFormats) == 3
    assert model.generation.totalOutputsPerRun == 18


def test_rejects_age_range_crossing_bands(valid_brief_data):
    """Audience age range crossing the 20-24 (younger) and 25-30 (older) boundary is rejected."""
    data = copy.deepcopy(valid_brief_data)
    data["audiences"][0]["age"]["minimum"] = 23
    data["audiences"][0]["age"]["maximum"] = 26  # crosses 24/25

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("crosses across the 20–24" in err for err in errors)


def test_rejects_wrong_product_color_for_younger_audience(valid_brief_data):
    """Younger audience (age <= 24) must use orange cooler."""
    data = copy.deepcopy(valid_brief_data)
    data["audiences"][0]["productColor"] = "white"  # P01 is age 20-23

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("MUST use 'orange' product" in err for err in errors)


def test_rejects_wrong_product_color_for_older_audience(valid_brief_data):
    """Older audience (age >= 25) must use white cooler."""
    data = copy.deepcopy(valid_brief_data)
    data["audiences"][2]["productColor"] = "orange"  # P03 is age 25-27

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("MUST use 'white' product" in err for err in errors)


def test_rejects_wrong_activity_to_background_pool(valid_brief_data):
    """Beach audience must resolve strictly to beach background pool."""
    data = copy.deepcopy(valid_brief_data)
    data["audiences"][2]["backgroundPoolId"] = "camping-la-mountains"  # P03 is beach

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("must resolve strictly to 'beach-west-coast'" in err for err in errors)


def test_rejects_camping_with_black_tagline(valid_brief_data):
    """Camping tagline pool cannot have black text color."""
    data = copy.deepcopy(valid_brief_data)
    # Find camping tagline pool
    for pool in data["taglinePools"]:
        if pool["id"] == "camping-taglines":
            pool["textColor"] = "#000000"

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("must have white text (#FFFFFF)" in err for err in errors)


def test_rejects_beach_with_white_tagline(valid_brief_data):
    """Beach tagline pool cannot have white text color."""
    data = copy.deepcopy(valid_brief_data)
    for pool in data["taglinePools"]:
        if pool["id"] == "beach-taglines":
            pool["textColor"] = "#FFFFFF"

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("must have black text (#000000)" in err for err in errors)


def test_rejects_invalid_audience_count(valid_brief_data):
    """Brief must contain exactly 6 audiences."""
    data = copy.deepcopy(valid_brief_data)
    data["audiences"].pop()  # now 5 audiences

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("at least 6 items" in err or "exactly 6 audiences" in err for err in errors)


def test_rejects_missing_output_format(valid_brief_data):
    """Brief must contain exactly the 3 required formats (1:1, 16:9, 9:16)."""
    data = copy.deepcopy(valid_brief_data)
    data["outputFormats"] = [
        {"id": "square", "aspectRatio": "1:1", "width": 1080, "height": 1080, "filenameTag": "1x1"}
    ]

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("at least 3 items" in err or "exactly the three standard formats" in err for err in errors)


def test_rejects_absolute_paths(valid_brief_data):
    """Absolute paths are rejected for security and portability."""
    data = copy.deepcopy(valid_brief_data)
    data["assetCatalog"]["brand-logo"] = "/Users/joem/assets/brand/logo.png"

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("Security Error" in err and "absolute path" in err for err in errors)


def test_rejects_parent_directory_traversal(valid_brief_data):
    """Directory traversal paths (..) are rejected."""
    data = copy.deepcopy(valid_brief_data)
    data["productAssets"]["orange"]["assetPath"] = "../secret/cooler.png"

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("Security Error" in err and "parent traversal" in err for err in errors)


def test_rejects_obsolete_black_tagline_layer(valid_brief_data):
    """LayersBackToFront must not hardcode 'blackTagline'."""
    data = copy.deepcopy(valid_brief_data)
    data["composition"]["layersBackToFront"] = [
        "selectedBackground",
        "productShadow",
        "selectedProductAsset",
        "blackTagline",
        "brandLogo"
    ]

    is_valid, model, errors = validate_brief_dict(data)
    assert is_valid is False
    assert any("blackTagline" in err for err in errors)
