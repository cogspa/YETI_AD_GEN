import { useEffect, useRef, useState } from 'react';
import type { PointerEvent, KeyboardEvent } from 'react';
import type { AspectRatio, CampaignBrief, DefaultLayout, LayerName, LayoutRegion } from '../types/campaign';
import { fetchDefaultLayouts, previewLayout, type LayoutPreview } from '../services/api';

const LAYERS: LayerName[] = ['logo_region', 'product_region', 'tagline_region'];
const LABELS = { logo_region: 'Logo', product_region: 'Product', tagline_region: 'Tagline' };
const RATIOS: AspectRatio[] = ['1:1', '16:9', '9:16'];
const FORMAT_LABELS = { '1:1': 'Square', '16:9': 'Landscape', '9:16': 'Vertical' };

export function constrainRegion(region: LayoutRegion): LayoutRegion {
  const width = Math.max(.01, Math.min(1, region.max_width_pct));
  const height = Math.max(.01, Math.min(1, region.max_height_pct));
  const ax = { left: 0, center: .5, right: 1 }[region.anchor_x];
  const ay = { top: 0, center: .5, bottom: 1 }[region.anchor_y];
  return { ...region, max_width_pct: width, max_height_pct: height,
    x: Math.max(width * ax, Math.min(1 - width * (1 - ax), region.x)),
    y: Math.max(height * ay, Math.min(1 - height * (1 - ay), region.y)) };
}

function elementBounds(region: LayoutRegion, size: [number, number], width: number, height: number) {
  const scale = Math.min(Math.floor(region.max_width_pct * width) / size[0], Math.floor(region.max_height_pct * height) / size[1]);
  const w = Math.max(1, Math.floor(size[0] * scale));
  const h = Math.max(1, Math.floor(size[1] * scale));
  const x = Math.floor(region.x * width) - (region.anchor_x === 'center' ? Math.floor(w / 2) : region.anchor_x === 'right' ? w : 0);
  const y = Math.floor(region.y * height) - (region.anchor_y === 'center' ? Math.floor(h / 2) : region.anchor_y === 'bottom' ? h : 0);
  return { left: `${x / width * 100}%`, top: `${y / height * 100}%`, width: `${w / width * 100}%`, height: `${h / height * 100}%` };
}

interface Props {
  brief: CampaignBrief;
  onChange: (brief: CampaignBrief) => void;
  disabled?: boolean;
}

export function LayoutEditor({ brief, onChange, disabled = false }: Props) {
  const [open, setOpen] = useState(false);
  const [ratio, setRatio] = useState<AspectRatio>('1:1');
  const [layer, setLayer] = useState<LayerName>('product_region');
  const [defaults, setDefaults] = useState<Record<AspectRatio, DefaultLayout> | null>(null);
  const [preview, setPreview] = useState<LayoutPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [activity, setActivity] = useState('camping');
  const [color, setColor] = useState('white');
  const board = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; region: LayoutRegion; layer: LayerName } | null>(null);
  const override = brief.layoutOverrides?.[ratio];
  const current = defaults?.[ratio];
  const regions = current ? Object.fromEntries(LAYERS.map(key => [key, override?.[key] || current[key]])) as Record<LayerName, LayoutRegion> : null;
  const layoutKey = JSON.stringify(regions);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setError(null);
    fetchDefaultLayouts().then(value => {
      if (!cancelled) setDefaults(value);
    }).catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load layouts.'); });
    return () => { cancelled = true; };
  }, [open, reload]);

  useEffect(() => {
    if (!open || layoutKey === 'null') return;
    const controller = new AbortController();
    setBusy(true);
    setError(null);
    const timer = window.setTimeout(() => {
      previewLayout(ratio, JSON.parse(layoutKey), activity, color, controller.signal)
        .then(value => { if (!controller.signal.aborted) setPreview(value); })
        .catch(err => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Preview unavailable.'); })
        .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    }, 300);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [open, ratio, layoutKey, activity, color, reload]);

  const update = (key: LayerName, value: LayoutRegion) => {
    if (disabled) return;
    onChange({ ...brief, layoutOverrides: { ...brief.layoutOverrides,
      [ratio]: { ...brief.layoutOverrides?.[ratio], [key]: constrainRegion(value) } } });
  };
  const reset = () => {
    const next = { ...brief.layoutOverrides };
    delete next[ratio];
    onChange({ ...brief, layoutOverrides: next });
  };
  const pointerDown = (event: PointerEvent<HTMLButtonElement>, key: LayerName) => {
    if (!regions || disabled) return;
    setLayer(key);
    drag.current = { x: event.clientX, y: event.clientY, region: regions[key], layer: key };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const pointerMove = (event: PointerEvent<HTMLButtonElement>) => {
    if (!drag.current || !board.current) return;
    const rect = board.current.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const start = drag.current;
    update(start.layer, { ...start.region, x: start.region.x + (event.clientX - start.x) / rect.width,
      y: start.region.y + (event.clientY - start.y) / rect.height });
  };
  const nudge = (event: KeyboardEvent<HTMLButtonElement>, key: LayerName) => {
    if (!regions || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
    event.preventDefault();
    const step = event.shiftKey ? .05 : .01;
    update(key, { ...regions[key], x: regions[key].x + (event.key === 'ArrowLeft' ? -step : event.key === 'ArrowRight' ? step : 0),
      y: regions[key].y + (event.key === 'ArrowUp' ? -step : event.key === 'ArrowDown' ? step : 0) });
  };
  const selected = regions?.[layer];

  return <section className="layout-editor" aria-label="Ad layout editor">
    <button type="button" className="layout-heading" aria-expanded={open} aria-controls="layout-editor-body" onClick={() => setOpen(!open)}>
      <span>AD LAYOUTS</span><span>{open ? 'Close editor −' : 'Edit placements +'}</span>
    </button>
    {open && <div id="layout-editor-body" className="layout-editor-body">
      <p>Set logo, product, and tagline placement for each ad size. Changes are saved in this campaign brief before generation.</p>
      <div className="layout-format-tabs" role="group" aria-label="Ad size">
        {RATIOS.map(value => <button key={value} type="button" aria-pressed={ratio === value}
          onClick={() => { setRatio(value); setPreview(null); drag.current = null; }}>
          {FORMAT_LABELS[value]} <span>{value}</span>{brief.layoutOverrides?.[value] && ' •'}
        </button>)}
      </div>
      {error && <div className="validation-error-banner" role="alert">{error} <button type="button" onClick={() => setReload(reload + 1)}>Retry preview</button></div>}
      {!defaults && !error && <p role="status">Loading standard layouts…</p>}
      {regions && current && selected && <>
        <div className="layout-editor-grid">
          <div>
            <div className="layout-board" ref={board} style={{ aspectRatio: ratio.replace(':', ' / '), maxWidth: ratio === '9:16' ? 250 : undefined }}>
              {preview ? <img src={preview.image} alt={`${FORMAT_LABELS[ratio]} ad layout preview using sample assets`} draggable={false} /> : <span className="layout-preview-placeholder">Rendering preview…</span>}
              {preview && LAYERS.map(key => <button type="button" key={key} disabled={disabled}
                className={`layout-element ${key === layer ? 'layout-element-selected' : ''}`}
                style={elementBounds(regions[key], preview.assetSizes[key], current.canvas_width, current.canvas_height)}
                aria-label={`Move ${LABELS[key].toLowerCase()}`} aria-pressed={key === layer}
                onClick={() => setLayer(key)} onPointerDown={event => pointerDown(event, key)} onPointerMove={pointerMove}
                onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }}
                onLostPointerCapture={() => { drag.current = null; }} onKeyDown={event => nudge(event, key)}>
                <span>{LABELS[key]}</span>
              </button>)}
            </div>
            <p className="layout-status" role="status">{busy ? 'Updating rendered preview…' : preview ? `${current.canvas_width} × ${current.canvas_height} · Drag an element or use arrow keys.` : ''}</p>
            <div className="layout-sample-controls">
              <label>Preview scene<select aria-label="Preview scene" value={activity} onChange={event => setActivity(event.target.value)}>
                <option value="camping">Camping</option><option value="beach">Beach</option><option value="tailgating">Tailgating</option>
              </select></label>
              <label>Preview cooler<select aria-label="Preview cooler" value={color} onChange={event => setColor(event.target.value)}>
                <option value="white">White</option><option value="orange">Orange</option>
              </select></label>
            </div>
            <p className="layout-hint">Sample scene only. Campaign backgrounds and audience assets are selected during generation.</p>
          </div>
          <fieldset className="layout-controls" disabled={disabled}>
            <legend>Placement controls</legend>
            <label>Element<select aria-label="Layout element" value={layer} onChange={event => setLayer(event.target.value as LayerName)}>
              {LAYERS.map(key => <option key={key} value={key}>{LABELS[key]}</option>)}
            </select></label>
            {([['x', 'Horizontal position'], ['y', 'Vertical position'], ['max_width_pct', 'Maximum width'], ['max_height_pct', 'Maximum height']] as const).map(([key, label]) =>
              <label key={key}>{label} (%)<input type="number" min={key === 'x' || key === 'y' ? 0 : 1} max={100} step={.1}
                aria-label={`${label} (%)`} value={Number((selected[key] * 100).toFixed(1))}
                onChange={event => { const value = event.target.valueAsNumber; if (Number.isFinite(value)) update(layer, { ...selected, [key]: value / 100 }); }} /></label>)}
            <label>Horizontal anchor<select aria-label="Horizontal anchor" value={selected.anchor_x} onChange={event => update(layer, { ...selected, anchor_x: event.target.value as LayoutRegion['anchor_x'] })}>
              <option value="left">Left</option><option value="center">Center</option><option value="right">Right</option>
            </select></label>
            <label>Vertical anchor<select aria-label="Vertical anchor" value={selected.anchor_y} onChange={event => update(layer, { ...selected, anchor_y: event.target.value as LayoutRegion['anchor_y'] })}>
              <option value="top">Top</option><option value="center">Center</option><option value="bottom">Bottom</option>
            </select></label>
            <button type="button" className="btn-secondary" onClick={reset}>Reset {FORMAT_LABELS[ratio].toLowerCase()} layout</button>
            <p className="layout-hint">Artwork keeps its proportions within the size limits. Position is measured at the selected anchor. Regions stay inside the canvas.</p>
          </fieldset>
        </div>
      </>}
    </div>}
  </section>;
}
