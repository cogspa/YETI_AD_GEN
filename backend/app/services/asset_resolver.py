"""Asset Resolver and Integrity Verifier for YETI Ad Generator."""

import os
import re
import io
import hashlib
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from PIL import Image

from backend.app.models.assets import (
    AssetRole,
    AssetStatus,
    ResolvedAssetInfo,
    AssetReadinessReport,
)

# Canonical mapping of standard roles to logical IDs and default relative paths
DEFAULT_ROLE_CONFIG: Dict[str, Dict[str, str]] = {
    "product_orange": {
        "logical_id": "product-cooler-orange",
        "relative_path": "assets/products/cooler_orange.png",
        "category": "Products",
        "is_blocking": True,
    },
    "product_white": {
        "logical_id": "product-cooler-white",
        "relative_path": "assets/products/cooler_white.png",
        "category": "Products",
        "is_blocking": True,
    },
    "background_beach": {
        "logical_id": "bg-beach",
        "relative_path": "assets/backgrounds/Beach.jpg",
        "category": "Backgrounds",
        "is_blocking": False,  # Eligible for Gemini fallback
    },
    "background_camping": {
        "logical_id": "bg-camping",
        "relative_path": "assets/backgrounds/Camping.jpg",
        "category": "Backgrounds",
        "is_blocking": False,  # Eligible for Gemini fallback
    },
    "background_tailgating": {
        "logical_id": "bg-tailgate",
        "relative_path": "assets/backgrounds/Tailgate.jpg",
        "category": "Backgrounds",
        "is_blocking": False,  # Eligible for Gemini fallback
    },
    "tagline_black": {
        "logical_id": "tagline-overlay-black",
        "relative_path": "assets/taglines/TAGLINE_black.png",
        "category": "Taglines",
        "is_blocking": True,
    },
    "tagline_white": {
        "logical_id": "tagline-overlay-white",
        "relative_path": "assets/taglines/TAGLINE_white.png",
        "category": "Taglines",
        "is_blocking": True,
    },
    "brand_logo": {
        "logical_id": "brand-logo",
        "relative_path": "assets/brand/Yeti_Logo_1.png",
        "category": "Brand & Typography",
        "is_blocking": True,
    },
    "brand_logo_black": {
        "logical_id": "brand-logo-black",
        "relative_path": "assets/brand/Yeti_Logo_1.png",
        "category": "Brand & Typography",
        "is_blocking": True,
    },
    "brand_logo_white": {
        "logical_id": "brand-logo-white",
        "relative_path": "assets/brand/Yeti_Logo_4.png",
        "category": "Brand & Typography",
        "is_blocking": True,
    },
    "font_regular": {
        "logical_id": "font-regular",
        "relative_path": "assets/fonts/DejaVuSans.ttf",
        "category": "Brand & Typography",
        "is_blocking": True,
    },
    "font_bold": {
        "logical_id": "font-bold",
        "relative_path": "assets/fonts/DejaVuSans-Bold.ttf",
        "category": "Brand & Typography",
        "is_blocking": True,
    },
    "layout_reference_1x1": {
        "logical_id": "layout-1x1",
        "relative_path": "ad_examples/1_1.png",
        "category": "Layout Reference",
        "is_blocking": False,
    },
    "layout_reference_16x9": {
        "logical_id": "layout-16x9",
        "relative_path": "ad_examples/16_9.png",
        "category": "Layout Reference",
        "is_blocking": False,
    },
    "layout_reference_9x16": {
        "logical_id": "layout-9x16",
        "relative_path": "ad_examples/9_16.png",
        "category": "Layout Reference",
        "is_blocking": False,
    },
}


class AssetResolver:
    def __init__(
        self,
        base_dir: Optional[str] = None,
        dropbox_cache_dir: Optional[str] = None,
        dropbox_available_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the AssetResolver.
        Args:
            base_dir: Root directory of the repository workspace (defaults to current working directory or repo root).
            dropbox_cache_dir: Optional path to local cached dropbox downloads.
            dropbox_available_paths: List of remote Dropbox relative paths known to be available.
        """
        self.base_dir = Path(base_dir or os.getcwd()).resolve()
        self.dropbox_cache_dir = Path(dropbox_cache_dir or (self.base_dir / ".dropbox_cache")).resolve()
        self.dropbox_available_paths = set(dropbox_available_paths or [])

    def _sanitize_and_validate_path(self, rel_path: str) -> Path:
        """
        Confirm path is a portable forward-slash relative path and stays within approved base directory.
        Raises ValueError if path is absolute or attempts directory traversal.
        """
        if not rel_path or not isinstance(rel_path, str):
            raise ValueError("Path must be a non-empty string.")

        # Check absolute path
        if rel_path.startswith("/") or re.match(r"^[a-zA-Z]:[\\/]", rel_path):
            raise ValueError(f"Security error: Absolute path '{rel_path}' is not allowed.")

        # Check traversal
        normalized = os.path.normpath(rel_path.replace("\\", "/"))
        if normalized.startswith("..") or "/../" in normalized or normalized == "..":
            raise ValueError(f"Security error: Path traversal detected in '{rel_path}'.")

        full_path = (self.base_dir / normalized).resolve()

        # Check full_path stays within base_dir or approved cache
        try:
            full_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(f"Security error: Path '{rel_path}' escapes base directory.")

        return full_path

    def _inspect_file(self, full_path: Path) -> Tuple[str, Optional[Tuple[int, int]], bool, int, str]:
        """
        Inspect physical file bytes:
        Returns:
            (format_type, dimensions_or_none, has_alpha, size_bytes, sha256_hash)
        """
        with open(full_path, "rb") as f:
            data = f.read()

        size_bytes = len(data)
        sha256_hash = hashlib.sha256(data).hexdigest()

        ext = full_path.suffix.lower()
        format_type = ext.replace(".", "").upper()
        dimensions: Optional[Tuple[int, int]] = None
        has_alpha = False

        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            try:
                with Image.open(io.BytesIO(data)) as img:
                    format_type = img.format or format_type
                    dimensions = (img.width, img.height)
                    has_alpha = img.mode in ("RGBA", "LA") or ("transparency" in img.info)
            except Exception as e:
                raise ValueError(f"Corrupt image file at '{full_path.name}': {str(e)}")
        elif ext in [".ttf", ".otf"]:
            format_type = "TTF" if ext == ".ttf" else "OTF"
            # Verify font header magic bytes
            if len(data) >= 4:
                magic = data[:4]
                if magic not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
                    raise ValueError(f"Corrupt font file at '{full_path.name}': Invalid font header magic bytes.")
        elif ext == ".svg":
            format_type = "SVG"
            # Basic safe inspection for SVG header
            if b"<svg" not in data[:2048].lower():
                raise ValueError(f"Corrupt SVG file at '{full_path.name}': Missing <svg> root element.")

        return format_type, dimensions, has_alpha, size_bytes, sha256_hash

    def resolve_role(
        self,
        role: str,
        override_rel_path: Optional[str] = None,
        custom_catalog: Optional[Dict[str, str]] = None,
    ) -> ResolvedAssetInfo:
        """
        Resolve a single asset role according to lookup priority:
        1. Valid local asset
        2. Cached Dropbox copy
        3. Dropbox catalog path
        4. Missing (missing_gemini_eligible for backgrounds, missing_blocking for others)
        """
        config = DEFAULT_ROLE_CONFIG.get(role, {
            "logical_id": role,
            "relative_path": override_rel_path or "",
            "category": "Custom",
            "is_blocking": True,
        })

        logical_id = config["logical_id"]
        rel_path = override_rel_path or (custom_catalog.get(logical_id) if custom_catalog else None) or config["relative_path"]
        is_blocking = config.get("is_blocking", True)
        is_background = role.startswith("background_")

        # 1. Check Local Path
        try:
            local_full_path = self._sanitize_and_validate_path(rel_path)
            if local_full_path.is_file():
                try:
                    fmt, dims, alpha, size, sha = self._inspect_file(local_full_path)
                    return ResolvedAssetInfo(
                        role=role,
                        logical_id=logical_id,
                        resolved_path=rel_path.replace("\\", "/"),
                        status="local",
                        format_type=fmt,
                        dimensions=dims,
                        has_alpha=alpha,
                        size_bytes=size,
                        sha256_hash=sha,
                        is_blocking=is_blocking,
                    )
                except ValueError as ve:
                    # File exists but is corrupt
                    return ResolvedAssetInfo(
                        role=role,
                        logical_id=logical_id,
                        resolved_path=rel_path.replace("\\", "/"),
                        status="missing_blocking" if is_blocking else "missing_gemini_eligible",
                        is_blocking=is_blocking,
                        error_message=str(ve),
                    )
        except ValueError as ve:
            # Traversal or invalid path syntax
            return ResolvedAssetInfo(
                role=role,
                logical_id=logical_id,
                resolved_path=rel_path,
                status="missing_blocking",
                is_blocking=True,
                error_message=str(ve),
            )

        # 2. Check Cached Dropbox Copy
        cache_full_path = (self.dropbox_cache_dir / rel_path).resolve()
        if cache_full_path.is_file():
            try:
                fmt, dims, alpha, size, sha = self._inspect_file(cache_full_path)
                return ResolvedAssetInfo(
                    role=role,
                    logical_id=logical_id,
                    resolved_path=f".dropbox_cache/{rel_path}".replace("\\", "/"),
                    status="cached_from_dropbox",
                    format_type=fmt,
                    dimensions=dims,
                    has_alpha=alpha,
                    size_bytes=size,
                    sha256_hash=sha,
                    is_blocking=is_blocking,
                )
            except Exception as e:
                pass

        # 3. Check Remote Dropbox Catalog Path
        if rel_path in self.dropbox_available_paths:
            return ResolvedAssetInfo(
                role=role,
                logical_id=logical_id,
                resolved_path=rel_path.replace("\\", "/"),
                status="dropbox_available",
                is_blocking=is_blocking,
            )

        # 4. Missing
        if is_background:
            status: AssetStatus = "missing_gemini_eligible"
        else:
            status = "missing_blocking"

        return ResolvedAssetInfo(
            role=role,
            logical_id=logical_id,
            resolved_path=rel_path.replace("\\", "/"),
            status=status,
            is_blocking=is_blocking,
            error_message=f"Asset not found at local or Dropbox locations ('{rel_path}').",
        )

    def resolve_logo_for_activity(self, activity: str) -> ResolvedAssetInfo:
        """
        Resolve white YETI logo across all campaign activities (beach, camping, tailgating).
        """
        return self.resolve_role("brand_logo_white")

    def generate_readiness_report(
        self,
        custom_catalog: Optional[Dict[str, str]] = None,
    ) -> AssetReadinessReport:
        """
        Inspect all standard roles and generate a truthful readiness report.
        """
        assets: Dict[str, ResolvedAssetInfo] = {}
        blocking_missing = 0
        gemini_eligible_missing = 0
        summary_messages: List[str] = []

        for role in DEFAULT_ROLE_CONFIG.keys():
            info = self.resolve_role(role, custom_catalog=custom_catalog)
            assets[role] = info

            if info.status == "missing_blocking":
                blocking_missing += 1
                summary_messages.append(f"BLOCKING: {role} ({info.logical_id}) is missing at '{info.resolved_path}'.")
            elif info.status == "missing_gemini_eligible":
                gemini_eligible_missing += 1
                summary_messages.append(f"FALLBACK AVAILABLE: {role} ({info.logical_id}) is missing; Gemini scene generation eligible.")
            elif info.status == "local":
                # Verified local
                pass
            elif info.status in ("cached_from_dropbox", "dropbox_available"):
                pass

        is_ready = blocking_missing == 0

        if is_ready and gemini_eligible_missing == 0:
            summary_messages.insert(0, "All primary assets are locally verified. 100% ready for deterministic rendering.")
        elif is_ready and gemini_eligible_missing > 0:
            summary_messages.insert(0, f"Ready with {gemini_eligible_missing} Gemini background fallback(s). Zero blocking assets missing.")
        else:
            summary_messages.insert(0, f"Generation BLOCKED: {blocking_missing} critical asset(s) are missing.")

        return AssetReadinessReport(
            is_ready_to_generate=is_ready,
            blocking_missing_count=blocking_missing,
            gemini_eligible_missing_count=gemini_eligible_missing,
            assets=assets,
            summary_messages=summary_messages,
        )
