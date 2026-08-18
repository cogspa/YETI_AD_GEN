"""Test suite for Asset Resolver and Integrity Verifier."""

import os
import pytest
import tempfile
from pathlib import Path
from backend.app.services.asset_resolver import AssetResolver, DEFAULT_ROLE_CONFIG


@pytest.fixture
def resolver():
    return AssetResolver()


def test_local_resolution_all_canonical_assets(resolver):
    """Confirm all standard local assets resolve with verified metadata."""
    report = resolver.generate_readiness_report()
    assert report.is_ready_to_generate is True
    assert report.blocking_missing_count == 0

    # Verify each expected canonical asset
    for role, config in DEFAULT_ROLE_CONFIG.items():
        info = report.assets[role]
        assert info.status == "local", f"Asset for {role} was expected to be 'local', got '{info.status}'"
        assert info.size_bytes > 0
        assert info.sha256_hash is not None
        assert len(info.sha256_hash) == 64

        if role == "product_orange":
            assert info.has_alpha is True, "Product orange must have alpha transparency channel."
            assert info.dimensions is not None
            assert info.dimensions[0] > 0 and info.dimensions[1] > 0

        if role == "product_white":
            assert info.format_type == "PNG"
            assert info.dimensions is not None
            assert info.dimensions[0] > 0 and info.dimensions[1] > 0

        if role == "brand_logo":
            assert info.resolved_path == "assets/brand/Yeti_Logo_1.png"
            assert info.has_alpha is True


def test_dropbox_placeholder_resolution():
    """Test resolving an asset via cached dropbox and remote dropbox availability."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cache_dir = tmp_path / ".dropbox_cache"
        cache_dir.mkdir(parents=True)

        # Create a mock cached file
        cached_file = cache_dir / "assets/backgrounds/CustomDropboxBg.jpg"
        cached_file.parent.mkdir(parents=True)
        # Write valid minimal JPEG header
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(cached_file, format="JPEG")

        custom_resolver = AssetResolver(
            base_dir=tmp_dir,
            dropbox_cache_dir=str(cache_dir),
            dropbox_available_paths=["assets/products/remote_cooler.png"],
        )

        # Test cached resolution
        cached_info = custom_resolver.resolve_role("background_beach", override_rel_path="assets/backgrounds/CustomDropboxBg.jpg")
        assert cached_info.status == "cached_from_dropbox"
        assert cached_info.dimensions == (100, 100)

        # Test remote dropbox catalog resolution
        remote_info = custom_resolver.resolve_role("product_orange", override_rel_path="assets/products/remote_cooler.png")
        assert remote_info.status == "dropbox_available"


def test_path_traversal_rejection(resolver):
    """Test that directory traversal attempts are rejected."""
    traversal_paths = [
        "../secret.png",
        "../../etc/passwd",
        "assets/products/../../../etc/hosts",
        "/absolute/path/to/asset.png",
    ]

    for bad_path in traversal_paths:
        info = resolver.resolve_role("product_orange", override_rel_path=bad_path)
        assert info.status == "missing_blocking"
        assert info.error_message is not None
        assert "Security error" in info.error_message


def test_corrupt_image_detection():
    """Test that a corrupt image file is caught and flagged."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        corrupt_file = tmp_path / "corrupt_cooler.png"
        with open(corrupt_file, "wb") as f:
            f.write(b"NOT_A_VALID_PNG_DATA_HEADER_CORRUPT_BYTES")

        custom_resolver = AssetResolver(base_dir=tmp_dir)
        info = custom_resolver.resolve_role("product_orange", override_rel_path="corrupt_cooler.png")
        assert info.status == "missing_blocking"
        assert info.error_message is not None
        assert "Corrupt image" in info.error_message


def test_missing_blocking_asset():
    """Test that a missing product/logo/tagline/font blocks generation."""
    with tempfile.TemporaryDirectory() as empty_dir:
        empty_resolver = AssetResolver(base_dir=empty_dir)

        # Product is blocking
        prod_info = empty_resolver.resolve_role("product_orange")
        assert prod_info.status == "missing_blocking"
        assert prod_info.is_blocking is True

        # Logo is blocking
        logo_info = empty_resolver.resolve_role("brand_logo")
        assert logo_info.status == "missing_blocking"
        assert logo_info.is_blocking is True

        # Tagline is blocking
        tagline_info = empty_resolver.resolve_role("tagline_black")
        assert tagline_info.status == "missing_blocking"
        assert tagline_info.is_blocking is True

        report = empty_resolver.generate_readiness_report()
        assert report.is_ready_to_generate is False
        assert report.blocking_missing_count > 0


def test_missing_gemini_eligible_background():
    """Test that a missing background is marked missing_gemini_eligible, not blocking."""
    with tempfile.TemporaryDirectory() as empty_dir:
        empty_resolver = AssetResolver(base_dir=empty_dir)

        bg_info = empty_resolver.resolve_role("background_beach")
        assert bg_info.status == "missing_gemini_eligible"
        assert bg_info.is_blocking is False

        bg_info2 = empty_resolver.resolve_role("background_camping")
        assert bg_info2.status == "missing_gemini_eligible"
        assert bg_info2.is_blocking is False
