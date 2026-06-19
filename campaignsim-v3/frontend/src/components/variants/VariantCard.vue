<template>
  <article class="variant-card">
    <div class="variant-card__header">
      <div>
        <h3>{{ variant.variant_name }}</h3>
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
