<template>
  <div class="error-state">
    <strong>{{ title }}</strong>
    <p>{{ message }}</p>
    <AppButton v-if="$slots.default" variant="secondary">
      <slot />
    </AppButton>
  </div>
</template>

<script setup>
import AppButton from "./AppButton.vue";

defineProps({
  title: {
    type: String,
    default: "Something needs attention",
  },
  message: {
    type: String,
    default: "Please try again.",
  },
});
</script>
