<template>
  <div class="dynamic-island" ref="rootRef" :class="{ 'is-open': isOpen }">
    <button
      class="dynamic-island__pill"
      type="button"
      :aria-expanded="isOpen"
      aria-haspopup="true"
      @click="toggle"
    >
      <span class="dynamic-island__avatar">{{ activeInitial }}</span>
      <span class="dynamic-island__name">{{ activeName }}</span>
      <span
        class="dynamic-island__status-dot"
        :data-status="activeStatus"
        aria-hidden="true"
      />
      <svg
        class="dynamic-island__chevron"
        :class="{ 'is-open': isOpen }"
        width="10"
        height="10"
        viewBox="0 0 10 10"
        fill="none"
        aria-hidden="true"
      >
        <path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <Transition name="island-expand">
      <div v-if="isOpen" class="dynamic-island__panel" role="menu">
        <div v-if="workspaceStore.briefs.length > 6" class="dynamic-island__search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="query"
            type="text"
            placeholder="Search businesses…"
            class="dynamic-island__search-input"
          />
        </div>

        <div class="dynamic-island__list">
          <p v-if="workspaceStore.briefsLoading && !workspaceStore.briefs.length" class="dynamic-island__empty">
            Loading your businesses…
          </p>
          <p v-else-if="!filteredBriefs.length" class="dynamic-island__empty">
            {{ workspaceStore.briefs.length ? `No businesses match “${query}”.` : "No businesses yet." }}
          </p>

          <button
            v-for="brief in filteredBriefs"
            :key="brief.id"
            type="button"
            class="dynamic-island__row"
            :class="{ 'is-active': brief.id === workspaceStore.activeBriefId }"
            :disabled="workspaceStore.switching"
            role="menuitem"
            @click="select(brief)"
          >
            <span class="dynamic-island__row-avatar">{{ initialFor(brief) }}</span>
            <span class="dynamic-island__row-body">
              <span class="dynamic-island__row-name">{{ brief.name }}</span>
              <span class="dynamic-island__row-meta">
                <span v-if="brief.business_type">{{ businessTypeLabel(brief.business_type) }}</span>
                <span class="dynamic-island__row-updated">{{ relativeTime(brief.updated_at) }}</span>
              </span>
            </span>
            <span v-if="workspaceStore.switchingBriefId === brief.id" class="dynamic-island__row-spinner" aria-hidden="true" />
            <StatusBadge v-else :status="brief.graph_status" />
          </button>
        </div>

        <div class="dynamic-island__divider" aria-hidden="true" />

        <button
          v-if="!showCreateForm"
          type="button"
          class="dynamic-island__new"
          @click="showCreateForm = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New business
        </button>

        <form v-else class="dynamic-island__create-form" @submit.prevent="handleCreate">
          <input
            v-model.trim="name"
            type="text"
            required
            autofocus
            placeholder="Business name"
            class="dynamic-island__create-input"
          />
          <select v-model="businessType" class="dynamic-island__create-input">
            <option v-for="opt in BUSINESS_TYPE_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <textarea
            v-model="content"
            rows="3"
            placeholder="Paste a short brief (optional — you can add this later)"
            class="dynamic-island__create-input dynamic-island__create-textarea"
          />
          <p v-if="error" class="dynamic-island__create-error">{{ error }}</p>
          <div class="dynamic-island__create-actions">
            <button type="submit" class="dynamic-island__create-submit" :disabled="creating">
              {{ creating ? "Creating…" : "Create & switch" }}
            </button>
            <button type="button" class="dynamic-island__create-cancel" @click="cancelCreate">Cancel</button>
          </div>
        </form>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { useCampaignStore } from "@/stores/campaignStore";
import { useBriefCreate, BUSINESS_TYPE_OPTIONS, businessTypeLabel } from "@/composables/useBriefCreate";

const workspaceStore = useWorkspaceStore();
const campaignStore = useCampaignStore();

const rootRef = ref(null);
const isOpen = ref(false);
const query = ref("");
const showCreateForm = ref(false);

const { name, content, businessType, creating, error, submit, reset } = useBriefCreate({
  onCreated: (brief) => workspaceStore.upsertBrief(brief),
});

const activeBrief = computed(() => workspaceStore.activeBrief);
const activeName = computed(() => activeBrief.value?.name || "Select a business");
const activeStatus = computed(() => activeBrief.value?.graph_status || "pending");
const activeInitial = computed(() => (activeBrief.value?.name || "?").charAt(0).toUpperCase());

const filteredBriefs = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return workspaceStore.briefs;
  return workspaceStore.briefs.filter((b) => b.name?.toLowerCase().includes(q));
});

function initialFor(brief) {
  return (brief.name || "?").charAt(0).toUpperCase();
}

function relativeTime(iso) {
  if (!iso) return "";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function toggle() {
  if (isOpen.value) close();
  else open();
}

function open() {
  isOpen.value = true;
  workspaceStore.loadBriefs();
}

function close() {
  isOpen.value = false;
  showCreateForm.value = false;
  query.value = "";
  reset();
}

function cancelCreate() {
  showCreateForm.value = false;
  reset();
}

async function select(brief) {
  if (workspaceStore.switching) return;
  if (brief.id === workspaceStore.activeBriefId) {
    close();
    return;
  }
  try {
    await workspaceStore.switchTo(brief.id);
  } catch (err) {
    campaignStore.setNotice(err?.message || "Could not switch businesses.");
  } finally {
    close();
  }
}

async function handleCreate() {
  try {
    const brief = await submit();
    showCreateForm.value = false;
    await workspaceStore.switchTo(brief.id);
    close();
  } catch {
    // Error already surfaced inline via the composable's `error` ref.
  }
}

function handleClickOutside(event) {
  if (rootRef.value && !rootRef.value.contains(event.target)) close();
}

function handleKeydown(event) {
  if (event.key === "Escape" && isOpen.value) close();
}

onMounted(() => {
  document.addEventListener("mousedown", handleClickOutside);
  document.addEventListener("keydown", handleKeydown);
  workspaceStore.loadBriefs();
});

onUnmounted(() => {
  document.removeEventListener("mousedown", handleClickOutside);
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.dynamic-island {
  position: fixed;
  top: 0.85rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 500;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.dynamic-island__pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  height: 2.35rem;
  padding: 0.3rem 0.85rem 0.3rem 0.3rem;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-full);
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur)) saturate(1.4);
  box-shadow: var(--shadow-md), var(--glass-highlight);
  color: var(--color-text);
  cursor: pointer;
  max-width: min(280px, 60vw);
  transition:
    border-color var(--transition-base),
    box-shadow var(--transition-base),
    transform var(--transition-base);
}

.dynamic-island__pill:hover {
  border-color: var(--glass-border-glow);
  box-shadow: var(--shadow-md), var(--glow-teal);
}

.dynamic-island.is-open .dynamic-island__pill {
  border-color: var(--glass-border-glow);
  box-shadow: var(--shadow-lg), var(--glow-teal);
}

.dynamic-island__avatar {
  display: inline-grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  background: var(--gradient-accent);
  color: #fff;
  font-weight: 800;
  font-size: 0.75rem;
  font-family: var(--font-display);
  flex-shrink: 0;
}

.dynamic-island__name {
  font-size: 0.8125rem;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.dynamic-island__status-dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: var(--color-text-ghost);
  flex-shrink: 0;
}

.dynamic-island__status-dot[data-status="ready"] {
  background: var(--color-success);
  box-shadow: 0 0 6px rgba(0, 201, 122, 0.6);
}

.dynamic-island__status-dot[data-status="building"],
.dynamic-island__status-dot[data-status="pending"] {
  background: var(--color-accent);
  box-shadow: 0 0 6px rgba(10, 191, 173, 0.6);
  animation: demoDotPulse 2.4s ease-in-out infinite;
}

.dynamic-island__status-dot[data-status="failed"] {
  background: var(--color-danger, #f03e3e);
}

.dynamic-island__chevron {
  color: var(--color-text-subtle);
  transition: transform var(--transition-fast);
  flex-shrink: 0;
}

.dynamic-island__chevron.is-open {
  transform: rotate(180deg);
}

/* ── Expanded panel ────────────────────────────────────────────────────── */
.dynamic-island__panel {
  margin-top: 0.5rem;
  width: min(340px, 88vw);
  max-height: min(28rem, 70vh);
  display: flex;
  flex-direction: column;
  border: 1px solid var(--glass-border-glow);
  border-radius: var(--radius-lg);
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur)) saturate(1.4);
  box-shadow: var(--shadow-lg), var(--glow-teal);
  padding: 0.6rem;
  overflow: hidden;
}

.dynamic-island__search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  margin-bottom: 0.4rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-input-bg);
  color: var(--color-text-subtle);
  flex-shrink: 0;
}

.dynamic-island__search-input {
  border: none;
  background: transparent;
  padding: 0;
  width: 100%;
}

.dynamic-island__search-input:focus {
  box-shadow: none;
}

.dynamic-island__list {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-height: 2rem;
}

.dynamic-island__empty {
  padding: 0.75rem 0.5rem;
  color: var(--color-text-subtle);
  font-size: 0.8125rem;
  text-align: center;
  margin: 0;
}

.dynamic-island__row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.5rem 0.5rem;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}

.dynamic-island__row:hover:not(:disabled) {
  background: var(--color-surface-muted);
}

.dynamic-island__row.is-active {
  background: var(--color-accent-soft);
}

.dynamic-island__row:disabled {
  cursor: default;
  opacity: 0.6;
}

.dynamic-island__row-avatar {
  display: inline-grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
  font-weight: 800;
  font-size: 0.7rem;
  font-family: var(--font-display);
  flex-shrink: 0;
}

.dynamic-island__row.is-active .dynamic-island__row-avatar {
  background: var(--gradient-accent);
  color: #fff;
}

.dynamic-island__row-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.dynamic-island__row-name {
  font-size: 0.8125rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dynamic-island__row-meta {
  display: flex;
  gap: 0.4rem;
  font-size: 0.7rem;
  color: var(--color-text-subtle);
}

.dynamic-island__row-updated::before {
  content: "·";
  margin-right: 0.4rem;
}

.dynamic-island__row-spinner {
  width: 0.9rem;
  height: 0.9rem;
  border: 2px solid var(--color-accent);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.dynamic-island__divider {
  height: 1px;
  background: var(--color-border);
  margin: 0.4rem 0.2rem;
  flex-shrink: 0;
}

.dynamic-island__new {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.55rem 0.6rem;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s, background 0.12s;
  flex-shrink: 0;
}

.dynamic-island__new:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: var(--color-accent-soft);
}

.dynamic-island__create-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-shrink: 0;
}

.dynamic-island__create-input {
  font-size: 0.8125rem;
}

.dynamic-island__create-textarea {
  resize: vertical;
  font-family: inherit;
}

.dynamic-island__create-error {
  color: var(--color-danger, #f03e3e);
  font-size: 0.75rem;
  margin: 0;
}

.dynamic-island__create-actions {
  display: flex;
  gap: 0.5rem;
}

.dynamic-island__create-submit {
  flex: 1;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--gradient-accent);
  color: #fff;
  font-weight: 700;
  font-size: 0.8125rem;
  padding: 0.55rem 0.75rem;
  box-shadow: var(--glow-accent-sm);
  cursor: pointer;
}

.dynamic-island__create-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dynamic-island__create-cancel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.55rem 0.75rem;
  cursor: pointer;
}

/* ── Expand transition ────────────────────────────────────────────────── */
.island-expand-enter-active,
.island-expand-leave-active {
  transition: opacity var(--transition-base), transform var(--transition-base);
  transform-origin: top center;
}

.island-expand-enter-from,
.island-expand-leave-to {
  opacity: 0;
  transform: scale(0.94) translateY(-6px);
}

@media (max-width: 680px) {
  .dynamic-island__name {
    max-width: 8rem;
  }
}

@media (max-width: 480px) {
  .dynamic-island {
    top: 0.6rem;
  }
  .dynamic-island__name {
    display: none;
  }
  .dynamic-island__pill {
    padding: 0.3rem;
    gap: 0.35rem;
  }
}
</style>
