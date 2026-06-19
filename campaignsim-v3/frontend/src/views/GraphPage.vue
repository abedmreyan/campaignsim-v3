<template>
  <AppLayout>
    <div class="kgp">

      <!-- ── Page header ──────────────────────────────────────────────── -->
      <header class="kgp__header">
        <div class="kgp__header-left">
          <p class="kgp__eyebrow">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="8" r="2.5"/><circle cx="12" cy="18" r="2.5"/>
              <path d="M8 7l4 9M16 9l-2 7"/>
            </svg>
            Knowledge Graph
          </p>
          <h1 class="kgp__title">Brand Intelligence Map</h1>
        </div>

        <div class="kgp__stats" aria-label="Graph statistics">
          <div class="kgp__stat">
            <span class="kgp__stat-val">{{ nodeCount }}</span>
            <span class="kgp__stat-lbl">entities</span>
          </div>
          <span class="kgp__stat-sep" aria-hidden="true" />
          <div class="kgp__stat">
            <span class="kgp__stat-val">{{ edgeCount }}</span>
            <span class="kgp__stat-lbl">relationships</span>
          </div>
          <span class="kgp__stat-sep" aria-hidden="true" />
          <div class="kgp__stat">
            <span class="kgp__stat-val">{{ typeCount }}</span>
            <span class="kgp__stat-lbl">entity types</span>
          </div>
        </div>

        <div class="kgp__actions">
          <RouterLink to="/process" class="app-button app-button--secondary app-button--sm">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Edit graph
          </RouterLink>
        </div>
      </header>

      <!-- ── Graph canvas ─────────────────────────────────────────────── -->
      <div class="kgp__canvas">

        <!-- Loading state -->
        <div v-if="store.graph.loading" class="kgp__loading" role="status" aria-live="polite">
          <div class="kgp__loading-ring">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="20" stroke="rgba(10,191,173,0.15)" stroke-width="3" />
              <circle cx="24" cy="24" r="20" stroke="url(#lg)" stroke-width="3"
                stroke-dasharray="62.8" stroke-dashoffset="47" stroke-linecap="round" />
              <defs>
                <linearGradient id="lg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#0ABFAD"/>
                  <stop offset="100%" stop-color="#00C97A"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <p class="kgp__loading-text">Building graph…</p>
        </div>

        <!-- Graph panel (has data) -->
        <GraphPanel
          v-else-if="hasGraph"
          :graphData="graphData"
          :showHeader="false"
          class="kgp__graph-panel"
        />

        <!-- Empty state -->
        <div v-else class="kgp__empty">
          <!-- Ghost graph illustration -->
          <svg class="kgp__empty-svg" viewBox="0 0 320 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <!-- Ghost edges -->
            <line x1="80" y1="80" x2="160" y2="50"  stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <line x1="160" y1="50" x2="240" y2="80" stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <line x1="80" y1="80" x2="100" y2="150" stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <line x1="160" y1="50" x2="160" y2="140" stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <line x1="240" y1="80" x2="220" y2="150" stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <line x1="100" y1="150" x2="160" y2="140" stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <line x1="160" y1="140" x2="220" y2="150" stroke="rgba(10,191,173,0.15)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <!-- Ghost nodes -->
            <circle cx="160" cy="50"  r="14" fill="rgba(10,191,173,0.06)" stroke="rgba(10,191,173,0.25)" stroke-width="1.5"/>
            <circle cx="80"  cy="80"  r="10" fill="rgba(10,191,173,0.04)" stroke="rgba(10,191,173,0.18)" stroke-width="1.2"/>
            <circle cx="240" cy="80"  r="10" fill="rgba(10,191,173,0.04)" stroke="rgba(10,191,173,0.18)" stroke-width="1.2"/>
            <circle cx="100" cy="150" r="8"  fill="rgba(10,191,173,0.03)" stroke="rgba(10,191,173,0.14)" stroke-width="1"/>
            <circle cx="160" cy="140" r="10" fill="rgba(10,191,173,0.04)" stroke="rgba(10,191,173,0.18)" stroke-width="1.2"/>
            <circle cx="220" cy="150" r="8"  fill="rgba(10,191,173,0.03)" stroke="rgba(10,191,173,0.14)" stroke-width="1"/>
          </svg>

          <p class="kgp__empty-title">No knowledge graph yet</p>
          <p class="kgp__empty-desc">
            Build your brand intelligence map in Step&nbsp;1 — the system extracts
            entities, relationships, and campaign context from your brief.
          </p>
          <RouterLink to="/process" class="app-button app-button--primary">
            Build knowledge graph
          </RouterLink>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup>
import { computed } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import GraphPanel from "@/components/graph/GraphPanel.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();

const graphData = computed(() => ({
  nodes: store.graph.nodes || [],
  edges: store.graph.edges || [],
}));

const hasGraph = computed(() => (store.graph.nodes?.length ?? 0) > 0);
const nodeCount = computed(() => store.graph.nodes?.length ?? 0);
const edgeCount = computed(() => store.graph.edges?.length ?? 0);

// Count distinct entity types from node labels
const typeCount = computed(() => {
  const types = new Set();
  (store.graph.nodes || []).forEach(n => {
    (n.labels || []).forEach(l => {
      if (l !== "Entity" && l !== "__Entity__") types.add(l);
    });
  });
  return types.size;
});
</script>

<style scoped>
/* ── Page shell ─────────────────────────────────────────────────────────── */
.kgp {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
  min-height: 0;
}

/* ── Header ─────────────────────────────────────────────────────────────── */
.kgp__header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 0.9rem clamp(1rem, 2.5vw, 1.75rem);
  border-bottom: 1px solid var(--glass-border);
  background:
    radial-gradient(ellipse 60% 100% at 0% 50%, rgba(10,191,173,0.07), transparent 55%),
    var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

/* Animated accent line at bottom of header */
.kgp__header::after {
  content: "";
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(10,191,173,0.6) 30%,
    rgba(0,201,122,0.8) 50%,
    rgba(10,191,173,0.6) 70%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: hdrSweep 5s ease-in-out infinite;
}
@keyframes hdrSweep {
  0%   { background-position: 100% 0; opacity: 0.7; }
  50%  { background-position: -100% 0; opacity: 1; }
  100% { background-position: 100% 0; opacity: 0.7; }
}

.kgp__header-left { flex-shrink: 0; }

.kgp__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin: 0 0 0.2rem;
}

.kgp__title {
  font-family: var(--font-display);
  font-size: clamp(1rem, 2vw, 1.25rem);
  font-weight: 800;
  letter-spacing: -0.025em;
  color: var(--color-text);
  margin: 0;
}

/* Stats group */
.kgp__stats {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
}
.kgp__stat {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: rgba(10,191,173,0.04);
}
.kgp__stat-val {
  font-size: 1rem;
  font-weight: 800;
  font-family: var(--font-display);
  color: var(--color-accent);
  letter-spacing: -0.03em;
  line-height: 1;
}
.kgp__stat-lbl {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.kgp__stat-sep {
  width: 1px;
  height: 1.5rem;
  background: var(--color-border);
  flex-shrink: 0;
}

.kgp__actions { flex-shrink: 0; }
.kgp__actions .app-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

/* ── Canvas ─────────────────────────────────────────────────────────────── */
.kgp__canvas {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  /* Remove the dotted grid from GraphPanel — the page handles background */
}

/* Make GraphPanel fill the canvas absolutely — no min-height cap */
.kgp__graph-panel {
  position: absolute;
  inset: 0;
  width: 100% !important;
  height: 100% !important;
  min-height: 0 !important;
}

/* ── Loading ────────────────────────────────────────────────────────────── */
.kgp__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 1rem;
}
.kgp__loading-ring {
  animation: spin 1.4s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.kgp__loading-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted);
}

/* ── Empty state ────────────────────────────────────────────────────────── */
.kgp__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 1rem;
  text-align: center;
  padding: 2rem;
}
.kgp__empty-svg {
  width: 320px;
  max-width: 80%;
  opacity: 0.7;
  animation: emptyFloat 5s ease-in-out infinite;
}
@keyframes emptyFloat {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-8px); }
}
.kgp__empty-title {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.kgp__empty-desc {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  max-width: 40ch;
  line-height: 1.6;
  margin: 0 0 0.5rem;
}
</style>
