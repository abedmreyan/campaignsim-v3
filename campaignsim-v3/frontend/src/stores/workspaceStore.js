import { defineStore } from "pinia";
import router from "@/router/index.js";
import { useCampaignStore } from "@/stores/campaignStore";
import { listBriefs, createBrief as createBriefApi } from "@/api/briefApi";

// Routes that carry an id scoped to the *previous* active brief's workflow
// (a simulation/campaign/report/session id as a route param) — switching
// businesses on one of these must land back in the workflow shell instead
// of leaving a stale param mounted.
const STALE_ON_SWITCH_ROUTES = new Set([
  "simulation-run",
  "report",
  "interaction",
  "CampaignReport",
  "IterationCompare",
  "designer-session",
]);

const BRIEFS_TTL_MS = 60000;

export const useWorkspaceStore = defineStore("workspace", {
  state: () => ({
    briefs: [],
    briefsLoading: false,
    briefsError: null,
    briefsLoadedAt: 0,
    switching: false,
    switchingBriefId: null,
  }),

  getters: {
    activeBriefId: () => useCampaignStore().brandBriefId,
    activeBrief(state) {
      const activeId = useCampaignStore().brandBriefId;
      return state.briefs.find((b) => b.id === activeId) || null;
    },
  },

  actions: {
    async loadBriefs({ force = false } = {}) {
      if (this.briefsLoading) return this.briefs;
      if (!force && this.briefs.length && Date.now() - this.briefsLoadedAt < BRIEFS_TTL_MS) {
        return this.briefs;
      }
      this.briefsLoading = true;
      this.briefsError = null;
      try {
        this.briefs = await listBriefs();
        this.briefsLoadedAt = Date.now();
        return this.briefs;
      } catch (error) {
        this.briefsError = error?.message || "Could not load your businesses.";
        throw error;
      } finally {
        this.briefsLoading = false;
      }
    },

    async createBrief(payload) {
      const brief = await createBriefApi(payload);
      this.briefs.unshift(brief);
      return brief;
    },

    upsertBrief(brief) {
      const idx = this.briefs.findIndex((b) => b.id === brief.id);
      if (idx === -1) this.briefs.unshift(brief);
      else this.briefs[idx] = brief;
    },

    removeBrief(id) {
      this.briefs = this.briefs.filter((b) => b.id !== id);
      const campaignStore = useCampaignStore();
      if (campaignStore.brandBriefId === id) campaignStore.clearBrief();
    },

    /**
     * Switch the whole app's active workflow to a different business, from
     * anywhere — not just the /briefs grid. Resets the single active-workflow
     * slice (campaignStore) and reloads it for the new brief, then routes
     * away from anything that was scoped to the old brief's ids.
     */
    async switchTo(briefId) {
      if (!briefId) return "needs-upload";
      const campaignStore = useCampaignStore();
      if (campaignStore.brandBriefId === briefId) return "ready";

      this.switching = true;
      this.switchingBriefId = briefId;
      try {
        campaignStore.resetProject();
        campaignStore.selectBrief(briefId);
        const result = await campaignStore.resumeBrief(briefId);

        if (result === "ready") {
          campaignStore.currentStep = this._landingStep(campaignStore);
        }

        const currentRouteName = router.currentRoute.value.name;
        if (STALE_ON_SWITCH_ROUTES.has(currentRouteName)) {
          router.push({ name: "process" });
        }
        return result;
      } finally {
        this.switching = false;
        this.switchingBriefId = null;
      }
    },

    // Resume at the furthest step the brief's saved state supports, rather
    // than always dumping the user back at step 1.
    _landingStep(campaignStore) {
      for (let step = 5; step >= 1; step--) {
        if (campaignStore.canNavigateToStep(step)) return step;
      }
      return 1;
    },
  },
});
