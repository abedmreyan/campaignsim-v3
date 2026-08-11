<template>
  <div class="view-stack stagger-in">
    <PageHeader
      title="Campaign Variants"
      eyebrow="Step 3"
      description="Create 1–6 message variants, validate fields, then launch the simulated A/B test."
    />

    <label class="objective-select">
      <span>Campaign objective</span>
      <select :value="store.campaignObjective" @change="store.setCampaignObjective($event.target.value)">
        <option value="">Not set (no scoring emphasis)</option>
        <option value="awareness">Awareness — reach and attention</option>
        <option value="conversion">Conversion — purchase/signup intent</option>
        <option value="retention">Retention — existing-audience re-engagement</option>
        <option value="launch">Launch — high-intensity single moment</option>
      </select>
    </label>

    <div
      v-if="store.variants.length"
      class="validation-banner"
      :class="{ 'is-ready': store.canStartSimulation && !validationMessage }"
    >
      <template v-if="store.canStartSimulation && !validationMessage">
        {{ store.variants.length }} variant{{ store.variants.length > 1 ? "s" : "" }} ready — launch simulation when you are set.
      </template>
      <template v-else-if="validationMessage">{{ validationMessage }}</template>
      <template v-else>Review variant content before launching.</template>
    </div>

    <DesignerChatPanel v-if="!store.isMockMode" class="designer-slot" />

    <div class="variant-builder">
      <div class="variant-builder__form">
        <VariantForm :editing="Boolean(editing)" :model-value="editing" @submit="saveVariant" @cancel="editing = null" />
      </div>
      <div>
        <EmptyState
          v-if="!store.variants.length"
          title="Create at least one variant"
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
import DesignerChatPanel from "@/components/variants/DesignerChatPanel.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const router = useRouter();
const editing = ref(null);

const validationMessage = computed(() => {
  if (store.variants.length === 0) return "";
  if (store.variants.length > 6) return "Maximum 6 variants per campaign.";
  const incomplete = store.variants.find((v) => !v.content?.headline || !v.channel);
  if (incomplete) return `Complete required fields for "${incomplete.variant_name}".`;
  return "";
});

function saveVariant(payload) {
  if (!editing.value && store.variants.length >= 6) {
    store.setNotice("A campaign supports a maximum of 6 variants.");
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

<style scoped>
.objective-select {
  display: block;
  max-width: 22rem;
}

.designer-slot {
  margin-bottom: 1.5rem;
}
</style>
