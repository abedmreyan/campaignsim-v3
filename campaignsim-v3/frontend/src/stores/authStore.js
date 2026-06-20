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
        const resp = await apiClient.get("/api/auth/me");
        this.user = resp.data;
      } catch {
        this.user = null;
      } finally {
        this.loading = false;
      }
    },

    async login(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.post("/api/auth/login", { email, password });
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
        });
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
