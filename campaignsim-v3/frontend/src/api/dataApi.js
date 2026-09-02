import { apiClient } from "./client";

const unwrap = (response) => response.data?.data ?? response.data;

// ---------------- Datasets ----------------

export async function listDatasets() {
  return unwrap(await apiClient.get("/api/data/datasets"));
}

export async function uploadDataset(file, name) {
  const form = new FormData();
  form.append("file", file);
  if (name) form.append("name", name);
  return unwrap(await apiClient.post("/api/data/datasets", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }));
}

export async function getDataset(datasetId) {
  return unwrap(await apiClient.get(`/api/data/datasets/${datasetId}`));
}

export async function deleteDataset(datasetId) {
  return unwrap(await apiClient.delete(`/api/data/datasets/${datasetId}`));
}

export async function getDatasetMapping(datasetId) {
  return unwrap(await apiClient.get(`/api/data/datasets/${datasetId}/mapping`));
}

export async function updateDatasetMapping(datasetId, mapping) {
  return unwrap(await apiClient.put(`/api/data/datasets/${datasetId}/mapping`, { mapping }));
}

export async function importDataset(datasetId) {
  return unwrap(await apiClient.post(`/api/data/datasets/${datasetId}/import`));
}

export async function segmentDataset(datasetId) {
  return unwrap(await apiClient.post(`/api/data/datasets/${datasetId}/segment`));
}

// Generic task poller — same task_id contract as graph build / campaign report.
export async function getTaskStatus(taskId) {
  return unwrap(await apiClient.get(`/api/graph/task/${taskId}`));
}

// ---------------- Segments ----------------

export async function listSegments(datasetId) {
  const params = datasetId ? { dataset_id: datasetId } : {};
  return unwrap(await apiClient.get("/api/data/segments", { params }));
}

export async function getSegment(segmentId) {
  return unwrap(await apiClient.get(`/api/data/segments/${segmentId}`));
}

export async function updateSegment(segmentId, { name, description, status } = {}) {
  const body = {};
  if (name !== undefined) body.name = name;
  if (description !== undefined) body.description = description;
  if (status !== undefined) body.status = status;
  return unwrap(await apiClient.put(`/api/data/segments/${segmentId}`, body));
}

export async function mergeSegments(segmentIds, name, description) {
  return unwrap(await apiClient.post("/api/data/segments/merge", {
    segment_ids: segmentIds, name, description,
  }));
}

export function segmentExportUrl(segmentId) {
  return `${apiClient.defaults.baseURL || ""}/api/data/segments/${segmentId}/export`;
}

// ---------------- Segment-grounded personas ----------------

export async function generatePersonasFromSegments({ simulationId, brandBriefId, segmentIds, totalN, mode }) {
  return unwrap(await apiClient.post("/api/simulation/personas/from-segments", {
    simulation_id: simulationId,
    brand_brief_id: brandBriefId || undefined,
    segment_ids: segmentIds,
    total_n: totalN,
    mode,
  }));
}
