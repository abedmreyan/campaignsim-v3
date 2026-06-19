import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/Home.vue";
import Process from "@/views/Process.vue";
import GraphPage from "@/views/GraphPage.vue";
import SimulationRunView from "@/views/SimulationRunView.vue";
import Step4Report from "@/views/Step4Report.vue";
import Step5Interaction from "@/views/Step5Interaction.vue";
import HistoryDatabase from "@/views/HistoryDatabase.vue";
import CampaignReportView from "@/views/CampaignReportView.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const routes = [
  {
    path: "/",
    name: "home",
    component: Home,
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
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach((to) => {
  const store = useCampaignStore();
  if (to.name === "simulation-run" && store.variants.length < 2) {
    store.setNotice("Create at least two campaign variants before starting a simulation.");
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
