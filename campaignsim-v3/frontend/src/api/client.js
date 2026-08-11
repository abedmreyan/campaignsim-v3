import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 30000,
  withCredentials: true,  // Send cookies on every request (required for httpOnly auth cookies)
});

// Response interceptor: normalize errors and handle 401 → auto-refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;

    // Auto-refresh: if we get a 401 and haven't already retried, call /refresh and retry once.
    // Skip for requests marked _skipRefresh (e.g. the initial session check in fetchMe).
    if (status === 401 && !error.config._retried && !error.config._skipRefresh) {
      error.config._retried = true;
      try {
        await apiClient.post("/api/auth/refresh");
        return apiClient(error.config);
      } catch {
        // Refresh failed (expired/revoked) — clear user and redirect to login,
        // but not if we're already on a public page (avoids infinite reload loop).
        try {
          const { useAuthStore } = await import("@/stores/authStore");
          const auth = useAuthStore();
          auth.user = null;
        } catch {
          // authStore not yet available (e.g., during boot) — safe to ignore
        }
        const publicPaths = ["/login", "/signup"];
        if (!publicPaths.includes(window.location.pathname)) {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    }

    const errorField = error?.response?.data?.error;
    const code = (typeof errorField === "object" && errorField?.code) || "NETWORK_ERROR";
    const message =
      error?.response?.data?.message ||
      (typeof errorField === "string" ? errorField : errorField?.message) ||
      error.message ||
      "Unexpected API error";

    return Promise.reject({
      status,
      code,
      message,
      details: error?.response?.data?.error?.details || {},
      raw: error,
    });
  },
);
