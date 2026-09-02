import { ref } from "vue";
import { apiClient } from "@/api/client.js";

export const BUSINESS_TYPE_OPTIONS = [
  { value: "", label: "Not set" },
  { value: "b2c_product", label: "B2C product" },
  { value: "b2b", label: "B2B" },
  { value: "services", label: "Services" },
  { value: "local", label: "Local business" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "app", label: "App / software" },
];

export const BUSINESS_TYPE_LABELS = Object.fromEntries(
  BUSINESS_TYPE_OPTIONS.filter((o) => o.value).map((o) => [o.value, o.label]),
);

export function businessTypeLabel(value) {
  return BUSINESS_TYPE_LABELS[value] || value;
}

/**
 * Shared "create a new business/brief" form state + submit flow, used by
 * both the full BrandBriefView management grid and the dynamic island's
 * quick-create row so the two don't drift.
 */
export function useBriefCreate({ onCreated } = {}) {
  const name = ref("");
  const content = ref("");
  const businessType = ref("");
  const contentMode = ref("text"); // "text" | "upload"
  const file = ref(null);
  const creating = ref(false);
  const uploading = ref(false);
  const error = ref(null);

  function reset() {
    name.value = "";
    content.value = "";
    businessType.value = "";
    contentMode.value = "text";
    file.value = null;
    error.value = null;
  }

  async function submit() {
    error.value = null;
    creating.value = true;
    try {
      const resp = await apiClient.post("/api/briefs", {
        name: name.value,
        content: contentMode.value === "text" ? content.value : "",
        business_type: businessType.value || undefined,
      });
      let brief = resp.data.data;

      if (contentMode.value === "upload" && file.value) {
        uploading.value = true;
        const formData = new FormData();
        formData.append("file", file.value);
        const uploadResp = await apiClient.post(
          `/api/briefs/${brief.id}/upload`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } },
        );
        brief = uploadResp.data.data;
        uploading.value = false;
      }

      onCreated?.(brief);
      reset();
      return brief;
    } catch (err) {
      error.value = err?.response?.data?.error?.message || err?.message || "Could not save this business.";
      throw err;
    } finally {
      creating.value = false;
      uploading.value = false;
    }
  }

  return {
    name,
    content,
    businessType,
    contentMode,
    file,
    creating,
    uploading,
    error,
    submit,
    reset,
  };
}
