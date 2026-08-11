<template>
  <div class="view-stack stagger-in">
    <PageHeader
      title="Audience Personas"
      eyebrow="Step 2"
      description="Generate segment-aware synthetic audiences from your knowledge graph."
    >
      <template #actions>
        <AppButton variant="secondary" :disabled="!store.personasReady" @click="store.goToStep(3)">
          Continue
        </AppButton>
      </template>
    </PageHeader>

    <AppCard>
      <div class="toolbar-row">
        <div>
          <span style="display: block; margin-bottom: 0.4rem; font-size: 0.8125rem; font-weight: 600">
            Persona count
          </span>
          <div class="segmented-control">
            <button
              v-for="n in counts"
              :key="n"
              type="button"
              :class="{ 'is-active': count === n }"
              @click="count = n"
            >
              {{ n }}
            </button>
          </div>
        </div>
        <label style="flex: 1; min-width: 180px">
          <span>Search</span>
          <input v-model.trim="search" type="search" placeholder="Name, segment, profession…" />
        </label>
        <div style="display: flex; gap: 0.5rem;">
          <AppButton
            variant="secondary"
            :disabled="!store.personas.items.length || store.personas.loading"
            @click="regenerateAll"
          >
            Regenerate all
          </AppButton>
          <AppButton
            :disabled="!store.graphReady || store.personas.loading"
            :loading="store.personas.loading"
            @click="store.generatePersonas(count)"
          >
            {{ store.personas.items.length ? "Generate more" : "Generate personas" }}
          </AppButton>
        </div>
      </div>

      <div v-if="segments.length" class="filter-chips" style="margin-top: 1rem">
        <button type="button" :class="{ 'is-active': !segmentFilter }" @click="segmentFilter = ''">All</button>
        <button
          v-for="seg in segments"
          :key="seg"
          type="button"
          :class="{ 'is-active': segmentFilter === seg }"
          @click="segmentFilter = seg"
        >
          {{ seg }}
        </button>
      </div>

      <div v-if="store.personas.loading" class="progress-block">
        <div class="progress-bar">
          <span :style="{ width: `${store.personas.progress || 12}%` }"></span>
        </div>
        <p>{{ store.personas.progressMessage || "Generating personas from graph context…" }}</p>
      </div>
      <ErrorState v-if="store.personas.error" :message="store.personas.error" />
    </AppCard>

    <AppCard v-if="!store.isMockMode" eyebrow="Real-data" title="Generate from customer segments">
      <p v-if="!approvedSegments.length && !segmentsLoading" class="segment-gen__empty">
        No approved segments yet. <RouterLink to="/audience/data">Upload and segment a customer dataset</RouterLink>
        to ground personas in real customer data.
      </p>
      <template v-else>
        <div class="segment-gen__picker">
          <label v-for="segment in approvedSegments" :key="segment.id" class="segment-gen__option">
            <input type="checkbox" :value="segment.id" v-model="selectedSegmentIds" />
            {{ segment.name }} ({{ segment.size }} customers)
          </label>
        </div>
        <div class="toolbar-row" style="margin-top: 0.75rem">
          <label>
            <span>Total personas</span>
            <input v-model.number="segmentTotalN" type="number" min="1" max="200" style="width: 6rem" />
          </label>
          <label>
            <span>Mode</span>
            <select v-model="segmentMode">
              <option value="hybrid">Hybrid — add to existing audience</option>
              <option value="segments">Segments only — replace audience (keep brand agent)</option>
            </select>
          </label>
          <AppButton
            :disabled="!selectedSegmentIds.length"
            :loading="segmentGenLoading"
            @click="generateFromSegments"
          >
            Generate segment personas
          </AppButton>
        </div>
        <ErrorState v-if="segmentGenError" :message="segmentGenError" />
      </template>
    </AppCard>

    <div v-if="store.personas.loading && !store.personas.items.length" class="persona-grid">
      <div v-for="n in 6" :key="n" class="skeleton-card">
        <SkeletonBlock variant="title" />
        <SkeletonBlock />
        <SkeletonBlock width="60%" />
      </div>
    </div>

    <EmptyState
      v-else-if="!store.personas.items.length"
      title="No personas yet"
      message="Generate personas from your brand knowledge graph to continue."
    />

    <div v-else class="persona-grid">
      <div v-for="persona in filteredPersonas" :key="persona.user_id || persona.id" class="persona-card-wrapper">
        <PersonaCard
          :persona="persona"
          @select="activePersona = persona"
        />
        <button
          class="persona-delete-btn"
          type="button"
          title="Delete persona"
          @click.stop="store.deletePersona(persona.id)"
        >
          &#x2715;
        </button>
      </div>
    </div>

    <PersonaDetailDrawer :persona="activePersona" @close="activePersona = null" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import PersonaCard from "@/components/personas/PersonaCard.vue";
import PersonaDetailDrawer from "@/components/personas/PersonaDetailDrawer.vue";
import { useCampaignStore } from "@/stores/campaignStore";
import { generatePersonasFromSegments, listSegments } from "@/api/dataApi";

const store = useCampaignStore();
const count = ref(30);
const search = ref("");
const segmentFilter = ref("");
const activePersona = ref(null);
const counts = [10, 20, 30, 50];

const approvedSegments = ref([]);
const segmentsLoading = ref(false);
const selectedSegmentIds = ref([]);
const segmentTotalN = ref(30);
const segmentMode = ref("hybrid");
const segmentGenLoading = ref(false);
const segmentGenError = ref(null);

async function loadApprovedSegments() {
  if (store.isMockMode) return;
  segmentsLoading.value = true;
  try {
    const all = await listSegments();
    approvedSegments.value = all.filter((s) => s.status === "approved");
  } catch {
    approvedSegments.value = [];
  } finally {
    segmentsLoading.value = false;
  }
}

async function generateFromSegments() {
  segmentGenLoading.value = true;
  segmentGenError.value = null;
  try {
    await generatePersonasFromSegments({
      simulationId: store.simulationId,
      segmentIds: selectedSegmentIds.value,
      totalN: segmentTotalN.value,
      mode: segmentMode.value,
    });
    await store.loadPersonas(store.brandBriefId);
  } catch (err) {
    segmentGenError.value = err?.message || "Could not generate personas from segments.";
  } finally {
    segmentGenLoading.value = false;
  }
}

// Load persisted personas from DB on mount
onMounted(() => {
  loadApprovedSegments();
  if (store.brandBriefId && !store.personas.items.length) {
    store.loadPersonas(store.brandBriefId);
  }
});

async function regenerateAll() {
  if (!store.brandBriefId) return;
  await store.clearPersonas(store.brandBriefId);
  store.generatePersonas(count.value);
}

const segments = computed(() => [...new Set(store.personas.items.map((p) => p.segment).filter(Boolean))]);

const filteredPersonas = computed(() =>
  store.personas.items.filter((persona) => {
    const matchesSegment = segmentFilter.value ? persona.segment === segmentFilter.value : true;
    const q = search.value.toLowerCase();
    const matchesSearch = q
      ? [persona.name, persona.segment, persona.profession, persona.country].some((field) =>
          String(field || "")
            .toLowerCase()
            .includes(q),
        )
      : true;
    return matchesSegment && matchesSearch;
  }),
);
</script>

<style scoped>
.segment-gen__empty {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.segment-gen__picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.5rem;
}

.segment-gen__option {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.88rem;
}

.persona-card-wrapper {
  position: relative;
}
.persona-delete-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  border: none;
  background: var(--color-danger, #ef4444);
  color: #fff;
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
}
.persona-card-wrapper:hover .persona-delete-btn {
  opacity: 1;
}
</style>
