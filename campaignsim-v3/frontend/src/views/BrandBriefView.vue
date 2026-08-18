<template>
  <AppLayout>
    <div class="view-stack stagger-in">
      <PageHeader
        title="Brand Briefs"
        eyebrow="Your workspace"
        description="Select a brief to launch a campaign, or create a new one."
      >
        <template #actions>
          <AppButton @click="showCreate = !showCreate">
            {{ showCreate ? "Cancel" : "New brief" }}
          </AppButton>
        </template>
      </PageHeader>

      <!-- Create form -->
      <Transition name="brief-form">
        <AppCard v-if="showCreate" class="brief-create-card">
          <form @submit.prevent="createBrief" class="brief-create-form">
            <div class="brief-create-form__row">
              <label class="brief-create-form__field">
                <span class="brief-create-form__label">Brief name</span>
                <input
                  v-model.trim="newName"
                  type="text"
                  required
                  placeholder="e.g. Airbnb Summer 2026"
                  class="brief-create-form__input"
                  autofocus
                />
              </label>
            </div>

            <label class="brief-create-form__field">
              <span class="brief-create-form__label">Business type <span class="brief-create-form__hint">(optional)</span></span>
              <select v-model="newBusinessType" class="brief-create-form__input">
                <option value="">Not set</option>
                <option value="b2c_product">B2C product</option>
                <option value="b2b">B2B</option>
                <option value="services">Services</option>
                <option value="local">Local business</option>
                <option value="ecommerce">E-commerce</option>
                <option value="app">App / software</option>
              </select>
            </label>

            <!-- Source toggle -->
            <div class="brief-create-form__source-tabs">
              <button
                type="button"
                class="brief-create-form__tab"
                :class="{ 'is-active': contentMode === 'text' }"
                @click="contentMode = 'text'"
              >Type content</button>
              <button
                type="button"
                class="brief-create-form__tab"
                :class="{ 'is-active': contentMode === 'upload' }"
                @click="contentMode = 'upload'"
              >Upload file</button>
            </div>

            <label v-if="contentMode === 'text'" class="brief-create-form__field">
              <span class="brief-create-form__label">Content</span>
              <textarea
                v-model="newContent"
                rows="7"
                placeholder="Paste or type your brand brief here…"
                class="brief-create-form__textarea"
              />
            </label>

            <div v-else class="brief-create-form__field">
              <span class="brief-create-form__label">File <span class="brief-create-form__hint">(PDF, Markdown, or TXT)</span></span>
              <label
                class="brief-upload-zone"
                :class="{ 'has-file': uploadFile }"
                @dragover.prevent
                @drop.prevent="onFileDrop"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".txt,.pdf,.md,.markdown"
                  class="brief-upload-zone__input"
                  @change="onFileChange"
                />
                <svg v-if="!uploadFile" class="brief-upload-zone__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span v-if="!uploadFile" class="brief-upload-zone__text">
                  Drag & drop or <span class="brief-upload-zone__browse">browse</span>
                </span>
                <span v-else class="brief-upload-zone__filename">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  {{ uploadFile.name }}
                  <button type="button" class="brief-upload-zone__clear" @click.prevent="uploadFile = null">✕</button>
                </span>
              </label>
            </div>

            <p v-if="formError" class="brief-form__error">{{ formError }}</p>

            <div class="brief-create-form__actions">
              <AppButton type="submit" :disabled="creating">
                {{ creating ? (uploading ? "Uploading…" : "Creating…") : "Create brief" }}
              </AppButton>
              <AppButton variant="secondary" @click="showCreate = false">Cancel</AppButton>
            </div>
          </form>
        </AppCard>
      </Transition>

      <!-- Loading skeletons -->
      <div v-if="loading" class="brief-grid">
        <div v-for="n in 3" :key="n" class="skeleton-card">
          <SkeletonBlock variant="title" />
          <SkeletonBlock width="80%" />
          <SkeletonBlock width="55%" />
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="briefs.length === 0 && !showCreate" class="brief-empty">
        <div class="brief-empty__orb" aria-hidden="true" />
        <svg class="brief-empty__icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <rect x="8" y="6" width="32" height="36" rx="4" stroke="currentColor" stroke-width="1.8"/>
          <path d="M16 16h16M16 22h16M16 28h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          <circle cx="36" cy="36" r="8" fill="var(--color-bg)" stroke="currentColor" stroke-width="1.8"/>
          <path d="M36 32v4l2 2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <h3 class="brief-empty__title">No briefs yet</h3>
        <p class="brief-empty__msg">Create your first brand brief to start building a simulation.</p>
        <AppButton @click="showCreate = true">Create your first brief</AppButton>
      </div>

      <!-- Brief grid -->
      <div v-else class="brief-grid">
        <div
          v-for="brief in briefs"
          :key="brief.id"
          class="brief-card"
          :class="{ 'is-active': campaignStore.brandBriefId === brief.id }"
          role="button"
          tabindex="0"
          @click="selectBrief(brief)"
          @keydown.enter="selectBrief(brief)"
        >
          <!-- Active selection indicator -->
          <span v-if="campaignStore.brandBriefId === brief.id" class="brief-card__active-bar" aria-hidden="true" />

          <div class="brief-card__top">
            <div class="brief-card__meta">
              <StatusBadge :status="brief.graph_status" />
            </div>
            <!-- Hover actions -->
            <div class="brief-card__hover-actions" @click.stop>
              <button class="brief-card__action-btn" title="Edit brief" @click="startEdit(brief)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button class="brief-card__action-btn brief-card__action-btn--danger" title="Delete brief" @click="deleteBrief(brief.id)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                  <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                </svg>
              </button>
            </div>
          </div>

          <h3 class="brief-card__name">{{ brief.name }}</h3>
          <p class="brief-card__preview">{{ brief.content?.slice(0, 120) || "No content yet." }}</p>
          <p v-if="brief.business_type" class="brief-card__business-type">{{ businessTypeLabel(brief.business_type) }}</p>

          <div class="brief-card__footer">
            <span class="brief-card__launch">
              Open brief
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </span>
          </div>

          <!-- Glow layer for active/hover state -->
          <div class="brief-card__glow" aria-hidden="true" />
        </div>
      </div>

      <!-- Edit drawer -->
      <DrawerPanel :open="!!editingBrief" @close="editingBrief = null" title="Edit brief">
        <form v-if="editingBrief" @submit.prevent="saveEdit" class="brief-edit-form">
          <label class="brief-create-form__field">
            <span class="brief-create-form__label">Name</span>
            <input v-model.trim="editName" type="text" required class="brief-create-form__input" />
          </label>
          <label class="brief-create-form__field">
            <span class="brief-create-form__label">Business type</span>
            <select v-model="editBusinessType" class="brief-create-form__input">
              <option value="">Not set</option>
              <option value="b2c_product">B2C product</option>
              <option value="b2b">B2B</option>
              <option value="services">Services</option>
              <option value="local">Local business</option>
              <option value="ecommerce">E-commerce</option>
              <option value="app">App / software</option>
            </select>
          </label>
          <label class="brief-create-form__field">
            <span class="brief-create-form__label">Content</span>
            <textarea v-model="editContent" rows="14" class="brief-create-form__textarea" />
          </label>
          <AppButton type="submit" :disabled="saving">{{ saving ? "Saving…" : "Save changes" }}</AppButton>
        </form>
      </DrawerPanel>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { apiClient } from "@/api/client.js";
import { useCampaignStore } from "@/stores/campaignStore";
import AppLayout from "@/layouts/AppLayout.vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import DrawerPanel from "@/components/common/DrawerPanel.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";

const router = useRouter();
const campaignStore = useCampaignStore();

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

const briefs = ref([]);
const loading = ref(true);
const showCreate = ref(false);
const creating = ref(false);
const uploading = ref(false);
const formError = ref(null);
const newName = ref("");
const newContent = ref("");
const newBusinessType = ref("");
const contentMode = ref("text"); // "text" | "upload"
const uploadFile = ref(null);
const fileInput = ref(null);

const editingBrief = ref(null);
const editName = ref("");
const editContent = ref("");
const editBusinessType = ref("");
const saving = ref(false);

function onFileChange(e) {
  uploadFile.value = e.target.files?.[0] || null;
}

function onFileDrop(e) {
  const file = e.dataTransfer.files?.[0];
  if (file) {
    uploadFile.value = file;
  }
}

async function loadBriefs() {
  loading.value = true;
  try {
    const resp = await apiClient.get("/api/briefs");
    briefs.value = resp.data.data;
  } finally {
    loading.value = false;
  }
}

async function createBrief() {
  formError.value = null;
  creating.value = true;
  try {
    // Step 1: create the brief record
    const resp = await apiClient.post("/api/briefs", {
      name: newName.value,
      content: contentMode.value === "text" ? newContent.value : "",
      business_type: newBusinessType.value || undefined,
    });
    let brief = resp.data.data;

    // Step 2: if a file was selected, upload it to populate content
    if (contentMode.value === "upload" && uploadFile.value) {
      uploading.value = true;
      const formData = new FormData();
      formData.append("file", uploadFile.value);
      const uploadResp = await apiClient.post(
        `/api/briefs/${brief.id}/upload`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      brief = uploadResp.data.data;
      uploading.value = false;
    }

    briefs.value.unshift(brief);
    showCreate.value = false;
    newName.value = "";
    newContent.value = "";
    newBusinessType.value = "";
    uploadFile.value = null;
    contentMode.value = "text";
  } catch (err) {
    formError.value = err?.message || "Could not save this brief.";
  } finally {
    creating.value = false;
    uploading.value = false;
  }
}

function selectBrief(brief) {
  campaignStore.selectBrief(brief.id);
  router.push("/process");
}

function startEdit(brief) {
  editingBrief.value = brief;
  editName.value = brief.name;
  editContent.value = brief.content || "";
  editBusinessType.value = brief.business_type || "";
}

async function saveEdit() {
  if (!editingBrief.value) return;
  saving.value = true;
  try {
    const resp = await apiClient.put(`/api/briefs/${editingBrief.value.id}`, {
      name: editName.value,
      content: editContent.value,
      business_type: editBusinessType.value || null,
    });
    const idx = briefs.value.findIndex((b) => b.id === editingBrief.value.id);
    if (idx !== -1) briefs.value[idx] = resp.data.data;
    editingBrief.value = null;
  } finally {
    saving.value = false;
  }
}

async function deleteBrief(id) {
  if (!confirm("Delete this brief and all its simulations?")) return;
  await apiClient.delete(`/api/briefs/${id}`);
  briefs.value = briefs.value.filter((b) => b.id !== id);
  if (campaignStore.brandBriefId === id) campaignStore.clearBrief();
}

onMounted(loadBriefs);
</script>

<style scoped>
/* ── Grid layout ─────────────────────────────────────────────────────── */
.brief-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

/* ── Brief cards ─────────────────────────────────────────────────────── */
.brief-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg, 0.75rem);
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.18s;
  outline: none;
}

.brief-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: 0 4px 24px rgba(0,0,0,0.22);
  transform: translateY(-2px);
}

.brief-card:hover .brief-card__glow {
  opacity: 1;
}

.brief-card:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.brief-card.is-active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 1px var(--color-accent), 0 4px 28px rgba(10,191,173,0.14);
}

.brief-card__active-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-accent);
  border-radius: 2px 2px 0 0;
}

/* top row: badge + hover actions */
.brief-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

/* hover action buttons — invisible until card is hovered */
.brief-card__hover-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.15s;
}

.brief-card:hover .brief-card__hover-actions {
  opacity: 1;
}

.brief-card__action-btn {
  display: inline-grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: var(--radius-sm, 0.375rem);
  border: 1px solid var(--color-border);
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s, background 0.12s;
}

.brief-card__action-btn:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text);
  background: var(--color-bg);
}

.brief-card__action-btn--danger:hover {
  border-color: rgba(248,113,113,0.5);
  color: var(--color-danger, #ef4444);
  background: var(--color-danger-soft);
}

.brief-card__name {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--color-text);
}

.brief-card__preview {
  flex: 1;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.brief-card__business-type {
  font-size: 0.75rem;
  color: var(--color-text-subtle);
  margin: 0;
}

.brief-card__footer {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
}

.brief-card__launch {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-subtle);
  transition: color 0.15s;
}

.brief-card:hover .brief-card__launch {
  color: var(--color-accent);
}

/* subtle ambient glow on hover */
.brief-card__glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 60% 50% at 50% 0%, rgba(10,191,173,0.07) 0%, transparent 70%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.brief-card.is-active .brief-card__glow {
  opacity: 1;
}

/* ── Empty state ─────────────────────────────────────────────────────── */
.brief-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  text-align: center;
  position: relative;
}

.brief-empty__orb {
  position: absolute;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(10,191,173,0.07) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.brief-empty__icon {
  width: 3rem;
  height: 3rem;
  color: var(--color-text-subtle);
  margin-bottom: 0.25rem;
  position: relative;
}

.brief-empty__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.brief-empty__msg {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  margin: 0 0 0.5rem;
  max-width: 28rem;
}

/* ── Create form ─────────────────────────────────────────────────────── */
.brief-create-card {
  margin-bottom: 0.25rem;
}

.brief-create-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.brief-create-form__row {
  display: grid;
  grid-template-columns: 1fr;
}

.brief-create-form__field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.brief-create-form__label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

.brief-create-form__input,
.brief-create-form__textarea {
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 0.5rem);
  background: var(--color-bg);
  color: var(--color-text);
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
  resize: vertical;
}

.brief-create-form__input:focus,
.brief-create-form__textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(10,191,173,0.12);
  outline: none;
}

.brief-create-form__textarea {
  font-family: inherit;
  line-height: 1.6;
}

.brief-create-form__actions {
  display: flex;
  gap: 0.75rem;
}

.brief-form__error {
  color: var(--color-danger, #ef4444);
  font-size: 0.85rem;
  margin: 0;
}

/* ── Source tabs (Type / Upload) ─────────────────────────────────────── */
.brief-create-form__source-tabs {
  display: flex;
  gap: 0.25rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.2rem;
  width: fit-content;
}

.brief-create-form__tab {
  padding: 0.3rem 0.875rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: calc(var(--radius-sm) - 2px);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.brief-create-form__tab.is-active {
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}

.brief-create-form__hint {
  font-weight: 400;
  color: var(--color-text-subtle);
}

/* ── Upload drop zone ────────────────────────────────────────────────── */
.brief-upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 8rem;
  border: 1.5px dashed var(--color-border);
  border-radius: var(--radius-md, 0.625rem);
  background: var(--color-bg);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  position: relative;
}

.brief-upload-zone:hover,
.brief-upload-zone.has-file {
  border-color: var(--color-accent);
  background: rgba(10,191,173,0.03);
}

.brief-upload-zone__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}

.brief-upload-zone__icon {
  width: 2rem;
  height: 2rem;
  color: var(--color-text-subtle);
}

.brief-upload-zone__text {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.brief-upload-zone__browse {
  color: var(--color-accent);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.brief-upload-zone__filename {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.brief-upload-zone__clear {
  display: inline-grid;
  place-items: center;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  border: none;
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
  font-size: 0.625rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.brief-upload-zone__clear:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger, #ef4444);
}

/* ── Edit drawer form ────────────────────────────────────────────────── */
.brief-edit-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

/* ── Create form enter/leave transition ──────────────────────────────── */
.brief-form-enter-active,
.brief-form-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.brief-form-enter-from,
.brief-form-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
