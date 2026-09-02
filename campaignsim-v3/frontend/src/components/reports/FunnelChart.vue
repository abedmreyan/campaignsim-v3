<template>
  <div v-if="stages.length" class="funnel-chart">
    <div v-for="(stage, i) in stages" :key="stage.key" class="funnel-chart__row">
      <span class="funnel-chart__label">{{ stage.label }}</span>
      <div class="funnel-chart__track">
        <div
          class="funnel-chart__fill"
          :style="{ width: `${stage.pct}%`, background: RAMP[i] }"
        />
      </div>
      <span class="funnel-chart__value">{{ stage.pct.toFixed(1) }}%</span>
    </div>
  </div>
  <p v-else class="funnel-chart__empty">No funnel data for this variant.</p>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  // { attention_pct, engagement_pct, amplification_pct, intent_pct }
  funnel: {
    type: Object,
    default: () => ({}),
  },
});

// Validated ordinal ramp (one hue, monotone lightness, dark-surface-safe) —
// see dataviz skill. Attention (lightest, widest) -> intent (darkest, narrowest).
const RAMP = ["#86b6ef", "#5598e7", "#256abf", "#184f95"];

const STAGE_DEFS = [
  { key: "attention_pct", label: "Attention" },
  { key: "engagement_pct", label: "Engagement" },
  { key: "amplification_pct", label: "Amplification" },
  { key: "intent_pct", label: "Intent" },
];

const stages = computed(() =>
  STAGE_DEFS
    .filter((s) => typeof props.funnel?.[s.key] === "number")
    .map((s) => ({ key: s.key, label: s.label, pct: props.funnel[s.key] })),
);
</script>

<style scoped>
.funnel-chart {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.funnel-chart__row {
  display: grid;
  grid-template-columns: 7rem 1fr 3.5rem;
  align-items: center;
  gap: 0.75rem;
}

.funnel-chart__label {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.funnel-chart__track {
  height: 0.6rem;
  border-radius: var(--radius-full, 999px);
  background: var(--color-surface-muted, rgba(255, 255, 255, 0.06));
  overflow: hidden;
}

.funnel-chart__fill {
  height: 100%;
  border-radius: var(--radius-full, 999px);
  transition: width 0.3s ease;
}

.funnel-chart__value {
  font-size: 0.8125rem;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
  text-align: right;
}

.funnel-chart__empty {
  font-size: 0.8125rem;
  color: var(--color-text-subtle);
}
</style>
