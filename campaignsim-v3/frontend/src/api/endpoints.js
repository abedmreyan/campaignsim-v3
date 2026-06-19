export const endpoints = {
  health: "/health",

  // Graph / project endpoints (actual backend API)
  graphOntologyGenerate: "/api/graph/ontology/generate",
  graphBuild: "/api/graph/build",
  graphTask: (taskId) => `/api/graph/task/${taskId}`,
  graphProjectById: (projectId) => `/api/graph/project/${projectId}`,
  graphData: (graphId) => `/api/graph/data/${graphId}`,
  graphById: (graphId) => `/api/graph/data/${graphId}`,
  graphRelations: (graphId) => `/api/graph/data/${graphId}`,
  graphSearch: (graphId) => `/api/graph/${graphId}/search`,
  graphUpdateFromSimulation: (graphId) => `/api/graph/${graphId}/update-from-sim`,

  simulationCreate: "/api/simulation/create",
  simulationPrepare: "/api/simulation/prepare",
  simulationPrepareStatus: "/api/simulation/prepare/status",
  simulationList: "/api/simulation/list",
  simulationHistory: "/api/simulation/history",
  simulationById: (simulationId) => `/api/simulation/${simulationId}`,

  generateProfiles: "/api/simulation/generate-profiles",
  generateProfilesStatus: "/api/simulation/generate-profiles/status",
  profiles: (simulationId) => `/api/simulation/${simulationId}/profiles`,
  profilesRealtime: (simulationId) => `/api/simulation/${simulationId}/profiles/realtime`,

  simulationStart: "/api/simulation/start",
  simulationAbTest: "/api/simulation/ab_test",
  simulationAbStatus: (campaignId) => `/api/simulation/ab_status/${campaignId}`,
  simulationStop: "/api/simulation/stop",
  simulationRunStatus: (simulationId) => `/api/simulation/${simulationId}/run-status`,
  assignSegments: "/api/simulation/assign_segments",
  campaignRecommendations: "/api/simulation/campaign_recommendations",
  campaignReport: (campaignId) => `/api/simulation/campaign_report/${campaignId}`,
  campaignTask: (taskId) => `/api/graph/task/${taskId}`,

  reportGenerate: "/api/report/generate",
  reportById: (reportId) => `/api/report/${reportId}`,
  reportInterview: "/api/report/interview",

  suggestBrandIntel: "/api/ai/suggest",
};
