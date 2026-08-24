<template>
  <AppLayout>
    <div class="data-view view-stack stagger-in">
    <PageHeader
      title="Customer Data"
      eyebrow="Audience"
      description="Upload a CRM/order export, confirm the column mapping, then segment your real customer base."
    >
      <template #actions>
        <RouterLink to="/audience/segments" class="app-button app-button--secondary app-button--sm">
          View segments →
        </RouterLink>
      </template>
    </PageHeader>

    <AppCard eyebrow="Upload" title="New dataset">
      <form class="data-view__upload-form" @submit.prevent="handleUpload">
        <label>
          <span>Name</span>
          <input v-model.trim="uploadName" type="text" placeholder="Q3 customer export" />
        </label>
        <label>
          <span>CSV or XLSX file</span>
          <input ref="fileInput" type="file" accept=".csv,.xlsx" required />
        </label>
        <AppButton type="submit" :loading="uploading">Upload</AppButton>
      </form>
      <ErrorState v-if="uploadError" :message="uploadError" />
    </AppCard>

    <AppLoader v-if="loading" label="Loading datasets…" />
    <EmptyState v-else-if="!datasets.length" title="No datasets yet" message="Upload a customer export to get started." />

    <div v-else class="data-view__list">
      <AppCard v-for="dataset in datasets" :key="dataset.id" class="data-view__dataset-card">
        <div class="data-view__dataset-header">
          <div>
            <h3>{{ dataset.name }}</h3>
            <p>{{ dataset.row_count }} rows · {{ dataset.source_type.toUpperCase() }}</p>
          </div>
          <StatusBadge :status="dataset.status" />
        </div>

        <div class="card-actions">
          <AppButton
            v-if="dataset.status === 'uploaded' || dataset.status === 'mapped'"
            variant="secondary"
            size="sm"
            @click="openMapping(dataset)"
          >
            Review mapping
          </AppButton>
          <AppButton
            v-if="dataset.status === 'mapped'"
            size="sm"
            :loading="busyDatasetId === dataset.id"
            @click="runImport(dataset)"
          >
            Import
          </AppButton>
          <AppButton
            v-if="dataset.status === 'imported' || dataset.status === 'segmented'"
            size="sm"
            :loading="busyDatasetId === dataset.id"
            @click="runSegment(dataset)"
          >
            {{ dataset.status === 'segmented' ? 'Re-segment' : 'Segment' }}
          </AppButton>
          <RouterLink
            v-if="dataset.status === 'segmented'"
            :to="{ path: '/audience/segments', query: { dataset_id: dataset.id } }"
            class="app-button app-button--secondary app-button--sm"
          >
            View segments
          </RouterLink>
          <AppButton variant="danger" size="sm" @click="removeDataset(dataset)">Delete</AppButton>
        </div>
        <p v-if="taskMessage[dataset.id]" class="data-view__task-message">{{ taskMessage[dataset.id] }}</p>
      </AppCard>
    </div>

    <!-- Mapping review modal -->
    <div v-if="mappingDataset" class="data-view__modal-overlay" @click.self="mappingDataset = null">
      <AppCard class="data-view__modal" :title="`Column mapping — ${mappingDataset.name}`">
        <AppLoader v-if="mappingLoading" label="Proposing mapping…" />
        <template v-else>
          <div class="data-view__mapping-grid">
            <div v-for="col in mappingColumns" :key="col" class="data-view__mapping-row">
              <span class="data-view__mapping-col">{{ col }}</span>
              <select v-model="mappingDraft[col]">
                <option :value="null">Not mapped (kept as extra)</option>
                <option v-for="(desc, field) in canonicalFields" :key="field" :value="field">
                  {{ field }} — {{ desc }}
                </option>
              </select>
            </div>
          </div>
          <ErrorState v-if="mappingError" :message="mappingError" />
          <div class="card-actions" style="margin-top: 1rem">
            <AppButton :loading="mappingSaving" @click="saveMapping">Confirm mapping</AppButton>
            <AppButton variant="secondary" @click="mappingDataset = null">Cancel</AppButton>
          </div>
        </template>
      </AppCard>
    </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { onMounted, ref } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import AppLoader from "@/components/common/AppLoader.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import {
  deleteDataset,
  getDatasetMapping,
  getTaskStatus,
  importDataset,
  listDatasets,
  segmentDataset,
  updateDatasetMapping,
  uploadDataset,
} from "@/api/dataApi";

const datasets = ref([]);
const loading = ref(false);
const uploading = ref(false);
const uploadError = ref(null);
const uploadName = ref("");
const fileInput = ref(null);
const busyDatasetId = ref(null);
const taskMessage = ref({});

const mappingDataset = ref(null);
const mappingLoading = ref(false);
const mappingSaving = ref(false);
const mappingError = ref(null);
const mappingColumns = ref([]);
const mappingDraft = ref({});
const canonicalFields = ref({});

async function load() {
  loading.value = true;
  try {
    datasets.value = await listDatasets();
  } catch (err) {
    uploadError.value = err?.message || "Could not load datasets.";
  } finally {
    loading.value = false;
  }
}

async function handleUpload() {
  const file = fileInput.value?.files?.[0];
  if (!file) return;
  uploading.value = true;
  uploadError.value = null;
  try {
    const dataset = await uploadDataset(file, uploadName.value);
    datasets.value.unshift(dataset);
    uploadName.value = "";
    if (fileInput.value) fileInput.value.value = "";
  } catch (err) {
    uploadError.value = err?.message || "Upload failed.";
  } finally {
    uploading.value = false;
  }
}

async function removeDataset(dataset) {
  if (!confirm(`Delete "${dataset.name}"? This removes its customers and segments too.`)) return;
  try {
    await deleteDataset(dataset.id);
    datasets.value = datasets.value.filter((d) => d.id !== dataset.id);
  } catch (err) {
    uploadError.value = err?.message || "Could not delete dataset.";
  }
}

async function openMapping(dataset) {
  mappingDataset.value = dataset;
  mappingLoading.value = true;
  mappingError.value = null;
  try {
    const { columns, mapping, canonical_fields } = await getDatasetMapping(dataset.id);
    mappingColumns.value = columns;
    canonicalFields.value = canonical_fields;
    mappingDraft.value = { ...mapping };
  } catch (err) {
    mappingError.value = err?.message || "Could not load mapping.";
  } finally {
    mappingLoading.value = false;
  }
}

async function saveMapping() {
  mappingSaving.value = true;
  mappingError.value = null;
  try {
    const updated = await updateDatasetMapping(mappingDataset.value.id, mappingDraft.value);
    const idx = datasets.value.findIndex((d) => d.id === updated.id);
    if (idx !== -1) datasets.value[idx] = updated;
    mappingDataset.value = null;
  } catch (err) {
    mappingError.value = err?.message || "Could not save mapping.";
  } finally {
    mappingSaving.value = false;
  }
}

async function pollTask(taskId, datasetId, onDone) {
  const MAX_ATTEMPTS = 60;
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    await new Promise((r) => setTimeout(r, 2000));
    const task = await getTaskStatus(taskId);
    taskMessage.value = { ...taskMessage.value, [datasetId]: task.message || task.status };
    if (task.status === "completed") {
      onDone(task.result);
      return;
    }
    if (task.status === "failed") {
      throw new Error(task.error || "Task failed.");
    }
  }
  throw new Error("Task timed out.");
}

async function runImport(dataset) {
  busyDatasetId.value = dataset.id;
  try {
    const { task_id } = await importDataset(dataset.id);
    await pollTask(task_id, dataset.id, async () => {
      const fresh = await listDatasets();
      datasets.value = fresh;
    });
  } catch (err) {
    uploadError.value = err?.message || "Import failed.";
  } finally {
    busyDatasetId.value = null;
    taskMessage.value = { ...taskMessage.value, [dataset.id]: "" };
  }
}

async function runSegment(dataset) {
  busyDatasetId.value = dataset.id;
  try {
    const { task_id } = await segmentDataset(dataset.id);
    await pollTask(task_id, dataset.id, async () => {
      const fresh = await listDatasets();
      datasets.value = fresh;
    });
  } catch (err) {
    uploadError.value = err?.message || "Segmentation failed.";
  } finally {
    busyDatasetId.value = null;
    taskMessage.value = { ...taskMessage.value, [dataset.id]: "" };
  }
}

onMounted(load);
</script>

<style scoped>
.data-view__upload-form {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  flex-wrap: wrap;
}

.data-view__list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.data-view__dataset-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.data-view__task-message {
  margin-top: 0.5rem;
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.data-view__modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--color-overlay-bg, rgba(0, 0, 0, 0.5));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}

.data-view__modal {
  max-width: 40rem;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
}

.data-view__mapping-grid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.data-view__mapping-row {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 0.75rem;
  align-items: center;
}

.data-view__mapping-col {
  font-weight: 600;
  font-size: 0.85rem;
}
</style>
