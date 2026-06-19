<template>
  <component :is="route.name === 'report' ? AppLayout : 'div'">
    <div class="view-stack stagger-in report-view">
      <PageHeader
        title="Insights Report"
        eyebrow="Step 4"
        description="Executive summary, variant rankings, and exportable artifacts from the completed simulation."
      />

      <ReportLoadingSkeleton v-if="store.report.loading" />

      <EmptyState
        v-else-if="!store.simulationCompleted && !report"
        title="Run simulation first"
        message="Complete a simulation run in Step 3 to unlock the insights report."
      >
        <RouterLink class="app-button app-button--secondary" to="/process" style="margin-top: 1rem">
          Back to campaign variants
        </RouterLink>
      </EmptyState>

      <div v-else-if="!report" class="report-pregenerate">
        <AppCard title="Generate insights" eyebrow="Ready">
          <p class="lead">Your simulation finished. Generate the recommendation report to compare variants and export results.</p>
          <div class="action-row" style="margin-top: 1rem">
            <AppButton :loading="store.report.loading" @click="generateAndStay">Generate report</AppButton>
          </div>
        </AppCard>
      </div>

      <ErrorState v-if="store.report.error" :message="store.report.error" />

      <template v-if="report && !store.report.loading">
        <div
          v-if="store.simulationCompleted"
          class="flow-banner flow-banner--success report-flow-banner"
          role="status"
        >
          <strong>Simulation complete</strong>
          <span>Results aggregated from {{ report.ranked_variants?.length || 0 }} variants. Review the winning recommendation below.</span>
        </div>

        <section class="report-hero report-hero--winner" id="metrics">
          <p class="report-hero__eyebrow">Winning variant · Key metrics</p>
          <h2>{{ winner?.variant_name || report.top_recommendation?.variant_name }}</h2>
          <p class="lead report-hero__rationale">
            {{ report.top_recommendation?.rationale || report.executive_summary }}
          </p>
          <div class="report-hero__metrics report-hero__metrics--reveal">
            <div class="report-hero__metric">
              <strong>{{ winner?.engagement_rate_pct ?? "—" }}%</strong>
              <span>Engagement rate</span>
            </div>
            <div class="report-hero__metric">
              <span
                class="trend-chip"
                :class="`trend-chip--${(winner?.trend || 'flat').replace('declining', 'down')}`"
              >
                {{ winner?.trend || "flat" }}
              </span>
              <span>Trend vs. baseline</span>
            </div>
            <div class="report-hero__metric">
              <strong>{{ report.ranked_variants?.length || 0 }}</strong>
              <span>Variants compared</span>
            </div>
          </div>
        </section>

        <div class="report-layout">
          <nav class="report-nav" aria-label="Report sections">
            <a
              v-for="section in sections"
              :key="section.id"
              href="#"
              :class="{ 'is-active': activeSection === section.id }"
              @click.prevent="scrollTo(section.id)"
            >
              {{ section.label }}
            </a>
          </nav>

          <div class="view-stack report-sections">
            <AppCard id="executive" title="Executive Summary" eyebrow="Overview">
              <p class="lead">{{ report.executive_summary }}</p>
            </AppCard>

            <RecommendationSummary
              id="summary"
              class="report-recommendation-block"
              :recommendation="report.top_recommendation"
            />

            <AppCard id="rankings" title="Ranked Variants" eyebrow="Evidence">
              <RankedVariantsTable :variants="report.ranked_variants" />
            </AppCard>

            <div id="channels" class="two-column report-charts">
              <AppCard title="Engagement scores">
                <EngagementChart :variants="report.ranked_variants" />
              </AppCard>
              <AppCard title="Action breakdown">
                <ActionBreakdown :data="topResult.action_breakdown" />
              </AppCard>
            </div>

            <div id="segments" class="two-column">
              <AppCard title="Segment matrix">
                <SegmentMatrix :segments="report.segment_performance" />
              </AppCard>
              <AppCard title="Strategic recommendations">
                <ul class="recommendation-list">
                  <li v-for="item in report.strategic_recommendations" :key="item">{{ item }}</li>
                </ul>
              </AppCard>
            </div>

            <AppCard id="export" title="Export & next steps">
              <div class="export-bar">
                <AppButton variant="ghost" @click="exportJson">Export JSON</AppButton>
                <AppButton variant="ghost" @click="exportCsv">Export CSV</AppButton>
                <span class="tooltip-wrap" title="PDF export requires backend support">
                  <AppButton variant="ghost" disabled>Export PDF</AppButton>
                </span>
                <AppButton @click="store.goToStep(5)">Persona insights →</AppButton>
              </div>
            </AppCard>

            <details class="report-debug-details">
              <summary>Technical report details</summary>
              <dl class="report-debug-details__dl">
                <div>
                  <dt>Report ID</dt>
                  <dd>{{ store.reportId || report.report_id || "—" }}</dd>
                </div>
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
          </div>
        </div>
      </template>
    </div>
  </component>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import ReportLoadingSkeleton from "@/components/reports/ReportLoadingSkeleton.vue";
import RankedVariantsTable from "@/components/reports/RankedVariantsTable.vue";
import RecommendationSummary from "@/components/reports/RecommendationSummary.vue";
import EngagementChart from "@/components/reports/EngagementChart.vue";
import SegmentMatrix from "@/components/reports/SegmentMatrix.vue";
import ActionBreakdown from "@/components/simulation/ActionBreakdown.vue";
import AppLayout from "@/layouts/AppLayout.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const route = useRoute();
const store = useCampaignStore();
const activeSection = ref("executive");

const report = computed(() => store.report.data);
const winner = computed(
  () => report.value?.ranked_variants?.find((v) => v.rank === 1) || report.value?.ranked_variants?.[0],
);
const topResult = computed(() => report.value?.results?.[0] || store.simulationRun.results?.[0] || {});

const sections = [
  { id: "metrics", label: "Winner" },
  { id: "executive", label: "Executive" },
  { id: "summary", label: "Recommendation" },
  { id: "rankings", label: "Rankings" },
  { id: "channels", label: "Channels" },
  { id: "segments", label: "Segments" },
  { id: "export", label: "Export" },
];

function scrollTo(id) {
  activeSection.value = id;
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadFromRoute() {
  const id = route.params.reportId;
  if (!id || report.value) return;
  store.reportId = String(id);
  try {
    await store.loadReport(String(id));
  } catch {
    store.setNotice("Could not load report for this link.");
  }
}

async function generateAndStay() {
  await store.generateReport();
}

function download(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function exportJson() {
  download("campaignsim-report.json", JSON.stringify(report.value, null, 2), "application/json");
}

function exportCsv() {
  const rows = report.value?.ranked_variants || [];
  const header = ["rank", "variant_name", "channel", "content_format", "engagement_rate_pct", "trend"];
  const csv = [
    header.join(","),
    ...rows.map((row) => header.map((key) => JSON.stringify(row[key] ?? "")).join(",")),
  ].join("\n");
  download("campaignsim-ranked-variants.csv", csv, "text/csv");
}

onMounted(() => {
  if (route.name === "report") {
    store.currentStep = 4;
    store.persist();
  }
  loadFromRoute();
});

watch(
  () => route.params.reportId,
  () => loadFromRoute(),
);
</script>
