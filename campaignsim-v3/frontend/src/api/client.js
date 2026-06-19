import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const code = error?.response?.data?.error?.code || "NETWORK_ERROR";
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error?.message ||
      error.message ||
      "Unexpected API error";

    return Promise.reject({
      status: error?.response?.status,
      code,
      message,
      details: error?.response?.data?.error?.details || {},
      raw: error,
    });
  },
);
