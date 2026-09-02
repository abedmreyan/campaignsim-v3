import { apiClient } from "./client";

const unwrap = (response) => response.data?.data ?? response.data;

export async function listBriefs() {
  return unwrap(await apiClient.get("/api/briefs"));
}

export async function createBrief({ name, content = "", business_type }) {
  return unwrap(await apiClient.post("/api/briefs", { name, content, business_type }));
}

export async function getBrief(briefId) {
  return unwrap(await apiClient.get(`/api/briefs/${briefId}`));
}

export async function rebuildGraph(briefId, { simulation_requirement } = {}) {
  return unwrap(
    await apiClient.post(`/api/briefs/${briefId}/rebuild-graph`, { simulation_requirement }),
  );
}

export async function updateBrief(briefId, { name, content, business_type }) {
  return unwrap(await apiClient.put(`/api/briefs/${briefId}`, { name, content, business_type }));
}

export async function deleteBrief(briefId) {
  return unwrap(await apiClient.delete(`/api/briefs/${briefId}`));
}
