/** Read cached history for landing preview only — no API calls. */

const MOCK_STATE_KEY = "campaignsim_mock_state";

/**
 * @param {number} max
 * @returns {Array<{ simulation_id: string, project_name: string, status: string, top_variant_name?: string, updated_at?: string }>}
 */
export function getRecentHistoryPreview(max = 3) {
  try {
    const raw = localStorage.getItem(MOCK_STATE_KEY);
    if (!raw) return [];

    const state = JSON.parse(raw);
    const items = state?.history?.items;
    if (!Array.isArray(items) || !items.length) return [];

    return items.slice(0, max).map((item) => ({
      simulation_id: item.simulation_id || item.id || "",
      project_name: item.project_name || "Untitled campaign",
      status: item.status || "completed",
      top_variant_name: item.top_variant_name || "",
      updated_at: item.updated_at || item.created_at || "",
    }));
  } catch {
    return [];
  }
}

/**
 * @param {string} iso
 * @returns {string}
 */
export function formatHistoryPreviewDate(iso) {
  if (!iso) return "";
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
    }).format(new Date(iso));
  } catch {
    return "";
  }
}
