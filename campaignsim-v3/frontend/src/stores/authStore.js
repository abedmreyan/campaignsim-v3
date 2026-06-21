import { defineStore } from "pinia";
import { apiClient } from "@/api/client.js";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,       // { id, email, display_name } or null
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
  },

  actions: {
    async fetchMe() {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.get("/api/auth/me", { _skipRefresh: true });
        this.user = resp.data;
      } catch (err) {
        // Access token may have expired — try refreshing before giving up.
        // This keeps the user logged in as long as their refresh token (30 days) is valid.
        if (err?.status === 401 || err?.raw?.response?.status === 401) {
          try {
            await apiClient.post("/api/auth/refresh", {}, { _skipRefresh: true });
            const resp = await apiClient.get("/api/auth/me", { _skipRefresh: true });
            this.user = resp.data;
            return;
          } catch {
            // Refresh token also expired — user must log in again
          }
        }
        this.user = null;
      } finally {
        this.loading = false;
      }
    },

    async login(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.post("/api/auth/login", { email, password }, { _skipRefresh: true });
        this.user = resp.data.user;
      } catch (err) {
        this.error = err.message || "Login failed";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async signup(email, password, displayName) {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.post("/api/auth/signup", {
          email,
          password,
          display_name: displayName,
        }, { _skipRefresh: true });
        this.user = resp.data.user;
      } catch (err) {
        this.error = err.message || "Signup failed";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      try {
        await apiClient.post("/api/auth/logout");
      } catch {
        // Best effort
      } finally {
        this.user = null;
        // Clear brief selection on logout
        sessionStorage.removeItem("cs_active_brief_id");
        window.location.href = "/login";
      }
    },
  },
});
