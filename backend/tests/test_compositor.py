"""Tests for AdCompositor and Layout Configuration."""

import os
import pytest
from pathlib import Path
from PIL import Image

from backend.app.models.layout import LAYOUT_CONFIGS
from backend.app.services.compositor import AdCompositor
from backend.app.services.asset_resolver import AssetResolver


@pytest.fixture
def compositor():
    return AdCompositor(font_path="assets/fonts/DejaVuSans-Bold.ttf")


@pytest.fixture
def resolver():
    return AssetResolver()


def test_layout_configs_stability():
    """Verify all 3 required aspect ratios are present with valid normalized bounds."""
    for ratio in ["1:1", "16:9", "9:16"]:
        assert ratio in LAYOUT_CONFIGS
        cfg = LAYOUT_CONFIGS[ratio]
        assert cfg.canvas_width > 0
        assert cfg.canvas_height > 0
        assert 0.0 < cfg.safe_margin_x_pct < 0.2
        assert 0.0 < cfg.safe_margin_y_pct < 0.2
        assert 0.0 < cfg.product_region.max_width_pct <= 1.0
        assert 0.0 < cfg.logo_region.max_width_pct <= 1.0
        assert 0.0 < cfg.tagline_region.max_width_pct <= 1.0


def test_composition_exact_dimensions(compositor, resolver):
    """Confirm composited output matches exact target dimensions for 1:1, 16:9, and 9:16."""
    bg = Image.open(resolver.resolve_role("background_beach").resolved_path)
    prod = Image.open(resolver.resolve_role("product_orange").resolved_path)
    tag = Image.open(resolver.resolve_role("tagline_black").resolved_path)
    logo = Image.open(resolver.resolve_role("brand_logo").resolved_path)

    expected_sizes = {
        "1:1": (1080, 1080),
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
    }

    for ratio, expected_dim in expected_sizes.items():
        ad_img = compositor.compose_ad(
            background_img=bg,
            product_img=prod,
            tagline_asset_or_text=tag,
            logo_img=logo,
            aspect_ratio=ratio,
        )
        assert ad_img.size == expected_dim, f"Ratio {ratio} returned {ad_img.size}, expected {expected_dim}"
        assert ad_img.mode in ("RGB", "RGBA")


def test_composition_preserves_product_aspect_ratio(compositor, resolver):
    """Confirm product packshot aspect ratio is preserved during scaling."""
    prod = Image.open(resolver.resolve_role("product_orange").resolved_path)
    orig_ratio = prod.width / prod.height

    # Using fit_within_region helper
    from backend.app.services.compositor import fit_within_region
    scaled_img, nw, nh = fit_within_region(prod, 500, 300)
    scaled_ratio = nw / nh
    assert abs(orig_ratio - scaled_ratio) < 0.02


def test_activity_tagline_color_rendering(compositor, resolver):
    """Test Beach with black copy and Camping/Tailgate with white copy."""
    bg_beach = Image.open(resolver.resolve_role("background_beach").resolved_path)
    bg_camp = Image.open(resolver.resolve_role("background_camping").resolved_path)
    prod_orange = Image.open(resolver.resolve_role("product_orange").resolved_path)
    prod_white = Image.open(resolver.resolve_role("product_white").resolved_path)
    logo = Image.open(resolver.resolve_role("brand_logo").resolved_path)

    # 1. Beach with programmatic black text
    beach_ad = compositor.compose_ad(
        background_img=bg_beach,
        product_img=prod_orange,
        tagline_asset_or_text="Go West.\nStay Cold.",
        logo_img=logo,
        aspect_ratio="1:1",
        tagline_color_hex="#000000",
    )
    assert beach_ad.size == (1080, 1080)

    # 2. Camping with programmatic white text
    camp_ad = compositor.compose_ad(
        background_img=bg_camp,
        product_img=prod_white,
        tagline_asset_or_text="Go Higher.\nStay Colder.",
        logo_img=logo,
        aspect_ratio="1:1",
        tagline_color_hex="#FFFFFF",
    )
    assert camp_ad.size == (1080, 1080)


def test_render_fixture_all_ratios_to_outputs(compositor, resolver):
    """Render test fixture in all three ratios and save to outputs/test_fixtures/."""
    out_dir = Path("outputs/test_fixtures")
    out_dir.mkdir(parents=True, exist_ok=True)

    bg = Image.open(resolver.resolve_role("background_tailgating").resolved_path)
    prod = Image.open(resolver.resolve_role("product_orange").resolved_path)
    tag = Image.open(resolver.resolve_role("tagline_white").resolved_path)
    logo = Image.open(resolver.resolve_role("brand_logo").resolved_path)

    for ratio in ["1:1", "16:9", "9:16"]:
        clean_tag = ratio.replace(":", "x")
        # Render clean final
        final_img = compositor.compose_ad(
            background_img=bg,
            product_img=prod,
            tagline_asset_or_text=tag,
            logo_img=logo,
            aspect_ratio=ratio,
            draw_debug_overlay=False,
        )
        final_path = out_dir / f"fixture_{clean_tag}.png"
        final_img.save(final_path, format="PNG")
        assert final_path.exists()
        assert final_path.stat().st_size > 0

        # Render debug overlay version
        debug_img = compositor.compose_ad(
            background_img=bg,
            product_img=prod,
            tagline_asset_or_text=tag,
            logo_img=logo,
            aspect_ratio=ratio,
            draw_debug_overlay=True,
        )
        debug_path = out_dir / f"fixture_{clean_tag}_debug.png"
        debug_img.save(debug_path, format="PNG")
        assert debug_path.exists()
