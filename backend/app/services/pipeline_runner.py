"""End-to-End Pipeline Execution Service for YETI Ad Generator."""

import os
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from PIL import Image

from backend.app.models.brief import CampaignBrief
from backend.app.models.pipeline import (
    GeneratedAdArtifact,
    CampaignRunResult,
    PipelineStageEvent,
)
from backend.app.services.brief_validator import validate_brief_dict
from backend.app.services.asset_resolver import AssetResolver
from backend.app.services.concept_planner import ConceptPlanner
from backend.app.services.compositor import AdCompositor
from backend.app.services.gemini_generator import GeminiBackgroundGenerator
from backend.app.services.contact_sheet import generate_campaign_contact_sheet
from backend.app.services.storage.base import StorageAdapter
from backend.app.services.storage import get_storage_adapter


class CampaignPipelineRunner:
    """
    Orchestrates end-to-end execution of the 18-ad campaign generation pipeline.
    """

    def __init__(
        self,
        asset_resolver: Optional[AssetResolver] = None,
        storage_adapter: Optional[StorageAdapter] = None,
        gemini_generator: Optional[GeminiBackgroundGenerator] = None,
        compositor: Optional[AdCompositor] = None,
        local_base_dir: str = "outputs",
    ):
        self.resolver = asset_resolver or AssetResolver()
        self.storage = storage_adapter or get_storage_adapter()
        self.gemini = gemini_generator or GeminiBackgroundGenerator(storage_adapter=self.storage)
        self.compositor = compositor or AdCompositor()
        self.planner = ConceptPlanner(self.resolver)
        self.base_dir = Path(local_base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def execute_campaign(
        self,
        brief_dict: Dict[str, Any],
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[PipelineStageEvent], None]] = None,
    ) -> CampaignRunResult:
        start_time = time.time()
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_id = f"run-{now_str}-{seed if seed is not None else 'auto'}"

        def emit_event(stage: str, pct: int, completed: int, msg: str):
            if progress_callback:
                progress_callback(
                    PipelineStageEvent(
                        stage=stage,
                        progress_pct=pct,
                        completed_items=completed,
                        total_items=18,
                        message=msg,
                    )
                )

        # Stage 1: Validating JSON Brief
        emit_event("Validating JSON", 5, 0, "Validating campaign brief contract and rules...")
        is_valid, brief_model, validation_errors = validate_brief_dict(brief_dict)
        if not is_valid or brief_model is None:
            raise ValueError(f"Brief validation failed: {'; '.join(validation_errors)}")

        # Stage 2: Resolving Controlled Assets
        emit_event("Resolving controlled assets", 15, 0, "Inspecting product packshots, logos, taglines, and backgrounds...")
        readiness = self.resolver.generate_readiness_report()
        if readiness.blocking_missing_count > 0:
            raise ValueError(f"Blocking assets missing: {'; '.join(readiness.summary_messages)}")

        # Setup Run Workspace Directories
        run_dir = self.base_dir / brief_model.campaign.id / "runs" / run_id
        outputs_dir = run_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Stage 3: Reading Repeat History
        emit_event("Reading repeat history", 25, 0, "Inspecting prior manifest history for repeat avoidance...")
        prior_manifest = None
        prior_manifest_path = f"campaigns/{brief_model.campaign.id}/generation-manifest.json"
        try:
            if self.storage.exists(prior_manifest_path):
                prior_manifest = self.storage.read_json(prior_manifest_path)
        except Exception:
            prior_manifest = None

        # Stage 4: Selecting Six Concepts
        emit_event("Selecting six concepts", 35, 0, "Planning 6 immutable audience concepts and 18 render plans...")
        plan_result = self.planner.plan_campaign(
            brief=brief_model,
            seed=seed,
            prior_manifest=prior_manifest,
        )

        effective_seed = plan_result.seed
        concepts = plan_result.concepts
        render_plans = plan_result.render_plans

        # Stage 5: Generating Missing Backgrounds If Needed
        emit_event("Generating missing backgrounds if needed", 45, 0, "Checking background readiness for all 6 concepts...")
        gemini_audiences: List[str] = []
        resolved_bg_images: Dict[str, Image.Image] = {}

        for concept in concepts:
            bg_path = concept.selected_background_path
            # Check if background file exists locally
            if os.path.exists(bg_path):
                resolved_bg_images[concept.concept_id] = Image.open(bg_path)
            else:
                # Missing background -> Trigger Gemini / Mock fallback
                gemini_audiences.append(concept.audience_id)
                gen_bg_meta = self.gemini.generate_background(
                    activity=concept.activity,
                    territory=concept.territory,
                )
                resolved_bg_images[concept.concept_id] = Image.open(gen_bg_meta.local_path)

        gemini_used = len(gemini_audiences) > 0

        # Stage 6 & 7: Rendering 18 Adaptations & Running Quality Checks
        ads: List[GeneratedAdArtifact] = []
        completed_count = 0

        # Preload shared assets
        product_images = {
            "product_orange": Image.open(self.resolver.resolve_role("product_orange").resolved_path),
            "product_white": Image.open(self.resolver.resolve_role("product_white").resolved_path),
        }
        tagline_images = {
            "tagline_black": Image.open(self.resolver.resolve_role("tagline_black").resolved_path),
            "tagline_white": Image.open(self.resolver.resolve_role("tagline_white").resolved_path),
        }
        logo_img = Image.open(self.resolver.resolve_role("brand_logo_white").resolved_path)

        for plan in render_plans:
            concept = next(c for c in concepts if c.concept_id == plan.concept_id)
            clean_ratio = plan.aspect_ratio.replace(":", "x")
            pct = 50 + int((completed_count / 18) * 35)
            emit_event(
                "Rendering 18 adaptations",
                pct,
                completed_count,
                f"Rendering {plan.audience_id} ({plan.aspect_ratio}) [{completed_count + 1}/18]...",
            )

            # Select assets
            bg_img = resolved_bg_images[concept.concept_id]
            prod_img = product_images[concept.product_role]
            tag_img = tagline_images["tagline_black"] if concept.activity == "beach" else tagline_images["tagline_white"]

            # Render via AdCompositor
            rendered_ad = self.compositor.compose_ad(
                background_img=bg_img,
                product_img=prod_img,
                tagline_asset_or_text=tag_img,
                logo_img=logo_img,
                aspect_ratio=plan.aspect_ratio,
            )

            # Stage 7 Quality Check: Dimensions match expected layout
            expected_dims = plan.output_dimensions
            if rendered_ad.size != expected_dims:
                raise ValueError(f"Rendered ad size {rendered_ad.size} does not match target {expected_dims}")

            # Save locally
            aud_out_dir = outputs_dir / concept.audience_id / clean_ratio
            aud_out_dir.mkdir(parents=True, exist_ok=True)
            ad_local_path = aud_out_dir / plan.target_filename
            rendered_ad.save(ad_local_path, format="PNG")

            filesize = ad_local_path.stat().st_size
            rel_local_path = str(ad_local_path.relative_to(self.base_dir)).replace("\\", "/")
            preview_url = f"/api/outputs/{rel_local_path}"

            bg_source = "gemini_generated" if concept.audience_id in gemini_audiences else "approved_asset"

            ad_artifact = GeneratedAdArtifact(
                artifact_id=f"art-{plan.plan_id}",
                concept_id=concept.concept_id,
                audience_id=concept.audience_id,
                audience_name=concept.audience_name,
                activity=concept.activity,
                territory=concept.territory,
                age_band=concept.age_band,
                product_color="orange" if "orange" in concept.product_role else "white",
                aspect_ratio=plan.aspect_ratio,
                dimensions=expected_dims,
                filename=plan.target_filename,
                local_path=str(ad_local_path).replace("\\", "/"),
                preview_url=preview_url,
                storage_path=f"campaigns/{brief_model.campaign.id}/runs/{run_id}/outputs/{concept.audience_id}/{clean_ratio}/{plan.target_filename}",
                filesize_bytes=filesize,
                background_source=bg_source,
                human_review_required=(bg_source != "approved_asset"),
            )
            ads.append(ad_artifact)
            completed_count += 1

        # Stage 8: Generate Contact Sheet
        emit_event("Running checks", 88, 18, "Generating campaign contact sheet grid...")
        contact_sheet_local = run_dir / "contact-sheet.jpg"
        generate_campaign_contact_sheet(
            campaign_name=brief_model.campaign.name,
            run_id=run_id,
            seed=effective_seed,
            concepts=concepts,
            ads=ads,
            output_path=str(contact_sheet_local),
        )
        cs_rel_path = str(contact_sheet_local.relative_to(self.base_dir)).replace("\\", "/")
        cs_preview_url = f"/api/outputs/{cs_rel_path}"

        # Stage 9: Generate ZIP Bundle
        zip_local_path = run_dir / f"{brief_model.campaign.id}_{run_id}_all_18_ads.zip"
        with zipfile.ZipFile(zip_local_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for ad in ads:
                zf.write(ad.local_path, arcname=f"{ad.audience_id}/{ad.filename}")
            zf.write(str(contact_sheet_local), arcname="contact-sheet.jpg")

        zip_rel_path = str(zip_local_path.relative_to(self.base_dir)).replace("\\", "/")
        zip_download_url = f"/api/outputs/{zip_rel_path}"

        # Stage 10: Generate Manifest and Report JSON
        manifest_data = {
            "campaignId": brief_model.campaign.id,
            "campaignName": brief_model.campaign.name,
            "runId": run_id,
            "seed": effective_seed,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "totalConcepts": 6,
            "totalAds": 18,
            "concepts": [c.model_dump() for c in concepts],
            "ads": [a.model_dump() for a in ads],
            "provenance": {
                "geminiUsed": gemini_used,
                "geminiAudiences": gemini_audiences,
                "summary": "All backgrounds reused from approved assets." if not gemini_used else f"Gemini background fallback used for: {', '.join(gemini_audiences)}.",
            },
        }

        manifest_local = run_dir / "generation-manifest.json"
        with open(manifest_local, "w", encoding="utf-8") as f:
            import json
            json.dump(manifest_data, f, indent=2)

        # Stage 11: Uploading to Dropbox / Storage
        emit_event("Uploading to Dropbox", 92, 18, "Uploading ads, contact sheet, and manifest to storage...")
        storage_status = self.storage.get_status()
        dropbox_shared_link = None
        dropbox_folder = f"campaigns/{brief_model.campaign.id}/runs/{run_id}"

        try:
            # Upload manifest
            self.storage.upload_json(
                manifest_data,
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/generation-manifest.json",
                overwrite=True,
            )
            # Update latest active campaign manifest pointer for repeat protection
            self.storage.upload_json(
                manifest_data,
                f"campaigns/{brief_model.campaign.id}/generation-manifest.json",
                overwrite=True,
            )
            # Upload contact sheet
            self.storage.upload(
                str(contact_sheet_local),
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/contact-sheet.jpg",
                overwrite=True,
            )
            # Upload each ad
            for ad in ads:
                if ad.storage_path:
                    self.storage.upload(ad.local_path, ad.storage_path, overwrite=True)

            # Try retrieving folder link
            dropbox_shared_link = self.storage.get_temporary_link(
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/contact-sheet.jpg"
            )
        except Exception as e:
            plan_result.warnings.append(f"Remote storage upload warning: {str(e)}")

        duration = round(time.time() - start_time, 2)
        emit_event("Complete", 100, 18, f"Successfully generated all 18 ads in {duration}s!")

        provenance_msg = (
            "All backgrounds reused from approved assets."
            if not gemini_used
            else f"Gemini AI scene generation used for audiences: {', '.join(gemini_audiences)}."
        )

        return CampaignRunResult(
            run_id=run_id,
            campaign_id=brief_model.campaign.id,
            campaign_name=brief_model.campaign.name,
            seed=effective_seed,
            status="success",
            started_at=now_str,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds=duration,
            total_concepts=len(concepts),
            total_outputs=len(ads),
            concepts=concepts,
            render_plans=render_plans,
            ads=ads,
            contact_sheet_local_path=str(contact_sheet_local).replace("\\", "/"),
            contact_sheet_preview_url=cs_preview_url,
            zip_bundle_local_path=str(zip_local_path).replace("\\", "/"),
            zip_bundle_download_url=zip_download_url,
            storage_mode=storage_status.mode,
            storage_root=storage_status.root,
            dropbox_folder_path=dropbox_folder,
            dropbox_shared_link=dropbox_shared_link,
            provenance_summary=provenance_msg,
            gemini_used=gemini_used,
            gemini_audiences=gemini_audiences,
            warnings=plan_result.warnings,
            errors=[],
        )
