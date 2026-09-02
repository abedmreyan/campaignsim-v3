import { apiClient } from "./client";

// Auth responses are { success, user } / { success, error } — not the
// generic { success, data } envelope used by the rest of the API, per the
// auth spec (docs/superpowers/specs/2026-06-19-...). Cookies are httpOnly;
// the backend sets/clears them on every call, nothing to store here.

export async function signup({ email, password, displayName }) {
  const res = await apiClient.post("/api/auth/signup", {
    email,
    password,
    display_name: displayName,
  });
  return res.data.user;
}

export async function login({ email, password }) {
  const res = await apiClient.post("/api/auth/login", { email, password });
  return res.data.user;
}

export async function logout() {
  await apiClient.post("/api/auth/logout");
}

export async function fetchCurrentUser() {
  const res = await apiClient.get("/api/auth/me");
  return res.data.user;
}
