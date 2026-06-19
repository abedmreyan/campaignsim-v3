<template>
  <div class="empty-state">
    <div class="empty-state__icon">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p>{{ message }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: "Nothing here yet",
  },
  message: {
    type: String,
    default: "Complete the previous action to populate this area.",
  },
  icon: {
    type: String,
    default: "CS",
  },
});
</script>
