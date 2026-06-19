<template>
  <div ref="chart" class="mini-chart"></div>
</template>

<script setup>
import * as d3 from "d3";
import { onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
});

const chart = ref(null);

function render() {
  if (!chart.value) return;
  d3.select(chart.value).selectAll("*").remove();
  const entries = Object.entries(props.data || {});
  if (!entries.length) return;
  const width = chart.value.clientWidth || 420;
  const height = 320;
  const margin = { top: 16, right: 12, bottom: 110, left: 46 };
  const svg = d3
    .select(chart.value)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("overflow", "visible");
  const x = d3.scaleBand().domain(entries.map(([key]) => key)).range([margin.left, width - margin.right]).padding(0.22);
  const y = d3.scaleLinear().domain([0, d3.max(entries, ([, value]) => value) || 1]).nice().range([height - margin.bottom, margin.top]);
  svg
    .append("g")
    .selectAll("rect")
    .data(entries)
    .join("rect")
    .attr("x", ([key]) => x(key))
    .attr("y", ([, value]) => y(value))
    .attr("width", x.bandwidth())
    .attr("height", ([, value]) => y(0) - y(value))
    .attr("rx", 5)
    .attr("fill", "#2563eb");
  svg
    .append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickSizeOuter(0))
    .selectAll("text")
    .attr("transform", "rotate(-25)")
    .style("text-anchor", "end")
    .attr("dx", "-0.15em")
    .attr("dy", "0.7em")
    .style("font-size", "10px");
  svg.append("g").attr("transform", `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(4));
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

watch(() => props.data, render, { deep: true });
</script>
