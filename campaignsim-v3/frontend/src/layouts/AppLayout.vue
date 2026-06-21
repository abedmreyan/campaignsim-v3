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
          <img src="/logo.png" alt="CampaignSim" class="sidebar__logo-img" />
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

        <RouterLink to="/briefs" class="sidebar__item" active-class="sidebar__item--active">
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <span class="sidebar__label">Briefs</span>
        </RouterLink>

        <button
          class="sidebar__item"
          :class="{ 'sidebar__item--active': isWorkflowActive }"
          @click="goToSimulations"
        >
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z"/>
          </svg>
          <span class="sidebar__label">Simulations</span>
        </button>

        <button
          class="sidebar__item"
          :class="{ 'sidebar__item--active': route.path === '/process' && store.currentStep === 3 }"
          :title="!store.brandBriefId ? 'Select a brief first' : ''"
          @click="goToVariants"
        >
          <svg class="sidebar__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          <span class="sidebar__label">Variants</span>
        </button>

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

      <div class="sidebar__spacer" />
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

      <!-- Right-side controls -->
      <div class="topbar__end">
        <div v-if="store.isMockMode" class="demo-chip">
          <span class="demo-chip__dot" aria-hidden="true" />
          <span class="demo-chip__label">Demo</span>
        </div>
        <StatusBadge v-else status="ready" label="Live" />

        <!-- User account menu -->
        <div class="user-menu" ref="userMenuRef">
          <button class="user-menu__trigger" @click="toggleUserMenu" :aria-expanded="userMenuOpen" aria-haspopup="menu">
            <span class="user-menu__avatar">{{ userInitial }}</span>
            <span class="user-menu__name">{{ auth.user?.display_name || "Account" }}</span>
            <svg class="user-menu__caret" :class="{ 'is-open': userMenuOpen }" width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
              <path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>

          <Transition name="dropdown">
            <div v-if="userMenuOpen" class="user-menu__dropdown" role="menu">
              <div class="user-menu__email">{{ auth.user?.email }}</div>
              <div class="user-menu__divider" aria-hidden="true" />
              <button class="user-menu__item" role="menuitem" @click="toggleTheme">
                <svg v-if="theme === 'dark'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="5"/>
                  <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                  <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
                {{ theme === 'dark' ? 'Light mode' : 'Dark mode' }}
              </button>
              <div class="user-menu__divider" aria-hidden="true" />
              <button class="user-menu__item" role="menuitem" disabled>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
                Settings
                <span class="user-menu__soon">Soon</span>
              </button>
              <div class="user-menu__divider" aria-hidden="true" />
              <button class="user-menu__item user-menu__item--danger" role="menuitem" @click="auth.logout()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16 17 21 12 16 7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                Sign out
              </button>
            </div>
          </Transition>
        </div>
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
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import StatusBadge from "@/components/common/StatusBadge.vue";
import { useCampaignStore } from "@/stores/campaignStore";
import { useAuthStore } from "@/stores/authStore";
import { useTheme } from "@/composables/useTheme";

const store = useCampaignStore();
const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const sidebarExpanded = ref(false);
const userMenuOpen = ref(false);
const userMenuRef = ref(null);
const { theme, toggle: toggleTheme, init: initTheme } = useTheme();
onMounted(initTheme);

const userInitial = computed(() => {
  const name = auth.user?.display_name || auth.user?.email || "?";
  return name[0].toUpperCase();
});

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value;
}

function handleClickOutside(e) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    userMenuOpen.value = false;
  }
}

onMounted(() => document.addEventListener("mousedown", handleClickOutside));
onUnmounted(() => document.removeEventListener("mousedown", handleClickOutside));

const stepItems = [
  { number: 1, label: "Knowledge Graph" },
  { number: 2, label: "Personas" },
  { number: 3, label: "Variants" },
  { number: 4, label: "Report" },
  { number: 5, label: "Insights" },
];

// Highlight Simulations nav item on any workflow route (excluding variants direct nav)
const isWorkflowActive = computed(() =>
  ["/process", "/simulation", "/report", "/interaction"].some(p =>
    route.path.startsWith(p)
  ) && store.currentStep !== 3
);

function goToSimulations() {
  if (route.path.startsWith("/process")) {
    // Already in the workflow — reset to step 1 so the click feels responsive
    store.goToStep(1);
  } else {
    router.push("/process");
  }
}

function goToVariants() {
  if (!store.brandBriefId) {
    store.setNotice("Select a brand brief before accessing variants.");
    router.push("/briefs");
    return;
  }
  store.goToStep(3);
  router.push("/process");
}

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
/* ── User account menu ────────────────────────────────────────────────── */
.user-menu {
  position: relative;
}

.user-menu__trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.625rem 0.3rem 0.3rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 500;
  transition: border-color 0.15s, background 0.15s;
  white-space: nowrap;
}

.user-menu__trigger:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface);
}

.user-menu__avatar {
  display: inline-grid;
  place-items: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  font-size: 0.6875rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-menu__name {
  max-width: 8rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-menu__caret {
  color: var(--color-text-subtle);
  transition: transform 0.15s;
  flex-shrink: 0;
}

.user-menu__caret.is-open {
  transform: rotate(180deg);
}

.user-menu__dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 14rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 0.625rem);
  box-shadow: 0 8px 32px rgba(0,0,0,0.24), 0 2px 8px rgba(0,0,0,0.12);
  z-index: 200;
  overflow: hidden;
}

.user-menu__email {
  padding: 0.625rem 0.875rem;
  font-size: 0.75rem;
  color: var(--color-text-subtle);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-menu__divider {
  height: 1px;
  background: var(--color-border);
  margin: 0;
}

.user-menu__item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s, color 0.12s;
}

.user-menu__item:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.user-menu__item:disabled {
  opacity: 0.5;
  cursor: default;
}

.user-menu__soon {
  margin-left: auto;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-subtle);
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: 2rem;
  padding: 0.1rem 0.4rem;
}

.user-menu__item--danger {
  color: var(--color-text-muted);
}

.user-menu__item--danger:hover {
  background: var(--color-danger-soft, rgba(239,68,68,0.08));
  color: var(--color-danger, #ef4444);
}

/* ── Dropdown animation ───────────────────────────────────────────────── */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.12s, transform 0.12s;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
