<template>
  <AppLayout>
    <div class="view-stack stagger-in">
      <PageHeader
        title="Campaign history"
        eyebrow="Archive"
        description="Review completed simulations, top variants, and reopen reports from past runs."
      >
        <template #actions>
          <AppButton variant="secondary" :loading="store.history.loading" @click="store.loadHistory">
            Refresh
          </AppButton>
        </template>
      </PageHeader>

      <p v-if="store.isMockMode" class="history-demo-note">
        Demo mode — history entries use mock archive data. Expand run details only when you need IDs for debugging.
      </p>

      <div class="history-filters">
        <div class="filter-chips">
          <button type="button" :class="{ 'is-active': statusFilter === '' }" @click="statusFilter = ''">
            All
          </button>
          <button
            type="button"
            :class="{ 'is-active': statusFilter === 'completed' }"
            @click="statusFilter = 'completed'"
          >
            Completed
          </button>
          <button
            type="button"
            :class="{ 'is-active': statusFilter === 'running' }"
            @click="statusFilter = 'running'"
          >
            Running
          </button>
        </div>
      </div>

      <HistorySkeletonGrid v-if="store.history.loading" :count="3" />
      <div v-else-if="store.history.error" class="history-error-block">
        <ErrorState :message="store.history.error" />
        <AppButton variant="secondary" size="sm" @click="store.loadHistory">Retry</AppButton>
      </div>

      <EmptyState
        v-else-if="!filteredItems.length"
        :title="store.history.items.length ? 'No matches' : 'No history yet'"
        :message="
          store.history.items.length
            ? 'Try a different status filter to see archived runs.'
            : 'Completed simulations will appear here after you finish a workflow.'
        "
      >
        <RouterLink class="app-button app-button--primary" to="/process" style="margin-top: 1rem">
          Start workflow
        </RouterLink>
      </EmptyState>

      <template v-else>
        <div class="history-table-wrap desktop-only">
          <table class="history-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Status</th>
                <th>Variants</th>
                <th>Top variant</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filteredItems"
                :key="item.simulation_id"
                class="history-table__row"
                :class="{ 'is-completed': item.status === 'completed' }"
              >
                <td>
                  <strong>{{ item.project_name }}</strong>
                </td>
                <td><StatusBadge :status="item.status" /></td>
                <td>{{ item.variants_count }}</td>
                <td>{{ item.top_variant_name || "—" }}</td>
                <td>{{ formatDate(item.updated_at) }}</td>
                <td>
                  <div class="history-table__actions">
                    <AppButton
                      size="sm"
                      :disabled="item.status !== 'completed'"
                      @click="openReport(item)"
                    >
                      Report
                    </AppButton>
                    <AppButton size="sm" variant="secondary" @click="resume(item)">
                      {{ item.status === 'running' ? 'Monitor' : 'Resume' }}
                    </AppButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="history-grid mobile-only">
          <article
            v-for="item in filteredItems"
            :key="item.simulation_id"
            class="history-card"
            :class="{ 'history-card--completed': item.status === 'completed' }"
          >
            <div class="history-card__head">
              <div>
                <h3>{{ item.project_name }}</h3>
                <p>{{ formatDate(item.updated_at) }}</p>
              </div>
              <StatusBadge :status="item.status" />
            </div>
            <div class="history-card__metrics">
              <MetricTile label="Variants" :value="item.variants_count" />
              <MetricTile label="Top variant" :value="item.top_variant_name || '—'" />
            </div>
            <details class="history-card__ids">
              <summary>Run details</summary>
              <dl>
                <div>
                  <dt>Simulation ID</dt>
                  <dd>{{ item.simulation_id }}</dd>
                </div>
                <div v-if="item.graph_id">
                  <dt>Graph ID</dt>
                  <dd>{{ item.graph_id }}</dd>
                </div>
                <div v-if="item.report_id">
                  <dt>Report ID</dt>
                  <dd>{{ item.report_id }}</dd>
                </div>
              </dl>
            </details>
            <div class="card-actions">
              <AppButton
                size="sm"
                :disabled="item.status !== 'completed'"
                @click="openReport(item)"
              >
                Open report
              </AppButton>
              <AppButton size="sm" variant="secondary" @click="resume(item)">
                {{ item.status === 'running' ? 'Monitor run' : 'Resume workflow' }}
              </AppButton>
            </div>
          </article>
        </div>
      </template>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import HistorySkeletonGrid from "@/components/history/HistorySkeletonGrid.vue";
import MetricTile from "@/components/common/MetricTile.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import AppLayout from "@/layouts/AppLayout.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const router = useRouter();
const statusFilter = ref("");

const filteredItems = computed(() =>
  statusFilter.value
    ? store.history.items.filter((item) => item.status === statusFilter.value)
    : store.history.items,
);

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

async function openReport(item) {
  store.simulationId = item.simulation_id;
  if (item.graph_id) store.graphId = item.graph_id;

  try {
    if (item.report_id) {
      store.reportId = item.report_id;
      await store.loadReport(item.report_id);
    } else if (item.status === "completed") {
      store.simulationRun.status = "completed";
      await store.generateReport();
    } else {
      store.setNotice("Report is available when the simulation is completed.");
      return;
    }
    store.goToStep(4);
    router.push({ name: "report", params: { reportId: store.reportId } });
  } catch {
    store.setNotice("Could not open report for this run.");
  }
}

function resume(item) {
  store.simulationId = item.simulation_id;
  if (item.graph_id) store.graphId = item.graph_id;

  if (item.status === "running") {
    router.push({ name: "simulation-run", params: { simulationId: item.simulation_id } });
    return;
  }

  store.goToStep(3);
  router.push("/process");
}

onMounted(() => {
  store.loadHistory();
});
</script>
