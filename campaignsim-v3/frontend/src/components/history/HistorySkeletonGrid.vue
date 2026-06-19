<template>
  <div class="history-skeleton-grid" aria-hidden="true">
    <div v-for="n in count" :key="n" class="history-skeleton-card">
      <SkeletonBlock variant="title" width="55%" />
      <SkeletonBlock variant="text" width="40%" />
      <div class="history-skeleton-card__metrics">
        <SkeletonBlock height="3.5rem" />
        <SkeletonBlock height="3.5rem" />
      </div>
      <SkeletonBlock height="2.25rem" width="70%" />
    </div>
  </div>
</template>

<script setup>
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";

defineProps({
  count: { type: Number, default: 3 },
});
</script>
