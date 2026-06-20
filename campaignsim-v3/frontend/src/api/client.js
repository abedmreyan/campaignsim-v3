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

    // Auto-refresh: if we get a 401 and haven't already retried, call /refresh and retry once
    if (status === 401 && !error.config._retried) {
      error.config._retried = true;
      try {
        await apiClient.post("/api/auth/refresh");
        return apiClient(error.config);
      } catch {
        // Refresh failed (expired/revoked) — clear user and redirect to login
        try {
          const { useAuthStore } = await import("@/stores/authStore");
          const auth = useAuthStore();
          auth.user = null;
        } catch {
          // authStore not yet available (e.g., during boot) — safe to ignore
        }
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    const code = error?.response?.data?.error?.code || "NETWORK_ERROR";
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error?.message ||
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
