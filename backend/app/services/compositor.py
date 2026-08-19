"""Pillow-based Composition Engine for YETI Ad Generator."""

import os
from typing import Optional, Union, Tuple, List, Literal
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageStat

from backend.app.models.layout import (
    RatioLayoutConfig,
    NormalizedRegion,
    LAYOUT_CONFIGS,
)


def is_white_logo(img: Image.Image) -> bool:
    """Determine if a logo asset is predominantly white/light in color."""
    try:
        rgba = img.convert("RGBA")
        r, _, _, a = rgba.split()
        mask = a.point(lambda p: 255 if p > 30 else 0)
        stat_r = ImageStat.Stat(r, mask=mask)
        return bool(stat_r.count[0] > 0 and stat_r.mean[0] > 180)
    except Exception:
        return False



def cover_crop_background(
    bg_img: Image.Image,
    target_width: int,
    target_height: int,
    focal_point: Tuple[float, float] = (0.5, 0.5),
) -> Image.Image:
    """
    Scale and crop background image to fill target dimensions (cover mode).
    Uses focal_point (0.0 to 1.0) to center the crop region.
    """
    src_w, src_h = bg_img.size
    target_ratio = target_width / target_height
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider than target: fit height, crop width
        new_h = target_height
        new_w = int(src_w * (target_height / src_h))
    else:
        # Source is taller than target: fit width, crop height
        new_w = target_width
        new_h = int(src_h * (target_width / src_w))

    scaled_bg = bg_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Calculate crop box using focal point
    focal_x, focal_y = focal_point
    left = int((new_w - target_width) * focal_x)
    top = int((new_h - target_height) * focal_y)

    # Clamp coordinates within bounds
    left = max(0, min(left, new_w - target_width))
    top = max(0, min(top, new_h - target_height))
    right = left + target_width
    bottom = top + target_height

    cropped = scaled_bg.crop((left, top, right, bottom))
    return cropped.convert("RGBA")


def fit_within_region(
    img: Image.Image,
    max_w: int,
    max_h: int,
) -> Tuple[Image.Image, int, int]:
    """
    Scale image proportionally to fit inside max_w and max_h.
    Preserves exact aspect ratio.
    Returns (scaled_image, new_width, new_height).
    """
    w, h = img.size
    scale = min(max_w / w, max_h / h, 1.0)  # Do not upscale beyond original
    # If original is smaller than box, we scale to match max box dimension
    scale_fit = min(max_w / w, max_h / h)
    new_w = max(1, int(w * scale_fit))
    new_h = max(1, int(h * scale_fit))

    scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return scaled, new_w, new_h


def calculate_anchor_coords(
    region: NormalizedRegion,
    element_w: int,
    element_h: int,
    canvas_w: int,
    canvas_h: int,
) -> Tuple[int, int]:
    """
    Calculate top-left pixel (x, y) coordinates for an element based on NormalizedRegion anchor rules.
    """
    base_x = int(region.x * canvas_w)
    base_y = int(region.y * canvas_h)

    if region.anchor_x == "left":
        pos_x = base_x
    elif region.anchor_x == "center":
        pos_x = base_x - (element_w // 2)
    elif region.anchor_x == "right":
        pos_x = base_x - element_w
    else:
        pos_x = base_x

    if region.anchor_y == "top":
        pos_y = base_y
    elif region.anchor_y == "center":
        pos_y = base_y - (element_h // 2)
    elif region.anchor_y == "bottom":
        pos_y = base_y - element_h
    else:
        pos_y = base_y

    return pos_x, pos_y


def render_contact_shadow(
    canvas_w: int,
    canvas_h: int,
    prod_x: int,
    prod_y: int,
    prod_w: int,
    prod_h: int,
    opacity: float = 0.35,
    blur_radius: int = 20,
) -> Image.Image:
    """
    Render a soft elliptical contact shadow directly beneath the product packshot base.
    """
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow_layer)

    shadow_w = int(prod_w * 0.82)
    shadow_h = max(8, int(prod_h * 0.09))
    center_x = prod_x + (prod_w // 2)
    bottom_y = prod_y + prod_h - int(prod_h * 0.04)

    bbox = [
        center_x - (shadow_w // 2),
        bottom_y - (shadow_h // 2),
        center_x + (shadow_w // 2),
        bottom_y + (shadow_h // 2),
    ]

    alpha_val = int(255 * opacity)
    draw.ellipse(bbox, fill=(10, 15, 20, alpha_val))

    blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return blurred


def render_programmatic_text(
    text: str,
    font_path: str,
    max_w: int,
    max_h: int,
    text_color_hex: str = "#000000",
    max_lines: int = 2,
) -> Image.Image:
    """
    Render campaign copy text with proper wrapping and auto-sizing.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) == 1 and len(text) > 28:
        # Wrap into 2 lines
        words = text.split()
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]

    lines = lines[:max_lines]

    # Binary search for best font size
    best_font = None
    best_size = 20
    for font_size in range(80, 16, -2):
        try:
            test_font = ImageFont.truetype(font_path, font_size)
        except Exception:
            test_font = ImageFont.load_default()

        # Check total height and max line width
        max_line_w = 0
        total_h = 0
        for line in lines:
            bbox = test_font.getbbox(line)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
            max_line_w = max(max_line_w, line_w)
            total_h += int(line_h * 1.35)

        if max_line_w <= max_w and total_h <= max_h:
            best_font = test_font
            best_size = font_size
            break

    if best_font is None:
        try:
            best_font = ImageFont.truetype(font_path, 20)
        except Exception:
            best_font = ImageFont.load_default()

    # Calculate final bounding size
    line_metrics = []
    text_w = 0
    text_h = 0
    for line in lines:
        bbox = best_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        text_w = max(text_w, lw)
        line_metrics.append((lw, lh))

    line_spacing = int(best_size * 0.3)
    text_h = sum(m[1] for m in line_metrics) + (len(lines) - 1) * line_spacing

    img = Image.new("RGBA", (max(text_w + 10, 10), max(text_h + 10, 10)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Parse color
    color_hex = text_color_hex.lstrip("#")
    if len(color_hex) == 6:
        r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        fill_color = (r, g, b, 255)
    else:
        fill_color = (0, 0, 0, 255) if "0" in color_hex else (255, 255, 255, 255)

    curr_y = 0
    for idx, line in enumerate(lines):
        line_w = line_metrics[idx][0]
        line_x = max(0, (img.width - line_w) // 2)
        draw.text((line_x, curr_y), line, font=best_font, fill=fill_color)
        curr_y += line_metrics[idx][1] + line_spacing

    return img


def draw_debug_safe_areas(
    canvas: Image.Image,
    layout: RatioLayoutConfig,
    logo_coords: Tuple[int, int, int, int],
    prod_coords: Tuple[int, int, int, int],
    tagline_coords: Tuple[int, int, int, int],
) -> Image.Image:
    """
    Draw a development-only safe area and bounding box overlay.
    """
    overlay = canvas.copy()
    draw = ImageDraw.Draw(overlay)
    W, H = layout.canvas_width, layout.canvas_height

    # Safe margin box (Cyan)
    sm_x = int(layout.safe_margin_x_pct * W)
    sm_y = int(layout.safe_margin_y_pct * H)
    draw.rectangle([sm_x, sm_y, W - sm_x, H - sm_y], outline=(0, 220, 255, 200), width=3)

    # Logo Box (Magenta)
    lx, ly, lw, lh = logo_coords
    draw.rectangle([lx, ly, lx + lw, ly + lh], outline=(255, 0, 255, 220), width=2)
    draw.text((lx, max(0, ly - 16)), "LOGO", fill=(255, 0, 255, 255))

    # Product Box (Yellow)
    px, py, pw, ph = prod_coords
    draw.rectangle([px, py, px + pw, py + ph], outline=(255, 220, 0, 220), width=2)
    draw.text((px, max(0, py - 16)), "PRODUCT", fill=(255, 220, 0, 255))

    # Tagline Box (Green)
    tx, ty, tw, th = tagline_coords
    draw.rectangle([tx, ty, tx + tw, ty + th], outline=(0, 255, 100, 220), width=2)
    draw.text((tx, max(0, ty - 16)), "TAGLINE", fill=(0, 255, 100, 255))

    return overlay


class AdCompositor:
    """Ad Compositor combining layout rules, assets, and typography into finished creative outputs."""

    def __init__(self, font_path: Optional[str] = None):
        self.font_path = font_path or "assets/fonts/DejaVuSans-Bold.ttf"

    def compose_ad(
        self,
        background_img: Image.Image,
        product_img: Image.Image,
        tagline_asset_or_text: Union[Image.Image, str],
        logo_img: Image.Image,
        aspect_ratio: Literal["1:1", "16:9", "9:16"] = "1:1",
        tagline_color_hex: str = "#000000",
        draw_debug_overlay: bool = False,
        product_gradient_path: Optional[str] = "assets/gradients/#grad1.png",
        logo_gradient_path: Optional[str] = "assets/gradients/#grad2.png",
        logo_white_gradient_path: Optional[str] = "assets/gradients/#grad2_white.png",
    ) -> Image.Image:
        """
        Render a finished ad in the requested aspect ratio following strict layer ordering:
        1. selectedBackground
        2. top gradient (#grad2.png for white logo, #grad2_white.png for black logo)
        3. product gradient (#grad1.png)
        4. optional productShadow
        5. selectedProductAsset
        6. selectedTaglineAsset
        7. selectedBrandLogo
        """
        layout = LAYOUT_CONFIGS.get(aspect_ratio)
        if not layout:
            raise ValueError(f"Unsupported aspect ratio '{aspect_ratio}'. Must be '1:1', '16:9', or '9:16'.")

        W, H = layout.canvas_width, layout.canvas_height

        # 1. Background Layer (Cover cropped)
        canvas = cover_crop_background(
            background_img,
            W,
            H,
            focal_point=layout.background_focal_point,
        )

        # 2. Top Gradient for Logo (#grad2.png for white logo, #grad2_white.png for black logo)
        is_white = is_white_logo(logo_img)
        chosen_logo_gradient = logo_gradient_path if is_white else logo_white_gradient_path

        if chosen_logo_gradient and os.path.exists(chosen_logo_gradient):
            try:
                with Image.open(chosen_logo_gradient) as g2_raw:
                    g2_rgba = g2_raw.convert("RGBA")
                    g2_w = W
                    g2_h = int(g2_rgba.height * (W / g2_rgba.width))
                    g2_scaled = g2_rgba.resize((g2_w, g2_h), Image.Resampling.LANCZOS)
                    g2_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    g2_layer.paste(g2_scaled, (0, 0), g2_scaled)
                    canvas = Image.alpha_composite(canvas, g2_layer)
            except Exception:
                pass


        # 3. Product Sizing and Position
        max_prod_w = int(layout.product_region.max_width_pct * W)
        max_prod_h = int(layout.product_region.max_height_pct * H)
        scaled_prod, prod_w, prod_h = fit_within_region(product_img, max_prod_w, max_prod_h)
        prod_x, prod_y = calculate_anchor_coords(
            layout.product_region, prod_w, prod_h, W, H
        )

        # 4. Product Glow Gradient (#grad1.png)
        if product_gradient_path and os.path.exists(product_gradient_path):
            try:
                with Image.open(product_gradient_path) as g1_raw:
                    g1_rgba = g1_raw.convert("RGBA")
                    g1_w = int(prod_w * 1.45)
                    g1_h = int(prod_h * 1.45)
                    g1_scaled = g1_rgba.resize((g1_w, g1_h), Image.Resampling.LANCZOS)
                    g1_x = prod_x + (prod_w - g1_w) // 2
                    g1_y = prod_y + (prod_h - g1_h) // 2
                    g1_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    g1_layer.paste(g1_scaled, (g1_x, g1_y), g1_scaled)
                    canvas = Image.alpha_composite(canvas, g1_layer)
            except Exception:
                pass

        # 5. Product Shadow
        if layout.shadow.enabled:
            shadow_layer = render_contact_shadow(
                W, H, prod_x, prod_y, prod_w, prod_h,
                opacity=layout.shadow.opacity,
                blur_radius=layout.shadow.blur_radius,
            )
            canvas = Image.alpha_composite(canvas, shadow_layer)

        # 6. Product Composite
        # Ensure product is RGBA
        prod_rgba = scaled_prod.convert("RGBA")
        canvas.paste(prod_rgba, (prod_x, prod_y), prod_rgba)


        # 5. Tagline Layer (Image Overlay or Programmatic Text)
        max_tag_w = int(layout.tagline_region.max_width_pct * W)
        max_tag_h = int(layout.tagline_region.max_height_pct * H)

        if isinstance(tagline_asset_or_text, Image.Image):
            scaled_tag, tag_w, tag_h = fit_within_region(tagline_asset_or_text, max_tag_w, max_tag_h)
            tag_rgba = scaled_tag.convert("RGBA")
        else:
            tag_rgba = render_programmatic_text(
                tagline_asset_or_text,
                self.font_path,
                max_tag_w,
                max_tag_h,
                text_color_hex=tagline_color_hex,
            )
            tag_w, tag_h = tag_rgba.size

        tag_x, tag_y = calculate_anchor_coords(
            layout.tagline_region, tag_w, tag_h, W, H
        )
        canvas.paste(tag_rgba, (tag_x, tag_y), tag_rgba)

        # 6. Brand Logo Layer
        max_logo_w = int(layout.logo_region.max_width_pct * W)
        max_logo_h = int(layout.logo_region.max_height_pct * H)
        scaled_logo, logo_w, logo_h = fit_within_region(logo_img, max_logo_w, max_logo_h)
        logo_rgba = scaled_logo.convert("RGBA")
        logo_x, logo_y = calculate_anchor_coords(
            layout.logo_region, logo_w, logo_h, W, H
        )
        canvas.paste(logo_rgba, (logo_x, logo_y), logo_rgba)

        # 7. Optional Debug Overlay
        if draw_debug_overlay:
            canvas = draw_debug_safe_areas(
                canvas,
                layout,
                (logo_x, logo_y, logo_w, logo_h),
                (prod_x, prod_y, prod_w, prod_h),
                (tag_x, tag_y, tag_w, tag_h),
            )

        return canvas
