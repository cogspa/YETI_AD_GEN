"""Pydantic models for Deterministic Quality Checks and Run Reports (Step 10)."""

from typing import List, Dict, Optional, Tuple, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class CheckResult(BaseModel):
    """Result of a single deterministic quality check rule."""
    check_id: str
    check_name: str
    category: Literal["blocking", "warning", "heuristic"]
    passed: bool
    details: str
    metrics: Optional[Dict[str, Any]] = None


class AudienceAudit(BaseModel):
    """Detailed audit per audience concept and its format renderings."""
    audience_id: str
    audience_name: str
    age_band: str
    activity: str
    territory: str
    product_role: str
    product_hash: str
    background_path: str
    tagline_text: str
    tagline_color: str
    contrast_score: float
    busyness_score: float
    safe_area_passed: bool
    aspect_ratio_preserved: bool
    provenance: str
    human_review_required: bool


class QualityReport(BaseModel):
    """Deterministic Quality Assurance & Compliance Report."""
    report_id: str
    campaign_id: str
    campaign_name: str
    run_id: str
    seed: int
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["passed", "passed_with_warnings", "failed"]
    total_checks_run: int
    blocking_checks_passed: int
    blocking_checks_total: int
    warning_count: int
    checks: List[CheckResult]
    audience_audits: List[AudienceAudit]
    warnings: List[str]
    errors: List[str]
    provenance_summary: str
    storage_mode: str
