<template>
  <component :is="route.name === 'interaction' ? AppLayout : 'div'">
    <div class="view-stack stagger-in">
      <PageHeader
        title="Persona Insights"
        eyebrow="Step 5"
        description="Interview synthetic personas about why they engaged—or ignored—your winning variant."
      />

      <EmptyState
        v-if="!store.report.data || !store.personas.items.length"
        title="Insights not ready"
        message="Complete the insights report and generate personas before starting interviews."
      />

      <template v-else>
        <PersonaInterviewPanel
          :personas="store.personas.items"
          :messages="store.interviewMessages"
          @ask="askPersona"
        />
        <AppCard title="Next steps" ghost>
          <p>Export JSON or CSV from the insights report, then archive runs in campaign history.</p>
          <div class="action-row">
            <RouterLink class="app-button app-button--secondary" to="/history">Campaign history</RouterLink>
            <AppButton variant="secondary" @click="store.goToStep(4)">Back to report</AppButton>
          </div>
        </AppCard>
      </template>
    </div>
  </component>
</template>

<script setup>
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import PersonaInterviewPanel from "@/components/interaction/PersonaInterviewPanel.vue";
import AppLayout from "@/layouts/AppLayout.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const route = useRoute();
const store = useCampaignStore();

onMounted(() => {
  if (route.name === "interaction") {
    store.currentStep = 5;
    store.persist();
  }
});

async function askPersona({ personaId, question }) {
  await store.interviewPersona(personaId, question);
}
</script>
