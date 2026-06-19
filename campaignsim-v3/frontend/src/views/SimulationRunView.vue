<template>
  <AppLayout>
    <div class="view-stack stagger-in mission-control-view">
      <PageHeader
        title="Simulation run"
        eyebrow="Mission control"
        :description="headerDescription"
      >
        <template #actions>
          <AppButton variant="secondary" size="sm" @click="router.push('/process')">
            Back to variants
          </AppButton>
        </template>
      </PageHeader>

      <div
        v-if="isComplete"
        class="flow-banner flow-banner--success"
        role="status"
      >
        <strong>Simulation complete</strong>
        <span>Variant engagement data is ready. Generate or open the insights report next.</span>
      </div>

      <div
        v-else-if="isFailed"
        class="flow-banner flow-banner--error"
        role="alert"
      >
        <strong>{{ statusHeadline }}</strong>
        <span>{{ store.simulationRun.error || "Check variant setup and try launching again from Step 3." }}</span>
      </div>

      <AppCard
        highlight
        class="mission-control-panel"
        :class="{
          'mission-control-panel--running': isRunning,
          'mission-control-panel--complete': isComplete,
          'mission-control-panel--failed': isFailed,
        }"
      >
        <div class="mission-control__header">
          <div class="mission-control__overall">
            <ProgressRing :percent="store.simulationRun.progress || 0" :size="64" :stroke="6" />
            <div>
              <p class="eyebrow">Overall progress</p>
              <h2 class="mission-control__title">{{ statusHeadline }}</h2>
              <p class="mission-control__sub">{{ etaCopy }}</p>
            </div>
          </div>
          <StatusBadge :status="store.simulationRun.status" :label="statusHeadline" />
        </div>

        <div v-if="isRunning" class="mission-control__activity" aria-live="polite">
          <p class="mission-control__activity-label">Live activity</p>
          <ul class="mission-activity-feed">
            <li v-for="(line, index) in activityLines" :key="index">{{ line }}</li>
          </ul>
        </div>

        <div v-if="showVariantGrid" class="mission-control__variants">
          <p class="eyebrow" style="margin-bottom: 0.65rem">Variant runs</p>
          <div class="progress-grid">
            <div
              v-for="variant in store.simulationRun.variants"
              :key="variant.variant_id"
              class="progress-card"
              :class="{
                'is-running': variant.status === 'running',
                'is-complete': variant.status === 'completed',
              }"
            >
              <SimulationProgressCard
                :title="variant.variant_name"
                :subtitle="variantRoundCopy(variant)"
                :status="variant.status"
                :progress="variant.progress"
              />
            </div>
          </div>
        </div>

        <div v-else-if="isBootstrapping" class="mission-control__loading">
          <div class="progress-grid">
            <div v-for="n in 2" :key="n" class="skeleton-card">
              <SkeletonBlock variant="title" width="50%" />
              <SkeletonBlock variant="text" />
              <SkeletonBlock height="0.5rem" style="margin-top: 1rem" />
            </div>
          </div>
          <p class="mission-control__sub" style="margin-top: 1rem; text-align: center">
            Syncing simulation status…
          </p>
        </div>

        <EmptyState
          v-else-if="isIdle"
          title="No simulation running"
          message="Create at least two campaign variants in Step 3, then launch the A/B simulation to track progress here."
        >
          <RouterLink class="app-button app-button--primary" to="/process" style="margin-top: 1rem">
            Go to campaign variants
          </RouterLink>
        </EmptyState>

        <ErrorState v-if="store.simulationRun.error" :message="store.simulationRun.error" />

        <details v-if="hasRunContext" class="mission-control__ids">
          <summary>Run details</summary>
          <dl>
            <div>
              <dt>Simulation ID</dt>
              <dd>{{ store.simulationId || "—" }}</dd>
            </div>
            <div>
              <dt>Run ID</dt>
              <dd>{{ store.simulationRun.runId || "—" }}</dd>
            </div>
          </dl>
        </details>

        <div class="mission-control__footer">
          <AppButton
            variant="danger"
            :disabled="!isRunning"
            @click="store.stopSimulation"
          >
            Stop simulation
          </AppButton>
          <AppButton
            :disabled="!isComplete"
            :loading="store.report.loading"
            @click="makeReport"
          >
            View insights report
          </AppButton>
        </div>
      </AppCard>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import { useRouter } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import ProgressRing from "@/components/common/ProgressRing.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import SimulationProgressCard from "@/components/simulation/SimulationProgressCard.vue";
import AppLayout from "@/layouts/AppLayout.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const router = useRouter();
let timer = null;

const status = computed(() => store.simulationRun.status);
const isRunning = computed(() => ["running", "pending"].includes(status.value));
const isComplete = computed(() => status.value === "completed");
const isFailed = computed(() => ["failed", "cancelled", "stopped"].includes(status.value));
const isIdle = computed(() => status.value === "idle" && !store.simulationRun.variants.length);
const isBootstrapping = computed(
  () => store.simulationRun.loading && !store.simulationRun.variants.length && !isIdle.value,
);
const showVariantGrid = computed(() => store.simulationRun.variants.length > 0);
const hasRunContext = computed(() => Boolean(store.simulationId || store.simulationRun.runId));

const statusHeadline = computed(() => {
  const map = {
    running: "Simulation in progress",
    completed: "Simulation complete",
    failed: "Simulation failed",
    cancelled: "Simulation cancelled",
    stopped: "Simulation stopped",
    idle: "Waiting to start",
    pending: "Starting…",
  };
  return map[status.value] || "Simulation status";
});

const headerDescription = computed(() => {
  const count = store.simulationRun.variants.length || store.variants.length;
  if (isComplete.value) return `${count} variants finished · insights report ready`;
  if (isRunning.value) return `Tracking ${count} variants · live status updates`;
  return "Monitor variant-level rounds and overall run progress";
});

const etaCopy = computed(() => {
  if (isComplete.value) return "All variant runs finished. Open the insights report when ready.";
  if (isRunning.value) {
    const lead = store.simulationRun.variants.find((v) => v.status === "running") || store.simulationRun.variants[0];
    if (lead?.current_round) {
      return `Leading variant at round ${lead.current_round} of ${lead.max_rounds || 10} · refreshing every 2s`;
    }
    return `Overall ${store.simulationRun.progress || 0}% · polling every 2 seconds`;
  }
  if (isFailed.value) return "Adjust variants or relaunch from Step 3.";
  return "Launch from Campaign Variants when ready.";
});

const activityLines = computed(() => {
  const lines = [];
  if (!isRunning.value) return lines;

  if (store.simulationRun.progress) {
    lines.push(`Aggregate progress at ${store.simulationRun.progress}%`);
  }

  store.simulationRun.variants.forEach((variant) => {
    const round = variant.current_round || 0;
    const max = variant.max_rounds || 10;
    const pct = Math.round(variant.progress || 0);
    lines.push(`${variant.variant_name}: ${variant.status || "pending"} · round ${round}/${max} (${pct}%)`);
  });

  if (!lines.length) {
    lines.push("Initializing variant runs…");
  }

  return lines;
});

function variantRoundCopy(variant) {
  const round = variant.current_round || 0;
  const max = variant.max_rounds || 10;
  return `Round ${round} of ${max}`;
}

async function refresh() {
  if (["running", "pending", "idle"].includes(store.simulationRun.status)) {
    await store.pollSimulationStatus();
  }
  if (["completed", "failed", "cancelled", "stopped"].includes(store.simulationRun.status) && timer) {
    window.clearInterval(timer);
    timer = null;
  }
}

async function makeReport() {
  const report = await store.generateReport();
  if (!report) return;
  store.goToStep(4);
  router.push({ name: "report", params: { reportId: report.report_id || store.reportId } });
}

onMounted(() => {
  refresh();
  timer = window.setInterval(refresh, 2000);
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
});
</script>
