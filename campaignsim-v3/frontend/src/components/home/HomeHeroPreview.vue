<template>
  <div class="hhp" aria-hidden="true">
    <!-- Header bar -->
    <div class="hhp__bar">
      <span class="hhp__bar-dot hhp__bar-dot--r" />
      <span class="hhp__bar-dot hhp__bar-dot--y" />
      <span class="hhp__bar-dot hhp__bar-dot--g" />
      <span class="hhp__bar-title">CampaignSim · Run #47</span>
      <span class="hhp__bar-live"><span class="hhp__live-dot" />Live</span>
    </div>

    <!-- Mini knowledge graph -->
    <div class="hhp__graph-wrap">
      <svg class="hhp__graph" viewBox="0 0 280 110" xmlns="http://www.w3.org/2000/svg">
        <!-- edges -->
        <line class="hhp__edge" x1="70" y1="35" x2="140" y2="22" />
        <line class="hhp__edge" x1="140" y1="22" x2="210" y2="38" />
        <line class="hhp__edge" x1="70" y1="35" x2="52" y2="78" />
        <line class="hhp__edge" x1="140" y1="22" x2="135" y2="80" />
        <line class="hhp__edge" x1="210" y1="38" x2="228" y2="82" />
        <line class="hhp__edge" x1="52" y1="78" x2="135" y2="80" />
        <line class="hhp__edge" x1="135" y1="80" x2="228" y2="82" />
        <!-- primary nodes -->
        <circle class="hhp__node hhp__node--p" cx="140" cy="22" r="11" />
        <circle class="hhp__node hhp__node--s" cx="70"  cy="35" r="9"  />
        <circle class="hhp__node hhp__node--s" cx="210" cy="38" r="8"  />
        <circle class="hhp__node hhp__node--t" cx="52"  cy="78" r="7"  />
        <circle class="hhp__node hhp__node--s" cx="135" cy="80" r="9"  />
        <circle class="hhp__node hhp__node--t" cx="228" cy="82" r="7"  />
        <!-- scanning pulse -->
        <circle class="hhp__scan" cx="140" cy="22" r="18" />
      </svg>
      <span class="hhp__graph-tag">Knowledge graph</span>
    </div>

    <!-- Step pipeline -->
    <div class="hhp__steps">
      <div
        v-for="(label, i) in stepLabels"
        :key="label"
        class="hhp__step"
        :class="{
          'hhp__step--done':   i < activeStep,
          'hhp__step--active': i === activeStep,
        }"
      >
        <span class="hhp__step-pip">
          <svg v-if="i < activeStep" width="8" height="8" viewBox="0 0 10 10"><path d="M2 5l2.5 2.5L8 2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>
        </span>
        <span class="hhp__step-name">{{ label }}</span>
        <span v-if="i === activeStep" class="hhp__step-badge">running</span>
      </div>
    </div>

    <!-- A/B bar chart -->
    <div class="hhp__ab">
      <span class="hhp__ab-label">Variant comparison</span>
      <div class="hhp__ab-bars">
        <div class="hhp__ab-row">
          <span class="hhp__ab-tag">A</span>
          <div class="hhp__ab-track">
            <div class="hhp__ab-fill hhp__ab-fill--a" style="width:78%" />
          </div>
          <span class="hhp__ab-pct">78%</span>
        </div>
        <div class="hhp__ab-row">
          <span class="hhp__ab-tag">B</span>
          <div class="hhp__ab-track">
            <div class="hhp__ab-fill hhp__ab-fill--b" style="width:54%" />
          </div>
          <span class="hhp__ab-pct">54%</span>
        </div>
      </div>
    </div>

    <!-- Metric chips -->
    <div class="hhp__metrics">
      <div class="hhp__metric hhp__metric--win">
        <span class="hhp__metric-val">+24%</span>
        <span class="hhp__metric-lbl">lift</span>
      </div>
      <div class="hhp__metric">
        <span class="hhp__metric-val">847</span>
        <span class="hhp__metric-lbl">personas</span>
      </div>
      <div class="hhp__metric">
        <span class="hhp__metric-val">5/5</span>
        <span class="hhp__metric-lbl">steps</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stepLabels: { type: Array, default: () => ["Graph", "Personas", "Variants", "Report", "Chat"] },
  activeStep: { type: Number, default: 3 },
});
</script>

<style scoped>
/* ── Card shell ─────────────────────────────────────────────────────────────── */
.hhp {
  width: 100%;
  max-width: 26rem;
  border-radius: 16px;
  background:
    radial-gradient(ellipse 70% 50% at 30% 20%, rgba(10,191,173,0.15), transparent 55%),
    rgba(10, 20, 20, 0.82);
  border: 1px solid rgba(10, 191, 173, 0.35);
  box-shadow:
    0 0 0 1px rgba(10, 191, 173, 0.12),
    0 8px 40px rgba(0, 0, 0, 0.6),
    0 0 60px rgba(10, 191, 173, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  overflow: hidden;
  animation: hhpFloat 6s ease-in-out infinite;
  font-family: 'DM Sans', system-ui, sans-serif;
}

@keyframes hhpFloat {
  0%, 100% { transform: translateY(0);    box-shadow: 0 0 60px rgba(10,191,173,0.18); }
  50%       { transform: translateY(-8px); box-shadow: 0 0 80px rgba(10,191,173,0.28); }
}

/* ── Title bar ──────────────────────────────────────────────────────────────── */
.hhp__bar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.8rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(10, 191, 173, 0.15);
}
.hhp__bar-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.hhp__bar-dot--r { background: #ff5f57; }
.hhp__bar-dot--y { background: #febc2e; }
.hhp__bar-dot--g { background: #28c840; }
.hhp__bar-title {
  flex: 1;
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(175, 200, 200, 0.7);
  padding-left: 0.35rem;
  letter-spacing: 0.02em;
}
.hhp__bar-live {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #00C97A;
  text-transform: uppercase;
}
.hhp__live-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #00C97A;
  box-shadow: 0 0 6px #00C97A;
  animation: liveBlink 1.4s ease-in-out infinite;
}
@keyframes liveBlink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

/* ── Knowledge graph ────────────────────────────────────────────────────────── */
.hhp__graph-wrap {
  position: relative;
  padding: 0.6rem 0.8rem 0;
}
.hhp__graph {
  width: 100%;
  display: block;
}
.hhp__graph-tag {
  position: absolute;
  top: 0.9rem; left: 1rem;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(10, 191, 173, 0.6);
}

.hhp__edge {
  stroke: rgba(10, 191, 173, 0.3);
  stroke-width: 1;
  stroke-dasharray: 4 3;
  animation: edgeDash 3s linear infinite;
}
@keyframes edgeDash {
  to { stroke-dashoffset: -14; }
}

.hhp__node { animation: nodePulse 3.5s ease-in-out infinite; }
.hhp__node--p { fill: rgba(10,191,173,0.75); stroke: #0ABFAD; stroke-width: 2;   filter: drop-shadow(0 0 6px rgba(10,191,173,0.8)); }
.hhp__node--s { fill: rgba(0,201,122,0.6);   stroke: #00C97A; stroke-width: 1.5; filter: drop-shadow(0 0 5px rgba(0,201,122,0.7)); }
.hhp__node--t { fill: rgba(10,191,173,0.2);  stroke: rgba(10,191,173,0.5); stroke-width: 1; }
@keyframes nodePulse {
  0%, 100% { opacity: 0.8; }
  50%       { opacity: 1; }
}

/* Scanning ring on primary node */
.hhp__scan {
  fill: none;
  stroke: rgba(10, 191, 173, 0.5);
  stroke-width: 1;
  animation: scanRing 2.5s ease-out infinite;
}
@keyframes scanRing {
  0%   { r: 11; opacity: 0.8; stroke-width: 2; }
  100% { r: 28; opacity: 0;   stroke-width: 0.5; }
}

/* ── Step pipeline ──────────────────────────────────────────────────────────── */
.hhp__steps {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 0.5rem 0.8rem;
  border-top: 1px solid rgba(10, 191, 173, 0.1);
  border-bottom: 1px solid rgba(10, 191, 173, 0.1);
  background: rgba(0, 0, 0, 0.18);
}
.hhp__step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.22rem;
  padding: 0.25rem 0;
  position: relative;
}
/* connector between steps */
.hhp__step + .hhp__step::before {
  content: "";
  position: absolute;
  left: 0; top: 0.55rem;
  width: 1px; height: 10px;
  background: rgba(10,191,173,0.2);
}

.hhp__step-pip {
  width: 16px; height: 16px;
  border-radius: 50%;
  border: 1.5px solid rgba(10,191,173,0.3);
  background: rgba(10,191,173,0.06);
  display: grid;
  place-items: center;
  color: transparent;
  transition: all 0.2s;
}
.hhp__step--done .hhp__step-pip {
  background: rgba(0,201,122,0.25);
  border-color: #00C97A;
  color: #00C97A;
}
.hhp__step--active .hhp__step-pip {
  background: rgba(10,191,173,0.25);
  border-color: #0ABFAD;
  box-shadow: 0 0 8px rgba(10,191,173,0.6);
  animation: activePip 1.8s ease-in-out infinite;
}
@keyframes activePip {
  0%, 100% { box-shadow: 0 0 8px rgba(10,191,173,0.5); }
  50%       { box-shadow: 0 0 14px rgba(10,191,173,0.9); }
}

.hhp__step-name {
  font-size: 0.58rem;
  font-weight: 600;
  color: rgba(175, 200, 200, 0.45);
  letter-spacing: 0.02em;
}
.hhp__step--done .hhp__step-name  { color: rgba(0,201,122,0.8); }
.hhp__step--active .hhp__step-name { color: #0ABFAD; }

.hhp__step-badge {
  font-size: 0.5rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #0ABFAD;
  background: rgba(10,191,173,0.12);
  border: 1px solid rgba(10,191,173,0.3);
  border-radius: 99px;
  padding: 0.05rem 0.3rem;
  animation: badgeFade 1.4s ease-in-out infinite;
}
@keyframes badgeFade {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}

/* ── A/B bar chart ──────────────────────────────────────────────────────────── */
.hhp__ab {
  padding: 0.65rem 0.8rem 0.5rem;
}
.hhp__ab-label {
  font-size: 0.58rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: rgba(175,200,200,0.45);
  display: block;
  margin-bottom: 0.45rem;
}
.hhp__ab-bars { display: grid; gap: 0.38rem; }
.hhp__ab-row {
  display: grid;
  grid-template-columns: 1rem 1fr 2.2rem;
  align-items: center;
  gap: 0.45rem;
}
.hhp__ab-tag {
  font-size: 0.62rem;
  font-weight: 800;
  color: rgba(175,200,200,0.6);
}
.hhp__ab-track {
  height: 6px;
  border-radius: 99px;
  background: rgba(255,255,255,0.05);
  overflow: hidden;
}
.hhp__ab-fill {
  height: 100%;
  border-radius: 99px;
  animation: barGrow 1.2s cubic-bezier(0.16,1,0.3,1) both;
}
.hhp__ab-fill--a {
  background: linear-gradient(90deg, #0ABFAD, #00C97A);
  box-shadow: 0 0 6px rgba(10,191,173,0.6);
  animation-delay: 0.3s;
}
.hhp__ab-fill--b {
  background: rgba(10,191,173,0.35);
  animation-delay: 0.5s;
}
@keyframes barGrow {
  from { width: 0 !important; }
}
.hhp__ab-pct {
  font-size: 0.6rem;
  font-weight: 700;
  color: rgba(175,200,200,0.55);
  text-align: right;
}

/* ── Metric chips ───────────────────────────────────────────────────────────── */
.hhp__metrics {
  display: flex;
  gap: 0.5rem;
  padding: 0 0.8rem 0.75rem;
}
.hhp__metric {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  padding: 0.45rem 0.5rem;
  border-radius: 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(10,191,173,0.12);
}
.hhp__metric--win {
  border-color: rgba(0,201,122,0.4);
  background: rgba(0,201,122,0.08);
}
.hhp__metric-val {
  font-size: 0.9rem;
  font-weight: 800;
  color: rgba(235,245,245,0.9);
  font-family: 'DM Mono', monospace;
  letter-spacing: -0.03em;
}
.hhp__metric--win .hhp__metric-val { color: #00C97A; }
.hhp__metric-lbl {
  font-size: 0.55rem;
  font-weight: 600;
  color: rgba(175,200,200,0.45);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
</style>
