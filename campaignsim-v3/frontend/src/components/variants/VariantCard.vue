<template>
  <article class="variant-card">
    <div class="variant-card__header">
      <div>
        <h3>
          {{ variant.variant_name }}
          <span v-if="variant.provenance === 'ai'" class="variant-card__ai-badge">AI-proposed</span>
        </h3>
        <p>{{ variant.channel }} · {{ variant.content?.format }}</p>
      </div>
      <StatusBadge :status="variant.status || 'pending'" />
    </div>
    <h4>{{ variant.content?.headline }}</h4>
    <p>{{ variant.content?.body }}</p>
    <div class="variant-card__meta">
      <span>{{ variant.content?.tone }}</span>
      <span>{{ variant.target_segment || "All segments" }}</span>
      <span>{{ variant.max_rounds }} rounds</span>
    </div>
    <div v-if="variant.rationale || variant.hypothesis" class="variant-card__ai-notes">
      <p v-if="variant.rationale"><strong>Rationale:</strong> {{ variant.rationale }}</p>
      <p v-if="variant.hypothesis"><strong>Hypothesis:</strong> {{ variant.hypothesis }}</p>
    </div>
    <div class="card-actions">
      <AppButton variant="secondary" @click="$emit('edit', variant)">Edit</AppButton>
      <AppButton variant="danger" @click="$emit('delete', variant.variant_id)">Delete</AppButton>
    </div>
  </article>
</template>

<script setup>
import AppButton from "@/components/common/AppButton.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";

defineProps({
  variant: {
    type: Object,
    required: true,
  },
});

defineEmits(["edit", "delete"]);
</script>

<style scoped>
.variant-card__ai-badge {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: var(--color-accent-soft, rgba(124, 92, 255, 0.15));
  color: var(--color-accent, #7c5cff);
  vertical-align: middle;
}

.variant-card__ai-notes {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  background: var(--color-surface-muted, rgba(127, 127, 127, 0.08));
  font-size: 0.85rem;
}

.variant-card__ai-notes p + p {
  margin-top: 0.25rem;
}
</style>

