<template>
  <div class="segment-matrix">
    <div v-for="item in segments" :key="item.segment" class="segment-matrix__row">
      <span>{{ item.segment }}</span>
      <strong>{{ item.engagement_rate_pct }}%</strong>
      <small>Best: {{ item.best_variant_id }}</small>
    </div>
  </div>
</template>

<script setup>
defineProps({
  segments: {
    type: Array,
    default: () => [],
  },
});
</script>
