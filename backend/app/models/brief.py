# ==============================================================================
# PYDANTIC VALIDATION CONTRACT: YETI CAMPAIGN BRIEF
# ==============================================================================
# This module defines the strict Pydantic schemas, field bounds, and custom validators
# governing all campaign briefs. It ensures brand safety, deterministic execution,
# and input integrity before any creative rendering takes place.
# ==============================================================================

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import re
from backend.app.models.layout import LayoutOverride


# PYDANTIC HELPER: Path security sanitizer blocking path traversal and absolute roots
def validate_portable_path(path_str: str, field_name: str) -> str:
    """Ensure path is a safe relative path without leading slashes or parent traversal."""
    if not isinstance(path_str, str) or not path_str.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    
    # Check for absolute path (starts with / or Windows drive like C:)
    if path_str.startswith('/') or re.match(r'^[a-zA-Z]:[\\/]', path_str):
        raise ValueError(
            f"Security Error: {field_name} contains an absolute path ('{path_str}'). Only portable relative paths are allowed."
        )
    
    # Check for directory traversal (..)
    parts = path_str.replace('\\', '/').split('/')
    if '..' in parts:
        raise ValueError(
            f"Security Error: {field_name} contains forbidden parent traversal ('..') in '{path_str}'."
        )
    
    return path_str


# PYDANTIC RULE (CampaignAgeRange):
# 1. Field bounds: minimum and maximum must be between 20 and 120.
# 2. Model validator (`validate_min_max`): ensures minimum does not exceed maximum.
class CampaignAgeRange(BaseModel):
    minimum: int = Field(ge=20, le=120, description="Minimum campaign age")
    maximum: int = Field(ge=20, le=120, description="Maximum campaign age")

    @model_validator(mode="after")
    def validate_min_max(self):
        if self.minimum > self.maximum:
            raise ValueError(f"Age minimum ({self.minimum}) cannot exceed age maximum ({self.maximum}).")
        return self


# PYDANTIC RULE (AudienceAgeRange):
# 1. Field bounds: target age must stay within 20 to 120.
# 2. Model validator (`validate_age_band_integrity`): enforces that a target persona
#    never crosses the 24/25 age boundary. Must be strictly younger (<=24) or older (>=25).
class AudienceAgeRange(BaseModel):
    minimum: int = Field(ge=20, le=120, description="Minimum target age")
    maximum: int = Field(ge=20, le=120, description="Maximum target age")
    band: Optional[Literal["younger", "older"]] = None

    @model_validator(mode="after")
    def validate_age_band_integrity(self):
        if self.minimum > self.maximum:
            raise ValueError(f"Age minimum ({self.minimum}) cannot exceed age maximum ({self.maximum}).")
        
        # Enforce that individual audience age range does not cross younger (20-24) and older (25+) bands
        is_younger = self.maximum <= 24
        is_older = self.minimum >= 25
        
        if not (is_younger or is_older):
            raise ValueError(
                f"Audience age range {self.minimum}–{self.maximum} crosses across the 20–24 (younger) and 25+ (older) age bands. Must belong strictly to one band."
            )
        
        return self


class CampaignMeta(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    market: str
    ageRange: CampaignAgeRange
    objective: str
    campaignLine: str


# PYDANTIC RULE (RepeatProtection):
# Uses @field_validator("priorManifestPath") to verify portable relative path security.
class RepeatProtection(BaseModel):
    scope: str = "run-and-prior-manifest"
    avoidImmediateBackgroundRepeat: bool = True
    avoidImmediateTaglineRepeat: bool = True
    priorManifestPath: Optional[str] = "campaigns/yeti-la-go-anywhere-2026/generation-manifest.json"

    @field_validator("priorManifestPath", mode="before")
    @classmethod
    def check_manifest_path(cls, v: Any) -> Optional[str]:
        if not v:
            return "campaigns/yeti-la-go-anywhere-2026/generation-manifest.json"
        return validate_portable_path(str(v), "repeatProtection.priorManifestPath")


# PYDANTIC RULE (GenerationSettings):
# 1. Field bounds: conceptsPerAudience >= 1, exactOutputCount between 1 and 216.
# 2. Model validator (`validate_quantities`): ensures totalOutputsPerRun matches
#    totalAudienceGroups * adsPerAudience when exactOutputCount is not specified.
class GenerationSettings(BaseModel):
    mode: str = "seeded-random"
    seed: Optional[int] = None
    conceptsPerAudience: int = Field(default=1, ge=1)
    totalAudienceGroups: Optional[int] = Field(default=None, ge=1)
    adsPerAudience: Optional[int] = Field(default=None, ge=1)
    totalOutputsPerRun: Optional[int] = Field(default=None, ge=1)
    exactOutputCount: Optional[int] = Field(default=None, ge=1, le=216)
    randomizeOncePerAudience: bool = True
    renderAllFormatsFromSameConcept: bool = True
    selectionRules: Optional[Dict[str, str]] = None
    repeatProtection: Optional[RepeatProtection] = Field(default_factory=RepeatProtection)

    @model_validator(mode="after")
    def validate_quantities(self):
        if self.exactOutputCount is None and self.totalAudienceGroups and self.adsPerAudience and self.totalOutputsPerRun:
            expected_total = self.totalAudienceGroups * self.adsPerAudience
            if self.totalOutputsPerRun != expected_total:
                # Synchronize if mismatch
                self.totalOutputsPerRun = expected_total
        return self


# PYDANTIC RULE (ProductAsset & TaglineAsset):
# Uses @field_validator("assetPath") to block absolute paths and directory traversal.
class ProductAsset(BaseModel):
    colorName: str
    assetCatalogId: Optional[str] = None
    assetPath: str
    assignedAgeBand: str

    @field_validator("assetPath")
    @classmethod
    def check_path(cls, v: str) -> str:
        return validate_portable_path(v, "productAssets.assetPath")


class TaglineAsset(BaseModel):
    colorName: str
    hex: str
    assetCatalogId: Optional[str] = None
    assetPath: str
    activities: List[str]

    @field_validator("assetPath")
    @classmethod
    def check_path(cls, v: str) -> str:
        return validate_portable_path(v, "taglineAssets.assetPath")


# PYDANTIC RULE (BackgroundPool):
# Uses @field_validator("assets") to ensure every background path in the pool is safe and portable.
class BackgroundPool(BaseModel):
    id: str
    activity: str
    territory: str
    visualDirection: str
    assets: List[str] = Field(default_factory=list)

    @field_validator("assets")
    @classmethod
    def check_assets(cls, v: List[str]) -> List[str]:
        for asset in v:
            validate_portable_path(asset, "backgroundPool.assets")
        return v


# PYDANTIC RULE (TaglinePool):
# 1. Field bounds: taglines list must contain at least 1 tagline (`min_length=1`).
# 2. Model validator (`validate_tagline_color_activity_match`): Brand color constraint:
#    beach and surfing MUST use black text (#000000); all other activities MUST use white text (#FFFFFF).
class TaglinePool(BaseModel):
    id: str
    activity: str
    textColor: str
    colorName: Optional[str] = None
    taglines: List[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_tagline_color_activity_match(self):
        hex_norm = self.textColor.strip().upper()
        if self.activity in ["beach", "surfing"] and hex_norm not in ["#000000", "#000", "BLACK"]:
            raise ValueError(
                f"Tagline pool '{self.id}' for activity '{self.activity}' must have black text (#000000), but found '{self.textColor}'."
            )
        if self.activity not in ["beach", "surfing"] and hex_norm not in ["#FFFFFF", "#FFF", "WHITE"]:
            raise ValueError(
                f"Tagline pool '{self.id}' for activity '{self.activity}' must have white text (#FFFFFF), but found '{self.textColor}'."
            )
        return self


# PYDANTIC RULE (Audience):
# 1. Field bounds: `id` and `name` must be non-empty strings (`min_length=1`).
# 2. Model validator (`validate_audience_rules`): Enforces product color targeting:
#    - Younger band (age <= 24) MUST use orange cooler packshot.
#    - Older band (age >= 25) MUST use white cooler packshot.
class Audience(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    age: AudienceAgeRange
    lifeStage: str
    activity: str
    territory: str
    backgroundPoolId: str
    taglinePoolId: str
    productModel: str
    productColor: Literal["orange", "white"]
    productAssetId: str

    @model_validator(mode="after")
    def validate_audience_rules(self):
        # 1. Product Color by Age Band
        if self.age.maximum <= 24 and self.productColor != "orange":
            raise ValueError(
                f"Audience {self.id} ({self.name}) age {self.age.minimum}–{self.age.maximum} is in the younger band (20–24) and MUST use 'orange' product, but specified '{self.productColor}'."
            )
        if self.age.minimum >= 25 and self.productColor != "white":
            raise ValueError(
                f"Audience {self.id} ({self.name}) age {self.age.minimum}–{self.age.maximum} is in the older band (25+) and MUST use 'white' product, but specified '{self.productColor}'."
            )
        
        # Pool integrity is checked against the brief, not a fixed location list.
        return self



class OutputFormat(BaseModel):
    id: Literal["square", "landscape", "vertical"]
    aspectRatio: Literal["1:1", "16:9", "9:16"]
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    filenameTag: str


# PYDANTIC RULE (Composition):
# 1. Field validator (`check_logo`): verifies portable path on logoAssetPath.
# 2. Model validator (`check_layers`): rejects deprecated hard-coded layer names like 'blackTagline'.
class Composition(BaseModel):
    layersBackToFront: List[str]
    logoAssetPath: str
    taglineColorRule: Optional[str] = None
    defaultCallToAction: Optional[str] = None

    @field_validator("logoAssetPath")
    @classmethod
    def check_logo(cls, v: str) -> str:
        return validate_portable_path(v, "composition.logoAssetPath")

    @model_validator(mode="after")
    def check_layers(self):
        # Disallow hard-coded 'blackTagline' in layer names; require 'selectedTaglineAsset' or 'tagline'
        if "blackTagline" in self.layersBackToFront:
            raise ValueError(
                "composition.layersBackToFront contains obsolete 'blackTagline'. Use 'selectedTaglineAsset' or 'tagline' for activity-specific color support."
            )
        return self


class DropboxIntegration(BaseModel):
    dropboxBasePath: str = "/YETI_Social_Automation/LA_2026"
    uploadGeneratedOutputs: bool = False


class GeminiIntegration(BaseModel):
    enabledForMissingBackgroundsOnly: bool = True
    model: str = "imagen-3.0-generate-002"


class Integrations(BaseModel):
    dropbox: DropboxIntegration = DropboxIntegration()
    gemini: GeminiIntegration = GeminiIntegration()


# PYDANTIC RULE (CampaignBriefModel):
# Top-level campaign specification contract. Enforces:
# 1. Field validator (`check_asset_catalog`): all catalog asset paths must be safe relative paths.
# 2. Model validator (`validate_campaign_integrity`):
#    - Rule 1: Audience IDs must be unique.
#    - Rule 2: Output formats must use valid aspect ratios (1:1, 16:9, 9:16).
#    - Rule 3: Output count synchronization (handles exactOutputCount and standard formula).
#    - Rule 4: Pool IDs must be unique and referenced pools must exist.
#    - Rule 5: Activity & territory cross-reference matching between audiences and pools.
class CampaignBriefModel(BaseModel):
    schemaVersion: str
    layoutOverrides: Dict[Literal["1:1", "16:9", "9:16"], LayoutOverride] = Field(default_factory=dict)
    campaign: CampaignMeta
    generation: GenerationSettings
    assetCatalog: Dict[str, str] = Field(default_factory=dict)
    layoutReference: Optional[Dict[str, str]] = None
    activityRules: Optional[Dict[str, Dict]] = None
    creativeRules: Optional[Dict] = None
    productAssets: Dict[str, ProductAsset]
    taglineAssets: Dict[str, TaglineAsset]
    backgroundPools: List[BackgroundPool]
    taglinePools: List[TaglinePool]
    audiences: List[Audience] = Field(min_length=1)
    outputFormats: List[OutputFormat] = Field(min_length=1)
    composition: Composition
    integrations: Integrations = Integrations()
    qualityChecks: Optional[List[str]] = None
    output: Dict

    @field_validator("assetCatalog")
    @classmethod
    def check_asset_catalog(cls, v: Dict[str, str]) -> Dict[str, str]:
        for k, p in v.items():
            validate_portable_path(p, f"assetCatalog['{k}']")
        return v

    @model_validator(mode="after")
    def validate_campaign_integrity(self):
        # 1. Verify unique audience IDs
        audience_ids = [a.id for a in self.audiences]
        if len(audience_ids) != len(set(audience_ids)):
            raise ValueError(
                f"Audience IDs must be unique. Found duplicates in: {audience_ids}"
            )

        # 2. Verify output formats have valid aspect ratios
        valid_ratios = {"1:1", "16:9", "9:16"}
        for fmt in self.outputFormats:
            if fmt.aspectRatio not in valid_ratios:
                raise ValueError(
                    f"Output format '{fmt.id}' has unsupported aspect ratio '{fmt.aspectRatio}'. Supported: {valid_ratios}"
                )

        # 3. Synchronize total outputs calculation
        if self.generation.exactOutputCount is not None:
            from backend.app.services.output_allocation import allocate_outputs
            if self.generation.exactOutputCount < len(self.audiences):
                raise ValueError("The exact ad count must give each audience at least one output.")
            allocation = allocate_outputs(self)
            self.generation.conceptsPerAudience = max(len(groups) for groups in allocation.values())
            self.generation.totalOutputsPerRun = self.generation.exactOutputCount
            self.generation.totalAudienceGroups = len(self.audiences)
            per_audience, remainder = divmod(self.generation.exactOutputCount, len(self.audiences))
            self.generation.adsPerAudience = None if remainder else per_audience
            self.generation.renderAllFormatsFromSameConcept = all(
                len(group) == len(self.outputFormats) for groups in allocation.values() for group in groups
            )
        expected_total = len(self.audiences) * len(self.outputFormats) * self.generation.conceptsPerAudience
        if self.generation.exactOutputCount is None and (self.generation.totalOutputsPerRun is None or self.generation.totalOutputsPerRun != expected_total):
            self.generation.totalOutputsPerRun = expected_total
        if self.generation.totalAudienceGroups is None:
            self.generation.totalAudienceGroups = len(self.audiences)
        if self.generation.exactOutputCount is None and self.generation.adsPerAudience is None:
            self.generation.adsPerAudience = len(self.outputFormats) * self.generation.conceptsPerAudience


        # 4. Verify pool references and their semantic assignments.
        backgrounds = {p.id: p for p in self.backgroundPools}
        taglines = {p.id: p for p in self.taglinePools}
        if len(backgrounds) != len(self.backgroundPools) or len(taglines) != len(self.taglinePools):
            raise ValueError("Background and tagline pool IDs must be unique.")
        bg_pool_ids = {p.id for p in self.backgroundPools}
        tagline_pool_ids = {p.id for p in self.taglinePools}

        for aud in self.audiences:
            if aud.backgroundPoolId not in bg_pool_ids:
                raise ValueError(
                    f"Audience {aud.id} references undefined backgroundPoolId '{aud.backgroundPoolId}'."
                )
            if aud.taglinePoolId not in tagline_pool_ids:
                raise ValueError(
                    f"Audience {aud.id} references undefined taglinePoolId '{aud.taglinePoolId}'."
                )

            pool = backgrounds[aud.backgroundPoolId]
            if pool.activity != aud.activity:
                raise ValueError(f"Audience {aud.id} activity '{aud.activity}' does not match background pool activity '{pool.activity}'.")
            if pool.territory.strip().casefold() != aud.territory.strip().casefold():
                raise ValueError(f"Audience {aud.id} territory does not match background pool territory.")
            if taglines[aud.taglinePoolId].activity != aud.activity:
                raise ValueError(f"Audience {aud.id} activity does not match tagline pool activity.")

        return self


# Alias for concise typing
CampaignBrief = CampaignBriefModel
