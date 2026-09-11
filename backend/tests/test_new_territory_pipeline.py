"""Exercise new-territory routing through real composition, using local test images."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from backend.app.models.brief_conversion import BriefIntent
from backend.app.models.generation import GeneratedBackgroundMetadata
from backend.app.services.brief_converter import compile_brief
from backend.app.services import pipeline_runner
from backend.app.services.storage.local import LocalStorageAdapter


def new_territory_brief(total=12):
    return compile_brief(BriefIntent(
        name="Inland Empire", market="Inland Empire", objective=None,
        audiences=[dict(name="Inland Empire Campers", minimumAge=41, maximumAge=120,
            lifeStage="Adult outdoor enthusiasts", activity="camping", territory="Inland Empire",
            visualDirection="Local foothills and a quiet campsite", backgroundPoolId=None,
            productModel="YETI Tundra 45")],
        formatIds=None, conceptsPerAudience=None, totalOutputs=total, seed=42,
        assumptions=[], questions=[],
    ))["brief"]


@pytest.fixture
def runner(tmp_path, monkeypatch):
    storage = LocalStorageAdapter(root_dir=str(tmp_path / "storage"))
    monkeypatch.setattr(pipeline_runner, "get_storage_adapter", lambda: storage)
    provider = MagicMock()
    def generate(**kwargs):
        target = tmp_path / f"gen-bg-camping-{provider.generate_for_audience.call_count}.png"
        Image.new("RGB", (1080, 1080), (60, 85, 55)).save(target)
        return GeneratedBackgroundMetadata(
            background_id=target.stem, activity=kwargs["activity"], territory=kwargs["territory"],
            prompt=kwargs["custom_prompt_suffix"], negative_prompt="", model_used="test-provider",
            duration_ms=1, dimensions=(1080,1080), local_path=str(target),
            ai_generated_background=True, is_mock=False, human_review_required=True, provenance="google-genai",
        )
    provider.generate_for_audience.side_effect = generate
    return pipeline_runner.CampaignPipelineRunner(storage_adapter=storage, gemini_generator=provider,
        local_base_dir=str(tmp_path / "outputs"))


def test_new_pool_routes_location_and_direction_to_generation(runner):
    result = runner.execute_campaign(new_territory_brief(), seed=42)
    assert result.total_outputs == 12
    assert len({ad.local_path for ad in result.ads}) == 12
    assert all(Path(ad.local_path).exists() for ad in result.ads)
    assert all(ad.territory == "Inland Empire" for ad in result.ads)
    assert all(ad.product_color == "white" and ad.human_review_required for ad in result.ads)
    assert runner.gemini.generate_for_audience.call_count == 4
    for call in runner.gemini.generate_for_audience.call_args_list:
        assert call.kwargs["territory"] == "Inland Empire"
        assert call.kwargs["custom_prompt_suffix"] == "Local foothills and a quiet campsite"


def test_placeholder_cannot_be_reported_as_a_generated_territory(runner):
    original = runner.gemini.generate_for_audience.side_effect
    def placeholder(**kwargs):
        result = original(**kwargs)
        return result.model_copy(update={"is_mock": True, "ai_generated_background": False, "provenance": "mock-generator"})
    runner.gemini.generate_for_audience.side_effect = placeholder
    with pytest.raises(RuntimeError, match="procedural placeholder"):
        runner.execute_campaign(new_territory_brief(), seed=42)


def test_twenty_ads_produce_twenty_unique_files_and_pass_count_checks(runner):
    from collections import Counter
    result = runner.execute_campaign(new_territory_brief(20), seed=42)
    assert result.total_outputs == 20
    assert result.total_concepts == 7
    assert len({ad.local_path for ad in result.ads}) == 20
    assert Counter(ad.aspect_ratio for ad in result.ads) == {"1:1": 7, "16:9": 7, "9:16": 6}
    assert all(Path(ad.local_path).exists() for ad in result.ads)
    report = result.quality_report
    if hasattr(report, 'model_dump'):
        report = report.model_dump()
    for check in report['checks']:
        if check['check_id'] in {'BLK-01', 'BLK-07'}:
            assert check['passed'], check['details']
