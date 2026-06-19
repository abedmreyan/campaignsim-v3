<template>
  <div class="recommendation-summary">
    <p class="eyebrow">Top recommendation</p>
    <h2>{{ recommendation?.variant_name || "No recommendation yet" }}</h2>
    <p>{{ recommendation?.reason }}</p>
  </div>
</template>

<script setup>
defineProps({
  recommendation: Object,
});
</script>
