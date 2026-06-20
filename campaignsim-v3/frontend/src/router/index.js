import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/Home.vue";
import Process from "@/views/Process.vue";
import GraphPage from "@/views/GraphPage.vue";
import SimulationRunView from "@/views/SimulationRunView.vue";
import Step4Report from "@/views/Step4Report.vue";
import Step5Interaction from "@/views/Step5Interaction.vue";
import HistoryDatabase from "@/views/HistoryDatabase.vue";
import CampaignReportView from "@/views/CampaignReportView.vue";
import LoginView from "@/views/LoginView.vue";
import SignupView from "@/views/SignupView.vue";
import BrandBriefView from "@/views/BrandBriefView.vue";
import { useCampaignStore } from "@/stores/campaignStore";

// Routes that do not require authentication
const PUBLIC_ROUTES = new Set(["home", "login", "signup"]);

const routes = [
  { path: "/",        name: "home",    component: Home },
  { path: "/login",   name: "login",   component: LoginView },
  { path: "/signup",  name: "signup",  component: SignupView },
  { path: "/briefs",  name: "brand-brief", component: BrandBriefView },
  { path: "/process", name: "process", component: Process },
  { path: "/graph",   name: "graph",   component: GraphPage },
  {
    path: "/simulation/:simulationId/run",
    name: "simulation-run",
    component: SimulationRunView,
  },
  { path: "/report/:reportId", name: "report", component: Step4Report },
  {
    path: "/interaction/:simulationId",
    name: "interaction",
    component: Step5Interaction,
  },
  { path: "/history", name: "history", component: HistoryDatabase },
  {
    path: "/campaign/:campaignId/report",
    name: "CampaignReport",
    component: CampaignReportView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach(async (to) => {
  // Public routes need no auth check
  if (PUBLIC_ROUTES.has(to.name)) return true;

  const { useAuthStore } = await import("@/stores/authStore");
  const auth = useAuthStore();

  // Attempt cookie-based restore if not yet loaded
  if (!auth.user) {
    await auth.fetchMe();
  }

  if (!auth.user) return "/login";

  // Workflow routes additionally require a selected brand brief
  const store = useCampaignStore();
  const workflowRoutes = new Set([
    "process", "graph", "simulation-run", "report", "interaction",
  ]);

  if (workflowRoutes.has(to.name) && !store.brandBriefId) {
    store.setNotice("Select a brand brief before entering the workflow.");
    return "/briefs";
  }

  // Legacy guards from original router
  if (to.name === "simulation-run" && store.variants.length < 2) {
    store.setNotice("Create at least two campaign variants before starting a simulation.");
    return "/process";
  }
  if (to.name === "report" && store.simulationRun?.status !== "completed" && !store.report?.data) {
    store.setNotice("Run a simulation before opening the report.");
    return "/process";
  }
  if (to.name === "interaction" && (!store.report?.data || store.personas.items.length === 0)) {
    store.setNotice("Generate a report and personas before interviewing personas.");
    return "/process";
  }

  return true;
});

export default router;
