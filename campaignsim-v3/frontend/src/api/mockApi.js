import { getMockData } from "@/data/mockData";

const delay = (ms = 550) => new Promise((resolve) => setTimeout(resolve, ms));
const clone = (value) => JSON.parse(JSON.stringify(value));

const state = {
  preparationProgress: 0,
  simulationProgress: 0,
  stopped: false,
  variants: [],
  personaCount: 30,
};

const mock = () => getMockData();

export async function healthCheck() {
  await delay(180);
  return {
    status: "ok",
    service: "CampaignSim Mock API",
    version: "mock-1.0.0",
    timestamp: new Date().toISOString(),
  };
}

export async function createSimulationProject() {
  await delay();
  const data = mock();
  return {
    ...data.project,
    simulation_id: data.project.simulation_id,
    status: "draft",
  };
}

export async function uploadBrandBrief({ file }) {
  await delay(700);
  const data = mock();
  return {
    project_id: data.project.project_id || "proj_mock_001",
    graph_id: data.project.graph_id,
    file: {
      file_id: "file_mock_123",
      filename: file?.name || "mock-brand-brief.pdf",
      mime_type: file?.type || "application/pdf",
      size_bytes: file?.size || 1240000,
    },
  };
}

export async function buildGraph() {
  await delay(300);
  return {
    task_id: "task_build_mock_001",
    status: "processing",
  };
}

export async function getGraphTask() {
  await delay(400);
  const data = mock();
  return {
    task_id: "task_build_mock_001",
    status: "completed",
    progress: 1,
    message: "Graph built successfully",
    result: {
      graph_id: data.project.graph_id,
    },
  };
}

export async function getGraphProject() {
  await delay(300);
  const data = mock();
  return {
    project_id: data.project.project_id || "proj_mock_001",
    graph_id: data.project.graph_id,
    status: "ready",
  };
}

export async function prepareGraph({ simulation_id, graph_id }) {
  await delay(400);
  state.preparationProgress = 0;
  return {
    task_id: "task_prepare_mock",
    simulation_id,
    graph_id,
    status: "processing",
  };
}

export async function getPreparationStatus({ task_id, simulation_id }) {
  await delay(420);
  state.preparationProgress = Math.min(100, state.preparationProgress + 28);
  const completed = state.preparationProgress >= 100;
  const data = mock();

  return {
    task_id,
    simulation_id,
    status: completed ? "completed" : "running",
    progress: state.preparationProgress,
    current_step: completed ? "Knowledge graph ready" : "Extracting marketing entities",
    graph_id: data.graph.graph_id,
    summary: completed
      ? {
          nodes_count: data.graph.nodes.length,
          edges_count: data.graph.edges.length,
          entity_types: [...new Set(data.graph.nodes.map((node) => node.type))],
        }
      : undefined,
  };
}

export async function getGraphRelations() {
  await delay();
  return clone(mock().graph);
}

const BRAND_INTEL_BY_INDUSTRY = {
  "SaaS / Software": {
    products: [
      { name: "Core Platform", description: "Primary subscription product" },
      { name: "Analytics Add-on", description: "Advanced reporting & dashboards" },
      { name: "Enterprise Tier", description: "Custom SLAs and dedicated support" },
    ],
    audiences: [
      { name: "Growth-Stage Startups", ageRange: "25–40", description: "Teams scaling fast, value automation" },
      { name: "Enterprise IT Buyers", ageRange: "35–55", description: "Security-focused, long procurement cycles" },
      { name: "Individual Developers", ageRange: "22–35", description: "Bottom-up adoption, self-serve onboarding" },
    ],
    channels: ["LinkedIn", "Google Search", "Product Hunt", "Developer Communities", "Email"],
    formats: ["Case Studies", "Webinars", "Interactive Demos", "Technical Blog Posts", "Free Trials"],
  },
  "Retail / E-commerce": {
    products: [
      { name: "Hero Product Line", description: "Best-selling flagship category" },
      { name: "Seasonal Collection", description: "Limited-time promotional bundles" },
      { name: "Loyalty Program", description: "Subscription or points-based rewards" },
    ],
    audiences: [
      { name: "Value Shoppers", ageRange: "28–45", description: "Price-sensitive, coupon hunters" },
      { name: "Trend-Driven Millennials", ageRange: "22–35", description: "Brand-conscious, social proof driven" },
      { name: "Gift Buyers", ageRange: "30–55", description: "Seasonal, high AOV intent" },
    ],
    channels: ["Instagram", "Facebook Ads", "Google Shopping", "Email", "TikTok"],
    formats: ["User-Generated Content", "Flash Sales", "Influencer Reviews", "Product Videos", "Email Sequences"],
  },
  "Financial Services": {
    products: [
      { name: "Core Account / Card", description: "Primary financial product" },
      { name: "Investment Product", description: "Wealth management or savings vehicle" },
      { name: "Insurance Bundle", description: "Protective financial layer" },
    ],
    audiences: [
      { name: "Young Professionals", ageRange: "24–35", description: "Building credit, salary-account seekers" },
      { name: "High-Net-Worth Individuals", ageRange: "40–60", description: "Wealth preservation, low risk tolerance" },
      { name: "Small Business Owners", ageRange: "30–50", description: "Cash-flow management, B2B needs" },
    ],
    channels: ["Google Search", "LinkedIn", "Financial Media", "Email", "Referral Programs"],
    formats: ["Comparison Guides", "Educational Webinars", "Calculators / Tools", "Whitepapers", "Trust Badges"],
  },
  "Healthcare": {
    products: [
      { name: "Core Health Service", description: "Primary clinical or wellness offering" },
      { name: "Preventive Care Package", description: "Screenings, wellness checks" },
      { name: "Digital Health Tool", description: "App or telehealth component" },
    ],
    audiences: [
      { name: "Chronic Condition Patients", ageRange: "40–65", description: "High engagement, loyalty-driven" },
      { name: "Health-Conscious Millennials", ageRange: "25–38", description: "Preventive focus, digital-native" },
      { name: "Caregiver Decision-Makers", ageRange: "35–55", description: "Buying for dependents" },
    ],
    channels: ["Google Search", "Facebook", "Healthcare Portals", "Email", "Physician Referral"],
    formats: ["Patient Testimonials", "Educational Articles", "FAQ Videos", "Symptom Checkers", "Trust Seals"],
  },
  "Consumer Goods / CPG": {
    products: [
      { name: "Flagship Product", description: "Core SKU driving brand recognition" },
      { name: "Premium Line", description: "Higher margin, premium positioning" },
      { name: "Starter Pack / Bundle", description: "Acquisition-focused bundle" },
    ],
    audiences: [
      { name: "Household Decision Makers", ageRange: "28–48", description: "Convenience and value focused" },
      { name: "Health-Conscious Consumers", ageRange: "22–40", description: "Ingredient transparency, ethical sourcing" },
      { name: "Brand Loyalists", ageRange: "30–55", description: "Repeat buyers, advocacy potential" },
    ],
    channels: ["Instagram", "TV / Streaming Ads", "Retail Media", "Email", "In-Store Displays"],
    formats: ["Lifestyle Photography", "Unboxing Videos", "Recipes / Tutorials", "Limited Editions", "Sampling Campaigns"],
  },
  "EdTech / Education": {
    products: [
      { name: "Core Course / Program", description: "Flagship learning product" },
      { name: "Certification Track", description: "Credential-based pathway" },
      { name: "Team / B2B License", description: "Bulk seats for organizations" },
    ],
    audiences: [
      { name: "Career Changers", ageRange: "25–40", description: "Upskilling for new roles, ROI focused" },
      { name: "Recent Graduates", ageRange: "20–28", description: "Entry-level credentials, job placement" },
      { name: "Corporate L&D Buyers", ageRange: "35–55", description: "Scalable training solutions" },
    ],
    channels: ["Google Search", "LinkedIn", "YouTube", "Email", "University Partnerships"],
    formats: ["Free Mini-Courses", "Outcome Statistics", "Instructor Credibility Content", "Webinars", "Comparison Tables"],
  },
};

const FALLBACK_INTEL = {
  products: [
    { name: "Core Offering", description: "Primary product or service" },
    { name: "Premium Tier", description: "Enhanced features or support level" },
    { name: "Entry Package", description: "Lower-barrier acquisition product" },
  ],
  audiences: [
    { name: "Primary Buyers", ageRange: "28–45", description: "Core demographic, high intent" },
    { name: "Emerging Segment", ageRange: "22–35", description: "Growth opportunity audience" },
    { name: "Loyal Advocates", ageRange: "35–55", description: "High LTV, referral potential" },
  ],
  channels: ["Google Search", "Social Media", "Email Marketing", "Content / SEO", "Paid Social"],
  formats: ["Educational Blog Posts", "Video Demos", "Case Studies", "Email Sequences", "Testimonials"],
};

function matchIndustryKey(industry) {
  const s = (industry || "").toLowerCase();
  if (s.includes("saas") || s.includes("software")) return "SaaS / Software";
  if (s.includes("retail") || s.includes("e-commerce") || s.includes("ecommerce")) return "Retail / E-commerce";
  if (s.includes("financial") || s.includes("finance") || s.includes("banking")) return "Financial Services";
  if (s.includes("health")) return "Healthcare";
  if (s.includes("consumer") || s.includes("cpg")) return "Consumer Goods / CPG";
  if (s.includes("edtech") || s.includes("education")) return "EdTech / Education";
  if (s.includes("food") || s.includes("beverage")) return "Consumer Goods / CPG";
  if (s.includes("media") || s.includes("entertainment")) return null;
  return null;
}

export async function suggestBrandIntel({ brandName, industry, valueProposition }) {
  await delay(1400);
  const key = matchIndustryKey(industry);
  const intel = (key && BRAND_INTEL_BY_INDUSTRY[key]) || FALLBACK_INTEL;
  return {
    brand: brandName,
    industry,
    suggestions: {
      products: intel.products,
      audiences: intel.audiences,
      channels: intel.channels,
      formats: intel.formats,
    },
  };
}

export async function getAbStatus() {
  await delay(400);
  const data = mock();
  return {
    campaign_id: "campaign_mock_001",
    total_variants: data.variants?.length || 2,
    completed: data.variants?.length || 2,
    failed: 0,
    all_done: true,
    variants: (data.variants || []).map((v) => ({
      variant_id: v.variant_id,
      variant_name: v.variant_name,
      channel: v.channel,
      runner_status: "completed",
      actions_count: 85,
    })),
  };
}

export async function generateCampaignRecommendations() {
  await delay(500);
  return {
    task_id: "task_campaign_report_mock",
    status: "processing",
  };
}

export async function getCampaignReport() {
  await delay(600);
  const data = mock();
  const results = clone(data.results || []);
  const report = clone(data.report || {});
  return {
    report_text: report.markdown_content || "## Campaign Report\n\nSimulation complete.",
    top_recommendation: report.top_recommendation || {
      variant_id: results[0]?.variant_id,
      variant_name: results[0]?.variant_name,
      reason: "Highest engagement rate across all tested personas.",
    },
    scored_variants: results,
    tool_calls_log: [],
  };
}

export async function generateProfiles({ simulation_id, count = 30 }) {
  await delay(650);
  state.personaCount = count;
  return {
    task_id: "task_personas_mock",
    simulation_id,
    status: "processing",
  };
}

export async function getProfiles() {
  await delay(650);
  const basePersonas = clone(mock().personas);
  const personas = Array.from({ length: state.personaCount }, (_item, index) => {
    const base = basePersonas[index % basePersonas.length];
    const suffix = index < basePersonas.length ? "" : ` ${index + 1}`;
    return {
      ...base,
      user_id: index + 1,
      user_name: `${base.user_name}_${index + 1}`,
      name: `${base.name}${suffix}`,
    };
  });
  return {
    personas,
  };
}

export async function startAbTest({ simulation_id, variants }) {
  await delay(650);
  state.simulationProgress = 0;
  state.stopped = false;
  state.variants = clone(variants);
  return {
    simulation_id,
    run_id: "run_ab_123",
    status: "running",
  };
}

export async function stopSimulation({ simulation_id, run_id }) {
  await delay(300);
  state.stopped = true;
  return {
    simulation_id,
    run_id,
    status: "stopped",
  };
}

export async function getSimulationRunStatus(simulationId) {
  await delay(420);
  if (state.stopped) {
    return {
      simulation_id: simulationId,
      run_id: "run_ab_123",
      status: "stopped",
      progress: state.simulationProgress,
      variants: state.variants,
    };
  }

  state.simulationProgress = Math.min(100, state.simulationProgress + 18);
  const completed = state.simulationProgress >= 100;
  const variants = (state.variants.length ? state.variants : mock().variants).map((variant, index) => {
    const offset = index * 12;
    const progress = Math.min(100, Math.max(0, state.simulationProgress - offset + 10));
    return {
      variant_id: variant.variant_id || `v${index + 1}`,
      variant_name: variant.variant_name,
      status: completed ? "completed" : progress > 8 ? "running" : "pending",
      progress,
      current_round: Math.ceil(progress / 10),
      max_rounds: variant.max_rounds || 10,
    };
  });

  return {
    simulation_id: simulationId,
    run_id: "run_ab_123",
    status: completed ? "completed" : "running",
    progress: state.simulationProgress,
    current_round: Math.ceil(state.simulationProgress / 10),
    max_rounds: 10,
    variants,
  };
}

export async function getVariantResults(variantId) {
  await delay(300);
  return clone(mock().results.find((result) => result.variant_id === variantId) || mock().results[0]);
}

export async function generateReport({ simulation_id }) {
  await delay(750);
  return {
    report_id: mock().report.report_id,
    simulation_id,
    status: "processing",
  };
}

export async function getReport() {
  await delay(500);
  const data = mock();
  return {
    ...clone(data.report),
    results: clone(data.results),
  };
}

export async function interviewPersona({ persona_id, question }) {
  await delay(550);
  const persona = mock().personas.find((item) => item.user_id === Number(persona_id)) || mock().personas[0];
  return {
    persona_id: persona.user_id,
    persona_name: persona.name,
    answer: `As ${persona.name}, I would say: ${question.toLowerCase().includes("email") ? "the email needs a clearer personal reason to click" : "the strongest message feels quick, useful, and aligned with my routine"}. The campaign works best when it respects my time and shows the product in a realistic moment.`,
    related_variant_id: "v1",
  };
}

export async function getHistory() {
  await delay(350);
  return {
    items: clone(mock().history),
  };
}
