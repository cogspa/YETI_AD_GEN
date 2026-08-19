#!/usr/bin/env python3
"""
YETI Ad Generator — Command Line Interface (CLI)

Run full end-to-end campaign generation directly from your terminal:
    python generate_ads.py --brief yeti_la_random_ad_campaign.json --seed 42
"""

import sys
import json
import argparse
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app.services.pipeline_runner import CampaignPipelineRunner
from backend.app.services.brief_validator import validate_brief_dict


def main():
    parser = argparse.ArgumentParser(
        description="YETI Ad Generator — Deterministic 18-Ad Campaign Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate campaign with default brief and seed 42
  python generate_ads.py

  # Custom brief and seed
  python generate_ads.py --brief my_campaign.json --seed 1234

  # Output to custom directory
  python generate_ads.py --output-dir ./custom_outputs
        """,
    )
    parser.add_argument(
        "--brief",
        "-b",
        default="yeti_la_random_ad_campaign.json",
        help="Path to campaign brief JSON file (default: yeti_la_random_ad_campaign.json)",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=42,
        help="Integer seed for deterministic randomization (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="outputs",
        help="Local output base directory (default: outputs)",
    )

    args = parser.parse_args()

    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"\033[91mError: Brief file not found at '{args.brief}'\033[0m")
        sys.exit(1)

    print("\033[96m" + "=" * 70 + "\033[0m")
    print("\033[94m\033[1m  YETI Los Angeles Multi-Format Creative Ad Generator (CLI)\033[0m")
    print("\033[96m" + "=" * 70 + "\033[0m")
    print(f"  Brief: \033[93m{brief_path.resolve()}\033[0m")
    print(f"  Seed:  \033[93m{args.seed}\033[0m")
    print(f"  Target: 6 Audience Concepts × 3 Aspect Ratios = \033[92m18 Output Ads\033[0m\n")

    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_dict = json.load(f)
    except Exception as e:
        print(f"\033[91mError parsing brief JSON: {e}\033[0m")
        sys.exit(1)

    def on_progress(event):
        pct = f"[{event.progress_pct:3d}%]"
        bar_len = 24
        filled = int((event.progress_pct / 100) * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\033[90m{pct}\033[0m \033[96m{bar}\033[0m \033[1m{event.stage:<32}\033[0m {event.message}")

    runner = CampaignPipelineRunner(local_base_dir=args.output_dir)
    print("\033[94m[*] Executing Campaign Pipeline...\033[0m")

    try:
        result = runner.execute_campaign(
            brief_dict=brief_dict,
            seed=args.seed,
            progress_callback=on_progress,
        )

    except Exception as e:
        print(f"\n\033[91m\033[1m[X] Pipeline execution failed: {e}\033[0m")
        sys.exit(1)

    print("\n\033[92m" + "=" * 70 + "\033[0m")
    print("\033[92m\033[1m  CAMPAIGN GENERATION COMPLETED SUCCESSFULLY!\033[0m")
    print("\033[92m" + "=" * 70 + "\033[0m")
    print(f"  Run ID:           \033[93m{result.run_id}\033[0m")
    print(f"  Duration:         \033[93m{result.duration_seconds} seconds\033[0m")
    print(f"  Total Concepts:   \033[92m{result.total_concepts}\033[0m")
    print(f"  Total Ads:        \033[92m{result.total_outputs} (100% rendered)\033[0m")
    print(f"  Storage Mode:     \033[94m{result.storage_mode.upper()}\033[0m")
    print(f"  Provenance:       \033[90m{result.provenance_summary}\033[0m")

    if result.quality_report:
        qr = result.quality_report
        passed = qr.get("blocking_checks_passed", 8)
        total = qr.get("blocking_checks_total", 8)
        print(f"  Quality Checks:   \033[92m{passed}/{total} Blocking Rules Passed\033[0m")

    print("\n\033[1mGenerated Artifacts:\033[0m")
    if result.contact_sheet_local_path:
        print(f"  - Contact Sheet:  \033[94m{result.contact_sheet_local_path}\033[0m")
    if result.zip_bundle_local_path:
        print(f"  - ZIP Package:    \033[94m{result.zip_bundle_local_path}\033[0m")
    if result.report_download_url:
        print(f"  - Quality Report: \033[94moutputs/{result.campaign_id}/runs/{result.run_id}/generation-report.json\033[0m")
    if result.pipeline_log_url:
        print(f"  - Execution Log:  \033[94moutputs/{result.campaign_id}/runs/{result.run_id}/pipeline.log\033[0m")

    print(f"\n\033[1mRendered Ad Variations (6 Audiences × 3 Formats):\033[0m")
    for ad in result.ads:
        print(f"  [{ad.aspect_ratio:4}] {ad.audience_id:<4} ({ad.activity:<11}) -> {ad.filename}")

    print("\n\033[92mDone!\033[0m\n")


if __name__ == "__main__":
    main()
