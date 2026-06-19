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
        <AppButton :disabled="!store.graphReady" :loading="store.personas.loading" @click="store.generatePersonas(count)">
          Generate personas
        </AppButton>
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
      <PersonaCard
        v-for="persona in filteredPersonas"
        :key="persona.user_id"
        :persona="persona"
        @select="activePersona = persona"
      />
    </div>

    <PersonaDetailDrawer :persona="activePersona" @close="activePersona = null" />
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import PersonaCard from "@/components/personas/PersonaCard.vue";
import PersonaDetailDrawer from "@/components/personas/PersonaDetailDrawer.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const count = ref(30);
const search = ref("");
const segmentFilter = ref("");
const activePersona = ref(null);
const counts = [10, 20, 30, 50];

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
