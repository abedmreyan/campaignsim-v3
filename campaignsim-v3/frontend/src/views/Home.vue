<template>
  <div class="home-page" :data-theme-home="theme">
    <!-- Animated network background -->
    <HomeNetworkBg />
    <!-- Particle swarm entrance (fires once on load, then loops gently) -->
    <ParticleSwarm />

    <header class="home-header">
      <div class="brand">
        <span>CS</span>
        <strong>CampaignSim</strong>
      </div>
      <div class="home-header__actions">
        <!-- Authenticated: Go to app -->
        <template v-if="auth.isAuthenticated">
          <RouterLink class="app-button app-button--primary home-header__cta" to="/briefs">
            Go to app
          </RouterLink>
        </template>
        <!-- Unauthenticated: Sign in only -->
        <template v-else>
          <RouterLink class="app-button app-button--ghost home-header__cta" to="/login">
            Sign in
          </RouterLink>
          <RouterLink class="app-button app-button--primary home-header__cta" to="/signup">
            Get started
          </RouterLink>
        </template>
      </div>
    </header>

    <main class="home-main">
      <!-- Hero -->
      <section class="home-hero-split" aria-labelledby="home-hero-title">
        <div class="home-hero-split__copy">
          <p class="home-eyebrow" ref="heroEyebrowRef">
            <span class="home-eyebrow__dot" aria-hidden="true"></span>
            Campaign intelligence
          </p>
          <h1 id="home-hero-title" ref="heroTitleRef">See which campaign<br><span class="home-hero__accent">wins</span> before you launch.</h1>
          <p class="home-hero-split__lead" ref="heroLeadRef">
            Upload a brand brief, build a knowledge graph and synthetic audience, run A/B
            simulations, and get a ranked report—with persona interviews on the winning variant.
          </p>
          <div class="home-proof" aria-label="Product highlights" ref="heroProofRef">
            <span><svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg> Knowledge graph AI</span>
            <span><svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg> Synthetic personas</span>
            <span><svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg> A/B simulation</span>
            <span><svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg> Exportable report</span>
          </div>
          <div class="home-hero-split__actions" ref="heroActionsRef">
            <template v-if="auth.isAuthenticated">
              <RouterLink class="app-button app-button--primary app-button--lg" to="/process">
                Go to app
              </RouterLink>
              <RouterLink class="app-button app-button--secondary" to="/history">
                View history
              </RouterLink>
            </template>
            <template v-else>
              <RouterLink class="app-button app-button--primary app-button--lg" to="/signup">
                Get started free
              </RouterLink>
              <RouterLink class="app-button app-button--secondary" to="/login">
                Sign in
              </RouterLink>
            </template>
          </div>
        </div>
        <div class="home-hero-split__preview-wrap" ref="heroPreviewRef">
          <HomeHeroPreview :step-labels="previewStepLabels" :active-step="3" />
        </div>
      </section>

      <!-- Entry bridge -->
      <HomeEntryBridge />

      <!-- From guesswork to evidence -->
      <section class="home-transform" aria-labelledby="home-transform-title" ref="sectionTransformRef">
        <div class="home-section-label" aria-hidden="true">01 — Why simulate</div>
        <h2 id="home-transform-title">From guesswork to evidence</h2>
        <div class="home-transform__grid">
          <div class="home-transform__col home-transform__col--before">
            <div class="home-transform__col-badge">Before</div>
            <h3>Without simulation</h3>
            <ul>
              <li>Launch budgets on gut feel and fragmented briefs.</li>
              <li>No shared view of audience segments or message fit.</li>
              <li>Learn what works only after wasted spend.</li>
            </ul>
          </div>
          <div class="home-transform__divider" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
          <div class="home-transform__col home-transform__col--highlight">
            <div class="home-transform__col-badge home-transform__col-badge--accent">With CampaignSim</div>
            <h3>Structured, evidence-led</h3>
            <ul>
              <li>Graph extracted from your PDF or text upload.</li>
              <li>Personas and variants tested in one connected workflow.</li>
              <li>Ranked report with engagement and segment breakdowns.</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Workflow journey -->
      <HomeWorkflowJourney :steps="workflowSteps" />

      <!-- Capabilities bento -->
      <section class="home-bento" aria-labelledby="home-bento-title" ref="sectionBentoRef">
        <div class="home-section-label" aria-hidden="true">03 — Capabilities</div>
        <h2 id="home-bento-title">Built for the full campaign loop</h2>
        <div class="home-bento__grid">
          <article v-for="cap in capabilities" :key="cap.title" class="home-bento__tile">
            <div class="home-bento__icon" aria-hidden="true">
              <component :is="cap.icon" />
            </div>
            <div class="home-bento__body">
              <h3>{{ cap.title }}</h3>
              <p>{{ cap.description }}</p>
            </div>
            <div class="home-bento__tile-glow" aria-hidden="true"></div>
          </article>
        </div>
      </section>

      <!-- Closing CTA -->
      <section class="home-close" aria-labelledby="home-close-title" ref="sectionCloseRef">
        <div class="home-close__inner">
          <div class="home-close__orb" aria-hidden="true"></div>
          <p class="home-eyebrow"><span class="home-eyebrow__dot"></span>Ready to start</p>
          <h2 id="home-close-title">Run your first simulation today.</h2>
          <p>Open the workflow with instant mock data—no backend required—or connect a live API when ready.</p>
          <div class="home-close__actions">
            <template v-if="auth.isAuthenticated">
              <RouterLink class="app-button app-button--primary app-button--lg" to="/process">
                Go to app
              </RouterLink>
              <RouterLink class="app-button app-button--secondary" to="/history">
                View history
              </RouterLink>
            </template>
            <template v-else>
              <RouterLink class="app-button app-button--primary app-button--lg" to="/signup">
                Create free account
              </RouterLink>
              <RouterLink class="app-button app-button--secondary" to="/login">
                Sign in
              </RouterLink>
            </template>
          </div>
        </div>
      </section>

      <p v-if="isMockMode" class="home-footer-note">
        Demo mode active. Set <code>VITE_USE_MOCKS=false</code> in <code>.env</code> to connect a live API.
      </p>
    </main>
  </div>
</template>

<script setup>
import { h, onMounted, onUnmounted, ref } from "vue";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import HomeEntryBridge from "@/components/home/HomeEntryBridge.vue";
import HomeHeroPreview from "@/components/home/HomeHeroPreview.vue";
import HomeWorkflowJourney from "@/components/home/HomeWorkflowJourney.vue";
import HomeNetworkBg from "@/components/home/HomeNetworkBg.vue";
import ParticleSwarm from "@/components/home/ParticleSwarm.vue";
import { isMockMode } from "@/api/campaignApi";
import { useTheme } from "@/composables/useTheme";
import { useAuthStore } from "@/stores/authStore";

gsap.registerPlugin(ScrollTrigger);

const { init: initTheme } = useTheme();
const auth = useAuthStore();

const previewStepLabels = ["Graph", "Personas", "Variants", "Report", "Chat"];

const workflowSteps = [
  { n: 1, title: "Knowledge Graph",    detail: "Extract entities and relationships from your brand brief." },
  { n: 2, title: "Audience Personas",  detail: "Build segment-aware synthetic customers at scale." },
  { n: 3, title: "Campaign Variants",  detail: "Draft message variants across channels for testing." },
  { n: 4, title: "Insights Report",    detail: "Rank variants with engagement and segment breakdowns." },
  { n: 5, title: "Persona Insights",   detail: "Interview winning personas and export findings." },
];

const iconProps = { xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 24 24", "aria-hidden": "true" };

const IconGraph  = () => h("svg", iconProps, [h("circle",{cx:"6",cy:"6",r:"2.5"}),h("circle",{cx:"18",cy:"8",r:"2.5"}),h("circle",{cx:"12",cy:"18",r:"2.5"}),h("path",{d:"M8 7l4 9M16 9l-2 7"})]);
const IconUsers  = () => h("svg", iconProps, [h("path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}),h("circle",{cx:"9",cy:"7",r:"3"}),h("path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}),h("path",{d:"M16 3.13a4 4 0 0 1 0 7.75"})]);
const IconZap    = () => h("svg", iconProps, [h("path",{d:"M13 2 3 14h9l-1 8 10-12h-9l1-8z"})]);
const IconChart  = () => h("svg", iconProps, [h("path",{d:"M3 3v18h18"}),h("path",{d:"M7 16v-5M12 16V8M17 16v-9"})]);

const capabilities = [
  { title: "Knowledge graph extraction", description: "Turn PDFs and text briefs into a searchable graph of brand entities, claims, and relationships.", icon: IconGraph },
  { title: "Synthetic persona panel",    description: "Generate segment-aware audiences grounded in your uploaded context—not generic personas.", icon: IconUsers },
  { title: "A/B simulation run",         description: "Compare variants with live-style progress, per-variant metrics, and mission-control visibility.", icon: IconZap },
  { title: "Report and persona chat",    description: "Surface a ranked winner with charts, then interview personas on the winning message.", icon: IconChart },
];

// Hero element refs for entrance animation
const heroEyebrowRef = ref(null);
const heroTitleRef   = ref(null);
const heroLeadRef    = ref(null);
const heroProofRef   = ref(null);
const heroActionsRef = ref(null);
const heroPreviewRef = ref(null);

// Section refs for scroll-reveal
const sectionTransformRef = ref(null);
const sectionBentoRef     = ref(null);
const sectionCloseRef     = ref(null);

let gsapCtx = null;

onMounted(async () => {
  initTheme();

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  gsapCtx = gsap.context(() => {
    // ── Hero entrance: staggered reveal on load ──────────────────────────
    gsap.set([heroEyebrowRef.value, heroTitleRef.value, heroLeadRef.value, heroProofRef.value, heroActionsRef.value], { opacity: 0, y: 24 });
    gsap.set(heroPreviewRef.value, { opacity: 0, x: 28, scale: 0.97 });

    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
    tl.to(heroEyebrowRef.value,  { opacity: 1, y: 0, duration: 0.6 }, 0.15)
      .to(heroTitleRef.value,    { opacity: 1, y: 0, duration: 0.7 }, 0.28)
      .to(heroLeadRef.value,     { opacity: 1, y: 0, duration: 0.6 }, 0.46)
      .to(heroProofRef.value,    { opacity: 1, y: 0, duration: 0.5 }, 0.62)
      .to(heroActionsRef.value,  { opacity: 1, y: 0, duration: 0.5 }, 0.74)
      .to(heroPreviewRef.value,  { opacity: 1, x: 0, scale: 1, duration: 0.8, ease: "power2.out" }, 0.32);

    tl.add(() => {
      const accent = document.querySelector(".home-hero__accent");
      if (accent) accent.classList.add("home-hero__accent--entrance");
    }, 0.85);

    // ── Scroll-reveal: each section fades in as it enters the viewport ───
    [sectionTransformRef.value, sectionBentoRef.value, sectionCloseRef.value].forEach((el) => {
      if (!el) return;
      gsap.from(el, {
        y: 48, opacity: 0, duration: 0.85, ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 85%", toggleActions: "play none none none" },
      });
    });

    // Stagger bento tiles
    const tiles = document.querySelectorAll(".home-bento__tile");
    if (tiles.length) {
      gsap.from(tiles, {
        y: 32, opacity: 0, stagger: 0.1, duration: 0.65, ease: "power2.out",
        scrollTrigger: { trigger: sectionBentoRef.value, start: "top 70%", toggleActions: "play none none none" },
      });
    }
  });
});

onUnmounted(() => {
  gsapCtx?.revert();
  ScrollTrigger.getAll().forEach(t => t.kill());
});
</script>
