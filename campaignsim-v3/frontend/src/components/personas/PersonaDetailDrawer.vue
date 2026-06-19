<template>
  <DrawerPanel
    :open="Boolean(persona)"
    :title="persona?.name || 'Persona'"
    eyebrow="Audience persona"
    @close="$emit('close')"
  >
    <template v-if="persona">
      <div class="persona-card__top" style="margin-bottom: 1rem">
        <span class="persona-card__avatar" :style="{ background: segmentColor(persona.segment) }">
          {{ initials(persona.name) }}
        </span>
        <div>
          <StatusBadge :status="persona.segment || 'pending'" :label="persona.segment" />
          <p style="margin-top: 0.5rem; color: var(--color-text-muted)">
            {{ persona.profession }} · {{ persona.country }} · {{ persona.age }}y
          </p>
        </div>
      </div>
      <p>{{ persona.bio }}</p>
      <div class="tag-row" style="margin-top: 1rem">
        <span>{{ persona.mbti }}</span>
        <span>{{ persona.gender }}</span>
      </div>
      <div v-if="persona.platform_preferences?.length" class="tag-row">
        <span v-for="platform in persona.platform_preferences" :key="platform">{{ platform }}</span>
      </div>
      <div v-if="persona.persona" style="margin-top: 1.25rem">
        <p class="eyebrow">Full narrative</p>
        <p style="line-height: 1.65">{{ persona.persona }}</p>
      </div>
    </template>
  </DrawerPanel>
</template>

<script setup>
import DrawerPanel from "@/components/common/DrawerPanel.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";

defineProps({
  persona: Object,
});

defineEmits(["close"]);

const SEGMENT_COLORS = {
  loyal: "#4f46e5",
  skeptical: "#d97706",
  explorer: "#059669",
  budget: "#64748b",
  premium: "#7c3aed",
};

function segmentColor(segment = "") {
  const key = segment?.toLowerCase?.() || "";
  return SEGMENT_COLORS[key] || "#4f46e5";
}

function initials(name = "") {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
</script>
