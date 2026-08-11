import { defineStore } from "pinia";
import {
  signup as signupApi,
  login as loginApi,
  logout as logoutApi,
  fetchCurrentUser,
} from "@/api/authApi";

function normalizeError(error, fallback = "Something went wrong.") {
  if (error?.error?.message) return error.error.message;
  return error?.message || fallback;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    loading: false,
    error: null,
    checkedSession: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
  },

  actions: {
    async signup({ email, password, displayName }) {
      this.loading = true;
      this.error = null;
      try {
        this.user = await signupApi({ email, password, displayName });
        this.checkedSession = true;
        return this.user;
      } catch (error) {
        this.error = normalizeError(error, "Could not create your account.");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async login({ email, password }) {
      this.loading = true;
      this.error = null;
      try {
        this.user = await loginApi({ email, password });
        this.checkedSession = true;
        return this.user;
      } catch (error) {
        this.error = normalizeError(error, "Invalid email or password.");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      try {
        await logoutApi();
      } finally {
        this.user = null;
        this.checkedSession = true;
      }
    },

    /** Attempt to restore the session from the httpOnly auth cookie. */
    async fetchMe() {
      this.loading = true;
      try {
        this.user = await fetchCurrentUser();
        return this.user;
      } catch {
        this.user = null;
        return null;
      } finally {
        this.loading = false;
        this.checkedSession = true;
      }
    },
  },
});
