import { defineStore } from "pinia";
import router from "@/router/index.js";
import { useDesignerStore } from "@/stores/designerStore";
import {
  createSimulationProject,
  uploadBrandBrief as uploadBriefApi,
  buildGraph as buildGraphApi,
  getGraphTask as getGraphTaskApi,
  getGraphProject as getGraphProjectApi,
  prepareGraph as prepareGraphApi,
  getPreparationStatus,
  getGraphRelations,
  generateProfiles,
  getProfileGenerationStatus,
  getProfiles,
  startAbTest as startAbTestApi,
  getAbStatus as getAbStatusApi,
  generateCampaignRecommendations as generateCampaignRecommendationsApi,
  getCampaignReport as getCampaignReportApi,
  stopSimulation as stopSimulationApi,
  getSimulationRunStatus,
  generateReport as generateReportApi,
  getReport,
  interviewPersona as interviewPersonaApi,
  getHistory,
  getCampaignsForBrief,
} from "@/api/campaignApi";
import { getBrief, rebuildGraph as rebuildGraphApi } from "@/api/briefApi";

const PROJECT_KEY = "campaignsim_current_project";
const STEP_KEY = "campaignsim_current_step";
const VARIANTS_KEY = "campaignsim_variants";
const MOCK_STATE_KEY = "campaignsim_mock_state";
// { [briefId]: { simulationId, graphId } } — the last simulation actually
// prepared (has twitter_profiles.csv on disk) for each brief. /api/simulation
// /create mints a brand-new, unprepared simulation on every call with no
// reuse logic server-side, so resumeBrief() must remember this itself or
// every re-open of a brief (now trivial via the workspace switcher) silently
// swaps in a throwaway simulation that fails at launch time.
const PREPARED_SIM_KEY = "campaignsim_prepared_simulations";

function getPreparedSimulation(briefId) {
  if (!briefId) return null;
  const map = readJson(PREPARED_SIM_KEY, {});
  return map[briefId] || null;
}

function setPreparedSimulation(briefId, simulationId, graphId) {
  if (!briefId || !simulationId || !graphId) return;
  const map = readJson(PREPARED_SIM_KEY, {});
  map[briefId] = { simulationId, graphId };
  try {
    localStorage.setItem(PREPARED_SIM_KEY, JSON.stringify(map));
  } catch {}
}

function readJson(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function normalizeError(error, fallback = "Something went wrong.") {
  if (error?.error?.message) return error.error.message;
  return error?.message || fallback;
}

function toApiVariant(variant) {
  return {
    variant_id: variant.variant_id,
    variant_name: variant.variant_name,
    channel: variant.channel,
    content: {
      format: variant.content?.format || variant.format,
      headline: variant.content?.headline || variant.headline,
      body: variant.content?.body || variant.body,
      cta: variant.content?.cta || variant.cta,
      visual_desc: variant.content?.visual_desc || variant.visual_desc || "",
      email_subject: variant.content?.email_subject || variant.email_subject || "",
      tone: variant.content?.tone || variant.tone,
    },
    target_segment: variant.target_segment || "",
    // 0 -> the backend falls back to the channel's own default round count.
    max_rounds: Number(variant.max_rounds || 0),
    status: variant.status || "pending",
    // Phase 2 — Designer agent provenance, preserved through edits so the
    // launched campaign's variant rows record which ones were AI-proposed.
    provenance: variant.provenance || "user",
    rationale: variant.rationale || null,
    hypothesis: variant.hypothesis || null,
  };
}

const persistedProject = readJson(PROJECT_KEY, null);
const persistedState = readJson(MOCK_STATE_KEY, null);

export const useCampaignStore = defineStore("campaign", {
  state: () => ({
    currentStep: Number(localStorage.getItem(STEP_KEY) || persistedState?.currentStep || 1),
    notice: null,
    brandBriefId: sessionStorage.getItem("cs_active_brief_id") || null,

    project: persistedProject || persistedState?.project || null,
    simulationId: persistedProject?.simulation_id || persistedState?.simulationId || null,
    graphId: persistedProject?.graph_id || persistedState?.graphId || null,
    // True only when this.simulationId is known to have twitter_profiles.csv
    // on disk (via prepareGraph() or generatePersonas()) or was restored from
    // a PREPARED_SIM_KEY cache hit in resumeBrief() — decoupled from
    // personas.items so restored-from-DB personas can't imply a launchable
    // simulation when the underlying simulationId was never prepared.
    simulationPrepared: persistedState?.simulationPrepared || false,
    campaignId: persistedState?.campaignId || null,
    reportId: persistedState?.reportId || null,
    uploadedFile: persistedState?.uploadedFile || null,

    graph: {
      nodes: persistedState?.graph?.nodes || [],
      edges: persistedState?.graph?.edges || [],
      loading: false,
      error: null,
      progress: 0,
      statusText: "",
    },

    personas: {
      items: persistedState?.personas?.items || [],
      loading: false,
      error: null,
      progress: 0,
      progressMessage: "",
    },

    variants: readJson(VARIANTS_KEY, persistedState?.variants || []),
    // "" | "awareness" | "conversion" | "retention" | "launch" — shapes which
    // funnel tier VariantScorer emphasises when ranking variants.
    campaignObjective: persistedState?.campaignObjective || "",

    simulationRun: {
      runId: persistedState?.simulationRun?.runId || null,
      status: persistedState?.simulationRun?.status || "idle",
      progress: 0,
      variants: persistedState?.simulationRun?.variants || [],
      results: persistedState?.simulationRun?.results || [],
      loading: false,
      error: null,
    },

    report: {
      data: persistedState?.report?.data || null,
      loading: false,
      error: null,
    },

    history: {
      items: persistedState?.history?.items || [],
      loading: false,
      error: null,
    },

    interviewMessages: persistedState?.interviewMessages || [],
  }),

  getters: {
    graphReady: (state) => state.graph.nodes.length > 0 && state.graph.edges.length > 0,
    personasReady: (state) => state.personas.items.length > 0,
    canStartSimulation: (state) => state.variants.length >= 1 && state.variants.length <= 6,
    simulationCompleted: (state) => state.simulationRun.status === "completed",
    modeLabel: () => (import.meta.env.VITE_USE_MOCKS === "true" ? "Mock mode" : "Live API"),
    isMockMode: () => import.meta.env.VITE_USE_MOCKS === "true",

    /** Presentation-only: drives .app-shell ambient canvas (idle | running | complete | error). */
    shellAmbientStatus(state) {
      if (state.graph.error || state.personas.error || state.simulationRun.error || state.report.error) {
        return "error";
      }
      if (
        state.graph.loading ||
        state.personas.loading ||
        state.report.loading ||
        state.simulationRun.loading ||
        state.simulationRun.status === "running"
      ) {
        return "running";
      }
      if (state.simulationRun.status === "completed" || state.report.data) {
        return "complete";
      }
      return "idle";
    },

    /** Presentation-only: command sidebar activity strip copy from existing store state. */
    shellActivityMessage(state) {
      if (state.graph.loading) {
        return state.graph.statusText || "Building graph…";
      }
      if (state.personas.loading) {
        return "Generating personas…";
      }
      if (state.report.loading) {
        return "Generating report…";
      }
      if (state.simulationRun.status === "running" || state.simulationRun.loading) {
        return state.simulationRun.progress
          ? `Running simulation… ${state.simulationRun.progress}%`
          : "Running simulation…";
      }
      if (state.currentStep === 1) {
        if (!state.uploadedFile && !state.graphId) return "Uploading brief…";
        if (state.graphId && !state.graph.nodes.length) return "Extracting entities…";
        if (state.graphReady) return "Graph ready — explore or continue.";
      }
      if (state.currentStep === 2 && !state.personas.items.length) {
        return "Generate audience personas.";
      }
      if (state.currentStep === 3 && state.variants.length < 1) {
        return "Add at least one campaign variant.";
      }
      if (state.currentStep === 4 && !state.report.data) {
        return state.simulationCompleted ? "Generate insights report." : "Complete simulation first.";
      }
      return "Ready for next action.";
    },

    workflowProgressPercent(state) {
      let completed = 0;
      if (state.graphId && state.graph.nodes.length) completed += 1;
      if (state.personas.items.length) completed += 1;
      if (state.variants.length >= 1) completed += 1;
      if (state.simulationRun.status === "completed") completed += 1;
      if (state.report.data) completed += 1;
      return Math.round((completed / 5) * 100);
    },

    stepStatuses(state) {
      const graphSubtitle = state.graph.loading
        ? "Building…"
        : state.graph.nodes.length
          ? "Graph ready"
          : state.graphId
            ? "Brief uploaded"
            : "Awaiting brief";
      const personaSubtitle = state.personas.loading
        ? "Generating…"
        : state.personas.items.length
          ? `${state.personas.items.length} personas`
          : "Not generated";
      const variantSubtitle =
        state.variants.length >= 1
          ? `${state.variants.length} variant${state.variants.length > 1 ? "s" : ""} ready`
          : "No variants";
      const reportSubtitle = state.report.data
        ? "Report ready"
        : state.simulationRun.status === "completed"
          ? "Generate report"
          : "After simulation";
      const interviewSubtitle = state.interviewMessages.length
        ? `${state.interviewMessages.length} messages`
        : "Chat with personas";

      return {
        1: graphSubtitle,
        2: personaSubtitle,
        3: variantSubtitle,
        4: reportSubtitle,
        5: interviewSubtitle,
      };
    },

    canNavigateToStep: (state) => (step) => {
      if (step <= 1) return true;
      if (step === 2) return Boolean(state.graphId) && state.graph.nodes.length > 0;
      if (step === 3) return state.personas.items.length > 0;
      if (step === 4) return state.simulationRun.status === "completed" || Boolean(state.report.data);
      if (step === 5) return Boolean(state.report.data);
      return false;
    },

    commandCtaLabel(state) {
      if (state.currentStep === 1 && !state.graphReady) return "Prepare knowledge graph";
      if (state.currentStep === 1 && state.graphReady) return "Continue to personas";
      if (state.currentStep === 2 && (!state.personas.items.length || !state.simulationPrepared)) return "Generate personas";
      if (state.currentStep === 2) return "Build campaign variants";
      if (state.currentStep === 3 && state.variants.length < 1) return "Add a variant";
      if (state.currentStep === 3 && !state.simulationPrepared) return "Generate personas to launch";
      if (state.currentStep === 3) return "Launch simulation";
      if (state.currentStep === 4 && !state.report.data) return "Generate insights report";
      if (state.currentStep === 4) return "Open persona insights";
      return "Continue workflow";
    },
  },

  actions: {
    setCampaignObjective(objective) {
      this.campaignObjective = objective || "";
      this.persist();
    },

    persist() {
      localStorage.setItem(STEP_KEY, String(this.currentStep));
      localStorage.setItem(VARIANTS_KEY, JSON.stringify(this.variants));
      localStorage.setItem(
        MOCK_STATE_KEY,
        JSON.stringify({
          currentStep: this.currentStep,
          project: this.project,
          simulationId: this.simulationId,
          graphId: this.graphId,
          simulationPrepared: this.simulationPrepared,
          campaignId: this.campaignId,
          reportId: this.reportId,
          uploadedFile: this.uploadedFile,
          graph: this.graph,
          personas: this.personas,
          variants: this.variants,
          campaignObjective: this.campaignObjective,
          simulationRun: this.simulationRun,
          report: this.report,
          history: this.history,
          interviewMessages: this.interviewMessages,
        }),
      );
      if (this.project) localStorage.setItem(PROJECT_KEY, JSON.stringify(this.project));
    },

    setNotice(message) {
      this.notice = message;
      window.setTimeout(() => {
        if (this.notice === message) this.notice = null;
      }, 4200);
    },

    selectBrief(id) {
      this.brandBriefId = id;
      sessionStorage.setItem("cs_active_brief_id", id);
    },

    clearBrief() {
      this.brandBriefId = null;
      sessionStorage.removeItem("cs_active_brief_id");
    },

    async uploadBrandBrief(file, simulationRequirement) {
      if (!file) throw new Error("Select a PDF or TXT brand brief first.");
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (!["pdf", "txt"].includes(extension)) {
        throw new Error("Only PDF and TXT brand briefs are supported.");
      }

      this.graph.loading = true;
      this.graph.error = null;
      this.graph.progress = 0;
      try {
        // Step 1: Upload file + generate ontology (creates project server-side).
        // Pass the already-selected brief so the backend updates it in place
        // instead of minting a new "Brand Briefs" row on every upload.
        this.graph.statusText = "Analyzing document…";
        const ontologyData = await uploadBriefApi({
          file,
          projectName: file.name.replace(/\.[^.]+$/, ""),
          simulationRequirement,
          briefId: this.brandBriefId,
        });
        const projectId = ontologyData.project_id;
        this.graph.progress = 20;

        // Step 2: Kick off async graph build
        this.graph.statusText = "Building knowledge graph…";
        const buildData = await buildGraphApi({ project_id: projectId });
        const taskId = buildData.task_id;
        this.graph.progress = 30;

        // Step 3: Poll until graph build completes
        const graphId = await this._pollGraphBuildTask(taskId, projectId);
        this.graph.progress = 85;

        // Step 4: Create simulation
        this.graph.statusText = "Creating simulation environment…";
        const simData = await createSimulationProject({ projectId, graphId });

        this.simulationId = simData.simulation_id;
        this.graphId = graphId;
        // Defensive: a fresh simulationId is never prepared yet, even though
        // this path chains into prepareGraph() on the happy path.
        this.simulationPrepared = false;
        this.uploadedFile = { filename: file.name, size: file.size };
        this.project = {
          ...(this.project || {}),
          simulation_id: simData.simulation_id,
          graph_id: graphId,
          project_id: projectId,
          project_name: file.name.replace(/\.[^.]+$/, ""),
          simulation_requirement: simulationRequirement || "",
          status: "preparing",
        };
        this.graph.progress = 100;
        this.persist();
        return simData;
      } catch (error) {
        this.graph.error = normalizeError(error, "Upload failed.");
        throw error;
      } finally {
        this.graph.loading = false;
        this.graph.statusText = "";
      }
    },

    async _pollGraphBuildTask(taskId, projectId) {
      const MAX_ATTEMPTS = 120; // 5 minutes at 2.5s intervals
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        await new Promise((r) => setTimeout(r, 2500));
        const task = await getGraphTaskApi(taskId);
        const status = task.status;
        this.graph.progress = Math.min(84, 30 + Math.round((task.progress || 0) * 55));
        this.graph.statusText = task.message || "Building graph…";
        if (status === "completed") {
          const graphId = task.result?.graph_id;
          if (graphId) return graphId;
          // Fallback: fetch project to get graph_id
          const project = await getGraphProjectApi(projectId);
          return project.graph_id;
        }
        if (status === "failed") throw new Error(task.message || "Graph build failed.");
      }
      throw new Error("Graph build timed out after 5 minutes.");
    },

    /**
     * Called when entering the workflow with a brief already selected
     * (e.g. "Open brief" from Brand Briefs). Loads that brief's existing
     * graph if it's already built, or rebuilds it from the brief's saved
     * content if not — either way, resuming into an active simulation
     * instead of prompting for a fresh upload.
     *
     * Returns "ready" if the graph/simulation is now loaded, or
     * "needs-upload" if the brief has no content yet to resume from.
     */
    async resumeBrief(briefId) {
      if (!briefId) return "needs-upload";

      this.graph.loading = true;
      this.graph.error = null;
      this.graph.progress = 0;
      try {
        const brief = await getBrief(briefId);
        let projectId = brief.project_id;
        let graphId = brief.graph_id;

        if (brief.graph_status !== "ready" || !graphId) {
          if (!(brief.content || "").trim()) {
            return "needs-upload";
          }
          this.graph.statusText = "Rebuilding graph from saved brief…";
          const rebuildData = await rebuildGraphApi(briefId);
          projectId = rebuildData.project_id;
          this.graph.progress = 30;
          graphId = await this._pollGraphBuildTask(rebuildData.task_id, projectId);
        }
        this.graph.progress = 85;

        this.graph.statusText = "Loading graph…";
        await this.loadGraphRelations(graphId);

        // Reuse the simulation that was actually prepared (has
        // twitter_profiles.csv on disk) last time this brief's graph was
        // ready, instead of always minting a fresh unprepared one — see
        // PREPARED_SIM_KEY above for why this matters.
        const cachedSim = getPreparedSimulation(briefId);
        let simulationId;
        let alreadyPrepared = false;
        if (cachedSim && cachedSim.graphId === graphId) {
          simulationId = cachedSim.simulationId;
          alreadyPrepared = true;
        } else {
          this.graph.statusText = "Creating simulation environment…";
          const simData = await createSimulationProject({ projectId, graphId });
          simulationId = simData.simulation_id;
        }

        this.simulationId = simulationId;
        this.graphId = graphId;
        // The only source of truth for whether this simulationId actually has
        // twitter_profiles.csv on disk — must not be inferred from restored
        // personas below, which can belong to a different, already-superseded
        // simulationId (that's exactly what broke launches before this fix).
        this.simulationPrepared = alreadyPrepared;
        this.uploadedFile = { filename: brief.name, size: (brief.content || "").length };
        this.project = {
          ...(this.project || {}),
          simulation_id: simulationId,
          graph_id: graphId,
          project_id: projectId,
          project_name: brief.name,
          status: alreadyPrepared ? "ready" : "preparing",
        };
        this.graph.progress = 100;

        // Restore any personas already generated for this brief — without
        // this, switching away and back (or a page refresh after a switch,
        // since resetProject() clears the localStorage snapshot) makes
        // fully-generated personas look gone even though they're saved
        // server-side, forcing an unnecessary regeneration.
        await this.loadPersonas(briefId);

        // Same restoration as personas, for the same reason: a generated
        // campaign report is safely persisted server-side (inside the
        // campaign's JSON file), but campaignId/report.data are wiped by
        // resetProject() on every switch and resumeBrief() never re-fetched
        // them, so a finished report looked gone until the user regenerated
        // it — for no reason, since nothing was actually lost.
        try {
          const recentCampaigns = await getCampaignsForBrief(briefId, { limit: 1 });
          const recent = recentCampaigns?.[0];
          if (recent?.campaign_id) {
            this.campaignId = recent.campaign_id;
            if (recent.has_report) {
              await this.loadCampaignReport(recent.campaign_id);
            } else if (recent.overall_status === "completed" || recent.overall_status === "failed") {
              this.simulationRun.status = recent.overall_status;
            }
          }
        } catch {
          // Non-fatal — resuming the brief's graph/personas still succeeds
          // without restoring campaign history.
        }

        this.persist();
        return "ready";
      } catch (error) {
        this.graph.error = normalizeError(error, "Could not resume this brief.");
        throw error;
      } finally {
        this.graph.loading = false;
        this.graph.statusText = "";
      }
    },

    async prepareGraph(fanOut = 1) {
      if (!this.simulationId || !this.graphId) {
        this.graph.error = "Upload a brand brief before building the graph.";
        return null;
      }

      this.graph.loading = true;
      this.graph.error = null;
      this.graph.progress = 0;
      try {
        const task = await prepareGraphApi({
          simulation_id: this.simulationId,
          graph_id: this.graphId,
          fan_out: fanOut,
        });
        // If already prepared, skip polling and just load relations
        if (!task.task_id || task.already_prepared) {
          this.graph.progress = 100;
        } else {
          await this.pollPreparationStatus(task.task_id);
        }
        await this.loadGraphRelations(this.graphId);
        this.project = { ...(this.project || {}), status: "ready" };
        this.simulationPrepared = true;
        setPreparedSimulation(this.brandBriefId, this.simulationId, this.graphId);
        this.persist();
        return task;
      } catch (error) {
        this.graph.error = normalizeError(error, "Graph build failed.");
        throw error;
      } finally {
        this.graph.loading = false;
      }
    },

    async pollPreparationStatus(taskId) {
      const MAX_ATTEMPTS = 60; // 3 min at 3s intervals
      const POLL_INTERVAL = 3000;
      let status = "running";
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL));
        const data = await getPreparationStatus({
          task_id: taskId,
          simulation_id: this.simulationId,
        });
        status = data.status;
        this.graph.progress = data.progress || 0;
        this.graph.statusText = data.current_step || "";
        this.persist();
        // Once the simulation is already prepared, the backend short-circuits
        // to "ready" on every subsequent poll (regardless of task_id) instead
        // of "completed" — both mean done.
        if (status === "completed" || status === "ready") return data;
        if (status === "failed") throw new Error(data.message || "Graph preparation failed.");
      }
      throw new Error("Graph preparation timed out after 3 minutes.");
    },

    async loadGraphRelations(graphId = this.graphId) {
      this.graph.loading = true;
      this.graph.error = null;
      try {
        const data = await getGraphRelations(graphId);
        this.graph.nodes = data.nodes || [];
        this.graph.edges = data.edges || [];
        this.graphId = data.graph_id || graphId;
        this.persist();
        return data;
      } catch (error) {
        this.graph.error = normalizeError(error, "Could not load graph relations.");
        throw error;
      } finally {
        this.graph.loading = false;
      }
    },

    async generatePersonas(count = 30) {
      if (!this.graphReady) {
        this.personas.error = "Build the knowledge graph before generating personas.";
        return null;
      }
      // Without a simulationId, the backend skips the twitter_profiles.csv
      // write entirely (it's gated on simulation_id being present) but the
      // task still reports success — that would let this function set
      // simulationPrepared = true on a simulation that was never actually
      // prepared. graphReady alone doesn't guarantee this is set — see the
      // Step1GraphBuild.vue onMounted fix for the resumeBrief() race this guards against.
      if (!this.simulationId) {
        this.personas.error = "No active simulation for this business — try reopening it from Brand Briefs.";
        return null;
      }

      this.personas.loading = true;
      this.personas.error = null;
      this.personas.progress = 5;
      this.personas.progressMessage = "";
      try {
        // Backend immediately returns a task_id; we poll until done.
        // entity_types filters to real audience personas only — brands/channels are excluded.
        const task = await generateProfiles({
          simulation_id: this.simulationId,
          graph_id: this.graphId,
          brief_id: this.brandBriefId,
          count,
          entity_types: ["CustomerPersona", "Person", "Influencer", "Consumer", "Buyer"],
          language: "en",
        });

        await this.pollProfileGenerationStatus(task.task_id);

        // personas.items already set from task result in pollProfileGenerationStatus.
        // Fall back to the /profiles endpoint only if task result had no profiles.
        if (!this.personas.items.length) {
          await this.loadPersonas(this.brandBriefId);
        }
        this.personas.progress = 100;
        this.personas.progressMessage = `${this.personas.items.length} personas generated`;
        // pollProfileGenerationStatus() only resolves on a "completed" task,
        // and the backend now fails that task if twitter_profiles.csv
        // couldn't be written — so reaching here is a trustworthy signal
        // this simulationId is actually launch-ready.
        this.simulationPrepared = true;
        setPreparedSimulation(this.brandBriefId, this.simulationId, this.graphId);
        this.persist();
        return this.personas.items;
      } catch (error) {
        this.personas.error = normalizeError(error, "Persona generation failed.");
        throw error;
      } finally {
        this.personas.loading = false;
      }
    },

    async pollProfileGenerationStatus(taskId) {
      const MAX_ATTEMPTS = 120; // 6 min at 3s intervals
      const POLL_INTERVAL = 3000;

      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL));
        const data = await getProfileGenerationStatus(taskId);

        // Mirror progress from backend (backend reports 5–95)
        if (typeof data.progress === "number") {
          this.personas.progress = data.progress;
        }
        if (data.message) {
          this.personas.progressMessage = data.message;
        }

        if (data.status === "completed") {
          // Load profiles directly from task result
          const profiles = data.result?.profiles || data.result?.items || [];
          if (profiles.length) {
            this.personas.items = profiles;
          }
          return;
        }

        if (data.status === "failed") {
          throw new Error(data.error || "Profile generation failed on the server.");
        }
      }
      throw new Error("Profile generation timed out — please try again.");
    },

    async loadPersonas(briefId) {
      this.personas.loading = true;
      this.personas.error = null;
      try {
        const { apiClient } = await import("@/api/client.js");
        const resp = await apiClient.get(`/api/briefs/${briefId}/personas`);
        this.personas.items = resp.data.data;
      } catch (err) {
        this.personas.error = err.message || "Failed to load personas";
      } finally {
        this.personas.loading = false;
      }
    },

    async deletePersona(personaId) {
      const { apiClient } = await import("@/api/client.js");
      await apiClient.delete(`/api/briefs/personas/${personaId}`);
      this.personas.items = this.personas.items.filter((p) => p.id !== personaId);
    },

    async clearPersonas(briefId) {
      const { apiClient } = await import("@/api/client.js");
      await apiClient.post(`/api/briefs/${briefId}/personas/clear`);
      this.personas.items = [];
    },

    addVariant(variant) {
      const apiVariant = toApiVariant({
        ...variant,
        variant_id: variant.variant_id || `v${Date.now()}`,
      });
      this.variants.push(apiVariant);
      this.persist();
    },

    updateVariant(id, payload) {
      const index = this.variants.findIndex((variant) => variant.variant_id === id);
      if (index === -1) return;
      this.variants[index] = toApiVariant({
        ...this.variants[index],
        ...payload,
        variant_id: id,
      });
      this.persist();
    },

    deleteVariant(id) {
      this.variants = this.variants.filter((variant) => variant.variant_id !== id);
      this.persist();
    },

    async startAbTest(selectedVariantIds = null) {
      const variantsToRun = selectedVariantIds
        ? this.variants.filter((v) => selectedVariantIds.includes(v.variant_id))
        : this.variants;

      if (variantsToRun.length < 1 || variantsToRun.length > 6) {
        throw new Error("Select 1 to 6 variants before starting the A/B simulation.");
      }

      if (!this.simulationPrepared) {
        throw new Error(
          'This simulation hasn\'t generated persona profiles yet — go back to Step 2 and click "Generate personas" before launching.',
        );
      }

      this.simulationRun.loading = true;
      this.simulationRun.error = null;
      try {
        const data = await startAbTestApi({
          simulation_id: this.simulationId,
          brand_name: this.project?.project_name || "",
          campaign_goal: this.project?.simulation_requirement || "",
          objective: this.campaignObjective || "",
          variants: variantsToRun.map(toApiVariant),
        });
        // Save campaign_id — required for ab_status polling and report generation
        this.campaignId = data.campaign_id || null;
        this.simulationRun.runId = data.campaign_id || data.run_id || null;
        this.simulationRun.status = "running";
        this.simulationRun.progress = 0;
        this.simulationRun.variants = (data.variants || this.variants).map((v) => ({
          variant_id: v.variant_id,
          variant_name: v.variant_name,
          status: "running",
          progress: 0,
        }));
        this.project = { ...(this.project || {}), status: "running" };
        this.persist();
        return data;
      } catch (error) {
        this.simulationRun.error = normalizeError(error, "Simulation failed to start.");
        throw error;
      } finally {
        this.simulationRun.loading = false;
      }
    },

    async pollSimulationStatus() {
      if (!this.campaignId && !this.simulationId) return null;
      this.simulationRun.loading = true;
      try {
        // Prefer campaign-level ab_status which gives per-variant completion
        if (this.campaignId) {
          const data = await getAbStatusApi(this.campaignId);
          // Clear any previous transient error on success
          if (this.simulationRun.error) this.simulationRun.error = null;
          const allDone = data.all_done;

          this.simulationRun.variants = (data.variants || []).map((v) => {
            const maxRounds = v.max_rounds || 10;
            if (v.runner_status === "completed") {
              return {
                variant_id: v.variant_id,
                variant_name: v.variant_name,
                status: "completed",
                progress: 100,
                current_round: maxRounds,
                max_rounds: maxRounds,
              };
            }
            if (v.runner_status === "failed") {
              return {
                variant_id: v.variant_id,
                variant_name: v.variant_name,
                status: "failed",
                progress: 0,
                current_round: null,
                max_rounds: maxRounds,
              };
            }
            // Use round_end event counts from backend (v.current_round / v.max_rounds)
            const currentRound = v.current_round || 0;
            const progress = currentRound > 0
              ? Math.min(95, Math.round((currentRound / maxRounds) * 100))
              : 0;
            return {
              variant_id: v.variant_id,
              variant_name: v.variant_name,
              status: "running",
              progress,
              current_round: currentRound,
              max_rounds: maxRounds,
            };
          });

          // Overall = average of per-variant progress (not just completed/total)
          const totalPct = this.simulationRun.variants.reduce((s, v) => s + (v.progress || 0), 0);
          this.simulationRun.progress = Math.round(totalPct / Math.max(1, this.simulationRun.variants.length));
          if (allDone) {
            // all_done means every variant reached a terminal state, not that
            // any of them succeeded — treating that as "completed" regardless
            // showed a green "Simulation complete" banner with every variant
            // marked Failed and 0% progress, and let the user attempt to
            // generate an insights report from zero successful variants
            // (canNavigateToStep(4)/simulationCompleted both gate on this
            // same status), which just hung forever with nothing to score.
            const anySucceeded = data.completed > 0;
            this.simulationRun.status = anySucceeded ? "completed" : "failed";
            this.project = { ...(this.project || {}), status: this.simulationRun.status };
          } else {
            this.simulationRun.status = "running";
          }
          this.persist();
          return data;
        }
        // Fallback: original run-status endpoint
        const data = await getSimulationRunStatus(this.simulationId, this.simulationRun.runId);
        if (this.simulationRun.error) this.simulationRun.error = null;
        this.simulationRun.status = data.status || "running";
        this.simulationRun.progress = data.progress || 0;
        if (data.status === "completed") {
          this.project = { ...(this.project || {}), status: "completed" };
        }
        this.persist();
        return data;
      } catch (error) {
        // 502/503/504 are transient Cloudflare/gateway blips — simulation may still be running.
        // Silently ignore them so a single network hiccup doesn't surface an error banner.
        const httpStatus = error?.response?.status;
        const isTransient = !httpStatus || httpStatus === 502 || httpStatus === 503 || httpStatus === 504;
        if (!isTransient) {
          this.simulationRun.error = normalizeError(error, "Could not refresh simulation status.");
          throw error;
        }
      } finally {
        this.simulationRun.loading = false;
      }
    },

    async stopSimulation() {
      try {
        const data = await stopSimulationApi({
          simulation_id: this.simulationId,
          run_id: this.simulationRun.runId,
        });
        this.simulationRun.status = data.status || "stopped";
        this.persist();
        return data;
      } catch (error) {
        this.simulationRun.error = normalizeError(error, "Could not stop simulation.");
        throw error;
      }
    },

    async loadVariantResults() {
      // Variant results come from the campaign report, loaded in generateReport().
      // This is a no-op kept for compatibility; generateReport populates simulationRun.results.
      return this.simulationRun.results;
    },

    async generateReport() {
      if (!this.simulationCompleted) {
        this.report.error = "Complete a simulation before generating the report.";
        return null;
      }
      if (!this.campaignId) {
        this.report.error = "No campaign ID found. Re-run the simulation.";
        return null;
      }

      this.report.loading = true;
      this.report.error = null;
      try {
        // Step 1: Kick off scoring + recommendation generation
        const task = await generateCampaignRecommendationsApi({
          campaign_id: this.campaignId,
          graph_id: this.graphId,
        });

        // Step 2: Poll task until complete
        if (task.task_id) {
          await this._pollCampaignReportTask(task.task_id);
        }

        // Step 3: Fetch the finished campaign report (has real metrics)
        const campaignReport = await getCampaignReportApi(this.campaignId);
        // Map campaign report to the shape the UI expects
        this.report.data = this._normalizeCampaignReport(campaignReport);
        this.simulationRun.results = campaignReport.scored_variants || [];
        this.persist();
        return this.report.data;
      } catch (error) {
        this.report.error = normalizeError(error, "Report generation failed.");
        throw error;
      } finally {
        this.report.loading = false;
      }
    },

    async _pollCampaignReportTask(taskId) {
      const MAX_ATTEMPTS = 60; // 5 min at 5s intervals
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        await new Promise((r) => setTimeout(r, 5000));
        try {
          const task = await getGraphTaskApi(taskId);
          if (task.status === "completed") return task;
          if (task.status === "failed") throw new Error(task.message || "Report generation failed.");
        } catch (err) {
          if (err?.message?.includes("Report generation failed")) throw err;
          // Network glitch — continue polling
        }
      }
      throw new Error("Report generation timed out.");
    },

    _normalizeCampaignReport(campaignReport) {
      const scored = campaignReport.scored_variants || [];
      // Sort by engagement_score descending
      const ranked = [...scored].sort((a, b) => (b.engagement_score || 0) - (a.engagement_score || 0));
      const best = ranked[0] || {};
      return {
        // Narrative markdown text
        markdown_content: campaignReport.report_text || "",
        // Structured metrics fields (matched to what Step4Report.vue renders)
        executive_summary: campaignReport.executive_summary || (() => {
          const rt = campaignReport.report_text || "";
          // Extract the content under the Executive Summary heading
          const match = rt.match(/##\s*\d*\.?\s*Executive Summary\s*\n+([\s\S]*?)(?=\n##|\n---|\n#\s|$)/i);
          if (match) return match[1].trim();
          // Fallback: skip any preamble lines before the first markdown heading
          const afterHeading = rt.replace(/^[\s\S]*?^#\s/m, "# ");
          const firstSection = afterHeading.split("\n\n").slice(1).find(p => p.trim().length > 40) || "";
          return firstSection.trim();
        })(),
        top_recommendation: (() => {
          const tr = campaignReport.top_recommendation;
          if (tr) {
            return {
              variant_id: tr.best_variant_id || tr.variant_id || best.variant_id,
              variant_name: tr.best_variant_name || tr.variant_name || best.variant_name,
              reason: tr.one_line_rationale || tr.reason || `Highest engagement at ${best.engagement_rate_pct ?? 0}%.`,
            };
          }
          return {
            variant_id: best.variant_id,
            variant_name: best.variant_name,
            reason: `Highest engagement at ${best.engagement_rate_pct ?? 0}%.`,
          };
        })(),
        ranked_variants: ranked.map((v, i) => ({
          rank: i + 1,
          variant_id: v.variant_id,
          variant_name: v.variant_name,
          channel: v.channel,
          content_format: v.content_format,
          engagement_rate_pct: v.engagement_rate_pct ?? 0,
          trend: v.trend || "flat",
        })),
        segment_performance: (() => {
          // Prefer explicit segment_scores if present on any variant
          if (best.segment_scores?.length) {
            return best.segment_scores.map((s) => ({
              segment: s.segment,
              best_variant_id: best.variant_id,
              engagement_rate_pct: s.engagement_rate_pct ?? 0,
            }));
          }
          // Derive from target_segment on each scored variant
          const bySegment = {};
          for (const v of ranked) {
            const seg = v.target_segment || "All";
            if (!bySegment[seg] || v.engagement_score > bySegment[seg].engagement_score) {
              bySegment[seg] = v;
            }
          }
          return Object.entries(bySegment).map(([segment, v]) => ({
            segment,
            best_variant_id: v.variant_id,
            best_variant_name: v.variant_name,
            engagement_rate_pct: v.engagement_rate_pct ?? 0,
          })).sort((a, b) => b.engagement_rate_pct - a.engagement_rate_pct);
        })(),
        channel_effectiveness: Object.entries(
          ranked.reduce((acc, v) => {
            const ch = v.channel || "unknown";
            if (!acc[ch]) acc[ch] = { total: 0, count: 0 };
            acc[ch].total += v.engagement_rate_pct || 0;
            acc[ch].count += 1;
            return acc;
          }, {}),
        ).map(([channel, { total, count }]) => ({
          channel,
          average_engagement_rate_pct: Math.round((total / count) * 100) / 100,
        })),
        strategic_recommendations: (() => {
          // Prefer structured field from backend
          if (Array.isArray(campaignReport.strategic_recommendations) && campaignReport.strategic_recommendations.length) {
            return campaignReport.strategic_recommendations;
          }
          // Extract bullet points from the Recommendations section of report_text
          const rt = campaignReport.report_text || "";
          const recSection = rt.match(/##\s*\d*\.?\s*(?:Top\s*\d*\s*)?Recommendations?\s*\n+([\s\S]*?)(?=\n##|\n---|\n#\s|$)/i);
          if (recSection) {
            const bullets = recSection[1].match(/\|\s*\*\*\d+\*\*\s*\|\s*\*\*([^|]+)\*\*/g);
            if (bullets?.length) {
              return bullets.map(b => b.replace(/\|\s*\*\*\d+\*\*\s*\|\s*\*\*/, "").replace(/\*\*$/, "").trim());
            }
            // Plain bullet list fallback
            const lines = recSection[1].split("\n").filter(l => /^[-*\d]/.test(l.trim()));
            if (lines.length) return lines.map(l => l.replace(/^[-*\d.]+\s*/, "").trim()).filter(Boolean);
          }
          return [];
        })(),
      };
    },

    async loadReport(reportId = this.reportId) {
      // Legacy fallback: load from the text-based report endpoint
      try {
        const report = await getReport(reportId);
        this.report.data = { ...(this.report.data || {}), ...report };
        this.reportId = report.report_id || reportId;
        this.persist();
        return report;
      } catch (error) {
        this.report.error = normalizeError(error, "Could not load report.");
        throw error;
      }
    },

    async loadCampaignReport(campaignId = this.campaignId) {
      this.report.loading = true;
      this.report.error = null;
      try {
        const data = await getCampaignReportApi(campaignId);
        this.report.data = this._normalizeCampaignReport(data);
        this.simulationRun.status = "completed";
        this.persist();
        return this.report.data;
      } catch (error) {
        this.report.error = normalizeError(error, "Could not load campaign report.");
        throw error;
      } finally {
        this.report.loading = false;
      }
    },

    async interviewPersona(personaId, question) {
      if (!this.report.data || this.personas.items.length === 0) {
        throw new Error("Generate a report and personas before interviewing personas.");
      }
      const userMessage = {
        role: "user",
        persona_id: personaId,
        content: question,
        created_at: new Date().toISOString(),
      };
      this.interviewMessages.push(userMessage);
      const answer = await interviewPersonaApi({
        simulation_id: this.simulationId,
        campaign_id: this.campaignId,
        persona_id: personaId,
        question,
      });
      this.interviewMessages.push({
        role: "assistant",
        persona_id: answer.persona_id,
        persona_name: answer.persona_name,
        content: answer.answer,
        created_at: new Date().toISOString(),
      });
      this.persist();
      return answer;
    },

    async loadHistory() {
      this.history.loading = true;
      this.history.error = null;
      try {
        const data = await getHistory();
        // getHistory() returns the unwrapped payload (array or object depending on St())
        // Handle both: raw array OR object with .data/.items/.history
        const raw = Array.isArray(data) ? data : (data?.data || data?.items || data?.history || []);
        this.history.items = raw.map((c) => {
          // Find the best completed variant (for "top variant" column)
          const variants = c.variants || [];
          const completed = variants.filter((v) => v.status === "completed");
          const topVariant = completed[0] || variants[0];
          return {
            // IDs
            simulation_id: c.simulation_id || c.campaign_id,
            campaign_id:   c.campaign_id,
            // Display
            project_name:  c.brand_name || c.campaign_goal || "Campaign",
            status:        c.overall_status || c.status || "pending",
            variants_count: c.variant_count ?? variants.length,
            top_variant_name: topVariant?.variant_name || null,
            // Dates
            created_at: c.created_at,
            updated_at: c.updated_at || c.created_at,
            // Navigation
            has_report: c.has_report || false,
            report_id:  c.report_id || null,
            graph_id:   c.graph_id || null,
            // Raw
            _raw: c,
          };
        });
        this.persist();
        return data;
      } catch (error) {
        this.history.error = normalizeError(error, "Could not load campaign history.");
        throw error;
      } finally {
        this.history.loading = false;
      }
    },

    goToStep(stepNumber) {
      if (!this.canNavigateToStep(stepNumber) && stepNumber !== this.currentStep) {
        const notices = {
          2: "Upload a brand brief and build the graph before continuing.",
          3: "Generate personas before defining campaign variants.",
          4: "Start and complete a simulation before opening the report.",
          5: "Generate the recommendation report before interviewing personas.",
        };
        this.setNotice(notices[stepNumber] || "Complete the previous step first.");
        return false;
      }
      this.currentStep = stepNumber;
      this.persist();

      const routeName = router.currentRoute.value.name;
      const workflowShellRoutes = new Set(["report", "interaction", "simulation-run"]);
      if (workflowShellRoutes.has(routeName)) {
        router.push({ name: "process" });
      }

      return true;
    },

    resetProject() {
      this.currentStep = 1;
      this.notice = null;
      this.project = null;
      this.simulationId = null;
      this.graphId = null;
      this.simulationPrepared = false;
      this.campaignId = null;
      this.reportId = null;
      this.uploadedFile = null;
      this.graph = { nodes: [], edges: [], loading: false, error: null, progress: 0, statusText: "" };
      this.personas = { items: [], loading: false, error: null, progress: 0 };
      this.variants = [];
      this.simulationRun = {
        runId: null,
        status: "idle",
        progress: 0,
        variants: [],
        results: [],
        loading: false,
        error: null,
      };
      this.report = { data: null, loading: false, error: null };
      this.interviewMessages = [];
      [PROJECT_KEY, STEP_KEY, VARIANTS_KEY, MOCK_STATE_KEY].forEach((key) => localStorage.removeItem(key));
      // A designer chat session is scoped to the simulation it was started
      // against — don't let it leak into the next campaign.
      useDesignerStore().reset();
    },
  },
});
