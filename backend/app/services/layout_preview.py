"""Preview approved sample assets through the production compositor; no AI calls."""
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image

from backend.app.models.layout import LayoutPreviewRequest, resolve_layout
from backend.app.services.compositor import AdCompositor

ROOT = Path(__file__).resolve().parents[3]


def render_layout_preview(request: LayoutPreviewRequest):
    background = {"beach": "Beach.jpg", "camping": "Camping.jpg", "tailgating": "Tailgate.jpg"}[request.activity]
    tagline = "black" if request.activity == "beach" else "white"
    logo = ROOT / "assets/brand" / ("Yeti_Logo_1.png" if request.activity in {"camping", "tailgating"} else "Yeti_Logo_4.png")
    with Image.open(ROOT / "assets/backgrounds" / background) as bg, \
         Image.open(ROOT / f"assets/products/cooler_{request.productColor}.png") as product, \
         Image.open(ROOT / f"assets/taglines/TAGLINE_{tagline}.png") as tag, \
         Image.open(logo) as mark:
        sizes = {"logo_region": mark.size, "product_region": product.size, "tagline_region": tag.size}
        rendered = AdCompositor().compose_ad(
            background_img=bg, product_img=product, tagline_asset_or_text=tag, logo_img=mark,
            aspect_ratio=request.aspectRatio, layout_override=request.layout,
            tagline_color_hex="#000000" if tagline == "black" else "#FFFFFF",
            logo_asset_path=str(logo),
            product_gradient_path=str(ROOT / "assets/gradients/#grad1.png"),
            logo_gradient_path=str(ROOT / "assets/gradients/#grad2.png"),
            logo_white_gradient_path=str(ROOT / "assets/gradients/#grad2_white.png"),
        )
    layout = resolve_layout(request.aspectRatio, request.layout)
    rendered.thumbnail((720, 720), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    rendered.save(buffer, format="PNG")
    return {
        "image": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii"),
        "assetSizes": sizes,
        "canvasWidth": layout.canvas_width, "canvasHeight": layout.canvas_height,
    }
