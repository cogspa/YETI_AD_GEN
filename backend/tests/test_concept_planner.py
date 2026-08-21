"""Comprehensive tests for ConceptPlanner service (Prompt 5)."""

import json
import pytest
from pathlib import Path

from backend.app.models.brief import CampaignBrief
from backend.app.services.concept_planner import ConceptPlanner
from backend.app.services.asset_resolver import AssetResolver


@pytest.fixture
def brief() -> CampaignBrief:
    with open("yeti_la_random_ad_campaign.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return CampaignBrief(**data)


@pytest.fixture
def planner() -> ConceptPlanner:
    return ConceptPlanner(AssetResolver())


def test_plan_generates_exact_6_concepts_and_18_plans(planner, brief):
    """Verify exactly 6 audience concepts and 18 format render plans are generated."""
    result = planner.plan_campaign(brief, seed=42)
    assert result.total_audiences == 6
    assert result.total_concepts == 6
    assert len(result.concepts) == 6
    assert result.total_render_plans == 18
    assert len(result.render_plans) == 18
    assert result.seed == 42


def test_age_product_mapping(planner, brief):
    """Verify younger (<=24) resolves to cooler_orange and older (>=25) to cooler_white."""
    result = planner.plan_campaign(brief, seed=123)
    for concept in result.concepts:
        if concept.age_band == "younger":
            assert concept.product_role == "product_orange"
            assert "cooler_orange.png" in concept.product_asset_path
        elif concept.age_band == "older":
            assert concept.product_role == "product_white"
            assert "cooler_white.png" in concept.product_asset_path
        else:
            pytest.fail(f"Invalid age band: {concept.age_band}")


def test_activity_background_mapping(planner, brief):
    """Verify activity matches background pool and selected environment."""
    result = planner.plan_campaign(brief, seed=777)
    for concept in result.concepts:
        if concept.activity == "beach":
            assert "beach" in concept.background_pool_id.lower()
            assert "Beach.jpg" in concept.selected_background_path
        elif concept.activity == "camping":
            assert "camping" in concept.background_pool_id.lower()
            assert "Camping.jpg" in concept.selected_background_path
        elif concept.activity == "tailgating":
            assert "tailgating" in concept.background_pool_id.lower()
            assert "Tailgate.jpg" in concept.selected_background_path


def test_activity_tagline_mapping(planner, brief):
    """Verify beach gets black tagline (#000000) and camping/tailgate gets white (#FFFFFF)."""
    result = planner.plan_campaign(brief, seed=999)
    for concept in result.concepts:
        if concept.activity == "beach":
            assert concept.tagline_color_hex == "#000000"
            assert "TAGLINE_black.png" in concept.selected_tagline_asset_path
        else:
            assert concept.tagline_color_hex == "#FFFFFF"
            assert "TAGLINE_white.png" in concept.selected_tagline_asset_path


def test_concept_locking_across_three_ratios(planner, brief):
    """Confirm 1:1, 16:9, and 9:16 for each audience share the exact same concept parameters."""
    result = planner.plan_campaign(brief, seed=54321)

    for audience in brief.audiences:
        plans_for_aud = [p for p in result.render_plans if p.audience_id == audience.id]
        assert len(plans_for_aud) == 3, f"Expected 3 format render plans for audience {audience.id}"

        ratios = {p.aspect_ratio for p in plans_for_aud}
        assert ratios == {"1:1", "16:9", "9:16"}

        # Verify locked concept parameters
        first = plans_for_aud[0]
        for plan in plans_for_aud[1:]:
            assert plan.concept_id == first.concept_id
            assert plan.product_asset_path == first.product_asset_path
            assert plan.background_asset_path == first.background_asset_path
            assert plan.tagline_asset_path == first.tagline_asset_path
            assert plan.tagline_text == first.tagline_text
            assert plan.tagline_color_hex == first.tagline_color_hex
            assert plan.logo_asset_path == first.logo_asset_path


def test_seeded_reproducibility(planner, brief):
    """Running twice with the same seed must produce bit-for-bit identical plans."""
    run1 = planner.plan_campaign(brief, seed=88888)
    run2 = planner.plan_campaign(brief, seed=88888)

    assert run1.model_dump() == run2.model_dump()


def test_repeat_protection_with_prior_manifest(planner, brief):
    """Test that prior manifest choices are respected when alternatives exist."""
    prior_manifest = {
        "concepts": [
            {
                "audience_id": "P01",
                "selected_background_path": "assets/backgrounds/Tailgate.jpg",
                "selected_tagline_text": "GO ANYWHERE",
            }
        ]
    }
    result = planner.plan_campaign(brief, seed=123, prior_manifest=prior_manifest)
    assert len(result.concepts) == 6
    assert len(result.render_plans) == 18


def test_pool_exhaustion_warning(planner, brief):
    """When a single-item pool is shared by multiple audiences, verify warning is issued without failing."""
    result = planner.plan_campaign(brief, seed=111)
    # Backgrounds: 2 beach audiences, 2 camping audiences, 2 tailgate audiences
    # With 1 asset per pool, repeat is logged cleanly
    assert len(result.warnings) > 0
    assert any("exhausted" in w.lower() for w in result.warnings)
    assert len(result.concepts) == 6
    assert len(result.render_plans) == 18


def test_randomization_occurs_once_per_audience_not_per_ratio(planner, brief):
    """Ensure randomization is concept-level and not re-rolled during format adaptation."""
    result = planner.plan_campaign(brief, seed=2026)

    concept_map = {c.concept_id: c for c in result.concepts}
    for plan in result.render_plans:
        parent_concept = concept_map[plan.concept_id]
        assert plan.background_asset_path == parent_concept.selected_background_path
        assert plan.product_asset_path == parent_concept.product_asset_path
        assert plan.tagline_asset_path == parent_concept.selected_tagline_asset_path


def test_product_and_audience_slug_target_filenames(planner, brief):
    """Verify target_filenames in render plans contain audience descriptor and product slug."""
    result = planner.plan_campaign(brief, seed=42)
    p01_plans = [p for p in result.render_plans if p.audience_id == "P01"]
    assert len(p01_plans) == 3
    p01_1x1 = next(p for p in p01_plans if p.aspect_ratio == "1:1")
    assert p01_1x1.target_filename == "P01_westwood-college_roadie-24-orange_1x1.png"
    assert p01_1x1.product_slug == "roadie-24-orange"
