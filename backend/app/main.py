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
from backend.app.services.asset_resolver import AssetResolver


app = FastAPI(
    title="YETI Ad Generator API",
    description="Creative Automation backend for scalable social campaigns.",
    version="1.0.0",
)

# CORS middleware for local Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resolver = AssetResolver()


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


@app.post("/api/campaign/generate", response_model=CampaignRunResult)
def generate_campaign_endpoint(
    brief: Dict[str, Any] = Body(...),
    seed: Optional[int] = None,
):
    """Executes end-to-end 18-ad campaign generation pipeline."""
    try:
        run_result = runner.execute_campaign(brief_dict=brief, seed=seed)
        return run_result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Ensure outputs directory exists
Path("outputs").mkdir(parents=True, exist_ok=True)

# Mount static files to serve generated ads, contact sheets, and zip archives
app.mount("/api/outputs", StaticFiles(directory="outputs", check_dir=False), name="outputs")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
