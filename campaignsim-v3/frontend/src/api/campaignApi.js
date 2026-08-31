import * as mockApi from "./mockApi";
import * as realApi from "./realApi";

// Mock mode is opt-in, not opt-out: an unset/missing env var must mean "real
// backend". The previous polarity (`!== "false"`) meant any build without a
// .env file — including production, which never had one — silently ran the
// entire graph/persona/simulation pipeline against fake mock data.
const useMocks = import.meta.env.VITE_USE_MOCKS === "true";
const api = useMocks ? mockApi : realApi;

export const isMockMode = useMocks;

export const healthCheck = api.healthCheck;
export const createSimulationProject = api.createSimulationProject;
export const uploadBrandBrief = api.uploadBrandBrief;
export const buildGraph = api.buildGraph;
export const getGraphTask = api.getGraphTask;
export const getGraphProject = api.getGraphProject;
export const prepareGraph = api.prepareGraph;
export const getPreparationStatus = api.getPreparationStatus;
export const getGraphRelations = api.getGraphRelations;
export const generateProfiles = api.generateProfiles;
export const getProfileGenerationStatus = api.getProfileGenerationStatus;
export const getProfiles = api.getProfiles;
export const startAbTest = api.startAbTest;
export const getAbStatus = api.getAbStatus;
export const generateCampaignRecommendations = api.generateCampaignRecommendations;
export const getCampaignReport = api.getCampaignReport;
export const stopSimulation = api.stopSimulation;
export const getSimulationRunStatus = api.getSimulationRunStatus;
export const getVariantResults = api.getVariantResults;
export const generateReport = api.generateReport;
export const getReport = api.getReport;
export const interviewPersona = api.interviewPersona;
export const getHistory = api.getHistory;
export const getCampaignsForBrief = api.getCampaignsForBrief;
export const suggestBrandIntel = api.suggestBrandIntel;
export const getChannels = api.getChannels;
export const draftChannel = api.draftChannel;
export const createChannel = api.createChannel;
export const deleteChannel = api.deleteChannel;
