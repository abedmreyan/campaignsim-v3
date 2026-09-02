import { apiClient } from "./client";

const unwrap = (response) => response.data?.data ?? response.data;

export async function createInsightSession(campaignId) {
  return unwrap(await apiClient.post("/api/insight/sessions", { campaign_id: campaignId }));
}

export async function getInsightSession(sessionId) {
  return unwrap(await apiClient.get(`/api/insight/sessions/${sessionId}`));
}

export async function sendInsightMessage(sessionId, message) {
  return unwrap(await apiClient.post(`/api/insight/sessions/${sessionId}/messages`, { message }));
}

export async function applyInsightProposal(sessionId) {
  return unwrap(await apiClient.post(`/api/insight/sessions/${sessionId}/proposals/apply`));
}

export async function getCampaignLineage(campaignId) {
  return unwrap(await apiClient.get(`/api/simulation/campaign_lineage/${campaignId}`));
}
