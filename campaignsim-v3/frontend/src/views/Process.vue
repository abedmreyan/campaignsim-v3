<template>
  <AppLayout>
    <Transition name="step-fade" mode="out-in">
      <component :is="activeComponent" :key="store.currentStep" />
    </Transition>
  </AppLayout>
</template>

<script setup>
import { computed } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import Step1GraphBuild from "./Step1GraphBuild.vue";
import Step2Personas from "./Step2Personas.vue";
import Step3Simulation from "./Step3Simulation.vue";
import Step4Report from "./Step4Report.vue";
import Step5Interaction from "./Step5Interaction.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();

const activeComponent = computed(() => {
  const components = {
    1: Step1GraphBuild,
    2: Step2Personas,
    3: Step3Simulation,
    4: Step4Report,
    5: Step5Interaction,
  };
  return components[store.currentStep] || Step1GraphBuild;
});
</script>
