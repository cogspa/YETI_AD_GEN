"""FastAPI Backend Application for YETI Creative Automation."""

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
