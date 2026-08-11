<template>
  <AppCard eyebrow="Co-design" title="Campaign Designer" class="designer-panel">
    <p class="designer-panel__intro">
      Chat with an AI strategist grounded in your brand's knowledge graph, channel
      registry, generated audience, and past campaign results. Proposals show up
      below as editable variant cards — nothing is added to the builder until you
      accept it.
    </p>

    <div v-if="!store.sessionId && !store.starting" class="designer-panel__start">
      <AppButton variant="secondary" @click="start">Start designer chat</AppButton>
    </div>

    <AppLoader v-else-if="store.starting" label="Starting designer session…" />

    <template v-else>
      <div ref="threadEl" class="designer-panel__thread">
        <div
          v-for="(message, index) in store.visibleMessages"
          :key="index"
          class="designer-message"
          :class="`designer-message--${message.role}`"
        >
          <span class="designer-message__role">{{ message.role === "user" ? "You" : "Strategist" }}</span>
          <p>{{ message.content }}</p>
        </div>
        <div v-if="store.sending" class="designer-message designer-message--assistant designer-message--thinking">
          <span class="designer-message__role">Strategist</span>
          <p>Thinking…</p>
        </div>
      </div>

      <ErrorState v-if="store.error" :message="store.error" />

      <form class="designer-panel__composer" @submit.prevent="submit">
        <textarea
          v-model="draftMessage"
          rows="2"
          placeholder="e.g. Help me design variants to drive trial among urban professionals."
          :disabled="store.sending || store.status !== 'active'"
        ></textarea>
        <AppButton type="submit" :loading="store.sending" :disabled="!draftMessage.trim() || store.status !== 'active'">
          Send
        </AppButton>
      </form>

      <div v-if="store.status !== 'active'" class="designer-panel__locked">
        This session is {{ store.status }} — start a new one to keep designing.
      </div>

      <div v-if="store.draft?.variants?.length" class="designer-panel__draft">
        <h3>Proposed variants</h3>
        <div class="designer-proposal-list">
          <article v-for="(variant, index) in store.draft.variants" :key="index" class="designer-proposal-card">
            <header>
              <h4>{{ variant.variant_name }}</h4>
              <span>{{ variant.channel }} · {{ variant.format }}</span>
            </header>
            <p class="designer-proposal-card__headline">{{ variant.headline }}</p>
            <p>{{ variant.body }}</p>
            <p class="designer-proposal-card__note"><strong>Rationale:</strong> {{ variant.rationale }}</p>
            <p class="designer-proposal-card__note"><strong>Hypothesis:</strong> {{ variant.hypothesis }}</p>
            <div class="card-actions">
              <AppButton size="sm" @click="addOne(variant)">Add to builder</AppButton>
            </div>
          </article>
        </div>
        <div class="card-actions">
          <AppButton variant="secondary" size="sm" @click="addAll">Add all to builder</AppButton>
          <AppButton variant="danger" size="sm" @click="store.discardDraft()">Discard proposal</AppButton>
        </div>
      </div>
    </template>
  </AppCard>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import AppLoader from "@/components/common/AppLoader.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import { useDesignerStore } from "@/stores/designerStore";
import { useCampaignStore } from "@/stores/campaignStore";

const MAX_VARIANTS = 6;

const store = useDesignerStore();
const campaignStore = useCampaignStore();
const draftMessage = ref("");
const threadEl = ref(null);

async function start() {
  try {
    await store.start(campaignStore.simulationId);
  } catch {
    // store.error already holds a user-facing message
  }
}

async function submit() {
  const message = draftMessage.value;
  draftMessage.value = "";
  try {
    await store.sendMessage(message);
  } catch {
    // store.error already holds a user-facing message
  }
}

function addOne(variant) {
  if (campaignStore.variants.length >= MAX_VARIANTS) {
    campaignStore.setNotice(`A campaign supports a maximum of ${MAX_VARIANTS} variants.`);
    return;
  }
  campaignStore.addVariant({ ...variant, provenance: "ai" });
}

function addAll() {
  const variants = store.draft?.variants || [];
  const room = MAX_VARIANTS - campaignStore.variants.length;
  if (room <= 0) {
    campaignStore.setNotice(`A campaign supports a maximum of ${MAX_VARIANTS} variants.`);
    return;
  }
  variants.slice(0, room).forEach((variant) => campaignStore.addVariant({ ...variant, provenance: "ai" }));
  if (variants.length > room) {
    campaignStore.setNotice(`Added ${room} of ${variants.length} proposed variants (6-variant limit reached).`);
  }
}

watch(
  () => store.messages.length,
  async () => {
    await nextTick();
    if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight;
  },
);
</script>

<style scoped>
.designer-panel__intro {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.designer-panel__thread {
  max-height: 22rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-right: 0.25rem;
}

.designer-message {
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-md);
  background: var(--color-surface-muted);
  max-width: 90%;
}

.designer-message--user {
  align-self: flex-end;
  background: var(--color-accent-soft);
}

.designer-message--thinking p {
  opacity: 0.6;
}

.designer-message__role {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-subtle);
  margin-bottom: 0.2rem;
}

.designer-panel__composer {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.9rem;
}

.designer-panel__composer textarea {
  flex: 1;
  resize: vertical;
}

.designer-panel__locked {
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.designer-panel__draft {
  margin-top: 1.25rem;
  border-top: 1px solid var(--color-border);
  padding-top: 1rem;
}

.designer-proposal-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.designer-proposal-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.9rem;
}

.designer-proposal-card header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.designer-proposal-card__headline {
  font-weight: 600;
}

.designer-proposal-card__note {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}
</style>
