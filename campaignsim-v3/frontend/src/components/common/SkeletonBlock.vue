<template>
  <div
    class="skeleton-block"
    :class="[`skeleton-block--${variant}`]"
    :style="blockStyle"
    aria-hidden="true"
  />
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: {
    type: String,
    default: "text",
  },
  width: String,
  height: String,
});

const blockStyle = computed(() => ({
  width: props.width || undefined,
  height: props.height || undefined,
}));
</script>
