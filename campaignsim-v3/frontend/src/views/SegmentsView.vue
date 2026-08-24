<template>
  <AppLayout>
    <div class="segments-view view-stack stagger-in">
    <PageHeader
      title="Customer Segments"
      eyebrow="Audience"
      description="Review, rename, merge, and approve segments before using them to ground personas."
    >
      <template #actions>
        <RouterLink to="/audience/data" class="app-button app-button--secondary app-button--sm">
          ← Datasets
        </RouterLink>
      </template>
    </PageHeader>

    <div v-if="selectedIds.length >= 2" class="segments-view__merge-bar">
      <span>{{ selectedIds.length }} segments selected</span>
      <AppButton size="sm" :loading="merging" @click="handleMerge">Merge selected</AppButton>
      <AppButton size="sm" variant="secondary" @click="selectedIds = []">Clear</AppButton>
    </div>

    <AppLoader v-if="loading" label="Loading segments…" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState
      v-else-if="!segments.length"
      title="No segments yet"
      message="Upload and segment a customer dataset first."
    />

    <div v-else class="segments-view__grid">
      <AppCard v-for="segment in segments" :key="segment.id" class="segments-view__card">
        <label class="segments-view__select">
          <input type="checkbox" :value="segment.id" v-model="selectedIds" />
        </label>
        <div class="segments-view__header">
          <div v-if="editingId !== segment.id">
            <h3>{{ segment.name }}</h3>
            <p>{{ segment.size }} customers</p>
          </div>
          <div v-else class="segments-view__edit-form">
            <input v-model="editDraft.name" type="text" />
            <textarea v-model="editDraft.description" rows="2"></textarea>
          </div>
          <StatusBadge :status="segment.status" />
        </div>

        <p v-if="editingId !== segment.id" class="segments-view__description">{{ segment.description }}</p>

        <dl class="segments-view__stats">
          <template v-for="[label, value] in statEntries(segment.stats)" :key="label">
            <dt>{{ label }}</dt>
            <dd>{{ value }}</dd>
          </template>
        </dl>

        <div class="card-actions">
          <template v-if="editingId === segment.id">
            <AppButton size="sm" :loading="saving" @click="saveEdit(segment)">Save</AppButton>
            <AppButton size="sm" variant="secondary" @click="editingId = null">Cancel</AppButton>
          </template>
          <template v-else>
            <AppButton size="sm" variant="secondary" @click="startEdit(segment)">Rename</AppButton>
            <AppButton
              v-if="segment.status === 'draft'"
              size="sm"
              @click="approve(segment)"
            >
              Approve
            </AppButton>
            <a :href="exportUrl(segment.id)" target="_blank" rel="noopener" class="app-button app-button--secondary app-button--sm">
              Export CSV
            </a>
          </template>
        </div>
      </AppCard>
    </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppLayout from "@/layouts/AppLayout.vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import AppLoader from "@/components/common/AppLoader.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import { listSegments, mergeSegments, segmentExportUrl, updateSegment } from "@/api/dataApi";

const route = useRoute();
const segments = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedIds = ref([]);
const editingId = ref(null);
const editDraft = ref({ name: "", description: "" });
const saving = ref(false);
const merging = ref(false);

function statEntries(stats) {
  if (!stats) return [];
  const labels = {
    avg_ltv: "Avg LTV", avg_age: "Avg age", avg_order_count: "Avg orders",
    avg_aov: "Avg order value", avg_email_open_rate: "Avg email open rate",
  };
  return Object.entries(labels)
    .filter(([key]) => stats[key] !== undefined && stats[key] !== null)
    .map(([key, label]) => [label, stats[key]]);
}

function exportUrl(segmentId) {
  return segmentExportUrl(segmentId);
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    segments.value = await listSegments(route.query.dataset_id);
  } catch (err) {
    error.value = err?.message || "Could not load segments.";
  } finally {
    loading.value = false;
  }
}

function startEdit(segment) {
  editingId.value = segment.id;
  editDraft.value = { name: segment.name, description: segment.description || "" };
}

async function saveEdit(segment) {
  saving.value = true;
  try {
    const updated = await updateSegment(segment.id, editDraft.value);
    const idx = segments.value.findIndex((s) => s.id === segment.id);
    if (idx !== -1) segments.value[idx] = updated;
    editingId.value = null;
  } catch (err) {
    error.value = err?.message || "Could not save segment.";
  } finally {
    saving.value = false;
  }
}

async function approve(segment) {
  try {
    const updated = await updateSegment(segment.id, { status: "approved" });
    const idx = segments.value.findIndex((s) => s.id === segment.id);
    if (idx !== -1) segments.value[idx] = updated;
  } catch (err) {
    error.value = err?.message || "Could not approve segment.";
  }
}

async function handleMerge() {
  merging.value = true;
  try {
    const merged = await mergeSegments(selectedIds.value);
    segments.value = segments.value.filter((s) => !selectedIds.value.includes(s.id));
    segments.value.unshift(merged);
    selectedIds.value = [];
  } catch (err) {
    error.value = err?.message || "Could not merge segments.";
  } finally {
    merging.value = false;
  }
}

watch(() => route.query.dataset_id, load);
onMounted(load);
</script>

<style scoped>
.segments-view__merge-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  border-radius: var(--radius-md);
  background: var(--color-accent-soft);
  margin-bottom: 1rem;
}

.segments-view__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
  gap: 1rem;
}

.segments-view__card {
  position: relative;
}

.segments-view__select {
  position: absolute;
  top: 1rem;
  right: 1rem;
}

.segments-view__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  padding-right: 1.5rem;
}

.segments-view__edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex: 1;
}

.segments-view__description {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0.5rem 0;
}

.segments-view__stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.3rem 0.75rem;
  font-size: 0.8rem;
  margin: 0.75rem 0;
}

.segments-view__stats dt {
  color: var(--color-text-subtle);
}

.segments-view__stats dd {
  font-weight: 600;
}
</style>
