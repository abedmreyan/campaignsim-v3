<template>
  <span
    class="status-badge"
    :class="[
      `status-badge--${normalized}`,
      { 'status-badge--pulse': shouldPulse, 'status-badge--settle': shouldSettle },
    ]"
  >
    {{ label || normalized }}
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  status: {
    type: String,
    default: "pending",
  },
  label: String,
});

const normalized = computed(() => props.status?.toLowerCase?.() || "pending");

const shouldPulse = computed(() =>
  ["running", "processing", "pending"].includes(normalized.value),
);

const shouldSettle = computed(() =>
  ["completed", "ready", "improving"].includes(normalized.value),
);
</script>
