export interface AgeRange {
  minimum: number;
  maximum: number;
  band?: string;
}

export interface CampaignMeta {
  id: string;
  name: string;
  market: string;
  ageRange: AgeRange;
  objective: string;
  campaignLine: string;
}

export interface Audience {
  id: string;
  name: string;
  age: AgeRange;
  lifeStage: string;
  activity: 'tailgating' | 'beach' | 'camping' | string;
  territory: string;
  backgroundPoolId: string;
  taglinePoolId: string;
  productModel: string;
  productColor: 'orange' | 'white' | string;
  productAssetId: string;
}

export interface OutputFormat {
  id: string;
  aspectRatio: string;
  width: number;
  height: number;
  filenameTag: string;
}

export interface ProductAsset {
  colorName: string;
  assetPath: string;
  assignedAgeBand: string;
}

export interface TaglineAsset {
  colorName: string;
  hex: string;
  assetPath: string;
  activities: string[];
}

export interface BackgroundPool {
  id: string;
  activity: string;
  territory: string;
  visualDirection: string;
  assets: string[];
}

export interface TaglinePool {
  id: string;
  activity: string;
  textColor: string;
  taglines: string[];
}

export interface CampaignBrief {
  layoutOverrides?: Partial<Record<AspectRatio, LayoutOverride>>;
  schemaVersion: string;
  campaign: CampaignMeta;
  generation?: {
    mode?: string;
    seed?: number | null;
    conceptsPerAudience?: number;
    randomizeOncePerAudience?: boolean;
    renderAllFormatsFromSameConcept?: boolean;
    adsPerAudience?: number;
    totalAudienceGroups?: number;
    totalOutputsPerRun?: number;
    exactOutputCount?: number | null;
    selectionRules?: Record<string, string>;
    repeatProtection?: Record<string, any>;
  };

  creativeRules?: Record<string, any>;
  productAssets?: Record<string, ProductAsset>;
  taglineAssets?: Record<string, TaglineAsset>;
  backgroundPools: BackgroundPool[];
  taglinePools: TaglinePool[];
  audiences: Audience[];
  outputFormats: OutputFormat[];
  composition?: {
    layersBackToFront: string[];
    logoAssetPath: string;
    taglineColorRule?: string;
    defaultCallToAction?: string;
  };
  qualityChecks?: string[];
  output?: {
    directory: string;
    filenamePattern: string;
    writeManifest: boolean;
    manifestFilename: string;
  };
}

export type AspectRatio = '1:1' | '16:9' | '9:16';
export type LayerName = 'logo_region' | 'product_region' | 'tagline_region';
export interface LayoutRegion {
  x: number;
  y: number;
  max_width_pct: number;
  max_height_pct: number;
  anchor_x: 'left' | 'center' | 'right';
  anchor_y: 'top' | 'center' | 'bottom';
}
export type LayoutOverride = Partial<Record<LayerName, LayoutRegion | null>>;
export type DefaultLayout = Record<LayerName, LayoutRegion> & { canvas_width: number; canvas_height: number };

export interface BriefValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  audienceCount: number;
  formatCount: number;
  totalOutputs: number;
}
