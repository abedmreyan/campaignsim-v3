<template>
  <div class="view-stack stagger-in">
    <PageHeader
      title="Brand Briefs"
      eyebrow="Your workspace"
      description="Select a brand brief to start a campaign, or create a new one."
    >
      <template #actions>
        <AppButton @click="showCreate = true">New brief</AppButton>
      </template>
    </PageHeader>

    <!-- Create form -->
    <AppCard v-if="showCreate">
      <form @submit.prevent="createBrief" style="display: flex; flex-direction: column; gap: 1rem;">
        <label>
          Brief name
          <input v-model.trim="newName" type="text" required placeholder="e.g. Airbnb Summer 2026" />
        </label>
        <label>
          Content
          <textarea v-model="newContent" rows="6" placeholder="Paste or type your brand brief here…" />
        </label>
        <div style="display: flex; gap: 0.75rem;">
          <AppButton type="submit" :disabled="creating">{{ creating ? "Creating…" : "Create" }}</AppButton>
          <AppButton variant="secondary" @click="showCreate = false">Cancel</AppButton>
        </div>
      </form>
    </AppCard>

    <EmptyState
      v-if="!loading && briefs.length === 0 && !showCreate"
      title="No briefs yet"
      message="Create your first brand brief to get started."
    />

    <div v-if="loading" class="persona-grid">
      <div v-for="n in 3" :key="n" class="skeleton-card">
        <SkeletonBlock variant="title" />
        <SkeletonBlock width="60%" />
      </div>
    </div>

    <div v-else class="brief-grid">
      <AppCard
        v-for="brief in briefs"
        :key="brief.id"
        class="brief-card"
        :class="{ 'is-active': campaignStore.brandBriefId === brief.id }"
        @click="selectBrief(brief)"
        role="button"
        tabindex="0"
        @keydown.enter="selectBrief(brief)"
      >
        <div class="brief-card-header">
          <h3 class="brief-card-name">{{ brief.name }}</h3>
          <StatusBadge :status="brief.graph_status" />
        </div>
        <p class="brief-card-content">{{ brief.content?.slice(0, 140) || "No content yet." }}</p>
        <div class="brief-card-actions" @click.stop>
          <AppButton variant="secondary" size="sm" @click="startEdit(brief)">Edit</AppButton>
          <AppButton variant="danger" size="sm" @click="deleteBrief(brief.id)">Delete</AppButton>
        </div>
      </AppCard>
    </div>

    <!-- Inline edit drawer -->
    <DrawerPanel :open="!!editingBrief" @close="editingBrief = null" title="Edit brief">
      <form v-if="editingBrief" @submit.prevent="saveEdit" style="display: flex; flex-direction: column; gap: 1rem; padding: 1rem;">
        <label>
          Name
          <input v-model.trim="editName" type="text" required />
        </label>
        <label>
          Content
          <textarea v-model="editContent" rows="12" />
        </label>
        <AppButton type="submit" :disabled="saving">{{ saving ? "Saving…" : "Save" }}</AppButton>
      </form>
    </DrawerPanel>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { apiClient } from "@/api/client.js";
import { useCampaignStore } from "@/stores/campaignStore";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import DrawerPanel from "@/components/common/DrawerPanel.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";

const router = useRouter();
const campaignStore = useCampaignStore();

const briefs = ref([]);
const loading = ref(true);
const showCreate = ref(false);
const creating = ref(false);
const newName = ref("");
const newContent = ref("");

const editingBrief = ref(null);
const editName = ref("");
const editContent = ref("");
const saving = ref(false);

async function loadBriefs() {
  loading.value = true;
  try {
    const resp = await apiClient.get("/api/briefs");
    briefs.value = resp.data.items;
  } finally {
    loading.value = false;
  }
}

async function createBrief() {
  creating.value = true;
  try {
    const resp = await apiClient.post("/api/briefs", {
      name: newName.value,
      content: newContent.value,
    });
    briefs.value.unshift(resp.data.brief);
    showCreate.value = false;
    newName.value = "";
    newContent.value = "";
  } finally {
    creating.value = false;
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
}

async function saveEdit() {
  if (!editingBrief.value) return;
  saving.value = true;
  try {
    const resp = await apiClient.put(`/api/briefs/${editingBrief.value.id}`, {
      name: editName.value,
      content: editContent.value,
    });
    const idx = briefs.value.findIndex((b) => b.id === editingBrief.value.id);
    if (idx !== -1) briefs.value[idx] = resp.data.brief;
    editingBrief.value = null;
  } finally {
    saving.value = false;
  }
}

async function deleteBrief(id) {
  if (!confirm("Delete this brief and all its personas?")) return;
  await apiClient.delete(`/api/briefs/${id}`);
  briefs.value = briefs.value.filter((b) => b.id !== id);
  if (campaignStore.brandBriefId === id) campaignStore.clearBrief();
}

onMounted(loadBriefs);
</script>

<style scoped>
.brief-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}
.brief-card {
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.brief-card.is-active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent);
}
.brief-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.brief-card-name { font-weight: 600; font-size: 1rem; }
.brief-card-content {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
  line-height: 1.5;
}
.brief-card-actions { display: flex; gap: 0.5rem; }
</style>
