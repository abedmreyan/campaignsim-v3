<template>
  <div class="iteration-compare-view view-stack stagger-in">
    <PageHeader
      title="Campaign Iterations"
      eyebrow="Lineage"
      description="How this campaign's metrics moved across redesigns."
    />

    <AppLoader v-if="loading" label="Loading iteration history…" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!lineage.length" title="No iterations found" message="This campaign has no lineage yet." />

    <div v-else class="iteration-table-wrap">
      <table class="iteration-table">
        <thead>
          <tr>
            <th>Iteration</th>
            <th>Campaign</th>
            <th>Avg engagement</th>
            <th>Best variant</th>
            <th>Best engagement</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in lineage"
            :key="entry.id"
            :class="{ 'is-current': entry.campaign_ref === route.params.campaignId }"
          >
            <td>#{{ entry.iteration }}</td>
            <td>{{ entry.brand_name }}</td>
            <td>{{ entry.scored ? `${entry.avg_engagement_rate_pct}%` : "Not yet scored" }}</td>
            <td>{{ entry.best_variant_name || "—" }}</td>
            <td>{{ entry.best_engagement_rate_pct != null ? `${entry.best_engagement_rate_pct}%` : "—" }}</td>
            <td>{{ formatDate(entry.created_at) }}</td>
            <td>
              <RouterLink :to="{ name: 'CampaignReport', params: { campaignId: entry.campaign_ref } }">
                View report →
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import AppLoader from "@/components/common/AppLoader.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import { getCampaignLineage } from "@/api/insightApi";

const route = useRoute();
const lineage = ref([]);
const loading = ref(false);
const error = ref(null);

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    lineage.value = await getCampaignLineage(route.params.campaignId);
  } catch (err) {
    error.value = err?.message || "Could not load iteration history.";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.iteration-table-wrap {
  overflow-x: auto;
}

.iteration-table {
  width: 100%;
  border-collapse: collapse;
}

.iteration-table th,
.iteration-table td {
  text-align: left;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.iteration-table tr.is-current {
  background: var(--color-accent-soft);
}
</style>
