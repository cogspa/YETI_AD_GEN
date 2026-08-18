"""Campaign Pipeline Runner - End-to-end orchestration of 18 YETI ads with Quality Checks & Reporting."""

import os
import json
import time
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from PIL import Image


from backend.app.models.brief import CampaignBriefModel
from backend.app.models.plan import AudienceConcept, FormatRenderPlan
from backend.app.models.pipeline import GeneratedAdArtifact, PipelineStageEvent, CampaignRunResult
from backend.app.services.brief_validator import validate_brief_dict
from backend.app.services.asset_resolver import AssetResolver
from backend.app.services.concept_planner import ConceptPlanner
from backend.app.services.gemini_generator import GeminiBackgroundGenerator
from backend.app.services.compositor import AdCompositor
from backend.app.services.contact_sheet import generate_campaign_contact_sheet
from backend.app.services.quality_checker import QualityChecker, redact_secrets
from backend.app.services.storage import get_storage_adapter, StorageAdapter


class CampaignPipelineRunner:
    """
    Orchestrates the complete 18-ad campaign pipeline:
    1. Validating JSON
    2. Resolving controlled assets
    3. Reading repeat history
    4. Selecting six concepts
    5. Generating missing backgrounds if needed
    6. Rendering 18 adaptations
    7. Generating contact sheet & ZIP bundle
    8. Running deterministic quality checks & audits
    9. Uploading to Dropbox
    10. Generating generation-report.json and pipeline.log
    """

    def __init__(
        self,
        asset_resolver: Optional[AssetResolver] = None,
        storage_adapter: Optional[StorageAdapter] = None,
        gemini_generator: Optional[GeminiBackgroundGenerator] = None,
        compositor: Optional[AdCompositor] = None,
        quality_checker: Optional[QualityChecker] = None,
        local_base_dir: str = "outputs",
    ):
        self.resolver = asset_resolver or AssetResolver()
        self.storage = storage_adapter
        self.gemini = gemini_generator or GeminiBackgroundGenerator(storage_adapter=self.storage)
        self.compositor = compositor or AdCompositor()
        self.planner = ConceptPlanner(self.resolver)
        self.checker = quality_checker or QualityChecker()
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

        log_entries: List[Dict[str, Any]] = []

        def log_entry(stage: str, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
            redacted_msg = redact_secrets(message)
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "runId": run_id,
                "stage": stage,
                "level": level,
                "message": redacted_msg,
            }
            if extra:
                entry["data"] = {k: redact_secrets(str(v)) if isinstance(v, str) else v for k, v in extra.items()}
            log_entries.append(entry)

        def emit_event(stage: str, pct: int, completed: int, msg: str):
            log_entry(stage, "INFO", msg)
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

        # Stage 1: Validating JSON
        emit_event("Validating JSON", 5, 0, "Validating campaign brief contract and rules...")
        is_valid, brief_model, validation_errors = validate_brief_dict(brief_dict)
        if not is_valid or not brief_model:
            log_entry("Validating JSON", "ERROR", f"Brief validation failed: {'; '.join(validation_errors)}")
            raise ValueError(f"Brief validation failed: {'; '.join(validation_errors)}")

        effective_seed = seed if seed is not None else brief_model.generation.seed
        if effective_seed is None:
            effective_seed = int(time.time() * 1000) % 1000000

        # Stage 2: Resolving controlled assets
        emit_event("Resolving controlled assets", 15, 0, "Checking local and remote asset readiness...")
        readiness = self.resolver.generate_readiness_report(custom_catalog=brief_model.assetCatalog)
        if not readiness.is_ready_to_generate:
            log_entry("Resolving controlled assets", "ERROR", f"Missing blocking assets: {readiness.summary_messages}")
            raise RuntimeError(f"Missing blocking assets: {', '.join(readiness.summary_messages)}")



        # Stage 3: Reading repeat history
        emit_event("Reading repeat history", 25, 0, "Checking prior run manifests for repeat avoidance...")
        prior_manifest = None
        if brief_model.generation.repeatProtection:
            pm_path = brief_model.generation.repeatProtection.priorManifestPath
            if pm_path:
                storage = self.storage or get_storage_adapter()
                try:
                    if storage.exists(pm_path):
                        prior_manifest = storage.read_json(pm_path)
                        if prior_manifest:
                            log_entry("Reading repeat history", "INFO", f"Loaded prior manifest from {pm_path}")
                except Exception as e:
                    log_entry("Reading repeat history", "WARNING", f"Could not load prior manifest: {e}")


        # Stage 4: Selecting six concepts
        emit_event("Selecting six concepts", 35, 0, f"Deterministically generating 6 audience plans with seed {effective_seed}...")
        plan_result = self.planner.plan_campaign(
            brief=brief_model,
            seed=effective_seed,
            prior_manifest=prior_manifest,
        )

        # Stage 5: Generating missing backgrounds if needed
        emit_event("Generating missing backgrounds if needed", 45, 0, "Checking if AI background fallback is required...")
        gemini_used = False
        gemini_audiences: List[str] = []

        for concept in plan_result.concepts:
            bg_path = Path(concept.selected_background_path)
            if not bg_path.exists():
                emit_event(
                    "Generating missing backgrounds if needed",
                    50,
                    0,
                    f"Generating missing background for {concept.audience_name} ({concept.activity})...",
                )
                bg_result = self.gemini.generate_for_audience(
                    activity=concept.activity,
                    territory=concept.territory,
                    audience_id=concept.audience_id,
                    campaign_id=brief_model.campaign.id,
                    run_id=run_id,
                )
                concept.selected_background_path = bg_result.local_path
                gemini_used = True
                gemini_audiences.append(concept.audience_id)
                log_entry("Generating missing backgrounds", "INFO", f"AI background generated for {concept.audience_id}", {"provenance": bg_result.provenance})

        # Create output directories for this run
        run_dir = self.base_dir / brief_model.campaign.id / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        ads_output_dir = run_dir / "outputs"
        ads_output_dir.mkdir(parents=True, exist_ok=True)

        # Stage 6: Rendering 18 adaptations
        emit_event("Rendering 18 adaptations", 55, 0, "Starting composite rendering for 6 concepts across 3 formats...")
        ads: List[GeneratedAdArtifact] = []
        render_plans: List[FormatRenderPlan] = []
        concepts: List[AudienceConcept] = []

        completed_ads = 0
        total_ads = 18

        for concept in plan_result.concepts:
            concepts.append(
                AudienceConcept(
                    concept_id=concept.concept_id,
                    audience_id=concept.audience_id,
                    audience_name=concept.audience_name,
                    age_band=concept.age_band,
                    activity=concept.activity,
                    territory=concept.territory,
                    product_role=concept.product_role,
                    product_asset_path=concept.product_asset_path,
                    background_pool_id=concept.background_pool_id,
                    selected_background_path=concept.selected_background_path,
                    tagline_pool_id=concept.tagline_pool_id,
                    selected_tagline_text=concept.selected_tagline_text,
                    selected_tagline_asset_path=concept.selected_tagline_asset_path,
                    tagline_color_hex=concept.tagline_color_hex,
                    logo_asset_path=concept.logo_asset_path,
                    seed_used=concept.seed_used,
                )
            )

            # Audience output folder
            aud_dir = ads_output_dir / concept.audience_id
            aud_dir.mkdir(parents=True, exist_ok=True)

            for ratio in ["1:1", "16:9", "9:16"]:
                fmt_folder = aud_dir / ratio.replace(":", "x")
                fmt_folder.mkdir(parents=True, exist_ok=True)

                out_filename = f"{concept.audience_id}_{concept.activity}_{concept.age_band}_{ratio.replace(':', 'x')}.png"
                out_path = fmt_folder / out_filename

                # Open PIL images for compositing
                with Image.open(concept.selected_background_path) as bg_im, \
                     Image.open(concept.product_asset_path) as prod_im, \
                     Image.open(concept.logo_asset_path) as logo_im, \
                     Image.open(concept.selected_tagline_asset_path) as tag_im:

                    rendered_img = self.compositor.compose_ad(
                        background_img=bg_im,
                        product_img=prod_im,
                        tagline_asset_or_text=tag_im,
                        logo_img=logo_im,
                        aspect_ratio=ratio,
                        tagline_color_hex=concept.tagline_color_hex,
                    )
                    rendered_img.save(out_path, format="PNG", optimize=True)

                filesize = out_path.stat().st_size
                dims = (rendered_img.width, rendered_img.height)


                # Relative path for serving
                rel_path = str(out_path.relative_to(self.base_dir)).replace("\\", "/")
                preview_url = f"/api/outputs/{rel_path}"
                storage_path = f"campaigns/{brief_model.campaign.id}/runs/{run_id}/outputs/{concept.audience_id}/{ratio.replace(':', 'x')}/{out_filename}"

                is_gemini_bg = concept.audience_id in gemini_audiences
                bg_source = "gemini_generated" if is_gemini_bg else "approved_asset"

                ad_artifact = GeneratedAdArtifact(
                    artifact_id=f"ad-{concept.concept_id}-{ratio.replace(':', 'x')}",
                    concept_id=concept.concept_id,
                    audience_id=concept.audience_id,
                    audience_name=concept.audience_name,
                    activity=concept.activity,
                    territory=concept.territory,
                    age_band=concept.age_band,
                    product_color="orange" if "orange" in concept.product_role else "white",
                    aspect_ratio=ratio,
                    dimensions=dims,
                    filename=out_filename,
                    local_path=str(out_path).replace("\\", "/"),
                    preview_url=preview_url,
                    storage_path=storage_path,
                    filesize_bytes=filesize,
                    background_source=bg_source,
                    human_review_required=is_gemini_bg,
                )
                ads.append(ad_artifact)

                completed_ads += 1
                progress_pct = 55 + int((completed_ads / total_ads) * 20)
                emit_event(
                    "Rendering 18 adaptations",
                    progress_pct,
                    completed_ads,
                    f"Rendered {concept.audience_id} ({ratio}) - {completed_ads}/{total_ads}",
                )

        render_plans = plan_result.render_plans



        # Stage 7: Contact Sheet Generation
        emit_event("Generating contact sheet", 78, 18, "Assembling master 6x3 campaign contact sheet...")
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

        # Stage 8: Generate ZIP Bundle
        zip_local_path = run_dir / f"{brief_model.campaign.id}_{run_id}_all_18_ads.zip"
        with zipfile.ZipFile(zip_local_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for ad in ads:
                zf.write(ad.local_path, arcname=f"{ad.audience_id}/{ad.filename}")
            zf.write(str(contact_sheet_local), arcname="contact-sheet.jpg")

        zip_rel_path = str(zip_local_path.relative_to(self.base_dir)).replace("\\", "/")
        zip_download_url = f"/api/outputs/{zip_rel_path}"

        # Stage 9: Running deterministic checks & Quality Report
        emit_event("Running checks", 85, 18, "Executing 8 blocking rules and quality heuristics...")
        storage = get_storage_adapter()
        storage_status = storage.get_status()

        quality_report = self.checker.run_all_checks(
            brief=brief_model,
            concepts=plan_result.concepts,
            ads=ads,
            run_id=run_id,
            seed=effective_seed,
            storage_mode=storage_status.mode,
        )

        report_local = run_dir / "generation-report.json"
        with open(report_local, "w", encoding="utf-8") as f:
            f.write(quality_report.model_dump_json(indent=2))
        report_rel_path = str(report_local.relative_to(self.base_dir)).replace("\\", "/")
        report_url = f"/api/outputs/{report_rel_path}"

        if quality_report.status == "failed":
            err_summary = "; ".join(quality_report.errors)
            log_entry("Running checks", "ERROR", f"Quality checks failed: {err_summary}")
            raise RuntimeError(f"Deterministic Quality Checks Failed: {err_summary}")

        # Stage 10: Generate Manifest & Secret-safe Pipeline Log
        manifest_data = {
            "campaignId": brief_model.campaign.id,
            "campaignName": brief_model.campaign.name,
            "runId": run_id,
            "seed": effective_seed,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "totalConcepts": 6,
            "totalAds": 18,
            "status": quality_report.status,
            "blockingChecksPassed": f"{quality_report.blocking_checks_passed}/{quality_report.blocking_checks_total}",
            "concepts": [c.model_dump() for c in concepts],
            "ads": [a.model_dump() for a in ads],
            "provenance": {
                "geminiUsed": gemini_used,
                "geminiAudiences": gemini_audiences,
                "summary": quality_report.provenance_summary,
            },
        }

        manifest_local = run_dir / "generation-manifest.json"
        with open(manifest_local, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        # Write Secret-safe JSONL pipeline log
        log_entry("Pipeline Execution", "INFO", f"Completed run {run_id} successfully.")
        log_local = run_dir / "pipeline.log"
        with open(log_local, "w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")
        log_rel_path = str(log_local.relative_to(self.base_dir)).replace("\\", "/")
        log_url = f"/api/outputs/{log_rel_path}"

        # Stage 11: Uploading to Dropbox / Storage
        emit_event("Uploading to Dropbox", 92, 18, "Uploading ads, contact sheet, report, and logs to storage...")
        dropbox_shared_link = None
        dropbox_folder = f"campaigns/{brief_model.campaign.id}/runs/{run_id}"

        try:
            # Upload manifest
            storage.upload_json(
                manifest_data,
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/generation-manifest.json",
                overwrite=True,
            )
            # Update latest active campaign manifest pointer for repeat protection
            storage.upload_json(
                manifest_data,
                f"campaigns/{brief_model.campaign.id}/generation-manifest.json",
                overwrite=True,
            )
            # Upload quality report
            storage.upload(
                str(report_local),
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/generation-report.json",
                overwrite=True,
            )
            # Upload secret-safe pipeline log
            storage.upload(
                str(log_local),
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/pipeline.log",
                overwrite=True,
            )
            # Upload contact sheet
            storage.upload(
                str(contact_sheet_local),
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/contact-sheet.jpg",
                overwrite=True,
            )
            # Upload each ad
            for ad in ads:
                if ad.storage_path:
                    storage.upload(ad.local_path, ad.storage_path, overwrite=True)

            # Retrieve folder or contact-sheet share link
            dropbox_shared_link = storage.get_temporary_link(
                f"campaigns/{brief_model.campaign.id}/runs/{run_id}/contact-sheet.jpg"
            )
        except Exception as e:
            plan_result.warnings.append(f"Remote storage upload warning: {str(e)}")

        duration = round(time.time() - start_time, 2)
        emit_event("Complete", 100, 18, f"Successfully generated all 18 ads in {duration}s!")

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
            dropbox_folder_path=dropbox_folder,
            dropbox_shared_link=dropbox_shared_link,
            quality_report=quality_report.model_dump(),
            report_download_url=report_url,
            pipeline_log_url=log_url,
            provenance_summary=quality_report.provenance_summary,
            gemini_used=gemini_used,
            gemini_audiences=gemini_audiences,
            warnings=quality_report.warnings,
            errors=quality_report.errors,
        )
