<template>
  <div class="hnbg" aria-hidden="true">
    <svg class="hnbg__svg" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="xMidYMid slice">
      <!-- Animated edges -->
      <g class="hnbg__edges">
        <line
          v-for="(edge, i) in edges"
          :key="`e${i}`"
          :x1="nodes[edge[0]].x"
          :y1="nodes[edge[0]].y"
          :x2="nodes[edge[1]].x"
          :y2="nodes[edge[1]].y"
          class="hnbg__edge"
          :style="{ animationDelay: `${i * 0.35}s` }"
        />
      </g>
      <!-- Nodes -->
      <g class="hnbg__nodes">
        <g
          v-for="(node, i) in nodes"
          :key="`n${i}`"
          class="hnbg__node-group"
          :style="{ animationDelay: `${i * 0.22}s`, animationDuration: `${6 + (i % 5)}s` }"
        >
          <circle
            :cx="node.x" :cy="node.y" :r="node.r + 8"
            class="hnbg__node-halo"
          />
          <circle
            :cx="node.x" :cy="node.y" :r="node.r"
            class="hnbg__node"
            :class="`hnbg__node--${node.type}`"
          />
        </g>
      </g>
    </svg>
    <!-- Noise texture overlay -->
    <div class="hnbg__noise"></div>
    <!-- Gradient vignette so content is readable -->
    <div class="hnbg__vignette"></div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref } from "vue";

const W = 1440;
const H = 900;

// Fixed node positions — spread across the canvas
const initialNodes = [
  { x: 180,  y: 160, r: 14, type: "primary"   },
  { x: 420,  y: 90,  r: 10, type: "secondary"  },
  { x: 700,  y: 200, r: 18, type: "primary"    },
  { x: 980,  y: 110, r: 9,  type: "tertiary"   },
  { x: 1200, y: 200, r: 13, type: "secondary"  },
  { x: 1350, y: 80,  r: 8,  type: "tertiary"   },
  { x: 100,  y: 400, r: 10, type: "tertiary"   },
  { x: 320,  y: 340, r: 12, type: "secondary"  },
  { x: 560,  y: 450, r: 16, type: "primary"    },
  { x: 820,  y: 380, r: 11, type: "secondary"  },
  { x: 1060, y: 440, r: 14, type: "primary"    },
  { x: 1280, y: 360, r: 9,  type: "tertiary"   },
  { x: 200,  y: 650, r: 11, type: "secondary"  },
  { x: 480,  y: 700, r: 8,  type: "tertiary"   },
  { x: 740,  y: 620, r: 13, type: "primary"    },
  { x: 1000, y: 680, r: 10, type: "secondary"  },
  { x: 1240, y: 600, r: 15, type: "primary"    },
  { x: 380,  y: 520, r: 7,  type: "tertiary"   },
  { x: 640,  y: 280, r: 9,  type: "secondary"  },
  { x: 900,  y: 550, r: 12, type: "secondary"  },
];

const edges = [
  [0,1],[1,2],[2,3],[3,4],[4,5],
  [0,7],[1,7],[2,8],[3,9],[4,10],[5,11],
  [6,7],[7,8],[8,9],[9,10],[10,11],
  [6,12],[7,13],[8,14],[9,15],[10,16],
  [12,13],[13,14],[14,15],[15,16],
  [1,18],[2,18],[7,17],[8,17],[17,18],
  [9,19],[10,19],[14,19],[15,20 % initialNodes.length],
];

// Reactive nodes with drift animation
const nodes = reactive(initialNodes.map(n => ({ ...n })));

let animFrame = null;
let t = 0;

function animate() {
  t += 0.004;
  nodes.forEach((node, i) => {
    const base = initialNodes[i];
    const freq1 = 0.7 + (i * 0.13);
    const freq2 = 0.5 + (i * 0.09);
    const amp = 18 + (i % 4) * 8;
    node.x = base.x + Math.sin(t * freq1 + i) * amp;
    node.y = base.y + Math.cos(t * freq2 + i * 0.7) * (amp * 0.6);
  });
  animFrame = requestAnimationFrame(animate);
}

onMounted(() => { animFrame = requestAnimationFrame(animate); });
onUnmounted(() => { if (animFrame) cancelAnimationFrame(animFrame); });
</script>

<style scoped>
.hnbg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.hnbg__svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* Edges */
.hnbg__edge {
  stroke: rgba(10, 191, 173, 0.28);
  stroke-width: 1;
  animation: edgePulse 4s ease-in-out infinite;
}
@keyframes edgePulse {
  0%, 100% { stroke: rgba(10, 191, 173, 0.18); stroke-width: 0.8; }
  50%       { stroke: rgba(10, 191, 173, 0.45); stroke-width: 1.4; }
}

/* Node halo (glow ring) */
.hnbg__node-halo {
  fill: none;
  stroke: rgba(10, 191, 173, 0.18);
  stroke-width: 1.5;
  animation: haloBreath 5s ease-in-out infinite;
}
@keyframes haloBreath {
  0%, 100% { opacity: 0; }
  40%       { opacity: 1; }
  60%       { opacity: 0.6; }
}

/* Nodes */
.hnbg__node {
  animation: nodePulse 4s ease-in-out infinite;
}
.hnbg__node--primary {
  fill: rgba(10, 191, 173, 0.75);
  stroke: rgba(10, 191, 173, 1);
  stroke-width: 2;
  filter: drop-shadow(0 0 12px rgba(10, 191, 173, 0.8));
}
.hnbg__node--secondary {
  fill: rgba(0, 201, 122, 0.65);
  stroke: rgba(0, 201, 122, 1);
  stroke-width: 1.5;
  filter: drop-shadow(0 0 8px rgba(0, 201, 122, 0.65));
}
.hnbg__node--tertiary {
  fill: rgba(10, 191, 173, 0.35);
  stroke: rgba(10, 191, 173, 0.7);
  stroke-width: 1;
  filter: drop-shadow(0 0 5px rgba(10, 191, 173, 0.4));
}
@keyframes nodePulse {
  0%, 100% { opacity: 0.75; }
  50%       { opacity: 1; }
}

/* Noise texture */
.hnbg__noise {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  background-size: 180px 180px;
  opacity: 0.028;
  mix-blend-mode: overlay;
}

/* Vignette keeps text readable — fades to 88% opacity so dot-grid shows through */
.hnbg__vignette {
  position: absolute;
  inset: 0;
  background:
    /* top centre — hero stays clear (fade starts later, at 45%) */
    radial-gradient(ellipse 70% 60% at 50% 0%,   transparent 45%, var(--color-bg) 92%),
    /* left / right edges */
    radial-gradient(ellipse 45% 40% at 0%   50%,  transparent 28%, var(--color-bg) 82%),
    radial-gradient(ellipse 45% 40% at 100% 50%,  transparent 28%, var(--color-bg) 82%),
    /* bottom */
    radial-gradient(ellipse 70% 50% at 50% 100%,  transparent 22%, var(--color-bg) 78%);
  opacity: 0.88;
}

/* In light mode, lower the overall vignette opacity so network nodes show */
:root .hnbg__vignette {
  opacity: 0.82;
}
</style>
