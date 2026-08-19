"""Pydantic models and strict validation contract for YETI campaign brief."""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import re


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


class CampaignAgeRange(BaseModel):
    minimum: int = Field(ge=20, le=30, description="Minimum campaign age")
    maximum: int = Field(ge=20, le=30, description="Maximum campaign age")

    @model_validator(mode="after")
    def validate_min_max(self):
        if self.minimum > self.maximum:
            raise ValueError(f"Age minimum ({self.minimum}) cannot exceed age maximum ({self.maximum}).")
        return self


class AudienceAgeRange(BaseModel):
    minimum: int = Field(ge=20, le=30, description="Minimum target age")
    maximum: int = Field(ge=20, le=30, description="Maximum target age")
    band: Optional[Literal["younger", "older"]] = None

    @model_validator(mode="after")
    def validate_age_band_integrity(self):
        if self.minimum > self.maximum:
            raise ValueError(f"Age minimum ({self.minimum}) cannot exceed age maximum ({self.maximum}).")
        
        # Enforce that individual audience age range does not cross younger (20-24) and older (25-30) bands
        is_younger = self.maximum <= 24
        is_older = self.minimum >= 25
        
        if not (is_younger or is_older):
            raise ValueError(
                f"Audience age range {self.minimum}–{self.maximum} crosses across the 20–24 (younger) and 25–30 (older) age bands. Must belong strictly to one band."
            )
        
        return self


class CampaignMeta(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    market: str
    ageRange: CampaignAgeRange
    objective: str
    campaignLine: str


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


class GenerationSettings(BaseModel):
    mode: str = "seeded-random"
    seed: Optional[int] = None
    conceptsPerAudience: int = Field(default=1, ge=1)
    totalAudienceGroups: Optional[int] = Field(default=None, ge=1)
    adsPerAudience: Optional[int] = Field(default=None, ge=1)
    totalOutputsPerRun: Optional[int] = Field(default=None, ge=1)
    randomizeOncePerAudience: bool = True
    renderAllFormatsFromSameConcept: bool = True
    selectionRules: Optional[Dict[str, str]] = None
    repeatProtection: Optional[RepeatProtection] = Field(default_factory=RepeatProtection)

    @model_validator(mode="after")
    def validate_quantities(self):
        if self.totalAudienceGroups and self.adsPerAudience and self.totalOutputsPerRun:
            expected_total = self.totalAudienceGroups * self.adsPerAudience
            if self.totalOutputsPerRun != expected_total:
                # Synchronize if mismatch
                self.totalOutputsPerRun = expected_total
        return self



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


class BackgroundPool(BaseModel):
    id: str
    activity: Literal["tailgating", "beach", "camping"]
    territory: str
    visualDirection: str
    assets: List[str]

    @field_validator("assets")
    @classmethod
    def check_assets(cls, v: List[str]) -> List[str]:
        for asset in v:
            validate_portable_path(asset, "backgroundPool.assets")
        return v


class TaglinePool(BaseModel):
    id: str
    activity: Literal["tailgating", "beach", "camping"]
    textColor: str
    colorName: Optional[str] = None
    taglines: List[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_tagline_color_activity_match(self):
        hex_norm = self.textColor.strip().upper()
        if self.activity == "beach" and hex_norm not in ["#000000", "#000", "BLACK"]:
            raise ValueError(
                f"Tagline pool '{self.id}' for activity 'beach' must have black text (#000000), but found '{self.textColor}'."
            )
        if self.activity in ["camping", "tailgating"] and hex_norm not in ["#FFFFFF", "#FFF", "WHITE"]:
            raise ValueError(
                f"Tagline pool '{self.id}' for activity '{self.activity}' must have white text (#FFFFFF), but found '{self.textColor}'."
            )
        return self


class Audience(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    age: AudienceAgeRange
    lifeStage: str
    activity: Literal["tailgating", "beach", "camping"]
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
                f"Audience {self.id} ({self.name}) age {self.age.minimum}–{self.age.maximum} is in the older band (25–30) and MUST use 'white' product, but specified '{self.productColor}'."
            )
        
        # 2. Activity to Background Pool Mapping
        if self.activity == "beach":
            if self.backgroundPoolId != "beach-west-coast":
                raise ValueError(
                    f"Audience {self.id} ({self.name}) has activity 'beach' and must resolve strictly to 'beach-west-coast' background pool, but found '{self.backgroundPoolId}'."
                )
        elif self.activity == "camping":
            if self.backgroundPoolId != "camping-la-mountains":
                raise ValueError(
                    f"Audience {self.id} ({self.name}) has activity 'camping' and must resolve strictly to 'camping-la-mountains' background pool, but found '{self.backgroundPoolId}'."
                )
        elif self.activity == "tailgating":
            if self.backgroundPoolId not in ["tailgating-westwood", "tailgating-south-central"]:
                raise ValueError(
                    f"Audience {self.id} ({self.name}) has activity 'tailgating' and must resolve strictly to Westwood or South Central tailgating pool, but found '{self.backgroundPoolId}'."
                )
        
        return self


class OutputFormat(BaseModel):
    id: Literal["square", "landscape", "vertical"]
    aspectRatio: Literal["1:1", "16:9", "9:16"]
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    filenameTag: str


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


class CampaignBriefModel(BaseModel):
    schemaVersion: str
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
        expected_total = len(self.audiences) * len(self.outputFormats) * self.generation.conceptsPerAudience
        if self.generation.totalOutputsPerRun is None or self.generation.totalOutputsPerRun != expected_total:
            self.generation.totalOutputsPerRun = expected_total
        if self.generation.totalAudienceGroups is None:
            self.generation.totalAudienceGroups = len(self.audiences)
        if self.generation.adsPerAudience is None:
            self.generation.adsPerAudience = len(self.outputFormats) * self.generation.conceptsPerAudience


        # 4. Verify all backgroundPoolIds and taglinePoolIds exist
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

        return self


# Alias for concise typing
CampaignBrief = CampaignBriefModel

