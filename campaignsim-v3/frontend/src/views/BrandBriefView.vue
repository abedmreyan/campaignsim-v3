<template>
  <div class="briefs-page">
    <header class="briefs-page__topbar">
      <RouterLink to="/" class="briefs-page__brand">
        <span>CS</span>
        <strong>CampaignSim</strong>
      </RouterLink>
      <div class="briefs-page__topbar-actions">
        <RouterLink to="/history" class="briefs-page__nav-link">History</RouterLink>
        <button class="briefs-page__nav-link briefs-page__logout" @click="handleLogout">
          Log out
        </button>
      </div>
    </header>

    <div class="briefs-page__body">
      <PageHeader
        eyebrow="Your workspace"
        title="Brand briefs"
        description="Reusable brand context for your campaigns. Write or paste a brief once, then reuse it across simulations."
      >
        <template #actions>
          <AppButton @click="showCreateForm = !showCreateForm">
            {{ showCreateForm ? "Cancel" : "New brief" }}
          </AppButton>
        </template>
      </PageHeader>

      <AppCard v-if="showCreateForm" class="brief-form-card" title="New brand brief">
        <form class="brief-form" @submit.prevent="handleCreate">
          <label>
            <span>Name</span>
            <input v-model="newName" type="text" required placeholder="e.g. Airbnb Referral 2026" />
          </label>
          <label>
            <span>Business type</span>
            <select v-model="newBusinessType">
              <option value="">Not set</option>
              <option value="b2c_product">B2C product</option>
              <option value="b2b">B2B</option>
              <option value="services">Services</option>
              <option value="local">Local business</option>
              <option value="ecommerce">E-commerce</option>
              <option value="app">App / software</option>
            </select>
          </label>
          <label>
            <span>Brief content</span>
            <textarea
              v-model="newContent"
              rows="8"
              placeholder="Paste or write the brand brief text here — product, audience, channels, goals…"
            ></textarea>
          </label>
          <p v-if="formError" class="brief-form__error">{{ formError }}</p>
          <AppButton type="submit" :loading="creating">Save brief</AppButton>
        </form>
      </AppCard>

      <AppLoader v-if="loading" label="Loading your briefs…" />

      <ErrorState v-else-if="error" title="Couldn't load briefs" :message="error">
        <button @click="loadBriefs">Retry</button>
      </ErrorState>

      <EmptyState
        v-else-if="briefs.length === 0"
        title="No brand briefs yet"
        message="Create your first brief to start building campaigns from it."
      />

      <div v-else class="brief-grid">
        <AppCard v-for="brief in briefs" :key="brief.id" class="brief-card">
          <div class="brief-card__header">
            <h3>{{ brief.name }}</h3>
            <StatusBadge :status="brief.graph_status" :label="brief.graph_status" />
          </div>
          <p class="brief-card__preview">{{ previewText(brief.content) }}</p>
          <div class="brief-card__meta">
            <span>{{ formatDate(brief.created_at) }}</span>
            <span v-if="brief.business_type">· {{ businessTypeLabel(brief.business_type) }}</span>
          </div>
          <div class="brief-card__actions">
            <RouterLink to="/process" class="brief-card__link">Use in workflow →</RouterLink>
            <button class="brief-card__delete" @click="handleDelete(brief)">Delete</button>
          </div>
        </AppCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/authStore";
import PageHeader from "@/components/common/PageHeader.vue";
import AppCard from "@/components/common/AppCard.vue";
import AppButton from "@/components/common/AppButton.vue";
import AppLoader from "@/components/common/AppLoader.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import { listBriefs, createBrief, deleteBrief } from "@/api/briefApi";

const router = useRouter();
const auth = useAuthStore();

async function handleLogout() {
  await auth.logout();
  router.push("/login");
}

const briefs = ref([]);
const loading = ref(false);
const error = ref(null);

const showCreateForm = ref(false);
const newName = ref("");
const newContent = ref("");
const newBusinessType = ref("");
const creating = ref(false);
const formError = ref(null);

async function loadBriefs() {
  loading.value = true;
  error.value = null;
  try {
    briefs.value = await listBriefs();
  } catch (err) {
    error.value = err?.message || "Something went wrong.";
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  formError.value = null;
  creating.value = true;
  try {
    const brief = await createBrief({
      name: newName.value,
      content: newContent.value,
      business_type: newBusinessType.value || undefined,
    });
    briefs.value.unshift(brief);
    newName.value = "";
    newContent.value = "";
    newBusinessType.value = "";
    showCreateForm.value = false;
  } catch (err) {
    formError.value = err?.message || "Could not save this brief.";
  } finally {
    creating.value = false;
  }
}

async function handleDelete(brief) {
  if (!confirm(`Delete "${brief.name}"? This cannot be undone.`)) return;
  try {
    await deleteBrief(brief.id);
    briefs.value = briefs.value.filter((b) => b.id !== brief.id);
  } catch (err) {
    error.value = err?.message || "Could not delete this brief.";
  }
}

function previewText(content) {
  if (!content) return "No content yet.";
  return content.length > 160 ? `${content.slice(0, 160)}…` : content;
}

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

const BUSINESS_TYPE_LABELS = {
  b2c_product: "B2C product",
  b2b: "B2B",
  services: "Services",
  local: "Local business",
  ecommerce: "E-commerce",
  app: "App / software",
};

function businessTypeLabel(value) {
  return BUSINESS_TYPE_LABELS[value] || value;
}

onMounted(loadBriefs);
</script>

<style scoped>
.briefs-page {
  min-height: 100vh;
}

.briefs-page__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 2rem;
  border-bottom: 1px solid var(--color-border);
}

.briefs-page__brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--color-text);
}

.briefs-page__brand span {
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-weight: 700;
  font-size: 0.75rem;
}

.briefs-page__topbar-actions {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.briefs-page__nav-link {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0;
}

.briefs-page__nav-link:hover {
  color: var(--color-text);
}

.briefs-page__body {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1100px;
  margin: 0 auto;
  padding: 2rem;
}

.brief-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 0.5rem;
}

.brief-form__error {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin: 0;
}

.brief-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.brief-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.brief-card__header h3 {
  margin: 0;
  font-size: 1rem;
}

.brief-card__preview {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  line-height: 1.5;
  min-height: 2.6em;
}

.brief-card__meta {
  font-size: 0.75rem;
  color: var(--color-text-subtle);
}

.brief-card__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.brief-card__link {
  color: var(--color-accent);
  font-size: 0.85rem;
}

.brief-card__delete {
  background: none;
  border: none;
  color: var(--color-danger);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0;
}
</style>
