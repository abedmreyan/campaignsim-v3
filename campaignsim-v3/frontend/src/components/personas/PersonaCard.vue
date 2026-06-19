<template>
  <article class="persona-card">
    <div class="persona-card__top">
      <span class="persona-card__avatar" :style="{ background: segmentColor }">{{ initials }}</span>
      <div>
        <h3>
          <span
            v-if="persona.segment"
            class="persona-card__segment-dot"
            :style="{ background: segmentColor }"
            aria-hidden="true"
          />
          {{ persona.name }}
        </h3>
        <p>{{ persona.profession }} · {{ persona.country }}</p>
      </div>
    </div>
    <div class="persona-card__meta">
      <span>{{ persona.age }} years</span>
      <span>{{ persona.gender }}</span>
      <span>{{ persona.mbti }}</span>
    </div>
    <StatusBadge :status="persona.segment || 'pending'" :label="persona.segment" />
    <p>{{ persona.bio }}</p>
    <div class="tag-row">
      <span v-for="platform in persona.platform_preferences" :key="platform">{{ platform }}</span>
    </div>
    <button class="link-button" type="button" @click="$emit('select', persona)">View full profile</button>
  </article>
</template>

<script setup>
import { computed } from "vue";
import StatusBadge from "@/components/common/StatusBadge.vue";

const props = defineProps({
  persona: {
    type: Object,
    required: true,
  },
});

defineEmits(["select"]);

const SEGMENT_COLORS = {
  loyal: "#4f46e5",
  skeptical: "#d97706",
  explorer: "#059669",
  budget: "#64748b",
  premium: "#7c3aed",
};

const segmentColor = computed(() => {
  const key = props.persona.segment?.toLowerCase?.() || "";
  return SEGMENT_COLORS[key] || "#4f46e5";
});

const initials = computed(() =>
  props.persona.name
    ?.split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase() || "P",
);
</script>
