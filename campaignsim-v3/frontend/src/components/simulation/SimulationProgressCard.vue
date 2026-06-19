<template>
  <article class="progress-card">
    <div class="progress-card__header">
      <div>
        <h3>{{ title }}</h3>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <StatusBadge :status="status" />
    </div>
    <div class="progress-bar">
      <span :style="{ width: `${Math.min(100, progress || 0)}%` }"></span>
    </div>
    <strong>{{ Math.round(progress || 0) }}%</strong>
  </article>
</template>

<script setup>
import StatusBadge from "@/components/common/StatusBadge.vue";

defineProps({
  title: String,
  subtitle: String,
  status: {
    type: String,
    default: "pending",
  },
  progress: {
    type: Number,
    default: 0,
  },
});
</script>
