<template>
  <div class="metric-tile">
    <span class="metric-tile__label">{{ label }}</span>
    <span class="metric-tile__value" :class="{ 'metric-tile__value--text': !isNumeric }">
      {{ displayValue }}
    </span>
    <span v-if="hint" class="metric-tile__hint">{{ hint }}</span>
  </div>
</template>

<script setup>
import { computed, toRef } from "vue";
import { useAnimatedNumber } from "@/composables/useAnimatedNumber";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: String,
});

const isNumeric = computed(() => {
  const num = Number(props.value);
  return Number.isFinite(num) && String(props.value).trim() !== "";
});

const animated = useAnimatedNumber(toRef(props, "value"));

const displayValue = computed(() => {
  if (isNumeric.value) return animated.value;
  return props.value;
});
</script>
