<template>
  <div class="per-round-chart">
    <div v-if="series.length > 1" class="per-round-chart__legend" role="list">
      <span
        v-for="(s, i) in series"
        :key="s.variant_id"
        class="per-round-chart__legend-item"
        role="listitem"
      >
        <span class="per-round-chart__swatch" :style="{ background: seriesColor(i) }" aria-hidden="true" />
        {{ s.variant_name }}
      </span>
    </div>
    <div class="per-round-chart__surface">
      <div ref="chart" class="chart-panel" role="img" :aria-label="chartLabel"></div>
      <div ref="tooltip" class="per-round-chart__tooltip" aria-hidden="true"></div>
    </div>
  </div>
</template>

<script setup>
import * as d3 from "d3";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps({
  // [{ variant_id, variant_name, per_round_engagement: [n, n, ...] }, ...]
  variants: {
    type: Array,
    default: () => [],
  },
});

// Validated dark-surface categorical palette (fixed order — see dataviz skill).
// CVD separation sits in the 8-12 floor band, which requires direct labels —
// the legend above and axis labels satisfy that.
const PALETTE = ["#3987e5", "#199e70", "#c98500", "#008300", "#9085e9", "#e66767", "#d55181", "#d95926"];

function seriesColor(i) {
  return PALETTE[i % PALETTE.length];
}

const series = computed(() =>
  (props.variants || []).filter((v) => Array.isArray(v.per_round_engagement) && v.per_round_engagement.length > 0),
);

const chartLabel = computed(() => `Engagement per round across ${series.value.length} variant(s)`);

const chart = ref(null);
const tooltip = ref(null);

function render() {
  if (!chart.value) return;
  d3.select(chart.value).selectAll("*").remove();

  const data = series.value;
  if (!data.length) return;

  const width = chart.value.clientWidth || 600;
  const height = 280;
  const margin = { top: 20, right: 20, bottom: 36, left: 48 };

  const maxRounds = Math.max(...data.map((s) => s.per_round_engagement.length));
  const maxScore = Math.max(0.01, ...data.flatMap((s) => s.per_round_engagement));

  const x = d3.scaleLinear().domain([1, maxRounds]).range([margin.left, width - margin.right]);
  const y = d3.scaleLinear().domain([0, maxScore]).nice().range([height - margin.bottom, margin.top]);

  const svg = d3
    .select(chart.value)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("overflow", "visible");

  svg
    .append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(Math.min(maxRounds, 10)).tickFormat(d3.format("d")))
    .selectAll("text")
    .style("font-size", "11px");

  svg.append("g").attr("transform", `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5)).selectAll("text").style("font-size", "11px");

  const line = d3
    .line()
    .x((_, i) => x(i + 1))
    .y((d) => y(d))
    .curve(d3.curveMonotoneX);

  const tip = d3.select(tooltip.value);

  data.forEach((s, seriesIndex) => {
    const color = seriesColor(seriesIndex);

    svg
      .append("path")
      .datum(s.per_round_engagement)
      .attr("fill", "none")
      .attr("stroke", color)
      .attr("stroke-width", 2)
      .attr("d", line);

    svg
      .selectAll(`.dot-${seriesIndex}`)
      .data(s.per_round_engagement)
      .join("circle")
      .attr("class", `dot-${seriesIndex}`)
      .attr("cx", (_, i) => x(i + 1))
      .attr("cy", (d) => y(d))
      .attr("r", 4)
      .attr("fill", color)
      .style("cursor", "pointer")
      .on("mouseenter", function (event, d) {
        const i = s.per_round_engagement.indexOf(d);
        tip
          .style("opacity", 1)
          .html(`<strong>${s.variant_name}</strong><br/>Round ${i + 1}: ${d.toFixed(3)}`);
      })
      .on("mousemove", (event) => {
        const bounds = chart.value.getBoundingClientRect();
        tip.style("left", `${event.clientX - bounds.left + 12}px`).style("top", `${event.clientY - bounds.top - 8}px`);
      })
      .on("mouseleave", () => tip.style("opacity", 0));
  });
}

let resizeObserver;

onMounted(() => {
  render();
  if (typeof ResizeObserver !== "undefined" && chart.value) {
    resizeObserver = new ResizeObserver(() => render());
    resizeObserver.observe(chart.value);
  }
});

onUnmounted(() => {
  resizeObserver?.disconnect();
});

watch(() => props.variants, render, { deep: true });
</script>

<style scoped>
.per-round-chart {
  position: relative;
}

.per-round-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
  margin-bottom: 0.75rem;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.per-round-chart__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.per-round-chart__swatch {
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 2px;
  flex-shrink: 0;
}

.per-round-chart__surface {
  position: relative;
}

.per-round-chart__tooltip {
  position: absolute;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.1s ease;
  background: var(--color-bg-elevated, #0c1919);
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-sm, 6px);
  padding: 0.45rem 0.65rem;
  font-size: 0.75rem;
  line-height: 1.4;
  color: var(--color-text, #fff);
  white-space: nowrap;
  z-index: 5;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
}
</style>
