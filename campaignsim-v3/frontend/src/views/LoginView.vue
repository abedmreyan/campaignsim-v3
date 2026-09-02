<template>
  <div class="auth-page">
    <div class="auth-page__brand">
      <span>CS</span>
      <strong>CampaignSim</strong>
    </div>

    <AppCard class="auth-card" title="Log in" eyebrow="Welcome back">
      <form class="auth-form" @submit.prevent="handleSubmit">
        <label>
          <span>Email</span>
          <input
            v-model="email"
            type="email"
            autocomplete="email"
            required
            placeholder="you@company.com"
          />
        </label>

        <label>
          <span>Password</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            placeholder="••••••••"
          />
        </label>

        <p v-if="auth.error" class="auth-form__error">{{ auth.error }}</p>

        <AppButton type="submit" block :loading="auth.loading">Log in</AppButton>
      </form>

      <p class="auth-card__footer">
        Don't have an account?
        <RouterLink to="/signup">Sign up</RouterLink>
      </p>
    </AppCard>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/authStore";
import AppCard from "@/components/common/AppCard.vue";
import AppButton from "@/components/common/AppButton.vue";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");

async function handleSubmit() {
  try {
    await auth.login({ email: email.value, password: password.value });
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    router.push(redirect);
  } catch {
    // error message is already surfaced via auth.error
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 2rem;
}

.auth-page__brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.05rem;
}

.auth-page__brand span {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-weight: 700;
  font-size: 0.8rem;
}

.auth-card {
  width: 100%;
  max-width: 400px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  margin-top: 0.5rem;
}

.auth-form label {
  display: block;
}

.auth-form__error {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin: -0.4rem 0 0;
}

.auth-card__footer {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.auth-card__footer a {
  color: var(--color-accent);
}
</style>
