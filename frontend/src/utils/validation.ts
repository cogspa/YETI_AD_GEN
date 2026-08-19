import type { BriefValidationResult } from '../types/campaign';

export function validateBrief(data: any): BriefValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data || typeof data !== 'object') {
    return {
      isValid: false,
      errors: ['Invalid JSON: Input must be a valid JSON object.'],
      warnings: [],
      audienceCount: 0,
      formatCount: 0,
      totalOutputs: 0,
    };
  }

  // Check campaign meta
  if (!data.campaign || typeof data.campaign !== 'object') {
    errors.push('Missing required "campaign" section.');
  } else {
    if (!data.campaign.id) errors.push('Missing "campaign.id".');
    if (!data.campaign.name) errors.push('Missing "campaign.name".');
  }

  // Check audiences
  let audienceCount = 0;
  if (!Array.isArray(data.audiences) || data.audiences.length === 0) {
    errors.push('Missing or empty "audiences" list.');
  } else {
    audienceCount = data.audiences.length;
    data.audiences.forEach((aud: any, idx: number) => {
      const id = aud.id || `Index ${idx}`;
      if (!aud.name) errors.push(`Audience [${id}] is missing a name.`);
      if (!aud.activity) errors.push(`Audience [${id}] is missing an activity.`);
      if (!aud.productColor) errors.push(`Audience [${id}] is missing productColor.`);
    });
  }

  // Check outputFormats
  let formatCount = 0;
  if (!Array.isArray(data.outputFormats) || data.outputFormats.length === 0) {
    errors.push('Missing or empty "outputFormats" list.');
  } else {
    formatCount = data.outputFormats.length;
    data.outputFormats.forEach((fmt: any, idx: number) => {
      const id = fmt.id || fmt.aspectRatio || `Format ${idx}`;
      if (!fmt.aspectRatio) errors.push(`Format [${id}] is missing aspectRatio.`);
      if (!fmt.width || !fmt.height) errors.push(`Format [${id}] is missing width/height dimensions.`);
    });
  }

  // Check backgroundPools & taglinePools
  if (!Array.isArray(data.backgroundPools) || data.backgroundPools.length === 0) {
    warnings.push('Brief does not declare backgroundPools (default fallbacks will be used).');
  }
  if (!Array.isArray(data.taglinePools) || data.taglinePools.length === 0) {
    warnings.push('Brief does not declare taglinePools.');
  }

  const conceptsPerAudience = Number(data.generation?.conceptsPerAudience) || 1;
  const totalOutputs = Number(data.generation?.totalOutputsPerRun) || (audienceCount * formatCount * conceptsPerAudience);

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    audienceCount,
    formatCount,
    totalOutputs,
  };
}

