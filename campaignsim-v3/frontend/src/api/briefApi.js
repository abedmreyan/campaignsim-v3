import { apiClient } from "./client";

const unwrap = (response) => response.data?.data ?? response.data;

export async function listBriefs() {
  return unwrap(await apiClient.get("/api/briefs"));
}

export async function createBrief({ name, content = "", business_type }) {
  return unwrap(await apiClient.post("/api/briefs", { name, content, business_type }));
}

export async function updateBrief(briefId, { name, content, business_type }) {
  return unwrap(await apiClient.put(`/api/briefs/${briefId}`, { name, content, business_type }));
}

export async function deleteBrief(briefId) {
  return unwrap(await apiClient.delete(`/api/briefs/${briefId}`));
}
