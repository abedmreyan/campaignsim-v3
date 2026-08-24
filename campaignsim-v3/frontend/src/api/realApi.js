import { apiClient } from "./client";
import { endpoints } from "./endpoints";

const unwrap = (response) => response.data?.data ?? response.data;

export async function healthCheck() {
  return unwrap(await apiClient.get(endpoints.health));
}

export async function createSimulationProject({ projectId, graphId } = {}) {
  return unwrap(await apiClient.post(endpoints.simulationCreate, {
    project_id: projectId,
    graph_id: graphId,
    enable_twitter: true,
    enable_reddit: true,
  }));
}

export async function uploadBrandBrief({ file, projectName, simulationRequirement, briefId }) {
  const formData = new FormData();
  formData.append("files", file);
  formData.append(
    "simulation_requirement",
    simulationRequirement || "Extract brand intelligence: products, audiences, channels, and competitive landscape",
  );
  formData.append("project_name", projectName || file.name.replace(/\.[^.]+$/, "") || "Campaign Brief");
  // Reuse the already-selected brief instead of minting a new one each upload.
  if (briefId) formData.append("brief_id", briefId);
  return unwrap(
    await apiClient.post(endpoints.graphOntologyGenerate, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  );
}

export async function buildGraph(payload) {
  return unwrap(await apiClient.post(endpoints.graphBuild, payload));
}

export async function getGraphTask(taskId) {
  return unwrap(await apiClient.get(endpoints.graphTask(taskId)));
}

export async function getGraphProject(projectId) {
  return unwrap(await apiClient.get(endpoints.graphProjectById(projectId)));
}

export async function prepareGraph(payload) {
  return unwrap(await apiClient.post(endpoints.simulationPrepare, payload));
}

export async function getPreparationStatus(payload) {
  return unwrap(await apiClient.post(endpoints.simulationPrepareStatus, payload));
}

export async function getGraphRelations(graphId) {
  return unwrap(await apiClient.get(endpoints.graphRelations(graphId)));
}

export async function generateProfiles(payload) {
  return unwrap(await apiClient.post(endpoints.generateProfiles, payload));
}

export async function getProfileGenerationStatus(taskId) {
  return unwrap(await apiClient.get(endpoints.generateProfilesStatus, { params: { task_id: taskId } }));
}

export async function getProfiles(simulationId) {
  return unwrap(await apiClient.get(endpoints.profiles(simulationId)));
}

export async function startAbTest(payload) {
  return unwrap(await apiClient.post(endpoints.simulationAbTest, payload));
}

export async function getAbStatus(campaignId) {
  return unwrap(await apiClient.get(endpoints.simulationAbStatus(campaignId)));
}

export async function generateCampaignRecommendations(payload) {
  return unwrap(await apiClient.post(endpoints.campaignRecommendations, payload));
}

export async function getCampaignReport(campaignId) {
  return unwrap(await apiClient.get(endpoints.campaignReport(campaignId)));
}

export async function stopSimulation(payload) {
  return unwrap(await apiClient.post(endpoints.simulationStop, payload));
}

export async function getSimulationRunStatus(simulationId, runId) {
  const config = runId ? { params: { run_id: runId } } : undefined;
  return unwrap(await apiClient.get(endpoints.simulationRunStatus(simulationId), config));
}

export async function getVariantResults(variantId) {
  return unwrap(await apiClient.get(endpoints.variantResults(variantId)));
}

export async function generateReport(payload) {
  return unwrap(await apiClient.post(endpoints.reportGenerate, payload));
}

export async function getReport(reportId) {
  return unwrap(await apiClient.get(endpoints.reportById(reportId)));
}

export async function interviewPersona(payload) {
  return unwrap(await apiClient.post(endpoints.reportInterview, payload));
}

export async function getHistory() {
  return unwrap(await apiClient.get(endpoints.simulationHistory));
}

export async function suggestBrandIntel(payload) {
  return unwrap(await apiClient.post(endpoints.suggestBrandIntel, payload));
}

export async function getChannels() {
  return unwrap(await apiClient.get(endpoints.channels));
}

export async function draftChannel(payload) {
  return unwrap(await apiClient.post(endpoints.channelDraft, payload));
}

export async function createChannel(payload) {
  return unwrap(await apiClient.post(endpoints.channels, payload));
}

export async function deleteChannel(channelId) {
  return unwrap(await apiClient.delete(endpoints.channelById(channelId)));
}
