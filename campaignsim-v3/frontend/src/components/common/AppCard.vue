<template>
  <section
    class="app-card"
    :class="{
      'app-card--flat': flat,
      'app-card--highlight': highlight,
      'app-card--ghost': ghost,
    }"
  >
    <div v-if="$slots.header || title" class="app-card__header">
      <div>
        <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
        <h2 v-if="title">{{ title }}</h2>
      </div>
      <slot name="header" />
    </div>
    <slot />
    <div v-if="$slots.actions" class="card-actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: String,
  eyebrow: String,
  flat: Boolean,
  highlight: Boolean,
  ghost: Boolean,
});
</script>
