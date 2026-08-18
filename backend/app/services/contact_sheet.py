"""Contact Sheet Generator for YETI Ad Campaigns."""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from backend.app.models.pipeline import GeneratedAdArtifact
from backend.app.models.plan import AudienceConcept


def generate_campaign_contact_sheet(
    campaign_name: str,
    run_id: str,
    seed: int,
    concepts: List[AudienceConcept],
    ads: List[GeneratedAdArtifact],
    output_path: str,
    font_path: str = "assets/fonts/DejaVuSans-Bold.ttf",
) -> str:
    """
    Generate a high-res, beautifully structured contact sheet (6 Audience Rows × 3 Format Columns).
    """
    # Grid Dimensions
    CELL_WIDTH = 480
    CELL_HEIGHT = 480
    HEADER_HEIGHT = 160
    ROW_LABEL_WIDTH = 280
    PADDING = 24
    COLS = 3  # 1:1, 16:9, 9:16
    ROWS = len(concepts)  # 6 Audiences

    TOTAL_WIDTH = ROW_LABEL_WIDTH + (COLS * (CELL_WIDTH + PADDING)) + PADDING * 2
    TOTAL_HEIGHT = HEADER_HEIGHT + (ROWS * (CELL_HEIGHT + PADDING)) + PADDING * 2

    canvas = Image.new("RGB", (TOTAL_WIDTH, TOTAL_HEIGHT), (15, 23, 30))  # Dark Slate YETI background
    draw = ImageDraw.Draw(canvas)

    # Fonts
    try:
        font_title = ImageFont.truetype(font_path, 32)
        font_sub = ImageFont.truetype(font_path, 16)
        font_label = ImageFont.truetype(font_path, 14)
        font_small = ImageFont.truetype(font_path, 12)
    except Exception:
        font_title = font_sub = font_label = font_small = ImageFont.load_default()

    # 1. Header Banner
    draw.rectangle([0, 0, TOTAL_WIDTH, HEADER_HEIGHT], fill=(10, 16, 22))
    draw.text((PADDING, 28), "YETI", font=font_title, fill=(255, 255, 255))
    draw.text((PADDING + 100, 32), f"|  {campaign_name.upper()}  —  CONTACT SHEET", font=font_title, fill=(0, 210, 255))
    draw.text(
        (PADDING, 85),
        f"RUN ID: {run_id}    |    SEED: {seed}    |    6 AUDIENCES × 3 FORMATS = 18 OUTPUTS",
        font=font_sub,
        fill=(160, 180, 200),
    )

    # Column Headers (1:1 Square, 16:9 Landscape, 9:16 Story)
    col_titles = ["1:1 SQUARE (1080×1080)", "16:9 LANDSCAPE (1920×1080)", "9:16 VERTICAL (1080×1920)"]
    for c_idx, title in enumerate(col_titles):
        col_x = ROW_LABEL_WIDTH + PADDING + c_idx * (CELL_WIDTH + PADDING)
        draw.text((col_x + 10, HEADER_HEIGHT - 32), title, font=font_label, fill=(0, 210, 255))

    # Map ads by (audience_id, aspect_ratio)
    ad_map: Dict[Tuple[str, str], GeneratedAdArtifact] = {
        (ad.audience_id, ad.aspect_ratio): ad for ad in ads
    }

    # 2. Draw Audience Rows
    curr_y = HEADER_HEIGHT + PADDING
    for r_idx, concept in enumerate(concepts):
        # Row background card for audience info
        row_rect = [
            PADDING,
            curr_y,
            ROW_LABEL_WIDTH - PADDING // 2,
            curr_y + CELL_HEIGHT,
        ]
        draw.rectangle(row_rect, fill=(20, 30, 40), outline=(35, 50, 65), width=1)

        # Row Text Labels
        aud_text_y = curr_y + 24
        draw.text((PADDING + 16, aud_text_y), f"AUDIENCE {concept.audience_id}", font=font_sub, fill=(0, 210, 255))
        aud_text_y += 28
        draw.text((PADDING + 16, aud_text_y), concept.audience_name[:24], font=font_label, fill=(255, 255, 255))
        aud_text_y += 32

        # Metadata bullets
        draw.text((PADDING + 16, aud_text_y), f"Age: {concept.age_band.upper()}", font=font_small, fill=(180, 195, 210))
        aud_text_y += 22
        draw.text((PADDING + 16, aud_text_y), f"Activity: {concept.activity.title()}", font=font_small, fill=(180, 195, 210))
        aud_text_y += 22
        draw.text((PADDING + 16, aud_text_y), f"Territory: {concept.territory}", font=font_small, fill=(180, 195, 210))
        aud_text_y += 22
        prod_color_text = "Orange Cooler" if "orange" in concept.product_role else "White Cooler"
        draw.text((PADDING + 16, aud_text_y), f"Product: {prod_color_text}", font=font_small, fill=(255, 170, 0) if "orange" in concept.product_role else (230, 240, 255))
        aud_text_y += 22
        draw.text((PADDING + 16, aud_text_y), f"Tagline: {concept.selected_tagline_text}", font=font_small, fill=(140, 160, 180))

        # 3. Draw Format Thumbnails for this Audience
        for c_idx, ratio in enumerate(["1:1", "16:9", "9:16"]):
            cell_x = ROW_LABEL_WIDTH + PADDING + c_idx * (CELL_WIDTH + PADDING)
            cell_y = curr_y

            # Cell Card
            draw.rectangle([cell_x, cell_y, cell_x + CELL_WIDTH, cell_y + CELL_HEIGHT], fill=(8, 12, 16), outline=(30, 42, 55), width=1)

            ad_item = ad_map.get((concept.audience_id, ratio))
            if ad_item and os.path.exists(ad_item.local_path):
                try:
                    with Image.open(ad_item.local_path) as ad_img:
                        # Scale to fit inside cell with inner padding
                        inner_max_w = CELL_WIDTH - 20
                        inner_max_h = CELL_HEIGHT - 20
                        scale = min(inner_max_w / ad_img.width, inner_max_h / ad_img.height)
                        thumb_w = int(ad_img.width * scale)
                        thumb_h = int(ad_img.height * scale)
                        thumb = ad_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS).convert("RGB")

                        paste_x = cell_x + (CELL_WIDTH - thumb_w) // 2
                        paste_y = cell_y + (CELL_HEIGHT - thumb_h) // 2
                        canvas.paste(thumb, (paste_x, paste_y))
                except Exception as e:
                    draw.text((cell_x + 20, cell_y + CELL_HEIGHT // 2), f"Load Error: {e}", fill=(255, 100, 100))
            else:
                draw.text((cell_x + 40, cell_y + CELL_HEIGHT // 2), "Output Pending", fill=(100, 120, 140))

        curr_y += CELL_HEIGHT + PADDING

    # Save to disk
    out_path = Path(output_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="JPEG", quality=92)
    return str(out_path)
