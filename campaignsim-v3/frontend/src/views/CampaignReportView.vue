<template>
  <AppLayout>
    <div class="campaign-report-view">
      <PageHeader eyebrow="Campaign" title="Recommendations report" description="Live A/B results and the knowledge graph behind them.">
        <template #actions>
          <div class="view-switcher">
            <button
              v-for="mode in ['graph', 'split', 'workbench']"
              :key="mode"
              class="switch-btn"
              :class="{ active: viewMode === mode }"
              @click="viewMode = mode"
            >
              {{ { graph: 'Graph', split: 'Split', workbench: 'Workbench' }[mode] }}
            </button>
          </div>
          <span class="status-indicator" :class="statusClass">
            <span class="dot"></span>
            {{ statusText }}
          </span>
        </template>
      </PageHeader>

      <!-- Main Content Area -->
      <main class="content-area">
        <!-- Left Panel: Graph -->
        <div class="panel-wrapper left" :style="leftPanelStyle">
          <GraphPanel
            :graphData="graphData"
            :loading="graphLoading"
            :currentPhase="4"
            :isSimulating="false"
            @refresh="refreshGraph"
            @toggle-maximize="toggleMaximize('graph')"
          />
        </div>

        <!-- Right Panel: Campaign Report -->
        <div class="panel-wrapper right" :style="rightPanelStyle">
          <Step5CampaignReport
            :campaignId="currentCampaignId"
            @add-log="addLog"
            @update-status="updateStatus"
          />
        </div>
      </main>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import GraphPanel from '../components/graph/GraphPanel.vue'
import Step5CampaignReport from '../components/Step5CampaignReport.vue'
import { getGraphRelations, getAbStatus } from '@/api/campaignApi'

const route = useRoute()

const props = defineProps({
  campaignId: String
})

// Layout
const viewMode = ref('workbench')

// Data
const currentCampaignId = ref(route.params.campaignId)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing')

// Layout computed
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph')     return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph')     return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const statusClass = computed(() => currentStatus.value)
const statusText = computed(() => {
  if (currentStatus.value === 'error')     return 'Error'
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Generating'
})

// Helpers
const addLog = (msg) => {
  const now = new Date()
  const time = now.toLocaleTimeString('en-US', { hour12: false }) + '.' + String(now.getMilliseconds()).padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) systemLogs.value.shift()
}

const updateStatus = (status) => {
  currentStatus.value = status
}

const toggleMaximize = (target) => {
  viewMode.value = viewMode.value === target ? 'split' : target
}

// Load graph from campaign metadata
const loadGraphForCampaign = async () => {
  if (!currentCampaignId.value) return
  try {
    const data = await getAbStatus(currentCampaignId.value)
    const graphId = data.graph_id
    if (graphId) await loadGraph(graphId)
  } catch {
    // graph is optional — don't block on failure
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    graphData.value = await getGraphRelations(graphId)
    addLog('Graph data loaded.')
  } catch (err) {
    addLog(`Graph load failed: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  loadGraphForCampaign()
}

onMounted(() => {
  addLog(`Campaign report view initialised: ${currentCampaignId.value}`)
  loadGraphForCampaign()
})
</script>

<style scoped>
.campaign-report-view {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF9800; animation: pulse 1s infinite; }
.status-indicator.completed .dot  { background: #4CAF50; }
.status-indicator.error .dot      { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

.content-area {
  flex: 1;
  min-height: 0;
  display: flex;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 0.625rem);
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}
</style>
