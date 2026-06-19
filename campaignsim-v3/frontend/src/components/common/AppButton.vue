<template>
  <button
    class="app-button"
    :class="[`app-button--${variant}`, `app-button--${size}`, { 'is-block': block }]"
    :disabled="disabled || loading"
    :type="type"
  >
    <span v-if="loading" class="button-spinner" aria-hidden="true"></span>
    <span v-if="$slots.icon" class="app-button__icon"><slot name="icon" /></span>
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: "primary",
  },
  size: {
    type: String,
    default: "md",
  },
  disabled: Boolean,
  loading: Boolean,
  block: Boolean,
  type: {
    type: String,
    default: "button",
  },
});
</script>
