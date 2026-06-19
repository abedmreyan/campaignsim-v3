<template>
  <!-- No overlay — canvas is transparent, page stays visible throughout -->
  <canvas
    v-if="!done"
    ref="canvasRef"
    class="pswarm-canvas"
    aria-hidden="true"
  />
</template>

<script setup>
/**
 * ParticleSwarm — integrated brand intro
 *
 * The page and network background are visible the whole time.
 * Sequence:
 *   1. SCATTER   — particles drift in from edges (blend with network nodes)
 *   2. CONVERGE1 — particles fly inward and form "CampaignSim" at center
 *   3. HOLD1     — brand name pulses / glows
 *   4. EXPLODE   — particles blast outward
 *   5. CONVERGE2 — particles arc toward the "wins" word in the hero text
 *   6. LAND      — particles settle on the word; glow class added to DOM element
 *   7. FADE      — particles fade out; glow removed; canvas done
 */
import { onMounted, onUnmounted, ref } from "vue";

const emit = defineEmits(["done", "wins-highlight", "wins-dim"]);

const canvasRef = ref(null);
const done      = ref(false);

let ctx       = null;
let raf       = null;
let W = 0, H  = 0;
let dpr       = 1;
let particles = [];
let targets1  = [];   // pixel samples for "CampaignSim"
let targets2  = [];   // pixel samples positioned over the real "wins" DOM element
let phase     = "scatter";
let phaseT    = 0;
let lastTime  = 0;

const DUR = {
  scatter:   400,
  converge1: 1450,
  hold1:     650,
  explode:   650,
  converge2: 1050,
  land:      480,
  fade:      550,
};

const COLORS = ["#0ABFAD","#0ABFAD","#0ABFAD","#00C97A","#00C97A","#7FDED5","#00E090"];

// ── Text pixel sampling ───────────────────────────────────────────────────────
function sampleOffscreen(text, fontSize, cx, cy) {
  const off = document.createElement("canvas");
  off.width  = W;
  off.height = H;
  const c    = off.getContext("2d");
  c.clearRect(0, 0, W, H);
  c.font         = `900 ${fontSize}px 'Space Grotesk','DM Sans',system-ui,sans-serif`;
  c.textAlign    = "center";
  c.textBaseline = "middle";
  c.fillStyle    = "#fff";
  c.fillText(text, cx, cy);

  const img  = c.getImageData(0, 0, W, H);
  const data = img.data;
  const step = Math.max(3, Math.round(W / 150));
  const pts  = [];
  for (let y = 0; y < H; y += step) {
    for (let x = 0; x < W; x += step) {
      if (data[(y * W + x) * 4 + 3] > 60) pts.push({ x, y });
    }
  }
  for (let i = pts.length - 1; i > 0; i--) {
    const j = (Math.random() * (i + 1)) | 0;
    [pts[i], pts[j]] = [pts[j], pts[i]];
  }
  return pts;
}

function sampleCampaignSim() {
  const fs = Math.round(Math.min(W * 0.082, H * 0.13, 86));
  return sampleOffscreen("CampaignSim", fs, W / 2, H / 2);
}

function sampleWinsAtElement() {
  const el = document.querySelector(".home-hero__accent");
  if (!el) return sampleOffscreen("wins", Math.round(Math.min(W * 0.22, 160)), W / 2, H / 2);

  const rect = el.getBoundingClientRect();
  const cx   = (rect.left + rect.right)   / 2;
  const cy   = (rect.top  + rect.bottom)  / 2;
  // Use the element's actual rendered height to pick a matching font size
  const fs   = Math.round(rect.height * 1.2);
  return sampleOffscreen("wins", fs, cx, cy);
}

// ── Particle factory ──────────────────────────────────────────────────────────
function makeParticle(i) {
  const side = (Math.random() * 4) | 0;
  let sx, sy;
  if      (side === 0) { sx = Math.random() * W; sy = -20; }
  else if (side === 1) { sx = W + 20;             sy = Math.random() * H; }
  else if (side === 2) { sx = Math.random() * W; sy = H + 20; }
  else                 { sx = -20;                sy = Math.random() * H; }

  return {
    x: sx, y: sy,
    tx: 0, ty: 0,    // CampaignSim target
    tx2: 0, ty2: 0,  // wins target
    vx:  (Math.random() - 0.5) * 1.4,
    vy:  (Math.random() - 0.5) * 1.4,
    evx: 0, evy: 0,
    r:     0.8 + Math.random() * 1.8,
    baseR: 0.8 + Math.random() * 1.8,
    color: COLORS[i % COLORS.length],
    alpha: 0.5 + Math.random() * 0.45,
    oAngle: Math.random() * Math.PI * 2,
    oSpeed: 0.007 + Math.random() * 0.012,
    pulse:  Math.random() * Math.PI * 2,
  };
}

function assignTargets() {
  particles.forEach((p, i) => {
    if (targets1.length) { const t = targets1[i % targets1.length]; p.tx  = t.x; p.ty  = t.y; }
    if (targets2.length) { const t = targets2[i % targets2.length]; p.tx2 = t.x; p.ty2 = t.y; }
  });
}

// ── Easing ────────────────────────────────────────────────────────────────────
function easeOutExpo(t)    { return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t); }
function easeInOutCubic(t) { return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2; }
function easeInCubic(t)    { return t * t * t; }
function easeOutCubic(t)   { return 1 - Math.pow(1 - t, 3); }

// ── Resize ────────────────────────────────────────────────────────────────────
function resize() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  dpr = window.devicePixelRatio || 1;
  W   = window.innerWidth;
  H   = window.innerHeight;
  canvas.width  = W * dpr;
  canvas.height = H * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  targets1 = sampleCampaignSim();
  if (particles.length) assignTargets();
}

// ── Render loop ───────────────────────────────────────────────────────────────
function tick(now) {
  const dt = Math.min(now - lastTime, 50);
  lastTime = now;
  phaseT  += dt;

  ctx.clearRect(0, 0, W, H);

  // ── Phase transitions ────────────────────────────────────────────────────
  if (phase === "scatter" && phaseT >= DUR.scatter) {
    phase = "converge1"; phaseT = 0;
    assignTargets();

  } else if (phase === "converge1" && phaseT >= DUR.converge1) {
    phase = "hold1"; phaseT = 0;

  } else if (phase === "hold1" && phaseT >= DUR.hold1) {
    phase = "explode"; phaseT = 0;
    particles.forEach(p => {
      const ang = Math.atan2(p.y - H / 2, p.x - W / 2) + (Math.random() - 0.5) * 1.0;
      const spd = 5 + Math.random() * 14;
      p.evx = Math.cos(ang) * spd;
      p.evy = Math.sin(ang) * spd;
    });

  } else if (phase === "explode" && phaseT >= DUR.explode) {
    phase = "converge2"; phaseT = 0;
    // Sample the actual wins element position now that we're mid-animation
    targets2 = sampleWinsAtElement();
    assignTargets();

  } else if (phase === "converge2" && phaseT >= DUR.converge2) {
    phase = "land"; phaseT = 0;
    emit("wins-highlight");
    const el = document.querySelector(".home-hero__accent");
    if (el) el.classList.add("home-hero__accent--lit");

  } else if (phase === "land" && phaseT >= DUR.land) {
    phase = "fade"; phaseT = 0;
    emit("wins-dim");
    const el = document.querySelector(".home-hero__accent");
    if (el) el.classList.remove("home-hero__accent--lit");

  } else if (phase === "fade" && phaseT >= DUR.fade) {
    done.value = true;
    emit("done");
    cancelAnimationFrame(raf);
    return;
  }

  const prog = Math.min(phaseT / DUR[phase], 1);
  const time = now * 0.001;

  // ── Per-particle update ───────────────────────────────────────────────────
  particles.forEach((p) => {
    if (phase === "scatter") {
      p.oAngle += p.oSpeed;
      p.x += p.vx + Math.sin(p.oAngle) * 0.5;
      p.y += p.vy + Math.cos(p.oAngle * 0.7) * 0.4;

    } else if (phase === "converge1") {
      const e      = easeOutExpo(prog);
      const spd    = 0.05 + e * 0.09;
      const jitter = (1 - e) * 1.5;
      p.x += (p.tx - p.x) * spd + Math.sin(time * 3.5 + p.pulse) * jitter;
      p.y += (p.ty - p.y) * spd + Math.cos(time * 2.8 + p.pulse) * jitter;

    } else if (phase === "hold1") {
      const vib = 0.35 * (1 - prog * 0.5);
      p.x = p.tx + Math.sin(time * 5   + p.pulse) * vib;
      p.y = p.ty + Math.cos(time * 4.2 + p.pulse + 1.1) * vib;

    } else if (phase === "explode") {
      const decay = 1 - easeInCubic(prog);
      p.x += p.evx * decay * (dt / 16);
      p.y += p.evy * decay * (dt / 16);

    } else if (phase === "converge2") {
      // Arc toward wins element — slightly springy approach
      const e   = easeOutCubic(prog);
      const spd = 0.04 + e * 0.10;
      p.x += (p.tx2 - p.x) * spd + Math.sin(time * 2.5 + p.pulse) * (1 - e) * 1.2;
      p.y += (p.ty2 - p.y) * spd + Math.cos(time * 2.0 + p.pulse) * (1 - e) * 1.2;

    } else if (phase === "land") {
      // Settle tightly on the letterform
      const vib = 0.25 * (1 - prog * 0.7);
      p.x = p.tx2 + Math.sin(time * 6   + p.pulse) * vib;
      p.y = p.ty2 + Math.cos(time * 5.1 + p.pulse + 0.8) * vib;

    } else if (phase === "fade") {
      // Stay roughly in place as they fade
      p.x += Math.sin(time * 2 + p.pulse) * 0.2;
      p.y += Math.cos(time * 1.8 + p.pulse) * 0.15;
    }

    // ── Alpha per phase ────────────────────────────────────────────────────
    let alpha = p.alpha;
    if (phase === "scatter")   alpha *= 0.25 + easeOutCubic(prog) * 0.55;
    if (phase === "converge1") alpha *= 0.55 + easeOutExpo(prog)  * 0.45;
    if (phase === "hold1")     alpha *= 0.90 + Math.sin(time * 4  + p.pulse) * 0.10;
    if (phase === "explode")   alpha *= 1 - easeInCubic(prog * 0.85);
    if (phase === "converge2") alpha *= 0.40 + easeOutCubic(prog) * 0.55;
    if (phase === "land")      alpha *= 0.90 + Math.sin(time * 4.5 + p.pulse) * 0.10;
    if (phase === "fade")      alpha *= 1 - easeInOutCubic(prog);

    // ── Radius per phase ───────────────────────────────────────────────────
    let r = p.baseR;
    if (phase === "hold1" || phase === "land") r *= 1.1 + Math.sin(time * 5.5 + p.pulse) * 0.22;
    if (phase === "explode") r *= 1 + easeInCubic(prog) * 1.8;

    if (alpha < 0.012 || r < 0.25) return;

    // Core dot
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fillStyle = p.color + Math.round(alpha * 255).toString(16).padStart(2, "0");
    ctx.fill();

    // Glow halo during hold and land
    const showHalo = phase === "hold1" || phase === "land"
      || (phase === "converge1" && prog > 0.7)
      || (phase === "converge2" && prog > 0.7);
    if (showHalo && r > 1) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, r * 3.2, 0, Math.PI * 2);
      ctx.fillStyle = p.color + Math.round(alpha * 0.12 * 255).toString(16).padStart(2, "0");
      ctx.fill();
    }
  });

  raf = requestAnimationFrame(tick);
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
  const canvas = canvasRef.value;
  ctx = canvas.getContext("2d");

  resize();
  window.addEventListener("resize", resize, { passive: true });

  const count = Math.min(Math.max(targets1.length, 300), 500);
  particles   = Array.from({ length: count }, (_, i) => makeParticle(i));
  assignTargets();

  lastTime = performance.now();
  raf = requestAnimationFrame(tick);
});

onUnmounted(() => {
  cancelAnimationFrame(raf);
  window.removeEventListener("resize", resize);
  // Clean up glow class if component unmounts mid-animation
  const el = document.querySelector(".home-hero__accent");
  if (el) el.classList.remove("home-hero__accent--lit");
  particles = [];
  targets1  = [];
  targets2  = [];
});
</script>

<style scoped>
/* Transparent canvas — page and network bg visible at all times */
.pswarm-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 100;         /* above all page content while active; removed when done */
  pointer-events: none;
  background: transparent;
}
</style>
