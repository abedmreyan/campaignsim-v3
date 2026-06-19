<template>
  <Teleport to="body">
    <div v-if="open" class="drawer-root">
      <div class="drawer-backdrop" @click="$emit('close')" />
      <aside class="drawer-panel" role="dialog" :aria-label="title" @keydown.esc="$emit('close')">
        <div class="drawer-panel__head">
          <div>
            <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
            <h2>{{ title }}</h2>
          </div>
          <button type="button" class="drawer-close" aria-label="Close" @click="$emit('close')">
            ×
          </button>
        </div>
        <div class="drawer-panel__body">
          <slot />
        </div>
      </aside>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  open: Boolean,
  title: { type: String, default: "Details" },
  eyebrow: String,
});

defineEmits(["close"]);
</script>
