<template>
  <div class="campaign-report-panel">
    <!-- Header Bar -->
    <div class="panel-header">
      <div class="header-left">
        <span class="panel-label">Campaign Recommendation Report</span>
        <span v-if="campaignId" class="campaign-id-badge">{{ campaignId }}</span>
      </div>
      <div class="header-actions">
        <button
          v-if="reportData && !isGenerating"
          class="action-btn secondary"
          @click="triggerGenerate(true)"
        >Regenerate</button>
        <button
          v-if="!reportData && !isGenerating"
          class="action-btn primary"
          :disabled="!campaignId"
          @click="triggerGenerate(false)"
        >Generate Recommendations</button>
      </div>
    </div>

    <!-- Generating State -->
    <div v-if="isGenerating" class="generating-state">
      <div class="spinner"></div>
      <p class="generating-text">Running ReACT recommendation agent…</p>
      <p class="generating-sub">This may take 30–60 seconds depending on the number of variants.</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMsg" class="error-state">
      <div class="error-icon">!</div>
      <p class="error-text">{{ errorMsg }}</p>
      <button class="action-btn primary" @click="triggerGenerate(false)">Retry</button>
    </div>

    <!-- No Campaign ID -->
    <div v-else-if="!campaignId" class="empty-state">
      <p>No campaign ID provided. Navigate here from a completed A/B simulation.</p>
    </div>

    <!-- No Report Yet -->
    <div v-else-if="!reportData" class="empty-state">
      <p>No recommendation report found for this campaign.</p>
      <p class="empty-sub">Click <strong>Generate Recommendations</strong> to run the analysis.</p>
    </div>

    <!-- Report Content -->
    <div v-else class="report-content">
      <!-- Top Recommendation Card -->
      <div v-if="topRec" class="top-rec-card">
        <div class="card-label">Top Recommendation</div>
        <h2 class="rec-title">{{ topRec.variant_name || topRec.variant_id || 'See Full Report Below' }}</h2>
        <div class="rec-meta-row">
          <span v-if="topRec.channel" class="meta-chip channel">{{ topRec.channel }}</span>
          <span v-if="topRec.content_format" class="meta-chip format">{{ topRec.content_format }}</span>
          <span v-if="topRec.target_segment" class="meta-chip segment">{{ topRec.target_segment }}</span>
          <span v-if="topRec.engagement_score != null" class="meta-chip score">
            Score: {{ (topRec.engagement_score * 100).toFixed(1) }}%
          </span>
        </div>
        <p v-if="topRec.rationale" class="rec-rationale">{{ topRec.rationale }}</p>
      </div>

      <!-- Variant Rankings Table -->
      <div v-if="scoredVariants && scoredVariants.length > 0" class="variant-table-section">
        <h3 class="section-title">Variant Rankings</h3>
        <table class="variant-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Variant</th>
              <th>Channel</th>
              <th>Format</th>
              <th>Segment</th>
              <th>Engagement</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(v, idx) in scoredVariants"
              :key="v.variant_id"
              :class="{ 'top-row': idx === 0 }"
            >
              <td class="rank-cell">
                <span class="rank-badge" :class="{ gold: idx === 0, silver: idx === 1, bronze: idx === 2 }">
                  {{ idx + 1 }}
                </span>
              </td>
              <td class="variant-name-cell">{{ v.variant_name || v.variant_id }}</td>
              <td>{{ v.channel || '—' }}</td>
              <td>{{ v.content_format || '—' }}</td>
              <td>{{ v.target_segment || 'All' }}</td>
              <td class="score-cell">
                <div class="score-bar-wrap">
                  <div
                    class="score-bar"
                    :style="{ width: scoreBarWidth(v.engagement_score) }"
                    :class="{ 'bar-top': idx === 0 }"
                  ></div>
                  <span class="score-label">{{ formatScore(v.engagement_score) }}</span>
                </div>
              </td>
              <td class="actions-cell">
                <span class="action-count positive">+{{ v.positive_actions || 0 }}</span>
                <span class="action-count negative">-{{ v.negative_actions || 0 }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Engagement over rounds + funnel breakdown -->
      <div v-if="scoredVariants.length > 0" class="charts-section theme-scope">
        <div class="chart-block">
          <h3 class="section-title">Engagement per round</h3>
          <PerRoundChart :variants="scoredVariants" />
        </div>
        <div v-if="topFunnel" class="chart-block">
          <h3 class="section-title">Funnel — {{ scoredVariants[0].variant_name || scoredVariants[0].variant_id }}</h3>
          <FunnelChart :funnel="topFunnel" />
        </div>
      </div>

      <!-- Full Report Text -->
      <div v-if="reportText" class="full-report-section">
        <h3 class="section-title">Full Analysis Report</h3>
        <div class="report-markdown" v-html="renderMarkdown(reportText)"></div>
      </div>

      <!-- Insight Agent + Iteration Lineage -->
      <div class="insight-section">
        <div class="insight-section__header">
          <h3 class="section-title">Iterate on this campaign</h3>
          <RouterLink :to="{ name: 'IterationCompare', params: { campaignId } }" class="iteration-history-link">
            View iteration history →
          </RouterLink>
        </div>
        <InsightChatPanel :campaign-id="campaignId" />
      </div>
    </div>

    <!-- System Logs -->
    <div v-if="logs.length > 0" class="log-panel">
      <div class="log-header">Log</div>
      <div class="log-scroll" ref="logScroll">
        <div v-for="(entry, i) in logs" :key="i" class="log-line">
          <span class="log-time">{{ entry.time }}</span>
          <span class="log-msg">{{ entry.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { generateCampaignRecommendations, getCampaignReport, getAbStatus } from '../api/simulation'
import PerRoundChart from './reports/PerRoundChart.vue'
import FunnelChart from './reports/FunnelChart.vue'
import InsightChatPanel from './reports/InsightChatPanel.vue'

const props = defineProps({
  campaignId: { type: String, default: null }
})

const emit = defineEmits(['add-log', 'update-status'])

// State
const isGenerating = ref(false)
const reportData = ref(null)
const errorMsg = ref(null)
const logs = ref([])
const logScroll = ref(null)

// Derived
const topRec = computed(() => reportData.value?.top_recommendation || null)
const scoredVariants = computed(() => reportData.value?.scored_variants || [])
const reportText = computed(() => reportData.value?.report_text || null)
const topFunnel = computed(() => {
  const funnel = scoredVariants.value[0]?.funnel
  return funnel && Object.keys(funnel).length ? funnel : null
})

// Max score for bar scaling
const maxScore = computed(() => {
  const variants = scoredVariants.value
  if (!variants.length) return 1
  return Math.max(...variants.map(v => v.engagement_score || 0), 0.01)
})

// Helpers
const addLog = (msg) => {
  const now = new Date()
  const time = now.toLocaleTimeString('en-US', { hour12: false }) + '.' + String(now.getMilliseconds()).padStart(3, '0')
  logs.value.push({ time, msg })
  if (logs.value.length > 100) logs.value.shift()
  emit('add-log', msg)
  nextTick(() => {
    if (logScroll.value) logScroll.value.scrollTop = logScroll.value.scrollHeight
  })
}

const formatScore = (score) => {
  if (score == null) return '—'
  return (score * 100).toFixed(1) + '%'
}

const scoreBarWidth = (score) => {
  if (score == null || maxScore.value === 0) return '0%'
  return Math.round((score / maxScore.value) * 100) + '%'
}

// Simple markdown renderer (reuses same pattern as Step5Interaction)
const renderMarkdown = (content) => {
  if (!content) return ''
  let html = content
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/^#### (.+)$/gm, '<h5 class="md-h5">$1</h5>')
    .replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li class="md-li">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="md-oli">$2</li>')
    .replace(/(<li class="md-li">.*?<\/li>\s*)+/g, '<ul class="md-ul">$&</ul>')
    .replace(/(<li class="md-oli">.*?<\/li>\s*)+/g, '<ol class="md-ol">$&</ol>')
    .replace(/\n\n/g, '</p><p class="md-p">')
  return `<p class="md-p">${html}</p>`
}

// Load existing report on mount
const loadReport = async () => {
  if (!props.campaignId) return
  try {
    addLog(`Checking for existing report: ${props.campaignId}`)
    const res = await getCampaignReport(props.campaignId)
    if (res.success && res.data?.report_text) {
      reportData.value = res.data
      addLog('Existing report loaded.')
      emit('update-status', 'completed')
    } else {
      addLog('No report found. Click "Generate Recommendations" to create one.')
    }
  } catch {
    addLog('Could not fetch report — backend may be unreachable.')
  }
}

// Polling
let pollTimer = null
const stopPolling = () => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }

const pollForReport = () => {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await getCampaignReport(props.campaignId)
      if (res.success && res.data?.report_text) {
        reportData.value = res.data
        isGenerating.value = false
        stopPolling()
        addLog('Recommendation report ready.')
        emit('update-status', 'completed')
      }
    } catch {
      // keep polling
    }
  }, 4000)
}

const triggerGenerate = async (force = false) => {
  if (!props.campaignId) return
  isGenerating.value = true
  errorMsg.value = null
  emit('update-status', 'processing')
  addLog(`Triggering recommendation generation (force=${force})…`)
  try {
    const res = await generateCampaignRecommendations({
      campaign_id: props.campaignId,
      force_regenerate: force
    })
    if (res.success) {
      addLog('Generation task started. Polling for result…')
      pollForReport()
    } else {
      isGenerating.value = false
      errorMsg.value = res.error || 'Failed to start recommendation generation.'
      addLog(`Error: ${errorMsg.value}`)
      emit('update-status', 'error')
    }
  } catch (err) {
    isGenerating.value = false
    errorMsg.value = err.message
    addLog(`Exception: ${err.message}`)
    emit('update-status', 'error')
  }
}

onMounted(() => {
  loadReport()
})

onUnmounted(() => {
  stopPolling()
})

watch(() => props.campaignId, (newId) => {
  if (newId) loadReport()
})
</script>

<style scoped>
.campaign-report-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

/* Header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #EAEAEA;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-label {
  font-size: 13px;
  font-weight: 700;
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.campaign-id-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  background: #F0F0F0;
  padding: 2px 8px;
  border-radius: 4px;
  color: #555;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #000;
  color: #FFF;
}

.action-btn.primary:hover { background: #333; }
.action-btn.primary:disabled { background: #CCC; cursor: not-allowed; }

.action-btn.secondary {
  background: #F0F0F0;
  color: #333;
}

.action-btn.secondary:hover { background: #E0E0E0; }

/* States */
.generating-state,
.error-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  text-align: center;
  color: #666;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #E0E0E0;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.generating-text { font-size: 15px; font-weight: 600; color: #333; margin: 0; }
.generating-sub { font-size: 12px; color: #999; margin: 0; }

.error-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #F44336;
  color: #FFF;
  font-weight: 800;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-text { font-size: 14px; color: #333; margin: 0; }

.empty-sub { font-size: 12px; color: #999; margin: 0; }

/* Report Content */
.report-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* Top Recommendation Card */
.top-rec-card {
  background: linear-gradient(135deg, #F8F9FF 0%, #EEF2FF 100%);
  border: 1px solid #C7D2FE;
  border-radius: 12px;
  padding: 24px;
}

.card-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #6366F1;
  margin-bottom: 8px;
}

.rec-title {
  font-size: 22px;
  font-weight: 700;
  color: #111;
  margin: 0 0 12px 0;
}

.rec-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.meta-chip {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
}

.meta-chip.channel  { background: #FEF3C7; color: #92400E; }
.meta-chip.format   { background: #EDE9FE; color: #5B21B6; }
.meta-chip.segment  { background: #D1FAE5; color: #065F46; }
.meta-chip.score    { background: #000; color: #FFF; }

.rec-rationale {
  font-size: 13px;
  color: #444;
  line-height: 1.6;
  margin: 0;
}

/* Variant Table */
.variant-table-section { display: flex; flex-direction: column; gap: 12px; }

.section-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #111;
  margin: 0;
}

.variant-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.variant-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #444;
  padding: 8px 12px;
  border-bottom: 2px solid #D1D5DB;
}

.variant-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #EBEBEB;
  color: #111;
}

.variant-table tr.top-row td { background: #FAFAFA; }

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  background: #D1D5DB;
  color: #111;
}

.rank-badge.gold   { background: #FDE68A; color: #92400E; }
.rank-badge.silver { background: #E5E7EB; color: #374151; }
.rank-badge.bronze { background: #FDE8D8; color: #9A3412; }

.variant-name-cell { font-weight: 600; color: #111; }

.score-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-bar {
  height: 6px;
  background: #CBD5E1;
  border-radius: 3px;
  min-width: 4px;
  transition: width 0.3s;
}

.score-bar.bar-top { background: #6366F1; }

.score-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #111; white-space: nowrap; font-weight: 600; }

.actions-cell { display: flex; gap: 8px; align-items: center; }

.action-count {
  font-size: 11px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  padding: 2px 6px;
  border-radius: 4px;
}

.action-count.positive { background: #D1FAE5; color: #065F46; }
.action-count.negative { background: #FEE2E2; color: #991B1B; }

/* Charts (per-round + funnel) — imported chart components use CS's dark-
   theme design tokens by default; override them locally to match this
   panel's light palette since custom properties still cascade through
   scoped child styles. */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.theme-scope {
  --color-text: #111;
  --color-text-muted: #555;
  --color-text-subtle: #999;
  --color-border: #EAEAEA;
  --color-bg-elevated: #FFF;
  --color-surface-muted: #F0F0F0;
  --radius-sm: 6px;
  --radius-full: 999px;
}

.chart-block { display: flex; flex-direction: column; gap: 12px; min-width: 0; }

/* Full Report */
.full-report-section { display: flex; flex-direction: column; gap: 12px; }

.report-markdown {
  font-size: 14px;
  line-height: 1.7;
  color: #111;
}

.report-markdown :deep(.md-h2) { font-size: 18px; font-weight: 700; margin: 20px 0 8px; color: #111; }
.report-markdown :deep(.md-h3) { font-size: 15px; font-weight: 700; margin: 16px 0 6px; color: #222; }
.report-markdown :deep(.md-h4) { font-size: 13px; font-weight: 700; margin: 12px 0 4px; color: #333; }
.report-markdown :deep(.md-p) { margin: 8px 0; }
.report-markdown :deep(.md-ul) { padding-left: 20px; margin: 8px 0; }
.report-markdown :deep(.md-li) { margin: 4px 0; }
.report-markdown :deep(strong) { color: #111; }
.report-markdown :deep(.code-block) { background: #F8F8F8; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
.report-markdown :deep(.inline-code) { background: #F0F0F0; padding: 1px 4px; border-radius: 3px; font-family: monospace; font-size: 12px; }

/* Log Panel */
.log-panel {
  flex-shrink: 0;
  max-height: 140px;
  border-top: 1px solid #EAEAEA;
  display: flex;
  flex-direction: column;
}

.log-header {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #444;
  padding: 6px 16px 4px;
  background: #F5F5F5;
  border-bottom: 1px solid #E5E5E5;
}

.log-scroll {
  overflow-y: auto;
  flex: 1;
  padding: 4px 16px 8px;
  background: #FAFAFA;
}

.log-line {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #222;
  line-height: 1.6;
  display: flex;
  gap: 10px;
}

.log-time { color: #555; flex-shrink: 0; font-weight: 600; }
.log-msg { word-break: break-word; }
</style>
