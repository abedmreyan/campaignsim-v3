<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">CampaignSim</h1>
      <p class="auth-subtitle">Create your account</p>

      <form @submit.prevent="submit" class="auth-form">
        <label>
          Display name
          <input v-model.trim="displayName" type="text" autocomplete="name" placeholder="Your name" />
        </label>
        <label>
          Email
          <input v-model.trim="email" type="email" autocomplete="email" required placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input v-model="password" type="password" autocomplete="new-password" required placeholder="8+ characters" />
        </label>

        <p v-if="auth.error" class="auth-error">{{ auth.error }}</p>

        <button type="submit" :disabled="auth.loading" class="auth-submit">
          {{ auth.loading ? "Creating account…" : "Create account" }}
        </button>
      </form>

      <p class="auth-switch">
        Already have an account? <RouterLink to="/login">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const email = ref("");
const password = ref("");
const displayName = ref("");

async function submit() {
  try {
    await auth.signup(email.value, password.value, displayName.value);
    const rawRedirect = route.query.redirect;
    const redirect = (rawRedirect && typeof rawRedirect === "string" && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//"))
      ? rawRedirect
      : "/process";
    router.push(redirect);
  } catch {
    // error is set on auth.error
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}
.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem 2rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
}
.auth-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; }
.auth-subtitle { color: var(--color-text-muted); margin-bottom: 2rem; }
.auth-form { display: flex; flex-direction: column; gap: 1rem; }
.auth-form label { display: flex; flex-direction: column; gap: 0.375rem; font-size: 0.875rem; font-weight: 500; }
.auth-form input { padding: 0.625rem 0.875rem; border: 1px solid var(--color-border); border-radius: 0.5rem; background: var(--color-bg); color: var(--color-text); font-size: 0.9375rem; }
.auth-error { color: var(--color-danger, #ef4444); font-size: 0.875rem; margin: 0; }
.auth-submit { margin-top: 0.5rem; padding: 0.75rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-switch { text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--color-text-muted); }
</style>
