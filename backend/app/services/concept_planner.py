"""Concept Planner for Multi-Audience Campaigns."""

import random
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from backend.app.models.brief import CampaignBrief, Audience
from backend.app.models.layout import LAYOUT_CONFIGS
from backend.app.models.plan import (
    AudienceConcept,
    FormatRenderPlan,
    CampaignPlanResult,
)
from backend.app.services.asset_resolver import AssetResolver


def make_product_slug(product_model: Optional[str], color: str) -> str:
    """
    Generate product slug e.g. roadie-24-orange, tundra-45-white.
    """
    model_str = product_model or "Roadie 24"
    clean_model = model_str.lower().replace("yeti", "").strip()
    clean_model = re.sub(r"[^a-z0-9]+", "-", clean_model).strip("-")
    if not clean_model:
        clean_model = "cooler"
    clean_color = color.lower().strip()
    if clean_color in clean_model:
        return clean_model
    return f"{clean_model}-{clean_color}"


def make_audience_slug(audience_name: str) -> str:
    """
    Generate slug from audience name e.g. "Westwood College Tailgaters" -> "westwood-college".
    """
    slug = re.sub(r"[^a-z0-9]+", "-", audience_name.lower()).strip("-")
    if slug.endswith("-tailgaters"):
        slug = slug[:-11]
    return slug


class ConceptPlanner:
    """
    Plans immutable audience concepts and deterministic 3-ratio format render plans.
    Guarantees that randomization occurs exactly once per audience concept (not per ratio).
    """

    def __init__(self, asset_resolver: Optional[AssetResolver] = None):
        self.resolver = asset_resolver or AssetResolver()

    def plan_campaign(
        self,
        brief: CampaignBrief,
        seed: Optional[int] = None,
        prior_manifest: Optional[Dict[str, Any]] = None,
    ) -> CampaignPlanResult:
        """
        Generate AudienceConcepts and FormatRenderPlans based on brief configuration.
        """
        if not brief.audiences:
            raise ValueError("Brief must contain at least 1 audience.")


        # 1. Deterministic Random Generator Setup
        effective_seed = seed if seed is not None else brief.generation.seed
        if effective_seed is None:
            effective_seed = random.randint(100000, 999999)

        rng = random.Random(effective_seed)

        # 2. Build Lookup Maps for Background and Tagline Pools
        bg_pool_map = {pool.id: pool for pool in brief.backgroundPools}
        tagline_pool_map = {pool.id: pool for pool in brief.taglinePools}

        # 3. Repeat Protection State
        current_run_bg_usage: Dict[str, int] = defaultdict(int)
        current_run_tagline_usage: Dict[str, int] = defaultdict(int)
        warnings: List[str] = []

        # Previous manifest mapping: audience_id -> { "background": path, "tagline": text }
        prior_audience_choices: Dict[str, Dict[str, str]] = {}
        if prior_manifest and "concepts" in prior_manifest:
            for item in prior_manifest.get("concepts", []):
                aid = item.get("audience_id")
                if aid:
                    prior_audience_choices[aid] = {
                        "background": item.get("selected_background_path", ""),
                        "tagline": item.get("selected_tagline_text", ""),
                    }

        concepts: List[AudienceConcept] = []
        render_plans: List[FormatRenderPlan] = []

        # 4. Plan Audience Groups
        concepts_per_aud = brief.generation.conceptsPerAudience or 1

        for audience in brief.audiences:
            for c_idx in range(concepts_per_aud):
                c_suffix = f"-v{c_idx+1}" if concepts_per_aud > 1 else ""
                concept_id = f"concept-{brief.campaign.id}-{audience.id}{c_suffix}-{effective_seed}"

                # Step A: Age Band -> Product Color Resolution
                if audience.age.maximum <= 24:
                    product_role = "product_orange"
                    product_res = self.resolver.resolve_role("product_orange")
                elif audience.age.minimum >= 25:
                    product_role = "product_white"
                    product_res = self.resolver.resolve_role("product_white")
                else:
                    raise ValueError(
                        f"Audience {audience.id} age range ({audience.age.minimum}-{audience.age.maximum}) crosses demographic boundary."
                    )

                # Step B: Activity -> Background Pool & Selection with Repeat Protection
                bg_pool = bg_pool_map.get(audience.backgroundPoolId)
                if not bg_pool:
                    raise ValueError(f"Background pool '{audience.backgroundPoolId}' not found in brief.")

                pool_bgs = bg_pool.assets
                if not pool_bgs:
                    # Empty asset pool: mark for automatic Gemini AI generation in pipeline Stage 5
                    selected_bg = f"outputs/generated-backgrounds/{audience.activity}-{audience.id}-pending.png"
                else:
                    # Filter against prior manifest if alternative options exist
                    prev_bg = prior_audience_choices.get(audience.id, {}).get("background")
                    eligible_bgs = [bg for bg in pool_bgs if bg != prev_bg] if len(pool_bgs) > 1 and prev_bg else pool_bgs

                    # Current run least-recently-used selection
                    min_usage = min(current_run_bg_usage[bg] for bg in eligible_bgs)
                    least_used_bgs = [bg for bg in eligible_bgs if current_run_bg_usage[bg] == min_usage]

                    # Deterministic selection from least-used
                    selected_bg = rng.choice(least_used_bgs)

                    if current_run_bg_usage[selected_bg] > 0:
                        warnings.append(
                            f"Pool '{audience.backgroundPoolId}' exhausted: background '{selected_bg}' reused for audience {audience.id}."
                        )
                    current_run_bg_usage[selected_bg] += 1

                # Step C: Activity -> Tagline Asset & Text Selection
                tag_pool = tagline_pool_map.get(audience.taglinePoolId)
                if not tag_pool:
                    raise ValueError(f"Tagline pool '{audience.taglinePoolId}' not found in brief.")

                pool_tags = tag_pool.taglines
                prev_tag = prior_audience_choices.get(audience.id, {}).get("tagline")
                eligible_tags = [t for t in pool_tags if t != prev_tag] if len(pool_tags) > 1 and prev_tag else pool_tags

                min_tag_usage = min(current_run_tagline_usage[t] for t in eligible_tags)
                least_used_tags = [t for t in eligible_tags if current_run_tagline_usage[t] == min_tag_usage]
                selected_tag_text = rng.choice(least_used_tags)
                current_run_tagline_usage[selected_tag_text] += 1

                # Activity Color & Tagline Asset
                if audience.activity in ["beach", "surfing"]:
                    tagline_color_hex = "#000000"
                    tagline_res = self.resolver.resolve_role("tagline_black")
                else:
                    tagline_color_hex = "#FFFFFF"
                    tagline_res = self.resolver.resolve_role("tagline_white")


                # Step D: Brand Logo (Crisp white wordmark)
                logo_res = self.resolver.resolve_logo_for_activity(audience.activity)

                # Step E: Construct Immutable AudienceConcept
                product_model = getattr(audience, "productModel", "YETI Roadie 24")
                product_color = "orange" if audience.age.maximum <= 24 else "white"
                product_slug = make_product_slug(product_model, product_color)
                aud_slug = make_audience_slug(audience.name)

                concept = AudienceConcept(
                    concept_id=concept_id,
                    audience_id=audience.id,
                    audience_name=audience.name + (f" (Var {c_idx+1})" if concepts_per_aud > 1 else ""),
                    age_band=audience.age.band,
                    activity=audience.activity,
                    territory=audience.territory,
                    product_model=product_model,
                    product_slug=product_slug,
                    audience_slug=aud_slug,
                    product_role=product_role,
                    product_asset_path=product_res.resolved_path,
                    background_pool_id=audience.backgroundPoolId,
                    selected_background_path=selected_bg,
                    tagline_pool_id=audience.taglinePoolId,
                    selected_tagline_text=selected_tag_text,
                    selected_tagline_asset_path=tagline_res.resolved_path,
                    tagline_color_hex=tagline_color_hex,
                    logo_asset_path=logo_res.resolved_path,
                    seed_used=effective_seed,
                )
                concepts.append(concept)

                # Step F: Expand Concept to Format Render Plans based on brief.outputFormats
                for output_fmt in brief.outputFormats:
                    ratio_name = output_fmt.aspectRatio
                    if ratio_name not in LAYOUT_CONFIGS:
                        continue
                    layout_cfg = LAYOUT_CONFIGS[ratio_name]
                    clean_ratio = ratio_name.replace(":", "x")
                    plan_id = f"plan-{concept.concept_id}-{clean_ratio}"
                    target_filename = f"{audience.id}_{aud_slug}{c_suffix}_{product_slug}_{clean_ratio}.png"

                    render_plan = FormatRenderPlan(
                        plan_id=plan_id,
                        concept_id=concept.concept_id,
                        audience_id=audience.id,
                        aspect_ratio=ratio_name,
                        output_dimensions=(layout_cfg.canvas_width, layout_cfg.canvas_height),
                        target_filename=target_filename,
                        product_slug=product_slug,
                        product_asset_path=concept.product_asset_path,
                        background_asset_path=concept.selected_background_path,
                        tagline_asset_path=concept.selected_tagline_asset_path,
                        tagline_text=concept.selected_tagline_text,
                        tagline_color_hex=concept.tagline_color_hex,
                        logo_asset_path=concept.logo_asset_path,
                        layout_config=layout_cfg,
                    )
                    render_plans.append(render_plan)



        return CampaignPlanResult(
            campaign_id=brief.campaign.id,
            seed=effective_seed,
            total_audiences=len(concepts),
            total_concepts=len(concepts),
            total_render_plans=len(render_plans),
            concepts=concepts,
            render_plans=render_plans,
            warnings=warnings,
        )
