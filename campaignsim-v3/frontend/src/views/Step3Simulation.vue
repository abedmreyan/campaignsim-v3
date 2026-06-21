<template>
  <div class="v3-root stagger-in">

    <!-- ── Header ─────────────────────────────────────────────────── -->
    <div class="v3-header">
      <div class="v3-header__copy">
        <p class="v3-eyebrow">Step 3</p>
        <h1 class="v3-title">Campaign Variants</h1>
        <p class="v3-sub">Build message variants and select which ones to pit against each other.</p>
      </div>
      <div class="v3-header__status" v-if="store.variants.length">
        <span
          class="v3-status-pill"
          :class="canLaunch ? 'v3-status-pill--ready' : 'v3-status-pill--warn'"
        >
          <span class="v3-status-pill__dot" />
          {{ canLaunch ? `${selectedIds.size} selected — ready` : selectionHint }}
        </span>
      </div>
    </div>

    <!-- ── Horizontal variant rail ────────────────────────────────── -->
    <div class="v3-rail-wrap">
      <!-- Scroll shadow left -->
      <div class="v3-rail-fade v3-rail-fade--left" :class="{ 'is-visible': canScrollLeft }" aria-hidden="true" />

      <!-- Rail -->
      <div class="v3-rail" ref="railRef" @scroll="onRailScroll">

        <!-- Existing variant cards -->
        <div
          v-for="(variant, index) in store.variants"
          :key="variant.variant_id"
          class="v3-card"
          :class="{
            'v3-card--selected': selectedIds.has(variant.variant_id),
            'v3-card--editing': editingId === variant.variant_id,
          }"
          :style="{ '--enter-delay': `${index * 60}ms` }"
          @click="toggleSelect(variant.variant_id)"
        >
          <!-- Channel colour bar -->
          <div class="v3-card__bar" :style="{ background: channelColor(variant.channel) }" />

          <!-- Selection badge -->
          <div class="v3-card__sel-badge" :class="{ 'is-checked': selectedIds.has(variant.variant_id) }">
            <svg v-if="selectedIds.has(variant.variant_id)" width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>

          <!-- Channel chip -->
          <div class="v3-card__channel-chip" :style="{ color: channelColor(variant.channel) }">
            <component :is="channelIcon(variant.channel)" class="v3-card__channel-icon" />
            {{ variant.channel }}
          </div>

          <!-- Core content -->
          <h3 class="v3-card__name">{{ variant.variant_name }}</h3>
          <p class="v3-card__headline">{{ variant.content?.headline }}</p>
          <p class="v3-card__body">{{ variant.content?.body }}</p>

          <div v-if="variant.content?.cta" class="v3-card__cta-pill">
            {{ variant.content.cta }}
          </div>

          <!-- Meta row -->
          <div class="v3-card__meta">
            <span>{{ variant.content?.format }}</span>
            <span class="v3-card__meta-dot" aria-hidden="true">·</span>
            <span>{{ variant.content?.tone }}</span>
            <span class="v3-card__meta-dot" aria-hidden="true">·</span>
            <span>{{ variant.max_rounds || 10 }}r</span>
          </div>
          <div v-if="variant.target_segment" class="v3-card__segment">
            {{ variant.target_segment }}
          </div>

          <!-- Hover actions -->
          <div class="v3-card__actions" @click.stop>
            <button class="v3-card__action" title="Edit variant" @click="openEdit(variant)">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Edit
            </button>
            <button class="v3-card__action v3-card__action--danger" title="Delete variant" @click="store.deleteVariant(variant.variant_id); selectedIds.delete(variant.variant_id)">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>
              Delete
            </button>
          </div>
        </div>

        <!-- Add variant card -->
        <button
          v-if="store.variants.length < 3"
          class="v3-add-card"
          @click="openAdd"
          :style="{ '--enter-delay': `${store.variants.length * 60}ms` }"
        >
          <span class="v3-add-card__ring">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </span>
          <span class="v3-add-card__label">Add variant</span>
          <span class="v3-add-card__hint">{{ store.variants.length }}/3 created</span>
        </button>

        <!-- Empty ghost when no variants -->
        <div v-if="!store.variants.length" class="v3-empty">
          <div class="v3-empty__orb" aria-hidden="true" />
          <svg class="v3-empty__icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="6" y="8" width="22" height="28" rx="3"/>
            <rect x="20" y="14" width="22" height="28" rx="3"/>
            <path d="M14 18h6M14 22h6M14 26h4"/>
            <path d="M28 22h6M28 26h6M28 30h4"/>
          </svg>
          <h3 class="v3-empty__title">No variants yet</h3>
          <p class="v3-empty__msg">Add 2–3 campaign variants to compare in simulation.</p>
        </div>

      </div>

      <!-- Scroll shadow right -->
      <div class="v3-rail-fade v3-rail-fade--right" :class="{ 'is-visible': canScrollRight }" aria-hidden="true" />

      <!-- Scroll arrows -->
      <button v-if="canScrollLeft" class="v3-scroll-btn v3-scroll-btn--left" @click="scroll(-1)" aria-label="Scroll left">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
      <button v-if="canScrollRight" class="v3-scroll-btn v3-scroll-btn--right" @click="scroll(1)" aria-label="Scroll right">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
    </div>

    <!-- ── Launch bar ─────────────────────────────────────────────── -->
    <Transition name="v3-bar">
      <div v-if="store.variants.length" class="v3-launch-bar">
        <div class="v3-launch-bar__info">
          <span v-if="selectedIds.size === 0" class="v3-launch-bar__hint">Select variants to compare</span>
          <span v-else class="v3-launch-bar__count">
            <strong>{{ selectedIds.size }}</strong> variant{{ selectedIds.size !== 1 ? 's' : '' }} selected for simulation
          </span>
          <button v-if="selectedIds.size < store.variants.length" class="v3-launch-bar__sel-all" @click="selectAll">
            Select all
          </button>
          <button v-else-if="selectedIds.size > 0" class="v3-launch-bar__sel-all" @click="selectedIds.clear()">
            Clear selection
          </button>
        </div>
        <button
          class="v3-launch-btn"
          :disabled="!canLaunch || store.simulationRun.loading"
          @click="launch"
        >
          <span v-if="store.simulationRun.loading" class="v3-launch-btn__spinner" />
          <template v-else>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            Launch simulation
          </template>
        </button>
      </div>
    </Transition>

    <!-- ── Add / Edit drawer ──────────────────────────────────────── -->
    <Teleport to="body">
    <Transition name="v3-drawer">
      <div v-if="drawerOpen" class="v3-drawer-overlay" @click.self="closeDrawer">
        <aside class="v3-drawer" role="dialog" :aria-label="editingVariant ? 'Edit variant' : 'Add variant'">
          <div class="v3-drawer__header">
            <h2 class="v3-drawer__title">{{ editingVariant ? 'Edit variant' : 'New variant' }}</h2>
            <button class="v3-drawer__close" @click="closeDrawer" aria-label="Close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div class="v3-drawer__body">
            <div class="v3-form">
              <div class="v3-form__row v3-form__row--2">
                <label class="v3-form__field">
                  <span class="v3-form__label">Variant name <em>*</em></span>
                  <input v-model.trim="form.variant_name" class="v3-form__input" placeholder="e.g. Instagram Video Ad" />
                </label>
                <label class="v3-form__field">
                  <span class="v3-form__label">Channel <em>*</em></span>
                  <select v-model="form.channel" class="v3-form__select">
                    <option value="">Select channel</option>
                    <option v-for="c in channels" :key="c" :value="c">{{ c }}</option>
                  </select>
                </label>
              </div>

              <div class="v3-form__row v3-form__row--2">
                <label class="v3-form__field">
                  <span class="v3-form__label">Format <em>*</em></span>
                  <select v-model="form.format" class="v3-form__select">
                    <option value="">Select format</option>
                    <option v-for="f in formats" :key="f" :value="f">{{ f }}</option>
                  </select>
                </label>
                <label class="v3-form__field">
                  <span class="v3-form__label">Tone</span>
                  <select v-model="form.tone" class="v3-form__select">
                    <option v-for="t in tones" :key="t" :value="t">{{ t }}</option>
                  </select>
                </label>
              </div>

              <label class="v3-form__field">
                <span class="v3-form__label">Headline <em>*</em></span>
                <input v-model.trim="form.headline" class="v3-form__input" placeholder="Zero Sugar. Zero Wait." />
              </label>

              <label class="v3-form__field">
                <span class="v3-form__label">Body <em>*</em></span>
                <textarea v-model.trim="form.body" class="v3-form__textarea" rows="3" placeholder="Premium cold brew ready in 30 seconds." />
              </label>

              <div class="v3-form__row v3-form__row--2">
                <label class="v3-form__field">
                  <span class="v3-form__label">CTA <em>*</em></span>
                  <input v-model.trim="form.cta" class="v3-form__input" placeholder="Try it now" />
                </label>
                <label class="v3-form__field">
                  <span class="v3-form__label">Target segment</span>
                  <input v-model.trim="form.target_segment" class="v3-form__input" placeholder="Urban Professionals" />
                </label>
              </div>

              <label v-if="form.channel === 'email'" class="v3-form__field">
                <span class="v3-form__label">Email subject <em>*</em></span>
                <input v-model.trim="form.email_subject" class="v3-form__input" placeholder="Your mornings just got better" />
              </label>

              <div class="v3-form__row v3-form__row--2">
                <label class="v3-form__field">
                  <span class="v3-form__label">Visual description</span>
                  <input v-model.trim="form.visual_desc" class="v3-form__input" placeholder="Fast-paced morning commute video." />
                </label>
                <label class="v3-form__field">
                  <span class="v3-form__label">Max rounds</span>
                  <input v-model.number="form.max_rounds" class="v3-form__input" type="number" min="1" max="50" />
                </label>
              </div>

              <div v-if="formErrors.length" class="v3-form__errors">
                <p v-for="e in formErrors" :key="e">{{ e }}</p>
              </div>
            </div>
          </div>

          <div class="v3-drawer__footer">
            <button class="v3-drawer__cancel" @click="closeDrawer">Cancel</button>
            <button class="v3-drawer__save" @click="submitForm">
              {{ editingVariant ? 'Save changes' : 'Add variant' }}
            </button>
          </div>
        </aside>
      </div>
    </Transition>
    </Teleport>

  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const router = useRouter();

// ── Rail scroll state ────────────────────────────────────────────────
const railRef = ref(null);
const canScrollLeft = ref(false);
const canScrollRight = ref(false);

function onRailScroll() {
  const el = railRef.value;
  if (!el) return;
  canScrollLeft.value = el.scrollLeft > 8;
  canScrollRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 8;
}

function scroll(dir) {
  const el = railRef.value;
  if (!el) return;
  el.scrollBy({ left: dir * 320, behavior: "smooth" });
}

onMounted(() => {
  setTimeout(onRailScroll, 100);
});

watch(() => store.variants.length, () => {
  setTimeout(onRailScroll, 100);
});

// ── Selection ────────────────────────────────────────────────────────
const selectedIds = reactive(new Set(store.variants.map((v) => v.variant_id)));

watch(() => store.variants, (variants) => {
  variants.forEach((v) => {
    if (!selectedIds.has(v.variant_id)) selectedIds.add(v.variant_id);
  });
}, { deep: true });

function toggleSelect(id) {
  if (selectedIds.has(id)) selectedIds.delete(id);
  else selectedIds.add(id);
}

function selectAll() {
  store.variants.forEach((v) => selectedIds.add(v.variant_id));
}

const canLaunch = computed(() => {
  const count = selectedIds.size;
  return count >= 2 && count <= 3 && !store.simulationRun.loading;
});

const selectionHint = computed(() => {
  if (selectedIds.size === 0) return "Select at least 2 variants";
  if (selectedIds.size === 1) return "Select 1 more variant";
  if (selectedIds.size > 3) return "Maximum 3 variants";
  return "Ready to launch";
});

// ── Channel colours & icons ──────────────────────────────────────────
const CHANNEL_COLORS = {
  email:     "#f59e0b",
  instagram: "#ec4899",
  tiktok:    "#ef4444",
  linkedin:  "#3b82f6",
};

function channelColor(ch) {
  return CHANNEL_COLORS[ch] || "var(--color-accent)";
}

const ChannelIcons = {
  email:     () => h("svg", { width: 12, height: 12, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }, [h("path", { d: "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" }), h("polyline", { points: "22,6 12,13 2,6" })]),
  instagram: () => h("svg", { width: 12, height: 12, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }, [h("rect", { x: 2, y: 2, width: 20, height: 20, rx: 5, ry: 5 }), h("circle", { cx: 12, cy: 12, r: 5 }), h("circle", { cx: 17.5, cy: 6.5, r: 1.5, fill: "currentColor", stroke: "none" })]),
  tiktok:    () => h("svg", { width: 12, height: 12, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }, [h("path", { d: "M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5" })]),
  linkedin:  () => h("svg", { width: 12, height: 12, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }, [h("path", { d: "M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" }), h("rect", { x: 2, y: 9, width: 4, height: 12 }), h("circle", { cx: 4, cy: 4, r: 2 })]),
};

function channelIcon(ch) {
  return ChannelIcons[ch] || ChannelIcons.email;
}

// ── Drawer / form ────────────────────────────────────────────────────
const drawerOpen = ref(false);
const editingVariant = ref(null);
const editingId = ref(null);
const formErrors = ref([]);

const channels = ["instagram", "email", "tiktok", "linkedin"];
const formats  = ["VideoAd", "CarouselPost", "EmailNewsletter", "ShortFormVideo", "SponsoredPost"];
const tones    = ["playful", "professional", "urgent", "neutral"];

const emptyForm = () => ({
  variant_name: "", channel: "", format: "", headline: "", body: "",
  cta: "", visual_desc: "", email_subject: "", tone: "neutral",
  target_segment: "", max_rounds: 10,
});

const form = reactive(emptyForm());

function hydrateForm(variant) {
  Object.assign(form, emptyForm(), variant ? {
    variant_name:  variant.variant_name || "",
    channel:       variant.channel || "",
    format:        variant.content?.format || "",
    headline:      variant.content?.headline || "",
    body:          variant.content?.body || "",
    cta:           variant.content?.cta || "",
    visual_desc:   variant.content?.visual_desc || "",
    email_subject: variant.content?.email_subject || "",
    tone:          variant.content?.tone || "neutral",
    target_segment: variant.target_segment || "",
    max_rounds:    variant.max_rounds || 10,
  } : {});
}

function openAdd() {
  editingVariant.value = null;
  editingId.value = null;
  hydrateForm(null);
  formErrors.value = [];
  drawerOpen.value = true;
}

function openEdit(variant) {
  editingVariant.value = variant;
  editingId.value = variant.variant_id;
  hydrateForm(variant);
  formErrors.value = [];
  drawerOpen.value = true;
}

function closeDrawer() {
  drawerOpen.value = false;
  editingVariant.value = null;
  editingId.value = null;
}

function validateForm() {
  const errs = [];
  const req = ["variant_name", "channel", "format", "headline", "body", "cta"];
  req.forEach((f) => { if (!form[f]) errs.push(`${f.replace(/_/g, " ")} is required`); });
  if (form.channel === "email" && !form.email_subject) errs.push("email subject is required");
  if (form.max_rounds < 1 || form.max_rounds > 50) errs.push("max rounds must be 1–50");
  formErrors.value = errs;
  return errs.length === 0;
}

function submitForm() {
  if (!validateForm()) return;
  const payload = { ...form };
  if (editingVariant.value) {
    store.updateVariant(editingVariant.value.variant_id, payload);
  } else {
    if (store.variants.length >= 3) {
      store.setNotice("Maximum 3 variants supported.");
      return;
    }
    store.addVariant(payload);
    // Auto-select newly added variant
    setTimeout(() => {
      store.variants.forEach((v) => selectedIds.add(v.variant_id));
    }, 50);
  }
  closeDrawer();
}

// ── Launch ───────────────────────────────────────────────────────────
async function launch() {
  try {
    await store.startAbTest([...selectedIds]);
    router.push({ name: "simulation-run", params: { simulationId: store.simulationId } });
  } catch (e) {
    store.setNotice(e.message || "Failed to start simulation.");
  }
}
</script>

<style scoped>
/* ── Root ────────────────────────────────────────────────────────── */
.v3-root {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 0;
}

/* ── Header ──────────────────────────────────────────────────────── */
.v3-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0 0 1.5rem;
  flex-wrap: wrap;
}

.v3-eyebrow {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin-bottom: 0.3rem;
}

.v3-title {
  font-size: clamp(1.4rem, 2.5vw, 1.75rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--color-text);
  line-height: 1.1;
  margin-bottom: 0.35rem;
}

.v3-sub {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  max-width: 42ch;
}

.v3-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.875rem;
  border-radius: 2rem;
  font-size: 0.8125rem;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.v3-status-pill--ready {
  background: rgba(10, 191, 173, 0.1);
  border-color: rgba(10, 191, 173, 0.3);
  color: var(--color-accent);
}

.v3-status-pill--warn {
  background: rgba(251, 191, 36, 0.08);
  border-color: rgba(251, 191, 36, 0.25);
  color: var(--color-warning, #f59e0b);
}

.v3-status-pill__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.v3-status-pill--ready .v3-status-pill__dot {
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.7); }
}

/* ── Rail wrapper ─────────────────────────────────────────────────── */
.v3-rail-wrap {
  position: relative;
  margin: 0 -0.5rem;
}

.v3-rail {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  overflow-y: visible;
  padding: 1rem 0.5rem 1.5rem;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.v3-rail::-webkit-scrollbar { display: none; }

/* ── Fade overlays ───────────────────────────────────────────────── */
.v3-rail-fade {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4rem;
  pointer-events: none;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.2s;
}
.v3-rail-fade.is-visible { opacity: 1; }
.v3-rail-fade--left  { left: 0; background: linear-gradient(to right, var(--color-bg), transparent); }
.v3-rail-fade--right { right: 0; background: linear-gradient(to left, var(--color-bg), transparent); }

/* ── Scroll buttons ──────────────────────────────────────────────── */
.v3-scroll-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.v3-scroll-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }
.v3-scroll-btn--left  { left: -0.5rem; }
.v3-scroll-btn--right { right: -0.5rem; }

/* ── Variant card ─────────────────────────────────────────────────── */
.v3-card {
  position: relative;
  flex: 0 0 300px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.25rem;
  padding-top: 1.5rem;
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-lg, 0.75rem);
  cursor: pointer;
  scroll-snap-align: start;
  overflow: hidden;
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.18s;
  animation: card-in 0.3s ease both;
  animation-delay: var(--enter-delay, 0ms);
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.v3-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: 0 6px 28px rgba(0,0,0,0.18);
  transform: translateY(-2px);
}

.v3-card--selected {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 1px var(--color-accent), 0 6px 28px rgba(10,191,173,0.12);
}

.v3-card--selected:hover {
  box-shadow: 0 0 0 1px var(--color-accent), 0 8px 32px rgba(10,191,173,0.18);
}

/* top colour bar */
.v3-card__bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: 3px 3px 0 0;
}

/* selection badge */
.v3-card__sel-badge {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  border: 1.5px solid var(--color-border);
  background: var(--color-bg);
  display: grid;
  place-items: center;
  transition: background 0.15s, border-color 0.15s;
  color: #fff;
  flex-shrink: 0;
}
.v3-card__sel-badge.is-checked {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

/* channel chip */
.v3-card__channel-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}
.v3-card__channel-icon {
  width: 11px;
  height: 11px;
}

.v3-card__name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  line-height: 1.25;
  margin-top: 0.125rem;
}

.v3-card__headline {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.4;
  font-style: italic;
}

.v3-card__body {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.v3-card__cta-pill {
  display: inline-block;
  align-self: flex-start;
  padding: 0.2rem 0.625rem;
  border: 1px solid var(--color-border);
  border-radius: 2rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-surface-muted, var(--color-bg));
}

.v3-card__meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--color-text-subtle);
  border-top: 1px solid var(--color-border);
  padding-top: 0.625rem;
  margin-top: 0.25rem;
  flex-wrap: wrap;
}
.v3-card__meta-dot { opacity: 0.4; }

.v3-card__segment {
  font-size: 0.75rem;
  color: var(--color-text-subtle);
}

/* Hover actions — hidden until hover */
.v3-card__actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  opacity: 0;
  transition: opacity 0.15s;
}
.v3-card:hover .v3-card__actions { opacity: 1; }

.v3-card__action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 0.375rem);
  background: var(--color-bg);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s;
}
.v3-card__action:hover { border-color: var(--color-border-strong); color: var(--color-text); }
.v3-card__action--danger:hover { border-color: rgba(239,68,68,0.4); color: #ef4444; }

/* ── Add card ─────────────────────────────────────────────────────── */
.v3-add-card {
  flex: 0 0 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1.5rem 1rem;
  border: 1.5px dashed var(--color-border);
  border-radius: var(--radius-lg, 0.75rem);
  background: transparent;
  color: var(--color-text-subtle);
  cursor: pointer;
  scroll-snap-align: start;
  transition: border-color 0.18s, color 0.18s, background 0.18s;
  animation: card-in 0.3s ease both;
  animation-delay: var(--enter-delay, 0ms);
}
.v3-add-card:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(10,191,173,0.03);
}
.v3-add-card__ring {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  display: grid;
  place-items: center;
  transition: transform 0.2s;
}
.v3-add-card:hover .v3-add-card__ring { transform: scale(1.1); }
.v3-add-card__label { font-size: 0.875rem; font-weight: 600; }
.v3-add-card__hint  { font-size: 0.75rem; opacity: 0.6; }

/* ── Empty state ─────────────────────────────────────────────────── */
.v3-empty {
  flex: 0 0 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 2rem;
  text-align: center;
  position: relative;
}
.v3-empty__orb {
  position: absolute;
  width: 240px; height: 240px;
  background: radial-gradient(circle, rgba(10,191,173,0.06) 0%, transparent 70%);
  border-radius: 50%;
}
.v3-empty__icon { width: 3rem; height: 3rem; color: var(--color-text-subtle); position: relative; }
.v3-empty__title { font-size: 1rem; font-weight: 600; color: var(--color-text); margin: 0; position: relative; }
.v3-empty__msg { font-size: 0.8125rem; color: var(--color-text-muted); margin: 0; max-width: 28rem; position: relative; }

/* ── Launch bar ──────────────────────────────────────────────────── */
.v3-launch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
  margin: 0.5rem -0.5rem 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg, 0.75rem);
}

.v3-launch-bar__info {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 0;
}

.v3-launch-bar__hint {
  font-size: 0.875rem;
  color: var(--color-text-subtle);
}

.v3-launch-bar__count {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.v3-launch-bar__count strong {
  color: var(--color-accent);
  font-weight: 700;
}

.v3-launch-bar__sel-all {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-subtle);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color 0.12s;
}
.v3-launch-bar__sel-all:hover { color: var(--color-text-muted); }

.v3-launch-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.25rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm, 0.5rem);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s, box-shadow 0.15s, transform 0.15s;
  flex-shrink: 0;
}
.v3-launch-btn:hover:not(:disabled) {
  box-shadow: 0 4px 20px rgba(10,191,173,0.35);
  transform: translateY(-1px);
}
.v3-launch-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

.v3-launch-btn__spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Launch bar transition ───────────────────────────────────────── */
.v3-bar-enter-active, .v3-bar-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.v3-bar-enter-from, .v3-bar-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

</style>

<!-- Drawer + form styles are global because the drawer is teleported to <body> -->
<style>
/* ── Drawer overlay ──────────────────────────────────────────────── */
.v3-drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(2px);
  z-index: 9999;
  display: flex;
  justify-content: flex-end;
}

.v3-drawer {
  width: min(480px, 100vw);
  height: 100%;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  box-shadow: -12px 0 48px rgba(0,0,0,0.2);
}

.v3-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.v3-drawer__title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  margin: 0;
}

.v3-drawer__close {
  width: 2rem; height: 2rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: border-color 0.12s, color 0.12s;
}
.v3-drawer__close:hover { border-color: var(--color-border-strong); color: var(--color-text); }

.v3-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.v3-drawer__footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

.v3-drawer__cancel {
  padding: 0.55rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s;
}
.v3-drawer__cancel:hover { border-color: var(--color-border-strong); color: var(--color-text); }

.v3-drawer__save {
  padding: 0.55rem 1.25rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s, box-shadow 0.15s;
}
.v3-drawer__save:hover { opacity: 0.88; box-shadow: 0 4px 16px rgba(10,191,173,0.3); }

/* ── Drawer transition ───────────────────────────────────────────── */
.v3-drawer-enter-active, .v3-drawer-leave-active {
  transition: opacity 0.22s;
}
.v3-drawer-enter-active .v3-drawer,
.v3-drawer-leave-active .v3-drawer {
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}
.v3-drawer-enter-from, .v3-drawer-leave-to { opacity: 0; }
.v3-drawer-enter-from .v3-drawer, .v3-drawer-leave-to .v3-drawer {
  transform: translateX(100%);
}

/* ── Form inside drawer ──────────────────────────────────────────── */
.v3-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.v3-form__row { display: grid; gap: 0.75rem; }
.v3-form__row--2 { grid-template-columns: 1fr 1fr; }

.v3-form__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.v3-form__label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-muted);
}
.v3-form__label em {
  font-style: normal;
  color: var(--color-accent);
  margin-left: 0.125rem;
}

.v3-form__input,
.v3-form__select,
.v3-form__textarea {
  padding: 0.55rem 0.8rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 0.5rem);
  color: var(--color-text);
  font-size: 0.875rem;
  transition: border-color 0.15s, box-shadow 0.15s;
  font-family: inherit;
}
.v3-form__input:focus,
.v3-form__select:focus,
.v3-form__textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(10,191,173,0.1);
  outline: none;
}
.v3-form__textarea { resize: vertical; line-height: 1.55; }

.v3-form__errors {
  padding: 0.75rem 1rem;
  background: rgba(239,68,68,0.07);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius-sm);
}
.v3-form__errors p {
  font-size: 0.8125rem;
  color: #ef4444;
  margin: 0 0 0.25rem;
}
.v3-form__errors p:last-child { margin-bottom: 0; }
</style>
