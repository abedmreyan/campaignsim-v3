<template>
  <div class="lock-scroll-cards">
    <div
      v-for="(item, i) in cardItems"
      :key="i"
      class="stat-card"
      :style="{ '--accent': item.accent }"
    >
      <div class="stat-icon">{{ item.icon }}</div>
      <div class="stat-value">{{ item.value }}</div>
      <div class="stat-label">{{ item.label }}</div>
      <div class="stat-bar">
        <div class="stat-bar-fill" :style="{ width: item.barPct + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  metrics: {
    type: Object,
    required: true,
    default: () => ({
      totalSpend: 0,
      totalImpressions: 0,
      totalClicks: 0,
      totalConversions: 0,
      clickRate: 0
    })
  }
})

function fmt(n) { return Number(n).toLocaleString() }
function fmtMoney(n) { return `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` }
function fmtPct(n) { return `${(Number(n) * 100).toFixed(2)}%` }

/**
 * Compute relative bar width (0–100) against the largest raw value
 * so the cards' bars give a proportional visual hint.
 */
const cardItems = computed(() => {
  const m = props.metrics
  const raw = [m.totalSpend, m.totalImpressions, m.totalClicks, m.totalConversions, (m.clickRate * 100)]
  const max = Math.max(...raw.map(Math.abs), 1)

  return [
    {
      icon: '💰',
      label: 'Total Spend',
      value: fmtMoney(m.totalSpend),
      barPct: Math.round((m.totalSpend / max) * 100),
      accent: '#FF4500'
    },
    {
      icon: '👁️',
      label: 'Impressions',
      value: fmt(m.totalImpressions),
      barPct: Math.round((m.totalImpressions / max) * 100),
      accent: '#6366f1'
    },
    {
      icon: '🖱️',
      label: 'Clicks',
      value: fmt(m.totalClicks),
      barPct: Math.round((m.totalClicks / max) * 100),
      accent: '#0ea5e9'
    },
    {
      icon: '✅',
      label: 'Conversions',
      value: fmt(m.totalConversions),
      barPct: Math.round((m.totalConversions / max) * 100),
      accent: '#22c55e'
    },
    {
      icon: '📈',
      label: 'Click Rate',
      value: fmtPct(m.clickRate),
      barPct: Math.round(((m.clickRate * 100) / max) * 100),
      accent: '#f59e0b'
    }
  ]
})
</script>

<style scoped>
/* ── Container ── */
.lock-scroll-cards {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

/* ── Individual card ── */
.stat-card {
  flex: 1;
  min-width: 120px;
  padding: 16px 14px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent, #FF4500);
  border-radius: 10px 10px 0 0;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow:
    0 8px 20px rgba(0, 0, 0, 0.10),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

/* ── Icon ── */
.stat-icon {
  font-size: 1.1rem;
  margin-bottom: 6px;
  line-height: 1;
}

/* ── Value ── */
.stat-value {
  font-size: 1.15rem;
  font-weight: 700;
  color: #111;
  letter-spacing: -0.5px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Label ── */
.stat-label {
  font-size: 0.72rem;
  color: #888;
  margin-top: 3px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ── Progress bar ── */
.stat-bar {
  margin-top: 10px;
  height: 3px;
  background: rgba(0, 0, 0, 0.07);
  border-radius: 2px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  background: var(--accent, #FF4500);
  border-radius: 2px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
