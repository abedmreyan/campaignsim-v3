<template>
  <div ref="chart" class="chart-panel"></div>
</template>

<script setup>
import * as d3 from "d3";
import { onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps({
  variants: {
    type: Array,
    default: () => [],
  },
});

const chart = ref(null);

function render() {
  if (!chart.value) return;
  d3.select(chart.value).selectAll("*").remove();
  const data = props.variants || [];
  if (!data.length) return;
  const width = chart.value.clientWidth || 600;
  const height = 320;
  const margin = { top: 24, right: 20, bottom: 110, left: 48 };
  const svg = d3
    .select(chart.value)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("overflow", "visible");
  const x = d3.scaleBand().domain(data.map((item) => item.variant_name)).range([margin.left, width - margin.right]).padding(0.28);
  const y = d3.scaleLinear().domain([0, Math.max(50, d3.max(data, (item) => item.engagement_rate_pct) || 0)]).nice().range([height - margin.bottom, margin.top]);

  svg
    .append("g")
    .selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", (item) => x(item.variant_name))
    .attr("y", (item) => y(item.engagement_rate_pct))
    .attr("width", x.bandwidth())
    .attr("height", (item) => y(0) - y(item.engagement_rate_pct))
    .attr("rx", 6)
    .attr("fill", (item, index) => (index === 0 ? "#059669" : "#2563eb"));

  svg
    .append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickSizeOuter(0))
    .selectAll("text")
    .attr("transform", "rotate(-18)")
    .style("text-anchor", "end")
    .attr("dx", "-0.15em")
    .attr("dy", "0.65em")
    .style("font-size", "11px");

  svg.append("g").attr("transform", `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5));
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
