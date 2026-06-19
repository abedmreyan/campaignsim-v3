<template>
  <div class="report-loading-skeleton" aria-busy="true" aria-label="Generating report">
    <div class="report-loading-skeleton__hero">
      <SkeletonBlock variant="title" width="35%" />
      <SkeletonBlock variant="title" width="70%" height="2rem" />
      <SkeletonBlock variant="text" width="90%" />
      <div class="report-loading-skeleton__metrics">
        <SkeletonBlock height="3.5rem" />
        <SkeletonBlock height="3.5rem" />
        <SkeletonBlock height="3.5rem" />
      </div>
    </div>
    <div class="report-loading-skeleton__body">
      <SkeletonBlock height="8rem" />
      <SkeletonBlock height="12rem" />
    </div>
  </div>
</template>

<script setup>
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
</script>
