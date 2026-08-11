<template>
  <div class="project-library">
    <div class="section-header">
      <div class="section-line"></div>
      <span class="section-title">Your Briefs &amp; Knowledge Graphs</span>
      <div class="section-line"></div>
    </div>

    <div v-if="loading" class="library-state">
      <div class="spinner"></div>
      <p>Loading your projects...</p>
    </div>

    <div v-else-if="projects.length === 0" class="library-state empty">
      <p class="empty-text">No briefs uploaded yet. Upload a brief above to get started.</p>
    </div>

    <div v-else class="cards-grid">
      <div
        v-for="project in projects"
        :key="project.project_id"
        class="brief-card"
        :class="['status-' + project.status]"
        @click="openProject(project)"
      >
        <div class="card-top">
          <span class="card-name">{{ project.name || 'Unnamed Brief' }}</span>
          <span class="status-badge" :class="statusClass(project.status)">
            {{ statusLabel(project.status) }}
          </span>
        </div>

        <div class="card-meta">
          <span class="meta-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            {{ project.files?.length || 0 }} file{{ (project.files?.length || 0) !== 1 ? 's' : '' }}
          </span>
          <span class="meta-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            {{ formatDate(project.created_at) }}
          </span>
        </div>

        <div v-if="project.graph_id" class="card-graph">
          <span class="graph-label">Graph</span>
          <span class="graph-id">{{ project.graph_id.slice(0, 16) }}...</span>
        </div>

        <div class="card-footer">
          <button class="open-btn" @click.stop="openProject(project)">
            Open Project
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects } from '../api/graph'

const router = useRouter()
const projects = ref([])
const loading = ref(false)

const loadProjects = async () => {
  try {
    loading.value = true
    const res = await listProjects(50)
    projects.value = (res.data || []).sort((a, b) => {
      return new Date(b.created_at || 0) - new Date(a.created_at || 0)
    })
  } catch (err) {
    console.error('Failed to load projects:', err)
    projects.value = []
  } finally {
    loading.value = false
  }
}

const openProject = (project) => {
  router.push({ name: 'Process', params: { projectId: project.project_id } })
}

const statusLabel = (status) => {
  const map = {
    created: 'Created',
    ontology_generated: 'Analysed',
    graph_building: 'Building KG',
    graph_completed: 'KG Ready',
    failed: 'Failed',
  }
  return map[status] || status
}

const statusClass = (status) => {
  if (status === 'graph_completed') return 'badge-green'
  if (status === 'graph_building') return 'badge-amber'
  if (status === 'failed') return 'badge-red'
  return 'badge-grey'
}

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(loadProjects)
</script>

<style scoped>
.project-library {
  padding: 2rem 1.5rem;
  width: 100%;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.4), transparent);
}

.section-title {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(16, 185, 129, 0.8);
  white-space: nowrap;
}

.library-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
  color: rgba(255, 255, 255, 0.4);
}

.library-state.empty .empty-text {
  font-size: 0.85rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-top-color: rgba(16, 185, 129, 0.8);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}

.brief-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.25rem;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, transform 0.15s;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.brief-card:hover {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.05);
  transform: translateY(-2px);
}

.brief-card.status-failed {
  border-color: rgba(239, 68, 68, 0.2);
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.card-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.3;
  flex: 1;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.status-badge {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-green {
  background: rgba(16, 185, 129, 0.15);
  color: rgba(16, 185, 129, 0.9);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-amber {
  background: rgba(245, 158, 11, 0.15);
  color: rgba(245, 158, 11, 0.9);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.badge-red {
  background: rgba(239, 68, 68, 0.15);
  color: rgba(239, 68, 68, 0.9);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.badge-grey {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.card-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.4);
}

.meta-item svg {
  opacity: 0.7;
  flex-shrink: 0;
}

.card-graph {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: 6px;
}

.graph-label {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(16, 185, 129, 0.7);
}

.graph-id {
  font-size: 0.68rem;
  font-family: monospace;
  color: rgba(255, 255, 255, 0.35);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  margin-top: auto;
}

.open-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: transparent;
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: rgba(16, 185, 129, 0.8);
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  width: 100%;
  justify-content: center;
}

.open-btn:hover {
  background: rgba(16, 185, 129, 0.12);
  color: rgba(16, 185, 129, 1);
}
</style>
