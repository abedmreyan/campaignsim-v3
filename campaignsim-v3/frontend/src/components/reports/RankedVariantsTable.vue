<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Variant</th>
          <th>Channel</th>
          <th>Format</th>
          <th>Engagement</th>
          <th>Trend</th>
          <th>Note</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="variant in variants" :key="variant.variant_id" :class="{ 'is-winner-row': variant.rank === 1 }">
          <td>
            <span v-if="variant.rank <= 3" class="rank-medal" :class="`rank-medal--${variant.rank}`">
              #{{ variant.rank }}
            </span>
            <span v-else>{{ variant.rank }}</span>
          </td>
          <td><strong>{{ variant.variant_name }}</strong></td>
          <td>{{ variant.channel }}</td>
          <td>{{ variant.content_format }}</td>
          <td><strong>{{ variant.engagement_rate_pct }}%</strong></td>
          <td><StatusBadge :status="variant.trend" /></td>
          <td>{{ variant.rank === 1 ? "Recommended winner" : "Supporting option" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import StatusBadge from "@/components/common/StatusBadge.vue";

defineProps({
  variants: {
    type: Array,
    default: () => [],
  },
});
</script>
