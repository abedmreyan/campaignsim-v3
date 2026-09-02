import { apiClient } from "./client";

const unwrap = (response) => response.data?.data ?? response.data;

export async function createDesignerSession({ simulationId, brandBriefId } = {}) {
  return unwrap(
    await apiClient.post("/api/designer/sessions", {
      simulation_id: simulationId || undefined,
      brand_brief_id: brandBriefId || undefined,
    }),
  );
}

export async function getDesignerSession(sessionId) {
  return unwrap(await apiClient.get(`/api/designer/sessions/${sessionId}`));
}

export async function sendDesignerMessage(sessionId, message) {
  return unwrap(await apiClient.post(`/api/designer/sessions/${sessionId}/messages`, { message }));
}

export async function updateDesignerDraft(sessionId, draft) {
  return unwrap(await apiClient.put(`/api/designer/sessions/${sessionId}/draft`, draft));
}

export async function commitDesignerSession(sessionId) {
  return unwrap(await apiClient.post(`/api/designer/sessions/${sessionId}/commit`));
}
