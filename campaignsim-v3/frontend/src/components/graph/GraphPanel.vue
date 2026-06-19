<template>
  <div class="graph-panel">
    <div v-if="showHeader" class="panel-header">
      <span class="panel-title">Knowledge Graph</span>
      <div class="header-tools">
        <button class="tool-btn" @click="$emit('refresh')" :disabled="loading" title="Refresh graph">
          <span class="icon-refresh" :class="{ spinning: loading }">↻</span>
          <span class="btn-text">Refresh</span>
        </button>
      </div>
    </div>

    <div class="graph-container" ref="graphContainer">
      <!-- Graph view -->
      <div v-if="resolvedNodes.length" class="graph-view">
        <svg ref="graphSvg" class="graph-svg"></svg>

        <!-- Detail panel -->
        <div v-if="selectedItem" class="detail-panel">
          <div class="detail-panel-header">
            <span class="detail-title">{{ selectedItem.type === "node" ? "Node Details" : "Relationship" }}</span>
            <span
              v-if="selectedItem.type === 'node'"
              class="detail-type-badge"
              :style="{ background: selectedItem.color, color: '#fff' }"
            >
              {{ selectedItem.entityType }}
            </span>
            <button class="detail-close" @click="closeDetailPanel">×</button>
          </div>

          <!-- Node detail -->
          <div v-if="selectedItem.type === 'node'" class="detail-content">
            <div class="detail-row">
              <span class="detail-label">Name:</span>
              <span class="detail-value">{{ selectedItem.data.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">UUID:</span>
              <span class="detail-value uuid-text">{{ selectedItem.data.uuid || selectedItem.data.id }}</span>
            </div>
            <div class="detail-row" v-if="selectedItem.data.created_at">
              <span class="detail-label">Created:</span>
              <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
            </div>
            <div
              class="detail-section"
              v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0"
            >
              <div class="section-title">Properties:</div>
              <div class="properties-list">
                <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                  <span class="property-key">{{ key }}:</span>
                  <span class="property-value">{{ value || "None" }}</span>
                </div>
              </div>
            </div>
            <div class="detail-section" v-if="selectedItem.data.summary">
              <div class="section-title">Summary:</div>
              <div class="summary-text">{{ selectedItem.data.summary }}</div>
            </div>
            <div
              class="detail-section"
              v-if="selectedItem.data.labels && selectedItem.data.labels.length > 0"
            >
              <div class="section-title">Labels:</div>
              <div class="labels-list">
                <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">
                  {{ label }}
                </span>
              </div>
            </div>
          </div>

          <!-- Edge detail -->
          <div v-else class="detail-content">
            <template v-if="selectedItem.data.isSelfLoopGroup">
              <div class="edge-relation-header self-loop-header">
                {{ selectedItem.data.source_name }} — Self Relations
                <span class="self-loop-count">{{ selectedItem.data.selfLoopCount }} items</span>
              </div>
              <div class="self-loop-list">
                <div
                  v-for="(loop, idx) in selectedItem.data.selfLoopEdges"
                  :key="loop.uuid || idx"
                  class="self-loop-item"
                  :class="{ expanded: expandedSelfLoops.has(loop.uuid || idx) }"
                >
                  <div class="self-loop-item-header" @click="toggleSelfLoop(loop.uuid || idx)">
                    <span class="self-loop-index">#{{ idx + 1 }}</span>
                    <span class="self-loop-name">{{ loop.name || loop.fact_type || "RELATED" }}</span>
                    <span class="self-loop-toggle">{{ expandedSelfLoops.has(loop.uuid || idx) ? "−" : "+" }}</span>
                  </div>
                  <div class="self-loop-item-content" v-show="expandedSelfLoops.has(loop.uuid || idx)">
                    <div class="detail-row" v-if="loop.uuid">
                      <span class="detail-label">UUID:</span>
                      <span class="detail-value uuid-text">{{ loop.uuid }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact">
                      <span class="detail-label">Fact:</span>
                      <span class="detail-value fact-text">{{ loop.fact }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact_type">
                      <span class="detail-label">Type:</span>
                      <span class="detail-value">{{ loop.fact_type }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.created_at">
                      <span class="detail-label">Created:</span>
                      <span class="detail-value">{{ formatDateTime(loop.created_at) }}</span>
                    </div>
                    <div v-if="loop.episodes && loop.episodes.length > 0" class="self-loop-episodes">
                      <span class="detail-label">Episodes:</span>
                      <div class="episodes-list compact">
                        <span v-for="ep in loop.episodes" :key="ep" class="episode-tag small">{{ ep }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="edge-relation-header">
                {{ selectedItem.data.source_name }} → {{ selectedItem.data.name || "RELATED_TO" }} →
                {{ selectedItem.data.target_name }}
              </div>
              <div class="detail-row">
                <span class="detail-label">UUID:</span>
                <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Label:</span>
                <span class="detail-value">{{ selectedItem.data.name || "RELATED_TO" }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Type:</span>
                <span class="detail-value">{{ selectedItem.data.fact_type || "Unknown" }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.fact">
                <span class="detail-label">Fact:</span>
                <span class="detail-value fact-text">{{ selectedItem.data.fact }}</span>
              </div>
              <div
                class="detail-section"
                v-if="selectedItem.data.episodes && selectedItem.data.episodes.length > 0"
              >
                <div class="section-title">Episodes:</div>
                <div class="episodes-list">
                  <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">{{ ep }}</span>
                </div>
              </div>
              <div class="detail-row" v-if="selectedItem.data.created_at">
                <span class="detail-label">Created:</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Loading state -->
      <div v-else-if="loading" class="graph-state">
        <div class="loading-spinner"></div>
        <p>Loading graph data…</p>
      </div>

      <!-- Empty state -->
      <div v-else class="graph-state">
        <div class="empty-icon">❖</div>
        <p class="empty-text">Waiting for knowledge graph…</p>
      </div>
    </div>

    <!-- Bottom bar: legend + edge-labels toggle in one compact strip -->
    <div v-if="resolvedNodes.length" class="graph-bottom-bar">
      <div v-if="entityTypes.length" class="legend-inline">
        <span
          v-for="type in entityTypes"
          :key="type.name"
          class="legend-chip"
          :title="type.name + ' (' + type.count + ')'"
        >
          <span class="legend-dot" :style="{ background: type.color }"></span>
          <span class="legend-label">{{ type.name }}</span>
        </span>
      </div>
      <label class="toggle-pill">
        <input type="checkbox" v-model="showEdgeLabels" />
        <span class="toggle-track">
          <span class="toggle-thumb"></span>
        </span>
        <span class="toggle-label">Labels</span>
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import * as d3 from "d3";

const props = defineProps({
  // Option A: flat arrays (Step1GraphBuild)
  nodes: { type: Array, default: null },
  edges: { type: Array, default: null },
  // Option B: graphData object (GraphPage)
  graphData: { type: Object, default: null },
  // Common
  loading: { type: Boolean, default: false },
  currentPhase: { type: Number, default: 0 },
  isSimulating: { type: Boolean, default: false },
  // Hide the internal "Knowledge Graph" header when the parent provides its own
  showHeader: { type: Boolean, default: true },
});

const emit = defineEmits(["refresh", "toggle-maximize", "select-node"]);

// Resolve props to a unified format
const resolvedNodes = computed(() => props.nodes ?? props.graphData?.nodes ?? []);
const resolvedEdges = computed(() => props.edges ?? props.graphData?.edges ?? []);

const graphContainer = ref(null);
const graphSvg = ref(null);
const selectedItem = ref(null);
const showEdgeLabels = ref(true);
const expandedSelfLoops = ref(new Set());

let currentSimulation = null;
let linkLabelsRef = null;
let linkLabelBgRef = null;

const SEMANTIC_COLORS = {
  Brand: "#3B82F6",
  CustomerPersona: "#10B981",
  MarketingChannel: "#F59E0B",
  Competitor: "#EF4444",
  ContentFormat: "#8B5CF6",
  Campaign: "#06B6D4",
  Person: "#6B7280",
  Product: "#F97316",
};
const FALLBACK_COLORS = ["#FF6B35", "#004E89", "#7B2D8E", "#1A936F", "#C5283D", "#E9724C"];

const entityTypes = computed(() => {
  const typeMap = {};
  let fallbackIdx = 0;
  resolvedNodes.value.forEach((node) => {
    const type = node.type || node.labels?.find((l) => l !== "Entity" && l !== "__Entity__") || "Entity";
    if (!typeMap[type]) {
      const color = SEMANTIC_COLORS[type] || FALLBACK_COLORS[fallbackIdx++ % FALLBACK_COLORS.length];
      typeMap[type] = { name: type, count: 0, color };
    }
    typeMap[type].count++;
  });
  return Object.values(typeMap);
});

const colorMap = computed(() => {
  const map = {};
  entityTypes.value.forEach((t) => (map[t.name] = t.color));
  return map;
});

const getColor = (type) => colorMap.value[type] || "#999";

const getNodeType = (node) =>
  node.type || node.labels?.find((l) => l !== "Entity" && l !== "__Entity__") || "Entity";

const formatDateTime = (dateStr) => {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return dateStr;
  }
};

const closeDetailPanel = () => {
  selectedItem.value = null;
  expandedSelfLoops.value = new Set();
};

const toggleSelfLoop = (id) => {
  const s = new Set(expandedSelfLoops.value);
  s.has(id) ? s.delete(id) : s.add(id);
  expandedSelfLoops.value = s;
};

const renderGraph = () => {
  if (!graphSvg.value || !resolvedNodes.value.length) return;

  if (currentSimulation) currentSimulation.stop();

  const container = graphContainer.value;
  const width = container.clientWidth || 800;
  const height = container.clientHeight || 500;

  const svg = d3
    .select(graphSvg.value)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", `0 0 ${width} ${height}`);

  svg.selectAll("*").remove();

  const nodesData = resolvedNodes.value;
  const edgesData = resolvedEdges.value;

  if (!nodesData.length) return;

  // Normalise: handle both real-API format (uuid/name/labels[]) and mock format (id/label/type)
  const getNodeId = (n) => n.uuid || n.id || "";
  const getNodeName = (n) => n.name || n.label || "Unnamed";

  // Build node map keyed by id
  const nodeMap = {};
  nodesData.forEach((n) => (nodeMap[getNodeId(n)] = n));

  const nodes = nodesData.map((n) => ({
    id: getNodeId(n),
    name: getNodeName(n),
    type: getNodeType(n),
    rawData: n,
  }));

  const nodeIds = new Set(nodes.map((n) => n.id));

  // Normalise edge endpoints: handle real-API (source_node_uuid/target_node_uuid) and mock (source/target)
  const getEdgeSrc = (e) => e.source_node_uuid || (typeof e.source === "object" ? e.source?.id : e.source) || "";
  const getEdgeTgt = (e) => e.target_node_uuid || (typeof e.target === "object" ? e.target?.id : e.target) || "";

  // Separate self-loops and multi-edges
  const edgePairCount = {};
  const selfLoopEdges = {};

  const tempEdges = edgesData.filter(
    (e) => nodeIds.has(getEdgeSrc(e)) && nodeIds.has(getEdgeTgt(e)),
  );

  tempEdges.forEach((e) => {
    const src = getEdgeSrc(e);
    const tgt = getEdgeTgt(e);
    if (src === tgt) {
      if (!selfLoopEdges[src]) selfLoopEdges[src] = [];
      selfLoopEdges[src].push({
        ...e,
        source_name: getNodeName(nodeMap[src]),
        target_name: getNodeName(nodeMap[tgt]),
      });
    } else {
      const pairKey = [src, tgt].sort().join("_");
      edgePairCount[pairKey] = (edgePairCount[pairKey] || 0) + 1;
    }
  });

  const edgePairIndex = {};
  const processedSelfLoopNodes = new Set();
  const edges = [];

  tempEdges.forEach((e) => {
    const src = getEdgeSrc(e);
    const tgt = getEdgeTgt(e);
    const isSelfLoop = src === tgt;

    if (isSelfLoop) {
      if (processedSelfLoopNodes.has(src)) return;
      processedSelfLoopNodes.add(src);
      const allSelfLoops = selfLoopEdges[src];
      const nodeName = getNodeName(nodeMap[src]) || "Unknown";
      edges.push({
        source: src,
        target: tgt,
        type: "SELF_LOOP",
        name: `Self Relations (${allSelfLoops.length})`,
        curvature: 0,
        isSelfLoop: true,
        rawData: {
          isSelfLoopGroup: true,
          source_name: nodeName,
          target_name: nodeName,
          selfLoopCount: allSelfLoops.length,
          selfLoopEdges: allSelfLoops,
        },
      });
      return;
    }

    const pairKey = [src, tgt].sort().join("_");
    const totalCount = edgePairCount[pairKey];
    const currentIndex = edgePairIndex[pairKey] || 0;
    edgePairIndex[pairKey] = currentIndex + 1;

    const isReversed = src > tgt;
    let curvature = 0;
    if (totalCount > 1) {
      const curvatureRange = Math.min(1.2, 0.6 + totalCount * 0.15);
      curvature = ((currentIndex / (totalCount - 1)) - 0.5) * curvatureRange * 2;
      if (isReversed) curvature = -curvature;
    }

    edges.push({
      source: src,
      target: tgt,
      type: e.fact_type || e.type || e.name || "RELATED",
      name: e.name || e.fact_type || e.type || "RELATED",
      curvature,
      isSelfLoop: false,
      pairIndex: currentIndex,
      pairTotal: totalCount,
      rawData: {
        ...e,
        source_name: getNodeName(nodeMap[src]),
        target_name: getNodeName(nodeMap[tgt]),
      },
    });
  });

  // Degree-based node sizes
  const degreeMap = {};
  nodes.forEach((n) => (degreeMap[n.id] = 0));
  edges.forEach((e) => {
    const src = typeof e.source === "object" ? e.source.id : e.source;
    const tgt = typeof e.target === "object" ? e.target.id : e.target;
    if (src !== tgt) {
      degreeMap[src] = (degreeMap[src] || 0) + 1;
      degreeMap[tgt] = (degreeMap[tgt] || 0) + 1;
    }
  });
  const maxDegree = Math.max(1, ...Object.values(degreeMap));
  const getNodeRadius = (id) => 7 + Math.round(((degreeMap[id] || 0) / maxDegree) * 10);

  // Force simulation
  const simulation = d3
    .forceSimulation(nodes)
    .force(
      "link",
      d3
        .forceLink(edges)
        .id((d) => d.id)
        .distance((d) => 150 + ((d.pairTotal || 1) - 1) * 50),
    )
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(50))
    .force("x", d3.forceX(width / 2).strength(0.04))
    .force("y", d3.forceY(height / 2).strength(0.04));

  currentSimulation = simulation;

  const g = svg.append("g");

  svg.call(
    d3
      .zoom()
      .extent([
        [0, 0],
        [width, height],
      ])
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => g.attr("transform", event.transform)),
  );

  // Path helpers
  const getLinkPath = (d) => {
    const sx = d.source.x,
      sy = d.source.y;
    const tx = d.target.x,
      ty = d.target.y;

    if (d.isSelfLoop) {
      const r = 30;
      return `M${sx + 8},${sy - 4} A${r},${r} 0 1,1 ${sx + 8},${sy + 4}`;
    }
    if (d.curvature === 0) return `M${sx},${sy} L${tx},${ty}`;

    const dx = tx - sx,
      dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offsetRatio = 0.25 + (d.pairTotal || 1) * 0.05;
    const baseOffset = Math.max(35, dist * offsetRatio);
    const cx = (sx + tx) / 2 + (-dy / dist) * d.curvature * baseOffset;
    const cy = (sy + ty) / 2 + (dx / dist) * d.curvature * baseOffset;
    return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`;
  };

  const getLinkMidpoint = (d) => {
    const sx = d.source.x,
      sy = d.source.y;
    const tx = d.target.x,
      ty = d.target.y;

    if (d.isSelfLoop) return { x: sx + 70, y: sy };
    if (d.curvature === 0) return { x: (sx + tx) / 2, y: (sy + ty) / 2 };

    const dx = tx - sx,
      dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offsetRatio = 0.25 + (d.pairTotal || 1) * 0.05;
    const baseOffset = Math.max(35, dist * offsetRatio);
    const cx = (sx + tx) / 2 + (-dy / dist) * d.curvature * baseOffset;
    const cy = (sy + ty) / 2 + (dx / dist) * d.curvature * baseOffset;
    return {
      x: 0.25 * sx + 0.5 * cx + 0.25 * tx,
      y: 0.25 * sy + 0.5 * cy + 0.25 * ty,
    };
  };

  // Links
  const linkGroup = g.append("g").attr("class", "links");

  const link = linkGroup
    .selectAll("path")
    .data(edges)
    .enter()
    .append("path")
    .attr("stroke", "#C0C0C0")
    .attr("stroke-width", 1.5)
    .attr("fill", "none")
    .style("cursor", "pointer")
    .on("click", (event, d) => {
      event.stopPropagation();
      linkGroup.selectAll("path").attr("stroke", "#C0C0C0").attr("stroke-width", 1.5);
      linkLabelBg.attr("fill", "rgba(255,255,255,0.95)");
      linkLabels.attr("fill", "#666");
      d3.select(event.target).attr("stroke", "#3498db").attr("stroke-width", 3);
      selectedItem.value = { type: "edge", data: d.rawData };
    });

  const linkLabelBg = linkGroup
    .selectAll("rect")
    .data(edges)
    .enter()
    .append("rect")
    .attr("fill", "rgba(255,255,255,0.95)")
    .attr("rx", 3)
    .attr("ry", 3)
    .style("cursor", "pointer")
    .style("pointer-events", "all")
    .style("display", showEdgeLabels.value ? "block" : "none")
    .on("click", (event, d) => {
      event.stopPropagation();
      linkGroup.selectAll("path").attr("stroke", "#C0C0C0").attr("stroke-width", 1.5);
      linkLabelBg.attr("fill", "rgba(255,255,255,0.95)");
      linkLabels.attr("fill", "#666");
      link.filter((l) => l === d).attr("stroke", "#3498db").attr("stroke-width", 3);
      d3.select(event.target).attr("fill", "rgba(52,152,219,0.1)");
      selectedItem.value = { type: "edge", data: d.rawData };
    });

  const linkLabels = linkGroup
    .selectAll("text")
    .data(edges)
    .enter()
    .append("text")
    .text((d) => d.name)
    .attr("font-size", "9px")
    .attr("fill", "#666")
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .style("cursor", "pointer")
    .style("pointer-events", "all")
    .style("font-family", "system-ui, sans-serif")
    .style("display", showEdgeLabels.value ? "block" : "none")
    .on("click", (event, d) => {
      event.stopPropagation();
      linkGroup.selectAll("path").attr("stroke", "#C0C0C0").attr("stroke-width", 1.5);
      linkLabelBg.attr("fill", "rgba(255,255,255,0.95)");
      linkLabels.attr("fill", "#666");
      link.filter((l) => l === d).attr("stroke", "#3498db").attr("stroke-width", 3);
      d3.select(event.target).attr("fill", "#3498db");
      selectedItem.value = { type: "edge", data: d.rawData };
    });

  linkLabelsRef = linkLabels;
  linkLabelBgRef = linkLabelBg;

  // Nodes
  const nodeGroup = g.append("g").attr("class", "nodes");

  const node = nodeGroup
    .selectAll("circle")
    .data(nodes)
    .enter()
    .append("circle")
    .attr("r", (d) => getNodeRadius(d.id))
    .attr("fill", (d) => getColor(d.type))
    .attr("stroke", "#fff")
    .attr("stroke-width", 2.5)
    .style("cursor", "pointer")
    .call(
      d3
        .drag()
        .on("start", (event, d) => {
          d.fx = d.x;
          d.fy = d.y;
          d._dragStartX = event.x;
          d._dragStartY = event.y;
          d._isDragging = false;
        })
        .on("drag", (event, d) => {
          const dx = event.x - d._dragStartX;
          const dy = event.y - d._dragStartY;
          if (!d._isDragging && Math.sqrt(dx * dx + dy * dy) > 3) {
            d._isDragging = true;
            simulation.alphaTarget(0.3).restart();
          }
          if (d._isDragging) {
            d.fx = event.x;
            d.fy = event.y;
          }
        })
        .on("end", (event, d) => {
          if (d._isDragging) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
          d._isDragging = false;
        }),
    )
    .on("click", (event, d) => {
      event.stopPropagation();
      node.attr("stroke", "#fff").attr("stroke-width", 2.5);
      linkGroup.selectAll("path").attr("stroke", "#C0C0C0").attr("stroke-width", 1.5);
      d3.select(event.target).attr("stroke", "#E91E63").attr("stroke-width", 4);
      link
        .filter((l) => l.source.id === d.id || l.target.id === d.id)
        .attr("stroke", "#E91E63")
        .attr("stroke-width", 2.5);
      selectedItem.value = { type: "node", data: d.rawData, entityType: d.type, color: getColor(d.type) };
      emit("select-node", d.rawData);
    })
    .on("mouseenter", (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).attr("stroke", "#333").attr("stroke-width", 3);
      }
    })
    .on("mouseleave", (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).attr("stroke", "#fff").attr("stroke-width", 2.5);
      }
    });

  // Node labels
  nodeGroup
    .selectAll("text")
    .data(nodes)
    .enter()
    .append("text")
    .text((d) => (d.name.length > 10 ? d.name.substring(0, 10) + "…" : d.name))
    .attr("font-size", "11px")
    .attr("fill", "#333")
    .attr("font-weight", "500")
    .attr("dx", 14)
    .attr("dy", 4)
    .style("pointer-events", "none")
    .style("font-family", "system-ui, sans-serif");

  // Tick
  simulation.on("tick", () => {
    link.attr("d", (d) => getLinkPath(d));

    linkLabels.each(function (d) {
      const mid = getLinkMidpoint(d);
      d3.select(this).attr("x", mid.x).attr("y", mid.y).attr("transform", "");
    });

    linkLabelBg.each(function (d, i) {
      const mid = getLinkMidpoint(d);
      const textEl = linkLabels.nodes()[i];
      try {
        const bbox = textEl.getBBox();
        d3.select(this)
          .attr("x", mid.x - bbox.width / 2 - 4)
          .attr("y", mid.y - bbox.height / 2 - 2)
          .attr("width", bbox.width + 8)
          .attr("height", bbox.height + 4)
          .attr("transform", "");
      } catch {
        // getBBox can fail in hidden elements
      }
    });

    node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

    nodeGroup
      .selectAll("text")
      .attr("x", (d) => d.x)
      .attr("y", (d) => d.y);
  });

  // Click on background deselects
  svg.on("click", () => {
    selectedItem.value = null;
    node.attr("stroke", "#fff").attr("stroke-width", 2.5);
    linkGroup.selectAll("path").attr("stroke", "#C0C0C0").attr("stroke-width", 1.5);
    linkLabelBg.attr("fill", "rgba(255,255,255,0.95)");
    linkLabels.attr("fill", "#666");
  });
};

watch(
  () => [resolvedNodes.value, resolvedEdges.value],
  () => nextTick(renderGraph),
  { deep: true },
);

watch(showEdgeLabels, (val) => {
  if (linkLabelsRef) linkLabelsRef.style("display", val ? "block" : "none");
  if (linkLabelBgRef) linkLabelBgRef.style("display", val ? "block" : "none");
});

const handleResize = () => nextTick(renderGraph);

onMounted(() => {
  window.addEventListener("resize", handleResize);
  nextTick(renderGraph);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  if (currentSimulation) currentSimulation.stop();
});
</script>

<style scoped>
.graph-panel {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #fafafa;
  background-image: radial-gradient(#d0d0d0 1.5px, transparent 1.5px);
  background-size: 24px 24px;
  overflow: hidden;
  /* min-height is intentionally absent here — the parent .s1-graph-panel__canvas
     or the absolute inset on GraphPage controls the height */
}

.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 14px 18px;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0));
  pointer-events: none;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  pointer-events: auto;
}

.header-tools {
  pointer-events: auto;
  display: flex;
  gap: 8px;
}

.tool-btn {
  height: 30px;
  padding: 0 10px;
  border: 1px solid #e0e0e0;
  background: #fff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  font-size: 12px;
}

.tool-btn:hover {
  background: #f5f5f5;
  color: #000;
}

.tool-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.btn-text {
  font-size: 11px;
}

.graph-container {
  width: 100%;
  height: 100%;
}

.graph-view {
  width: 100%;
  height: 100%;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
  /* Let nodes render beyond the SVG viewport — the panel clips at its own edge */
  overflow: visible;
}

.graph-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.2;
}

.empty-text {
  font-size: 14px;
}

/* ── Compact bottom bar ─────────────────────────────────────────────────── */
.graph-bottom-bar {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.07);
  border-radius: 999px;
  padding: 5px 10px 5px 12px;
  z-index: 10;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  pointer-events: auto;
  flex-wrap: wrap;
  min-height: 32px;
}

/* Legend chips — inline, scrollable on overflow */
.legend-inline {
  display: flex;
  align-items: center;
  gap: 4px 10px;
  flex: 1;
  flex-wrap: wrap;
  overflow: hidden;
}

.legend-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: default;
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  font-size: 10.5px;
  color: #555;
  white-space: nowrap;
  font-family: system-ui, sans-serif;
}

/* Toggle pill */
.toggle-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;
}

.toggle-pill input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.toggle-track {
  position: relative;
  display: inline-block;
  width: 28px;
  height: 16px;
  background: #d0d0d0;
  border-radius: 999px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle-pill input:checked ~ .toggle-track {
  background: #6366f1;
}

.toggle-pill input:checked ~ .toggle-track .toggle-thumb {
  transform: translateX(12px);
}

.toggle-pill .toggle-label {
  font-size: 10.5px;
  color: #666;
  white-space: nowrap;
}

/* Detail panel */
.detail-panel {
  position: absolute;
  top: 52px;
  right: 16px;
  width: 300px;
  max-height: calc(100% - 80px);
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  font-size: 13px;
  z-index: 20;
  display: flex;
  flex-direction: column;
}

.detail-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: #fafafa;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.detail-title {
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.detail-type-badge {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 500;
  margin-left: auto;
  margin-right: 10px;
}

.detail-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 0;
  transition: color 0.2s;
}

.detail-close:hover {
  color: #333;
}

.detail-content {
  padding: 14px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  margin-bottom: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-label {
  color: #888;
  font-size: 11px;
  font-weight: 500;
  min-width: 70px;
}

.detail-value {
  color: #333;
  flex: 1;
  word-break: break-word;
  font-size: 12px;
}

.detail-value.uuid-text {
  font-family: monospace;
  font-size: 10px;
  color: #666;
}

.detail-value.fact-text {
  line-height: 1.5;
  color: #444;
}

.detail-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.properties-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.property-item {
  display: flex;
  gap: 6px;
}

.property-key {
  color: #888;
  font-weight: 500;
  min-width: 80px;
  font-size: 11px;
}

.property-value {
  color: #333;
  flex: 1;
  font-size: 11px;
}

.summary-text {
  line-height: 1.6;
  color: #444;
  font-size: 11px;
}

.labels-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.label-tag {
  padding: 3px 10px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  font-size: 10px;
  color: #555;
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.episode-tag {
  display: inline-block;
  padding: 4px 8px;
  background: #f8f8f8;
  border: 1px solid #e8e8e8;
  border-radius: 5px;
  font-family: monospace;
  font-size: 10px;
  color: #666;
  word-break: break-all;
}

.edge-relation-header {
  background: #f8f8f8;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 12px;
  font-weight: 500;
  color: #333;
  line-height: 1.5;
  word-break: break-word;
}

.self-loop-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
  border: 1px solid #c8e6c9;
}

.self-loop-count {
  margin-left: auto;
  font-size: 10px;
  color: #666;
  background: rgba(255, 255, 255, 0.8);
  padding: 2px 6px;
  border-radius: 8px;
}

.self-loop-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.self-loop-item {
  background: #fafafa;
  border: 1px solid #eaeaea;
  border-radius: 6px;
}

.self-loop-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: #f5f5f5;
  cursor: pointer;
  transition: background 0.2s;
}

.self-loop-item-header:hover {
  background: #eee;
}

.self-loop-item.expanded .self-loop-item-header {
  background: #e8e8e8;
}

.self-loop-index {
  font-size: 9px;
  font-weight: 600;
  color: #888;
  background: #e0e0e0;
  padding: 1px 5px;
  border-radius: 3px;
}

.self-loop-name {
  font-size: 11px;
  font-weight: 500;
  color: #333;
  flex: 1;
}

.self-loop-toggle {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #888;
  background: #e0e0e0;
  border-radius: 3px;
}

.self-loop-item-content {
  padding: 10px;
  border-top: 1px solid #eaeaea;
}

.self-loop-episodes {
  margin-top: 6px;
}

.episodes-list.compact {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 3px;
}

.episode-tag.small {
  padding: 2px 5px;
  font-size: 9px;
}

/* Loading spinner */
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 14px;
}
</style>
