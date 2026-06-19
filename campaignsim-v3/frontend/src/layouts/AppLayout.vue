<template>
  <div
    class="app-shell"
    :class="{ 'app-shell--expanded': sidebarExpanded }"
    :data-step="store.currentStep"
    :data-status="store.shellAmbientStatus"
    :data-page="currentPage"
  >
    <!-- ── Left Sidebar ──────────────────────────────────────────────── -->
    <aside class="app-sidebar">
      <!-- Brand -->
      <div class="sidebar__brand">
        <RouterLink to="/" class="sidebar__logo-link">
          <span class="sidebar__logo-mark">CS</span>
          <span class="sidebar__logo-text">CampaignSim</span>
        </RouterLink>
      </div>

      <!-- Collapse toggle -->
      <button
        class="sidebar__collapse-btn"
        :title="sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'"
        :aria-label="sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'"
        @click="sidebarExpanded = !sidebarExpanded"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path
            :d="sidebarExpanded ? 'M8 2L4 6L8 10' : 'M4 2L8 6L4 10'"
            stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
          />
        </svg>
      </button>

      <!-- Primary navigation -->
      <nav class="sidebar__nav" aria-label="Main navigation">
        <RouterLink to="/" class="sidebar__item" exact-active-class="sidebar__item--active">
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M3 12L12 3L21 12V21H15V15H9V21H3V12Z"/>
          </svg>
          <span class="sidebar__label">Home</span>
        </RouterLink>

        <RouterLink
          to="/process"
          class="sidebar__item"
          :class="{ 'sidebar__item--active': isWorkflowActive }"
        >
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z"/>
          </svg>
          <span class="sidebar__label">Simulations</span>
        </RouterLink>

        <RouterLink to="/graph" class="sidebar__item" active-class="sidebar__item--active">
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="8" r="2.5"/><circle cx="12" cy="18" r="2.5"/>
            <path d="M8 7l4 9M16 9l-2 7"/>
          </svg>
          <span class="sidebar__label">Graph</span>
        </RouterLink>

        <RouterLink to="/history" class="sidebar__item" active-class="sidebar__item--active">
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="9"/>
            <path d="M12 7V12L15.5 14.5"/>
          </svg>
          <span class="sidebar__label">History</span>
        </RouterLink>
      </nav>

      <div class="sidebar__divider" aria-hidden="true" />

      <!-- Future sections -->
      <div class="sidebar__section-label">Integrations</div>

      <div class="sidebar__item sidebar__item--soon" title="CRM Integrations — Coming soon">
        <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        <span class="sidebar__label">CRM</span>
        <span class="sidebar__soon-tag">Soon</span>
      </div>

      <div class="sidebar__item sidebar__item--soon" title="User Enrollment — Coming soon">
        <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M19 8v6M22 11H16"/>
        </svg>
        <span class="sidebar__label">Users</span>
        <span class="sidebar__soon-tag">Soon</span>
      </div>

      <!-- Spacer pushes settings to bottom -->
      <div class="sidebar__spacer" />

      <button class="sidebar__item sidebar__item--btn" title="Settings" aria-label="Settings">
        <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span class="sidebar__label">Settings</span>
      </button>

      <div class="sidebar__user">
        <span class="sidebar__avatar">A</span>
        <span class="sidebar__label sidebar__user-text">Account</span>
      </div>
    </aside>

    <!-- ── Topbar ─────────────────────────────────────────────────────── -->
    <header class="topbar">
      <!-- Project context -->
      <div class="topbar__project">
        <h1 class="topbar__sim-name">{{ store.project?.name || "Campaign workspace" }}</h1>
        <StatusBadge
          :status="store.project?.status || 'draft'"
          :label="store.project?.status || 'Draft'"
        />
      </div>

      <!-- Quick-stat pills -->
      <div class="topbar__pills" aria-label="Project metrics">
        <span class="topbar__pill">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          {{ store.personas.items.length || 0 }} personas
        </span>
        <span class="topbar__pill">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          {{ store.variants.length || 0 }} variants
        </span>
        <span class="topbar__pill topbar__pill--prog">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          {{ store.workflowProgressPercent }}%
        </span>
      </div>

      <!-- Right-side controls -->
      <div class="topbar__end">
        <div v-if="store.isMockMode" class="demo-chip">
          <span class="demo-chip__dot" aria-hidden="true" />
          <span class="demo-chip__label">Demo</span>
        </div>
        <StatusBadge v-else status="ready" label="Live" />

        <button
          class="theme-toggle"
          :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
          :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleTheme"
        >
          <svg v-if="theme === 'dark'" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- ── Notice banner ──────────────────────────────────────────────── -->
    <Transition name="notice-slide">
      <div v-if="store.notice" class="notice" role="alert">{{ store.notice }}</div>
    </Transition>

    <!-- ── Main content ───────────────────────────────────────────────── -->
    <main class="content-main">
      <slot />
    </main>

    <!-- ── Bottom Step Rail ───────────────────────────────────────────── -->
    <nav class="app-steps" aria-label="Workflow steps">
      <!-- Progress track line -->
      <div class="app-steps__track" aria-hidden="true">
        <div class="app-steps__track-fill" :style="{ width: trackFillWidth }" />
      </div>

      <button
        v-for="step in stepItems"
        :key="step.number"
        class="app-steps__step"
        :class="{
          'app-steps__step--done':   step.number < store.currentStep,
          'app-steps__step--active': step.number === store.currentStep,
          'app-steps__step--locked': !store.canNavigateToStep(step.number) && step.number !== store.currentStep,
        }"
        :disabled="!store.canNavigateToStep(step.number) && step.number !== store.currentStep"
        :aria-current="step.number === store.currentStep ? 'step' : undefined"
        @click="onSelectStep(step.number)"
      >
        <!-- Active glow bar at top of step -->
        <span v-if="step.number === store.currentStep" class="app-steps__glow" aria-hidden="true" />

        <span class="app-steps__pip" aria-hidden="true">
          <svg
            v-if="step.number < store.currentStep"
            width="9" height="9" viewBox="0 0 10 10" fill="none"
          >
            <path d="M1.5 5L4 7.5L8.5 2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-else>{{ step.number }}</span>
        </span>
        <span class="app-steps__name">{{ step.label }}</span>
        <span v-if="step.number === store.currentStep" class="app-steps__running-dot" aria-hidden="true" />
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import MetricTile from "@/components/common/MetricTile.vue";
import ProgressRing from "@/components/common/ProgressRing.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";
import { useCampaignStore } from "@/stores/campaignStore";
import { useTheme } from "@/composables/useTheme";

const store = useCampaignStore();
const router = useRouter();
const route = useRoute();

const sidebarExpanded = ref(false);
const { theme, toggle: toggleTheme, init: initTheme } = useTheme();
onMounted(initTheme);

const stepItems = [
  { number: 1, label: "Knowledge Graph" },
  { number: 2, label: "Personas" },
  { number: 3, label: "Variants" },
  { number: 4, label: "Report" },
  { number: 5, label: "Insights" },
];

// Highlight Simulations nav item on any workflow route
const isWorkflowActive = computed(() =>
  ["/process", "/simulation", "/report", "/interaction"].some(p =>
    route.path.startsWith(p)
  )
);

// Current page identifier for per-page CSS backgrounds
const currentPage = computed(() => {
  const p = route.path;
  if (p.startsWith("/graph"))       return "graph";
  if (p.startsWith("/simulation"))  return "simulation";
  if (p.startsWith("/report"))      return "report";
  if (p.startsWith("/interaction")) return "interaction";
  if (p.startsWith("/history"))     return "history";
  return "process"; // default for /process and all step views
});

// Track fill: 0% at step 1, 100% at step 5
const trackFillWidth = computed(() => {
  const pct = ((store.currentStep - 1) / (stepItems.length - 1)) * 100;
  return `${Math.min(100, Math.max(0, pct))}%`;
});

function onSelectStep(step) {
  if (store.canNavigateToStep(step) || step === store.currentStep) {
    store.goToStep(step);
  }
}
</script>

<style scoped>
/* ── Theme toggle ─────────────────────────────────────────────────────── */
.theme-toggle {
  display: inline-grid;
  place-items: center;
  width: 2rem; height: 2rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-strong);
  background: transparent;
  color: var(--color-text-subtle);
  cursor: pointer;
  flex-shrink: 0;
  transition:
    border-color var(--transition-fast),
    color var(--transition-fast),
    background var(--transition-fast),
    box-shadow var(--transition-fast);
}
.theme-toggle:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(10,191,173,0.06);
  box-shadow: var(--glow-accent-sm);
}
</style>
