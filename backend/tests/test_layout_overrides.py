import base64
import json
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pydantic import ValidationError

from backend.app.models.brief import CampaignBriefModel
from backend.app.models.layout import LAYOUT_CONFIGS, LayoutOverride, LayoutPreviewRequest, resolve_layout
from backend.app.services.compositor import AdCompositor
from backend.app.services.layout_preview import render_layout_preview
from backend.app.services.concept_planner import ConceptPlanner
from backend.app.services import pipeline_runner
from backend.app.services.storage.local import LocalStorageAdapter


def override(x=.2):
    return LayoutOverride(product_region=dict(x=x, y=.5, max_width_pct=.1, max_height_pct=.1, anchor_x="center", anchor_y="center"))


def test_defaults_are_unchanged_after_overrides():
    original = LAYOUT_CONFIGS['1:1'].model_dump()
    custom = resolve_layout('1:1', override())
    assert custom.product_region.x == .2
    assert custom.logo_region == LAYOUT_CONFIGS['1:1'].logo_region
    assert resolve_layout('16:9').product_region.x == .5
    assert LAYOUT_CONFIGS['1:1'].model_dump() == original


@pytest.mark.parametrize('change', [dict(x=-1), dict(max_width_pct=0), dict(x=.99), dict(anchor_x='invalid')])
def test_invalid_or_off_canvas_region_rejected(change):
    region = override().product_region.model_dump()
    region.update(change)
    with pytest.raises(ValidationError):
        LayoutOverride(product_region=region)


@pytest.mark.parametrize('ratio', ['1:1', '16:9', '9:16'])
def test_compositor_uses_custom_placement(ratio):
    renderer = AdCompositor()
    def render(x):
        return renderer.compose_ad(Image.new('RGB', (20,20), 'white'), Image.new('RGBA',(20,20),'red'),
            Image.new('RGBA',(20,5),'green'), Image.new('RGBA',(20,5),'blue'), aspect_ratio=ratio,
            layout_override=override(x), product_gradient_path=None, logo_gradient_path=None, logo_white_gradient_path=None)
    left, right = render(.2), render(.8)
    w,h = left.size
    assert left.getpixel((int(.2*w),int(.5*h)))[:3] == (255,0,0)
    assert right.getpixel((int(.8*w),int(.5*h)))[:3] == (255,0,0)
    assert right.getpixel((int(.2*w),int(.5*h)))[:3] != (255,0,0)


def test_preview_uses_real_compositor_without_generation():
    result = render_layout_preview(LayoutPreviewRequest(aspectRatio='9:16', layout=override()))
    image = Image.open(BytesIO(base64.b64decode(result['image'].split(',')[1])))
    assert image.size == (405,720)
    assert result['canvasWidth'] == 1080
    assert set(result['assetSizes']) == {'logo_region','product_region','tagline_region'}


def test_layout_survives_validation_planning_rendering_and_manifest(tmp_path, monkeypatch):
    brief = json.load(open('yeti_la_random_ad_campaign.json'))
    brief['audiences'] = brief['audiences'][:1]
    brief['generation']['exactOutputCount'] = 1
    brief['layoutOverrides'] = {'1:1': override().model_dump(exclude_none=True)}
    model = CampaignBriefModel.model_validate(brief)
    plans = ConceptPlanner().plan_campaign(model, seed=42)
    assert plans.render_plans[0].layout_config.product_region.x == .2
    storage = LocalStorageAdapter(root_dir=str(tmp_path/'storage'))
    monkeypatch.setattr(pipeline_runner,'get_storage_adapter',lambda:storage)
    compositor = AdCompositor()
    spy = MagicMock(wraps=compositor)
    runner = pipeline_runner.CampaignPipelineRunner(storage_adapter=storage, compositor=spy, local_base_dir=str(tmp_path/'outputs'))
    result = runner.execute_campaign(brief, seed=42)
    assert result.total_outputs == 1
    assert spy.compose_ad.call_args.kwargs['layout_override'].product_region.x == .2
    manifest = next((tmp_path/'outputs').rglob('generation-manifest.json'))
    assert json.loads(manifest.read_text())['layoutOverrides']['1:1']['product_region']['x'] == .2


def test_preview_api_rejects_canvas_and_invalid_positions():
    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    assert client.get('/api/layouts').json()['1:1']['canvas_width'] == 1080
    assert client.post('/api/layout/preview',json={'aspectRatio':'4:3'}).status_code == 422
    assert client.post('/api/layout/preview',json={'aspectRatio':'1:1','layout':{'canvas_width':99}}).status_code == 422
