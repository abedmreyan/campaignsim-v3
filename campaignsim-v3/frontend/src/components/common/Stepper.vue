<template>
  <nav class="stepper" :class="{ 'stepper--horizontal': horizontal }" aria-label="Workflow steps">
    <button
      v-for="step in steps"
      :key="step.number"
      class="stepper__item"
      :class="{
        'is-active': step.number === currentStep,
        'is-complete': step.number < currentStep,
      }"
      type="button"
      :disabled="step.disabled"
      :title="stepTooltip(step)"
      :aria-label="stepTooltip(step)"
      @click="$emit('select', step.number)"
    >
      <span class="stepper__number">{{ step.number }}</span>
      <span class="stepper__content">
        <span class="stepper__label">{{ step.label }}</span>
        <span v-if="step.subtitle" class="stepper__sub">{{ step.subtitle }}</span>
      </span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  currentStep: {
    type: Number,
    required: true,
  },
  steps: {
    type: Array,
    required: true,
  },
  horizontal: Boolean,
});

defineEmits(["select"]);

function stepTooltip(step) {
  if (step.subtitle) {
    return `${step.label} — ${step.subtitle}`;
  }
  return step.label;
}
</script>
