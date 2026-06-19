<template>
  <div class="view-stack stagger-in">
    <PageHeader
      title="Campaign Variants"
      eyebrow="Step 3"
      description="Create 2–3 message variants, validate fields, then launch the simulated A/B test."
    />

    <div
      v-if="store.variants.length"
      class="validation-banner"
      :class="{ 'is-ready': store.canStartSimulation && !validationMessage }"
    >
      <template v-if="store.canStartSimulation && !validationMessage">
        {{ store.variants.length }} variants ready — launch simulation when you are set.
      </template>
      <template v-else-if="validationMessage">{{ validationMessage }}</template>
      <template v-else>Review variant content before launching.</template>
    </div>

    <div class="variant-builder">
      <div class="variant-builder__form">
        <VariantForm :editing="Boolean(editing)" :model-value="editing" @submit="saveVariant" @cancel="editing = null" />
      </div>
      <div>
        <EmptyState
          v-if="!store.variants.length"
          title="Create at least two variants"
          message="Add campaign variants with channel, format, and headline to compare in simulation."
        />
        <div v-else class="variant-list">
          <VariantCard
            v-for="variant in store.variants"
            :key="variant.variant_id"
            :variant="variant"
            @edit="editing = $event"
            @delete="store.deleteVariant"
          />
        </div>
        <div class="action-row" style="margin-top: 1.25rem">
          <AppButton size="lg" :disabled="!store.canStartSimulation" :loading="store.simulationRun.loading" @click="start">
            Launch simulation
          </AppButton>
        </div>
        <ErrorState v-if="validationMessage && store.variants.length" :message="validationMessage" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import VariantForm from "@/components/variants/VariantForm.vue";
import VariantCard from "@/components/variants/VariantCard.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const router = useRouter();
const editing = ref(null);

const validationMessage = computed(() => {
  if (store.variants.length === 0) return "";
  if (store.variants.length < 2) return "Add at least 2 variants before starting the A/B test.";
  if (store.variants.length > 3) return "Maximum 3 variants in this demo configuration.";
  const incomplete = store.variants.find((v) => !v.content?.headline || !v.channel);
  if (incomplete) return `Complete required fields for "${incomplete.variant_name}".`;
  return "";
});

function saveVariant(payload) {
  if (!editing.value && store.variants.length >= 3) {
    store.setNotice("The demo supports a maximum of 3 variants.");
    return;
  }
  if (editing.value) {
    store.updateVariant(editing.value.variant_id, payload);
    editing.value = null;
  } else {
    store.addVariant(payload);
  }
}

async function start() {
  await store.startAbTest();
  router.push({ name: "simulation-run", params: { simulationId: store.simulationId } });
}
</script>
