import type { CampaignBrief } from '../types/campaign';

export const YETI_GO_ANYWHERE_2026_BRIEF: CampaignBrief = {
  schemaVersion: "1.0.0",
  campaign: {
    id: "yeti-la-go-anywhere-2026",
    name: "Go Anywhere with YETI",
    market: "Los Angeles, California",
    ageRange: {
      minimum: 20,
      maximum: 30
    },
    objective: "Generate randomized, locally relevant YETI ads for Los Angeles audiences while keeping product color, environment and typography controlled by campaign rules.",
    campaignLine: "Go Anywhere with YETI"
  },
  generation: {
    mode: "seeded-random",
    seed: null,
    randomizeOncePerAudience: true,
    renderAllFormatsFromSameConcept: true,
    adsPerAudience: 3,
    totalAudienceGroups: 6,
    totalOutputsPerRun: 18,
    selectionRules: {
      background: "Randomly select one background from the audience's assigned backgroundPoolId.",
      tagline: "Randomly select one tagline from the audience's assigned taglinePoolId.",
      taglineColor: "Use black tagline (#000000) for beach activity. Use white tagline (#FFFFFF) for camping and tailgating (college) activities.",
      productColor: "Use orange when audience age maximum is 24 or younger. Use white when audience age minimum is 25 or older.",
      formats: "Render the selected concept once in every format listed in outputFormats."
    },
    repeatProtection: {
      scope: "run-and-prior-manifest",
      avoidImmediateBackgroundRepeat: true,
      avoidImmediateTaglineRepeat: true,
      priorManifestPath: "outputs/yeti-la-go-anywhere-2026/generation-manifest.json"
    }
  },
  creativeRules: {
    tagline: {
      rules: "Beach has the black tagline (#000000). Camping and College/Tailgating have the white tagline (#FFFFFF).",
      beach: {
        colorName: "Black",
        hex: "#000000",
        assetPath: "assets/taglines/TAGLINE_black.png"
      },
      camping: {
        colorName: "White",
        hex: "#FFFFFF",
        assetPath: "assets/taglines/TAGLINE_white.png"
      },
      tailgating: {
        colorName: "White",
        hex: "#FFFFFF",
        assetPath: "assets/taglines/TAGLINE_white.png"
      },
      maximumLines: 2,
      preferredPlacement: "lower-left",
      requireContrastBehindText: true
    },
    product: {
      preserveOfficialLogo: true,
      preserveProductShape: true,
      doNotGenerateTextOnProduct: true,
      remainPrimaryForegroundElement: true
    },
    background: {
      productMustRemainDominant: true,
      avoidBusyPatternsBehindProduct: true,
      avoidBusyPatternsBehindTagline: true,
      allowSubtleRegionalCues: true
    },
    universityRestrictions: {
      useUclaOrUscMarks: false,
      implyUniversityEndorsement: false,
      allowedLocationReferences: [
        "Westwood",
        "South Central Los Angeles"
      ]
    }
  },
  productAssets: {
    orange: {
      colorName: "Orange",
      assetPath: "assets/products/cooler_orange.png",
      assignedAgeBand: "20-24"
    },
    white: {
      colorName: "White",
      assetPath: "assets/products/cooler_white.png",
      assignedAgeBand: "25-30"
    }
  },
  taglineAssets: {
    black: {
      colorName: "Black",
      hex: "#000000",
      assetPath: "assets/taglines/TAGLINE_black.png",
      activities: ["beach"]
    },
    white: {
      colorName: "White",
      hex: "#FFFFFF",
      assetPath: "assets/taglines/TAGLINE_white.png",
      activities: ["camping", "tailgating"]
    }
  },
  backgroundPools: [
    {
      id: "tailgating-westwood",
      activity: "tailgating",
      territory: "Westwood",
      visualDirection: "A lively but uncluttered Los Angeles game-day tailgate near Westwood, with neutral campus-area architecture and no university logos or trademarks.",
      assets: [
        "assets/backgrounds/Tailgate.jpg"
      ]
    },
    {
      id: "tailgating-south-central",
      activity: "tailgating",
      territory: "South Central Los Angeles",
      visualDirection: "An energetic but visually controlled urban game-day tailgate in South Central Los Angeles, without USC logos, mascots or trademarked graphics.",
      assets: [
        "assets/backgrounds/Tailgate.jpg"
      ]
    },
    {
      id: "beach-west-coast",
      activity: "beach",
      territory: "Westside Los Angeles coast",
      visualDirection: "A bright Westside Los Angeles beach environment with soft sand, coastal atmosphere and open negative space for a black tagline.",
      assets: [
        "assets/backgrounds/Beach.jpg"
      ]
    },
    {
      id: "camping-la-mountains",
      activity: "camping",
      territory: "Los Angeles mountain outskirts",
      visualDirection: "A calm mountain camping environment in the Los Angeles outskirts with trees, distant ridgelines and sufficient contrast for a white tagline.",
      assets: [
        "assets/backgrounds/Camping.jpg"
      ]
    }
  ],
  taglinePools: [
    {
      id: "tailgating-taglines",
      activity: "tailgating",
      textColor: "#FFFFFF",
      taglines: [
        "Game Day Starts Here.",
        "Pack the Cold. Bring the Crowd.",
        "Cold From Kickoff to the Final Whistle."
      ]
    },
    {
      id: "beach-taglines",
      activity: "beach",
      textColor: "#000000",
      taglines: [
        "Go West. Stay Cold.",
        "Cold Drinks. Long Coast Days.",
        "Keep the Coast Cold."
      ]
    },
    {
      id: "camping-taglines",
      activity: "camping",
      textColor: "#FFFFFF",
      taglines: [
        "Go Higher. Stay Colder.",
        "Built for the First Campout.",
        "Weekend Altitude. All-Day Cold."
      ]
    }
  ],
  audiences: [
    {
      id: "P01",
      name: "Westwood College Tailgaters",
      age: { minimum: 20, maximum: 23, band: "younger" },
      lifeStage: "Undergraduate college student",
      activity: "tailgating",
      territory: "Westwood",
      backgroundPoolId: "tailgating-westwood",
      taglinePoolId: "tailgating-taglines",
      productModel: "YETI Roadie 24",
      productColor: "orange",
      productAssetId: "orange"
    },
    {
      id: "P02",
      name: "South Central College Tailgaters",
      age: { minimum: 20, maximum: 24, band: "younger" },
      lifeStage: "Undergraduate college student",
      activity: "tailgating",
      territory: "South Central Los Angeles",
      backgroundPoolId: "tailgating-south-central",
      taglinePoolId: "tailgating-taglines",
      productModel: "YETI Tundra 45",
      productColor: "orange",
      productAssetId: "orange"
    },
    {
      id: "P03",
      name: "Westside Recent Graduates",
      age: { minimum: 25, maximum: 27, band: "older" },
      lifeStage: "College graduate or young professional",
      activity: "beach",
      territory: "Westside Los Angeles coast",
      backgroundPoolId: "beach-west-coast",
      taglinePoolId: "beach-taglines",
      productModel: "YETI Roadie 24",
      productColor: "white",
      productAssetId: "white"
    },
    {
      id: "P04",
      name: "College Friends Beach Day",
      age: { minimum: 20, maximum: 24, band: "younger" },
      lifeStage: "College student or recent graduate",
      activity: "beach",
      territory: "Westside Los Angeles coast",
      backgroundPoolId: "beach-west-coast",
      taglinePoolId: "beach-taglines",
      productModel: "YETI Roadie 24",
      productColor: "orange",
      productAssetId: "orange"
    },
    {
      id: "P05",
      name: "First-Time Family Campers",
      age: { minimum: 27, maximum: 30, band: "older" },
      lifeStage: "Young parent taking an early family camping trip",
      activity: "camping",
      territory: "Los Angeles mountain outskirts",
      backgroundPoolId: "camping-la-mountains",
      taglinePoolId: "camping-taglines",
      productModel: "YETI Tundra 45",
      productColor: "white",
      productAssetId: "white"
    },
    {
      id: "P06",
      name: "Graduate Adventure Campers",
      age: { minimum: 25, maximum: 30, band: "older" },
      lifeStage: "Graduate student or young professional",
      activity: "camping",
      territory: "Los Angeles mountain outskirts",
      backgroundPoolId: "camping-la-mountains",
      taglinePoolId: "camping-taglines",
      productModel: "YETI Roadie 24",
      productColor: "white",
      productAssetId: "white"
    }
  ],
  outputFormats: [
    { id: "square", aspectRatio: "1:1", width: 1080, height: 1080, filenameTag: "1x1" },
    { id: "landscape", aspectRatio: "16:9", width: 1920, height: 1080, filenameTag: "16x9" },
    { id: "vertical", aspectRatio: "9:16", width: 1080, height: 1920, filenameTag: "9x16" }
  ],
  composition: {
    layersBackToFront: [
      "selectedBackground",
      "productShadow",
      "selectedProductAsset",
      "tagline",
      "brandLogo"
    ],
    logoAssetPath: "assets/brand/Yeti_Logo_1.png",
    taglineColorRule: "Beach: #000000 (Black), Camping/Tailgating: #FFFFFF (White)",
    defaultCallToAction: "Explore YETI"
  },
  qualityChecks: [
    "background activity matches audience activity",
    "background pool matches assigned territory",
    "tagline color is #000000 for beach and #FFFFFF for camping/tailgating",
    "tagline remains readable against background",
    "audiences age 20-24 use the orange product asset",
    "audiences age 25-30 use the white product asset",
    "product shape and logo are not distorted",
    "no unlicensed UCLA or USC marks appear",
    "all three output formats are created for every audience",
    "final dimensions match the selected output format"
  ],
  output: {
    directory: "outputs/yeti-la-go-anywhere-2026",
    filenamePattern: "{campaignId}_{audienceId}_{activity}_{productColor}_{backgroundIndex}_{taglineIndex}_{formatTag}.png",
    writeManifest: true,
    manifestFilename: "generation-manifest.json"
  }
};

export const SAMPLE_BRIEFS: { id: string; filename: string; label: string; brief: CampaignBrief }[] = [
  {
    id: "yeti-la-go-anywhere-2026",
    filename: "yeti-la-go-anywhere-2026.json",
    label: "yeti-la-go-anywhere-2026.json (18 Ads)",
    brief: YETI_GO_ANYWHERE_2026_BRIEF
  },
  {
    id: "yeti-la-random-ad-campaign-36",
    filename: "yeti_la_random_ad_campaign_36.json",
    label: "yeti_la_random_ad_campaign_36.json (36 Ads)",
    brief: {
      ...YETI_GO_ANYWHERE_2026_BRIEF,
      generation: {
        ...YETI_GO_ANYWHERE_2026_BRIEF.generation,
        conceptsPerAudience: 2,
        totalAudienceGroups: 6,
        adsPerAudience: 6,
        totalOutputsPerRun: 36
      }
    }
  },
  {
    id: "yeti-la-random-ad-campaign-72",
    filename: "yeti_la_random_ad_campaign_72.json",
    label: "yeti_la_random_ad_campaign_72.json (72 Ads - 12 Demographics + Gemini AI)",
    brief: {
      ...YETI_GO_ANYWHERE_2026_BRIEF,
      campaign: {
        ...YETI_GO_ANYWHERE_2026_BRIEF.campaign,
        name: "Go Anywhere with YETI (72-Ad Multi-Audience Campaign)"
      },
      generation: {
        ...YETI_GO_ANYWHERE_2026_BRIEF.generation,
        conceptsPerAudience: 2,
        totalAudienceGroups: 12,
        adsPerAudience: 6,
        totalOutputsPerRun: 72
      },
      audiences: [
        ...YETI_GO_ANYWHERE_2026_BRIEF.audiences,
        {
          id: "P07",
          name: "Hollywood Hills Trail Hikers (Gemini AI Scene)",
          age: { minimum: 20, maximum: 23, band: "younger" },
          lifeStage: "College outdoor fitness club",
          activity: "hiking",
          territory: "Hollywood Hills and Griffith Park",
          backgroundPoolId: "hiking-la-trails",
          taglinePoolId: "hiking-taglines",
          productModel: "YETI Roadie 24",
          productColor: "orange",
          productAssetId: "orange"
        },
        {
          id: "P08",
          name: "Griffith Park Ridgeline Trekkers (Gemini AI Scene)",
          age: { minimum: 26, maximum: 30, band: "older" },
          lifeStage: "Young professional weekend trail runners",
          activity: "hiking",
          territory: "Hollywood Hills and Griffith Park",
          backgroundPoolId: "hiking-la-trails",
          taglinePoolId: "hiking-taglines",
          productModel: "YETI Tundra 45",
          productColor: "white",
          productAssetId: "white"
        },
        {
          id: "P09",
          name: "Malibu Point Dawn Surfers (Gemini AI Scene)",
          age: { minimum: 21, maximum: 24, band: "younger" },
          lifeStage: "Collegiate surf team",
          activity: "surfing",
          territory: "Malibu Surfrider Beach",
          backgroundPoolId: "surfing-pacific-coast",
          taglinePoolId: "surfing-taglines",
          productModel: "YETI Roadie 24",
          productColor: "orange",
          productAssetId: "orange"
        },
        {
          id: "P10",
          name: "South Bay Sunset Surfers (Gemini AI Scene)",
          age: { minimum: 25, maximum: 29, band: "older" },
          lifeStage: "Coastal young professionals",
          activity: "surfing",
          territory: "Malibu Surfrider Beach",
          backgroundPoolId: "surfing-pacific-coast",
          taglinePoolId: "surfing-taglines",
          productModel: "YETI Tundra 45",
          productColor: "white",
          productAssetId: "white"
        },
        {
          id: "P11",
          name: "Marina Del Rey Anglers (Gemini AI Scene)",
          age: { minimum: 22, maximum: 24, band: "younger" },
          lifeStage: "Coastal adventure anglers",
          activity: "fishing",
          territory: "Marina Del Rey Coastal Waters",
          backgroundPoolId: "fishing-la-harbor",
          taglinePoolId: "fishing-taglines",
          productModel: "YETI Roadie 24",
          productColor: "orange",
          productAssetId: "orange"
        },
        {
          id: "P12",
          name: "Stoney Point Rock Climbers (Gemini AI Scene)",
          age: { minimum: 25, maximum: 30, band: "older" },
          lifeStage: "Weekend bouldering and climbing crew",
          activity: "climbing",
          territory: "Stoney Point Mountain Rocks",
          backgroundPoolId: "climbing-stoney-point",
          taglinePoolId: "climbing-taglines",
          productModel: "YETI Tundra 45",
          productColor: "white",
          productAssetId: "white"
        }
      ]
    }
  }
];

