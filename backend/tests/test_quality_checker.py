"""Tests for Deterministic Quality Checks, Blocking Rules, and Secret Redaction (Step 10)."""

import pytest
import copy
from pathlib import Path
from backend.app.models.brief import CampaignBriefModel
from backend.app.services.concept_planner import ConceptPlanner
from backend.app.services.asset_resolver import AssetResolver
from backend.app.services.quality_checker import QualityChecker, redact_secrets
from backend.app.services.pipeline_runner import CampaignPipelineRunner


@pytest.fixture(scope="module")
def sample_brief():
    import json
    with open("yeti_la_random_ad_campaign.json", "r") as f:
        data = json.load(f)
    return CampaignBriefModel.model_validate(data)


@pytest.fixture(scope="module")
def quality_checker():
    return QualityChecker(base_asset_dir="assets")


@pytest.fixture(scope="module")
def valid_run_result(sample_brief):
    runner = CampaignPipelineRunner()
    return runner.execute_campaign(sample_brief.model_dump(), seed=42)


def test_secret_redaction():
    """Verify that all secret patterns (Dropbox tokens, Gemini keys, Bearer auth) are deterministically redacted."""
    raw_log = "Uploaded with token sl.u.AF329847293847293847293847293847293847293847293847293847293847293847293847 and key AIzaSyA1234567890123456789012345678901 and Bearer secret_bearer_token_1234567890"
    redacted = redact_secrets(raw_log)

    assert "sl.u." not in redacted
    assert "[REDACTED_DROPBOX_TOKEN]" in redacted or "[REDACTED_TOKEN]" in redacted
    assert "AIzaSy" not in redacted
    assert "[REDACTED_GEMINI_KEY]" in redacted or "[REDACTED_KEY]" in redacted
    assert "secret_bearer_token_1234567890" not in redacted


def test_quality_checker_passes_valid_run(valid_run_result):
    """Verify that a valid standard campaign run passes all 8 blocking checks."""
    assert valid_run_result.status == "success"
    report = valid_run_result.quality_report
    assert report is not None
    assert report["blocking_checks_passed"] == 8
    assert report["blocking_checks_total"] == 8
    assert report["status"] in ("passed", "passed_with_warnings")


def test_blocking_check_fails_on_dimension_mismatch(sample_brief, valid_run_result, quality_checker):
    """Verify BLK-02 fails if any ad has non-standard dimensions."""
    # Mutate dimensions of first ad
    tampered_ads = copy.deepcopy(valid_run_result.ads)
    tampered_ads[0].dimensions = (1000, 1000)

    report = quality_checker.run_all_checks(
        brief=sample_brief,
        concepts=valid_run_result.concepts,
        ads=tampered_ads,
        run_id="test-run",
        seed=42,
        storage_mode="local",
    )

    assert report.status == "failed"
    blk_02 = next(c for c in report.checks if c.check_id == "BLK-02")
    assert blk_02.passed is False
    assert any("Dimension mismatches" in e for e in report.errors)


def test_blocking_check_fails_on_age_product_color_mismatch(sample_brief, valid_run_result, quality_checker):
    """Verify BLK-04 fails if younger audience receives white cooler or older receives orange."""
    # Tamper concept 0 (younger) to have white cooler
    tampered_concepts = copy.deepcopy(valid_run_result.concepts)
    tampered_concepts[0].product_role = "product_white"

    report = quality_checker.run_all_checks(
        brief=sample_brief,
        concepts=tampered_concepts,
        ads=valid_run_result.ads,
        run_id="test-run",
        seed=42,
        storage_mode="local",
    )

    assert report.status == "failed"
    blk_04 = next(c for c in report.checks if c.check_id == "BLK-04")
    assert blk_04.passed is False


def test_blocking_check_fails_on_tagline_color_violation(sample_brief, valid_run_result, quality_checker):
    """Verify BLK-06 fails if Beach uses white tagline or Camping uses black tagline."""
    # Find a beach concept and give it white tagline
    tampered_concepts = copy.deepcopy(valid_run_result.concepts)
    for c in tampered_concepts:
        if c.activity == "beach":
            c.tagline_color_hex = "#FFFFFF"

    report = quality_checker.run_all_checks(
        brief=sample_brief,
        concepts=tampered_concepts,
        ads=valid_run_result.ads,
        run_id="test-run",
        seed=42,
        storage_mode="local",
    )

    assert report.status == "failed"
    blk_06 = next(c for c in report.checks if c.check_id == "BLK-06")
    assert blk_06.passed is False


def test_blocking_check_fails_on_missing_format_locking(sample_brief, valid_run_result, quality_checker):
    """Verify BLK-07 fails if an audience has fewer than 3 formats or missing ratio."""
    # Remove 9:16 format from first concept
    target_cid = valid_run_result.concepts[0].concept_id
    tampered_ads = [a for a in valid_run_result.ads if not (a.concept_id == target_cid and a.aspect_ratio == "9:16")]

    report = quality_checker.run_all_checks(
        brief=sample_brief,
        concepts=valid_run_result.concepts,
        ads=tampered_ads,
        run_id="test-run",
        seed=42,
        storage_mode="local",
    )

    assert report.status == "failed"
    blk_07 = next(c for c in report.checks if c.check_id == "BLK-07")
    assert blk_07.passed is False
