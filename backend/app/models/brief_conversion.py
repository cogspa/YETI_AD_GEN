"""Closed extraction schema; trusted code supplies asset paths and campaign rules."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BriefConversionRequest(StrictModel):
    text: str = Field(min_length=10, max_length=12000)

    @field_validator("text", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class AudienceIntent(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    minimumAge: int = Field(ge=20, le=120)
    maximumAge: int = Field(ge=20, le=120)
    lifeStage: str = Field(min_length=1, max_length=200)
    activity: Literal["beach", "camping", "tailgating", "hiking", "surfing", "fishing", "climbing"]
    territory: str = Field(min_length=1, max_length=200)
    visualDirection: str | None = Field(max_length=1500)
    backgroundPoolId: Literal[
        "tailgating-westwood", "tailgating-south-central", "beach-west-coast",
        "camping-la-mountains", "hiking-la-trails", "surfing-pacific-coast",
        "fishing-la-harbor", "climbing-stoney-point",
    ] | None
    productModel: Literal["YETI Roadie 24", "YETI Tundra 45"]


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
