import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/Home.vue";
import Process from "@/views/Process.vue";
import GraphPage from "@/views/GraphPage.vue";
import SimulationRunView from "@/views/SimulationRunView.vue";
import Step4Report from "@/views/Step4Report.vue";
import Step5Interaction from "@/views/Step5Interaction.vue";
import HistoryDatabase from "@/views/HistoryDatabase.vue";
import CampaignReportView from "@/views/CampaignReportView.vue";
import DesignerSessionView from "@/views/DesignerSessionView.vue";
import IterationCompareView from "@/views/IterationCompareView.vue";
import DataView from "@/views/DataView.vue";
import SegmentsView from "@/views/SegmentsView.vue";
import LoginView from "@/views/LoginView.vue";
import SignupView from "@/views/SignupView.vue";
import BrandBriefView from "@/views/BrandBriefView.vue";
import { useCampaignStore } from "@/stores/campaignStore";
import { useAuthStore } from "@/stores/authStore";
import { isMockMode } from "@/api/campaignApi";

const PUBLIC_ROUTE_NAMES = new Set(["home", "login", "signup"]);

const routes = [
  {
    path: "/",
    name: "home",
    component: Home,
  },
  {
    path: "/login",
    name: "login",
    component: LoginView,
  },
  {
    path: "/signup",
    name: "signup",
    component: SignupView,
  },
  {
    path: "/briefs",
    name: "briefs",
    component: BrandBriefView,
  },
  {
    path: "/process",
    name: "process",
    component: Process,
  },
  {
    path: "/graph",
    name: "graph",
    component: GraphPage,
  },
  {
    path: "/simulation/:simulationId/run",
    name: "simulation-run",
    component: SimulationRunView,
  },
  {
    path: "/report/:reportId",
    name: "report",
    component: Step4Report,
  },
  {
    path: "/interaction/:simulationId",
    name: "interaction",
    component: Step5Interaction,
  },
  {
    path: "/history",
    name: "history",
    component: HistoryDatabase,
  },
  {
    path: "/campaign/:campaignId/report",
    name: "CampaignReport",
    component: CampaignReportView,
  },
  {
    path: "/campaign/:campaignId/iterations",
    name: "IterationCompare",
    component: IterationCompareView,
  },
  {
    path: "/designer/sessions/:sessionId",
    name: "designer-session",
    component: DesignerSessionView,
  },
  {
    path: "/audience/data",
    name: "audience-data",
    component: DataView,
  },
  {
    path: "/audience/segments",
    name: "audience-segments",
    component: SegmentsView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach(async (to) => {
  // Mock mode is a sandboxed, backend-free demo — auth doesn't apply.
  if (!isMockMode && !PUBLIC_ROUTE_NAMES.has(to.name)) {
    const auth = useAuthStore();

    if (!auth.checkedSession) {
      await auth.fetchMe();
    }

    if (!auth.isAuthenticated) {
      return { name: "login", query: { redirect: to.fullPath } };
    }
  }

  if (!isMockMode && ["login", "signup"].includes(to.name)) {
    const auth = useAuthStore();
    if (!auth.checkedSession) {
      await auth.fetchMe();
    }
    if (auth.isAuthenticated) {
      return { name: "briefs" };
    }
  }

  const store = useCampaignStore();
  if (to.name === "simulation-run" && store.variants.length < 1) {
    store.setNotice("Create at least one campaign variant before starting a simulation.");
    return { name: "process" };
  }

  if (to.name === "report" && store.simulationRun.status !== "completed" && !store.report.data) {
    store.setNotice("Run a simulation before opening the report.");
    return { name: "process" };
  }

  if (to.name === "interaction" && (!store.report.data || store.personas.items.length === 0)) {
    store.setNotice("Generate a report and personas before interviewing personas.");
    return { name: "process" };
  }

  return true;
});

export default router;
