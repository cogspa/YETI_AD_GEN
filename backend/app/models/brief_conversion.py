# ==============================================================================
# PYDANTIC VALIDATION CONTRACT: BRIEF CONVERSION & INTENT EXTRACTION
# ==============================================================================
# Defines closed, strictly-validated schemas for AI brief-to-JSON conversion.
# Compatible with both OpenAI Strict Structured Outputs and Google Gemini JSON Schemas.
# Enforces bounds to prevent hallucinated structures and payload injections.
# ==============================================================================

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


# PYDANTIC RULE: extra="forbid" rejects any undeclared keys for schema rigidity
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# PYDANTIC RULE (BriefConversionRequest):
# 1. Field bounds: raw user prompt text must be between 10 and 12,000 characters.
# 2. Field validator (`trim_text`, mode="before"): strips whitespace before validation.
class BriefConversionRequest(StrictModel):
    text: str = Field(min_length=10, max_length=12000)

    @field_validator("text", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


# PYDANTIC RULE (AudienceIntent):
# 1. Closed schema with extra="forbid".
# 2. Strict age bounds: ge=20, le=120.
# 3. String length caps to prevent unbounded prompt expansion.
# 4. Strict product model Literal restricted to approved SKUs.
class AudienceIntent(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    minimumAge: int = Field(ge=20, le=120)
    maximumAge: int = Field(ge=20, le=120)
    lifeStage: str = Field(min_length=1, max_length=200)
    activity: str = Field(min_length=1, max_length=80)
    territory: str = Field(min_length=1, max_length=200)
    visualDirection: str | None = Field(max_length=1500)
    backgroundPoolId: str | None = Field(max_length=100)
    productModel: Literal["YETI Roadie 24", "YETI Tundra 45"]


# PYDANTIC RULE (BriefIntent):
# Bounded extraction container for LLM Structured Outputs:
# 1. Nullable fields represent unspecified optional parameters.
# 2. Audiences list capped at 24.
# 3. Format IDs restricted to Literal["square", "landscape", "vertical"] (max 3).
# 4. Concepts per audience bounded between 1 and 10.
# 5. Total outputs bounded between 1 and 216.
# 6. Assumptions and questions capped at 20 and 10 items.
class BriefIntent(StrictModel):
    # Every extraction field is required; null means the user did not specify it.
    name: str | None = Field(max_length=120)
    market: str | None = Field(max_length=200)
    objective: str | None = Field(max_length=1000)
    audiences: list[AudienceIntent] | None = Field(max_length=24)
    formatIds: list[Literal["square", "landscape", "vertical"]] | None = Field(max_length=3)
    conceptsPerAudience: int | None = Field(ge=1, le=10)
    totalOutputs: int | None = Field(ge=1, le=216)
    seed: int | None
    assumptions: list[str] = Field(max_length=20)
    questions: list[str] = Field(max_length=10)

