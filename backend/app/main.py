import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(override=True)

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

from backend.app.models.brief import CampaignBriefModel
from backend.app.models.assets import AssetReadinessReport
from backend.app.services.brief_validator import validate_brief_dict
from backend.app.models.brief_conversion import BriefConversionRequest
from backend.app.services.brief_converter import BriefConversionError, convert_natural_language_brief
from backend.app.services.asset_resolver import AssetResolver


app = FastAPI(
    title="YETI Ad Generator API",
    description="Creative Automation backend for scalable social campaigns.",
    version="1.0.0",
)

# CORS middleware for local Vite frontend and Netlify deployments
cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://yeti-ad-generator.netlify.app",
]
if cors_origins_env:
    for o in cors_origins_env.split(","):
        if o.strip() and o.strip() not in allowed_origins:
            allowed_origins.append(o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

resolver = AssetResolver()


from backend.app.models.layout import LAYOUT_CONFIGS, LayoutPreviewRequest
from backend.app.services.layout_preview import render_layout_preview


@app.get("/api/layouts")
def get_default_layouts():
    return {ratio: layout.model_dump() for ratio, layout in LAYOUT_CONFIGS.items()}


@app.post("/api/layout/preview")
def preview_layout(request: LayoutPreviewRequest):
    try:
        return render_layout_preview(request)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="The sample layout could not be rendered. Check the approved preview assets.") from exc


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "YETI Ad Generator", "version": "1.0.0"}


@app.get("/api/assets/readiness", response_model=AssetReadinessReport)
def get_asset_readiness():
    """Returns a truthful readiness report for all required assets."""
    report = resolver.generate_readiness_report()
    return report


from backend.app.services.storage import get_storage_adapter, StorageStatus

@app.get("/api/storage/status", response_model=StorageStatus)
def get_storage_status():
    """Returns storage status (configured/reachable) without leaking secrets."""
    adapter = get_storage_adapter()
    return adapter.get_status()


@app.get("/api/integrations/status")
def get_integrations_status():
    """Returns live readiness for Storage and Gemini AI scene provider."""
    storage_adapter = get_storage_adapter()
    gemini_gen = GeminiBackgroundGenerator()
    return {
        "storage": storage_adapter.get_status().model_dump(),
        "gemini": {
            "configured": gemini_gen.is_configured(),
            "model": gemini_gen.model_name,
            "status": "active" if gemini_gen.is_configured() else "standby",
        }
    }



@app.post("/api/brief/convert")
async def convert_brief_endpoint(request: BriefConversionRequest):
    """Convert plain language to a validated draft, without rendering or uploading ads."""
    try:
        return await convert_natural_language_brief(request.text)
    except BriefConversionError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"message": str(exc), "errors": exc.errors}) from exc


@app.post("/api/brief/validate")
def validate_brief_endpoint(brief: Dict[str, Any] = Body(...)):
    """Validates campaign brief against strict contract."""
    is_valid, model, errors = validate_brief_dict(brief)
    return {
        "isValid": is_valid,
        "errors": errors,
        "audienceCount": len(model.audiences) if model else 0,
        "formatCount": len(model.outputFormats) if model else 0,
        "totalOutputs": model.generation.totalOutputsPerRun if model else 0,
    }


from backend.app.models.plan import CampaignPlanResult
from backend.app.services.concept_planner import ConceptPlanner

planner = ConceptPlanner(resolver)


@app.post("/api/campaign/plan", response_model=CampaignPlanResult)
def plan_campaign_endpoint(
    brief: Dict[str, Any] = Body(...),
    seed: Optional[int] = None,
):
    """Plans 6 immutable audience concepts and 18 deterministic format render plans."""
    is_valid, model, errors = validate_brief_dict(brief)
    if not is_valid or model is None:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid campaign brief", "errors": errors},
        )

    try:
        plan_result = planner.plan_campaign(model, seed=seed)
        return plan_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from backend.app.models.generation import GeneratedBackgroundMetadata, GenerationRequest
from backend.app.services.gemini_generator import GeminiBackgroundGenerator

generator = GeminiBackgroundGenerator()


@app.post("/api/backgrounds/generate", response_model=GeneratedBackgroundMetadata)
def generate_background_endpoint(req: GenerationRequest = Body(...)):
    """Generates a missing background using Gemini or deterministic mock provider."""
    try:
        bg_meta = generator.generate_background(
            activity=req.activity,
            territory=req.territory,
            custom_prompt_suffix=req.custom_prompt_suffix,
            force_mock=req.force_mock,
        )
        return bg_meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import FileResponse
from backend.app.models.pipeline import CampaignRunResult
from backend.app.services.pipeline_runner import CampaignPipelineRunner

runner = CampaignPipelineRunner()


# ==============================================================================
# INTERVIEW TRACE: Entry Point (Web UI / API Request)
# "Trace one campaign from request to output" -> Stage 0: Ingestion
# React client sends brief JSON + optional seed -> FastAPI forwards to CampaignPipelineRunner
# ==============================================================================
@app.post("/api/campaign/generate", response_model=CampaignRunResult)
def generate_campaign_endpoint(
    brief: Dict[str, Any] = Body(...),
    seed: Optional[int] = None,
):
    """
    Executes end-to-end multi-format campaign generation pipeline.
    
    Trace lifecycle:
      1. Validates brief contract with Pydantic
      2. Resolves & hashes controlled brand assets
      3. Checks repeat history (prior manifest)
      4. Deterministically plans concepts using seed
      5. Generates missing backgrounds via Gemini AI (or procedural fallback)
      6. Composites 3 aspect ratios per concept via Pillow (fit_within_region)
      7. Builds contact sheet & ZIP bundle
      8. Runs 8 blocking quality checks
      9. Syncs outputs & manifest to storage
    """
    try:
        run_result = runner.execute_campaign(brief_dict=brief, seed=seed)
        return run_result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


from pathlib import Path
from fastapi.responses import FileResponse, Response

# Ensure outputs directory exists
Path("outputs").mkdir(parents=True, exist_ok=True)


@app.get("/api/outputs/{file_path:path}")
def serve_output_file(file_path: str):
    """
    Serves output assets (ads, contact sheets, reports, zip archives) reliably
    across multi-instance Cloud Run containers with local caching and cloud storage fallback.
    """
    clean_path = file_path.lstrip("/")
    local_target = Path("outputs") / clean_path

    # 1. Serve immediately if found on local disk
    if local_target.exists() and local_target.is_file():
        return FileResponse(
            path=str(local_target),
            headers={"Cache-Control": "public, max-age=86400"},
        )

    # 2. Resilient Cloud Storage Fallback (Dropbox / Firebase / GCS)
    try:
        storage = get_storage_adapter()
        status = storage.get_status()
        if status.configured:
            # Check storage path: e.g. "campaigns/..." or fallback relative
            remote_candidates = [
                f"campaigns/{clean_path}",
                clean_path,
            ]
            for candidate in remote_candidates:
                try:
                    if storage.exists(candidate):
                        local_target.parent.mkdir(parents=True, exist_ok=True)
                        storage.download(candidate, str(local_target))
                        return FileResponse(
                            path=str(local_target),
                            headers={"Cache-Control": "public, max-age=86400"},
                        )
                except Exception:
                    continue
    except Exception:
        pass

    raise HTTPException(status_code=404, detail=f"Output asset '{file_path}' not found.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
