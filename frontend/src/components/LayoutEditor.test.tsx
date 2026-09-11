// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import { useState } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { LayoutEditor } from './LayoutEditor';
import * as api from '../services/api';
import { YETI_GO_ANYWHERE_2026_BRIEF } from '../data/sampleBriefs';
import type { AspectRatio, DefaultLayout, LayoutRegion } from '../types/campaign';

const region: LayoutRegion = { x:.5, y:.5, max_width_pct:.2, max_height_pct:.2, anchor_x:'center', anchor_y:'center' };
const defaults = Object.fromEntries(['1:1','16:9','9:16'].map(ratio => [ratio, {
  logo_region:{...region}, product_region:{...region}, tagline_region:{...region}, canvas_width:1080, canvas_height:1080,
}])) as Record<AspectRatio, DefaultLayout>;
const preview: api.LayoutPreview = { image:'data:image/png;base64,', canvasWidth:1080, canvasHeight:1080,
  assetSizes:{logo_region:[100,30],product_region:[200,150],tagline_region:[300,60]} };

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
function Harness() {
  const [brief,setBrief] = useState(YETI_GO_ANYWHERE_2026_BRIEF);
  return <LayoutEditor brief={brief} onChange={setBrief} />;
}
function setup() {
  vi.spyOn(api,'fetchDefaultLayouts').mockResolvedValue(defaults);
  const request = vi.spyOn(api,'previewLayout').mockResolvedValue(preview);
  render(<Harness />);
  fireEvent.click(screen.getByRole('button',{name:/Edit placements/}));
  return request;
}

describe('Per-format layout editing', () => {
  it('keeps placement changes isolated by size and supports resetting one size', async () => {
    const request = setup();
    const input = await screen.findByLabelText('Horizontal position (%)');
    fireEvent.change(input,{target:{value:'25'}});
    expect(input).toHaveValue(25);
    await waitFor(() => expect(request).toHaveBeenCalledWith('1:1',expect.objectContaining({product_region:expect.objectContaining({x:.25})}),'camping','white',expect.any(AbortSignal)));
    fireEvent.click(screen.getByRole('button',{name:/Landscape/}));
    expect(screen.getByLabelText('Horizontal position (%)')).toHaveValue(50);
    fireEvent.click(screen.getByRole('button',{name:/Square/}));
    expect(screen.getByLabelText('Horizontal position (%)')).toHaveValue(25);
    fireEvent.click(screen.getByRole('button',{name:'Reset square layout'}));
    expect(screen.getByLabelText('Horizontal position (%)')).toHaveValue(50);
  });

  it('moves selected artwork with keyboard controls', async () => {
    setup();
    const product = await screen.findByRole('button',{name:'Move product'});
    fireEvent.keyDown(product,{key:'ArrowRight'});
    expect(screen.getByLabelText('Horizontal position (%)')).toHaveValue(51);
    fireEvent.keyDown(product,{key:'ArrowDown',shiftKey:true});
    expect(screen.getByLabelText('Vertical position (%)')).toHaveValue(55);
  });

  it('clamps placement to keep the element region on the canvas', async () => {
    setup();
    fireEvent.change(await screen.findByLabelText('Horizontal position (%)'),{target:{value:'100'}});
    expect(screen.getByLabelText('Horizontal position (%)')).toHaveValue(90);
  });

  it('shows a useful error if layout defaults cannot be loaded', async () => {
    vi.spyOn(api,'fetchDefaultLayouts').mockRejectedValue(new Error('Backend unavailable.'));
    render(<Harness />);
    fireEvent.click(screen.getByRole('button',{name:/Edit placements/}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Backend unavailable.');
    expect(screen.getByRole('button',{name:'Retry preview'})).toBeEnabled();
  });
});
