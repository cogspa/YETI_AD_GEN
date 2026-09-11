"""Conversion tests use a simulated provider; no paid API calls or ad generation."""

import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.models.brief_conversion import BriefIntent, BriefConversionRequest
from backend.app.services import brief_converter as converter
from backend.app.services.brief_validator import validate_brief_dict


@pytest.fixture(autouse=True)
def isolate_provider_settings(monkeypatch):
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_BRIEF_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_BRIEF_MODEL", raising=False)


def intent(**changes):
    data = dict(name=None, market=None, objective=None, audiences=None, formatIds=None,
                conceptsPerAudience=None, totalOutputs=None, seed=None,
                assumptions=[], questions=[])
    data.update(changes)
    return BriefIntent.model_validate(data)


def audience(**changes):
    data = dict(name="LA Beachgoers", minimumAge=20, maximumAge=30,
                lifeStage="Students and young professionals", backgroundPoolId="beach-west-coast",
                productModel="YETI Roadie 24", activity="beach", territory="Westside Los Angeles coast", visualDirection=None)
    data.update(changes)
    if data["backgroundPoolId"] == "hiking-la-trails":
        data.update(activity="hiking", territory="Hollywood Hills and Griffith Park")
    return data


def test_defaults_compile_to_existing_schema():
    result = converter.compile_brief(intent())
    valid, model, errors = validate_brief_dict(result["brief"])
    assert valid, errors
    assert result["summary"] == {"audienceCount": 6, "formatCount": 3, "totalOutputs": 18}
    assert model.generation.adsPerAudience == 3
    assert model.output["directory"] == f"outputs/{model.campaign.id}"
    assert model.campaign.id != "yeti-la-go-anywhere-2026"
    assert model.generation.repeatProtection.priorManifestPath.startswith(model.output["directory"])
    assert all(p.taglines == ["GO ANYWHERE"] for p in model.taglinePools)


def test_age_band_split_and_exact_quantity():
    result = converter.compile_brief(intent(audiences=[audience()], totalOutputs=12))
    brief = result["brief"]
    assert [a["productColor"] for a in brief["audiences"]] == ["orange", "white"]
    assert [a["age"]["band"] for a in brief["audiences"]] == ["younger", "older"]
    assert brief["generation"]["conceptsPerAudience"] == 2
    assert brief["generation"]["adsPerAudience"] == 6
    assert len(brief["backgroundPools"]) == 1
    assert brief["taglinePools"][0]["textColor"] == "#000000"
    assert any("Split" in item for item in result["assumptions"])


def test_selected_format_and_generated_background():
    result = converter.compile_brief(intent(audiences=[audience(minimumAge=25, backgroundPoolId="hiking-la-trails")], formatIds=["vertical"], totalOutputs=2))
    brief = result["brief"]
    assert result["summary"]["totalOutputs"] == 2
    assert brief["outputFormats"][0]["width"] == 1080
    assert brief["outputFormats"][0]["height"] == 1920
    assert brief["backgroundPools"][0]["assets"] == []
    assert brief["taglinePools"][0]["textColor"] == "#FFFFFF"
    assert result["warnings"]


@pytest.mark.parametrize("changes,match", [
    ({"totalOutputs": 5}, "at least 6"),
    ({"totalOutputs": 36, "conceptsPerAudience": 1}, "conflicts"),
    ({"audiences": []}, "at least one"),
    ({"formatIds": []}, "distinct formats"),
    ({"formatIds": ["square", "square"]}, "distinct formats"),
    ({"questions": ["Which supported market?"]}, "clarify"),
    ({"audiences": [audience(minimumAge=29, maximumAge=25)]}, "reversed"),
])
def test_conflicting_requests_do_not_produce_a_draft(changes, match):
    with pytest.raises(converter.BriefConversionError, match=match):
        converter.compile_brief(intent(**changes))


def test_compiler_does_not_mutate_templates():
    first = converter.compile_brief(intent(audiences=[audience()]))
    second = converter.compile_brief(intent())
    assert len(first["brief"]["audiences"]) == 2
    assert len(second["brief"]["audiences"]) == 6


@pytest.mark.parametrize("count", [1, 2, 7, 20, 29])
def test_arbitrary_exact_counts(count):
    result = converter.compile_brief(intent(audiences=[audience(minimumAge=35, maximumAge=35)], totalOutputs=count))
    valid, model, errors = validate_brief_dict(result["brief"])
    assert valid, errors
    assert model.generation.exactOutputCount == count
    assert model.generation.totalOutputsPerRun == count
    assert sum(result["formatCounts"].values()) == count
    assert max(result["formatCounts"].values()) - min(result["formatCounts"].values()) <= 1
    if count == 20:
        assert result["formatCounts"] == {"square": 7, "landscape": 7, "vertical": 6}


def test_exact_count_spread_across_multiple_audiences():
    result = converter.compile_brief(intent(totalOutputs=20))
    from backend.app.services.output_allocation import allocate_outputs
    _, model, _ = validate_brief_dict(result["brief"])
    allocation = allocate_outputs(model)
    counts = [sum(map(len, groups)) for groups in allocation.values()]
    assert sum(counts) == 20
    assert sorted(counts) == [3, 3, 3, 3, 4, 4]
    assert model.generation.adsPerAudience is None


def test_new_territory_and_over_40_audience_create_generated_pool():
    result = converter.compile_brief(intent(market="Inland Empire, California", totalOutputs=12,
        audiences=[audience(name="Inland Empire campers", minimumAge=41, maximumAge=120,
            activity="camping", territory="Inland Empire, California", backgroundPoolId=None,
            visualDirection="A campsite near local foothills in warm evening light.")]))
    brief = result["brief"]
    assert result["summary"] == {"audienceCount": 1, "formatCount": 3, "totalOutputs": 12}
    assert brief["generation"]["conceptsPerAudience"] == 4
    assert brief["audiences"][0]["age"] == {"minimum": 41, "maximum": 120, "band": "older"}
    assert brief["audiences"][0]["productColor"] == "white"
    pool = brief["backgroundPools"][0]
    assert pool["assets"] == []
    assert pool["territory"] == brief["campaign"]["market"] == "Inland Empire, California"
    assert pool["id"] == brief["audiences"][0]["backgroundPoolId"]
    assert brief["activityRules"]["camping"]["allowedBackgroundPoolIds"] == [pool["id"]]
    assert "foothills" in pool["visualDirection"]


def test_mismatched_catalog_id_cannot_reuse_an_unrelated_photo():
    result = converter.compile_brief(intent(audiences=[audience(territory="Miami, Florida")]))
    pool = result["brief"]["backgroundPools"][0]
    assert pool["id"] != "beach-west-coast"
    assert pool["territory"] == "Miami, Florida"
    assert pool["assets"] == []


def test_two_territories_get_distinct_pools():
    result = converter.compile_brief(intent(audiences=[
        audience(territory="Miami, Florida", minimumAge=41, maximumAge=60),
        audience(territory="San Diego, California", minimumAge=41, maximumAge=60),
    ]))
    assert len(result["brief"]["backgroundPools"]) == 2
    assert len({a["backgroundPoolId"] for a in result["brief"]["audiences"]}) == 2


def test_open_ended_activity_skiing_compiles_and_validates():
    result = converter.compile_brief(intent(
        market="Compton, California",
        totalOutputs=6,
        audiences=[audience(
            name="Ed from Compton",
            minimumAge=32,
            maximumAge=32,
            activity="skiing",
            territory="Compton, California",
            backgroundPoolId=None,
            visualDirection="Ed skiing on snowy mountain slopes.",
        )],
    ))
    valid, model, errors = validate_brief_dict(result["brief"])
    assert valid, errors
    brief = result["brief"]
    assert brief["audiences"][0]["activity"] == "skiing"
    assert brief["audiences"][0]["productColor"] == "white"
    assert brief["audiences"][0]["taglinePoolId"] == "skiing-taglines"
    assert len(brief["taglinePools"]) == 1
    assert brief["taglinePools"][0]["id"] == "skiing-taglines"
    assert brief["taglinePools"][0]["textColor"] == "#FFFFFF"
    assert "skiing" in brief["activityRules"]
    assert brief["activityRules"]["skiing"]["taglineTextColor"] == "#FFFFFF"


def test_extraction_schema_is_closed_and_all_properties_required():
    schema = BriefIntent.model_json_schema()
    for item in [schema, *schema["$defs"].values()]:
        assert item["additionalProperties"] is False
        assert set(item["required"]) == set(item["properties"])


def mock_provider(monkeypatch, body, status=200):
    captured = []

    def handle(request):
        captured.append(json.loads(request.content))
        return httpx.Response(status, json=body)

    original = httpx.AsyncClient
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(converter.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    return captured


def completed(text):
    return {"status": "completed", "output": [
        {"type": "reasoning", "summary": []},
        {"type": "message", "content": [{"type": "output_text", "text": text}]},
    ]}


@pytest.mark.asyncio
async def test_provider_contract_and_success(monkeypatch):
    captured = mock_provider(monkeypatch, completed(intent(totalOutputs=36).model_dump_json()))
    result = await converter.convert_natural_language_brief("Create 36 ads for the standard YETI audiences.")
    assert result["summary"]["totalOutputs"] == 36
    assert captured[0]["model"] == "gpt-6-astra"
    assert captured[0]["text"]["format"]["strict"] is True
    assert captured[0]["store"] is False
    assert captured[0]["input"][1]["role"] == "user"
    assert "temperature" not in captured[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("body,status,expected", [
    (completed("not json"), 200, 502),
    ({"status": "incomplete", "output": []}, 200, 502),
    ({"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "No"}]}]}, 200, 422),
    ({"error": {"message": "secret provider details"}}, 401, 502),
    ({"error": {"message": "secret provider details"}}, 429, 503),
])
async def test_provider_errors_are_actionable_and_do_not_leak_details(monkeypatch, body, status, expected):
    mock_provider(monkeypatch, body, status)
    with pytest.raises(converter.BriefConversionError) as caught:
        await converter.convert_natural_language_brief("Create YETI ads")
    assert caught.value.status_code == expected
    assert "secret" not in str(caught.value)


@pytest.mark.asyncio
async def test_unconfigured_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(converter.BriefConversionError, match="OPENAI_API_KEY") as caught:
        await converter.convert_natural_language_brief("Create YETI ads")
    assert caught.value.status_code == 503


def test_endpoint_validates_text_and_preserves_error_details(monkeypatch):
    # Import registers the production handler; isolate it from all generation routes.
    from backend.app.main import convert_brief_endpoint
    app = FastAPI()
    app.post("/api/brief/convert")(convert_brief_endpoint)
    client = TestClient(app)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "openai")
    for text in ["", "   ", "short", "a" * 12001]:
        assert client.post("/api/brief/convert", json={"text": text}).status_code == 422
    result = client.post("/api/brief/convert", json={"text": "Create 18 YETI ads."})
    assert result.status_code == 503
    assert "OPENAI_API_KEY" in result.json()["detail"]["message"]
    assert BriefConversionRequest(text="  Create 18 ads.  ").text == "Create 18 ads."


def gemini_completed(text):
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"thought": True, "text": "Internal reasoning is not the JSON draft."},
        {"text": text},
    ]}}]}


@pytest.mark.asyncio
async def test_gemini_success_uses_same_schema_and_compiler(monkeypatch):
    captured = mock_provider(monkeypatch, gemini_completed(intent(totalOutputs=36).model_dump_json()))
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = await converter.convert_natural_language_brief("Create 36 YETI ads for Los Angeles.")
    assert result["summary"]["totalOutputs"] == 36
    assert validate_brief_dict(result["brief"])[0]
    schema = captured[0]["generationConfig"]["responseJsonSchema"]
    assert set(schema["required"]) == set(BriefIntent.model_fields)
    assert schema["additionalProperties"] is False
    assert '"$ref"' not in json.dumps(schema)
    assert '"maxLength"' not in json.dumps(schema)
    assert captured[0]["contents"][0]["role"] == "user"
    assert "systemInstruction" in captured[0]
    assert "reasoning" not in captured[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("body,status,expected", [
    (gemini_completed("not json"), 200, 502),
    ({"candidates": []}, 200, 502),
    ({"candidates": [{"finishReason": "MAX_TOKENS"}]}, 200, 502),
    ({"candidates": [{"finishReason": "SAFETY"}]}, 200, 422),
    ({"promptFeedback": {"blockReason": "SAFETY"}}, 200, 422),
    ({"error": {"message": "secret provider details"}}, 403, 502),
    ({"error": {"message": "secret provider details"}}, 429, 503),
])
async def test_gemini_failure_does_not_return_a_draft(monkeypatch, body, status, expected):
    mock_provider(monkeypatch, body, status)
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    with pytest.raises(converter.BriefConversionError) as caught:
        await converter.convert_natural_language_brief("Create YETI ads")
    assert caught.value.status_code == expected
    assert "secret" not in str(caught.value)


@pytest.mark.asyncio
async def test_gemini_missing_key_does_not_fall_back_to_openai(monkeypatch):
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with pytest.raises(converter.BriefConversionError, match="GEMINI_API_KEY"):
        await converter.convert_natural_language_brief("Create YETI ads")


@pytest.mark.asyncio
async def test_unknown_provider_is_a_configuration_error(monkeypatch):
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "unsupported")
    with pytest.raises(converter.BriefConversionError, match="BRIEF_CONVERSION_PROVIDER"):
        await converter.convert_natural_language_brief("Create YETI ads")


@pytest.mark.asyncio
async def test_gemini_bounds_are_still_enforced_locally(monkeypatch):
    invalid = intent(audiences=[audience()]).model_dump()
    invalid["audiences"][0]["minimumAge"] = 19
    mock_provider(monkeypatch, gemini_completed(json.dumps(invalid)))
    monkeypatch.setenv("BRIEF_CONVERSION_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    with pytest.raises(converter.BriefConversionError, match="invalid brief"):
        await converter.convert_natural_language_brief("Create YETI ads for LA audiences.")
