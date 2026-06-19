<template>
  <div class="loader-state">
    <span class="loader-state__spinner" aria-hidden="true"></span>
    <p>{{ label }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: "Loading...",
  },
});
</script>
