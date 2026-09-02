<template>
  <AppCard eyebrow="Iterate" title="Insight Agent" class="insight-panel">
    <p class="insight-panel__intro">
      Ask why a variant performed the way it did — the agent can drill into the action
      log, interview simulated personas in character, check the Designer's recorded
      hypotheses against outcomes, and compare this campaign to prior iterations. Ask it
      to redesign the campaign when you're ready to test a fix.
    </p>

    <div v-if="!store.sessionId && !store.starting" class="insight-panel__start">
      <AppButton variant="secondary" @click="start">Start insight chat</AppButton>
    </div>

    <AppLoader v-else-if="store.starting" label="Loading campaign results…" />

    <template v-else>
      <div ref="threadEl" class="insight-panel__thread">
        <div
          v-for="(message, index) in store.visibleMessages"
          :key="index"
          class="insight-message"
          :class="`insight-message--${message.role}`"
        >
          <span class="insight-message__role">{{ message.role === "user" ? "You" : "Analyst" }}</span>
          <p>{{ message.content }}</p>
        </div>
        <div v-if="store.sending" class="insight-message insight-message--assistant insight-message--thinking">
          <span class="insight-message__role">Analyst</span>
          <p>Thinking…</p>
        </div>
        <div v-if="!store.visibleMessages.length && !store.sending" class="insight-panel__empty">
          Ask a question about these results — e.g. "Why did the lowest-ranked variant underperform?"
        </div>
      </div>

      <ErrorState v-if="store.error" :message="store.error" />

      <form class="insight-panel__composer" @submit.prevent="submit">
        <textarea
          v-model="draftMessage"
          rows="2"
          placeholder="e.g. Why did engagement drop off for the email variant?"
          :disabled="store.sending"
        ></textarea>
        <AppButton type="submit" :loading="store.sending" :disabled="!draftMessage.trim()">Send</AppButton>
      </form>

      <div v-if="store.draft?.variants?.length" class="insight-panel__draft">
        <h3>Proposed redesign</h3>
        <div class="insight-proposal-list">
          <article v-for="(variant, index) in store.draft.variants" :key="index" class="insight-proposal-card">
            <header>
              <h4>{{ variant.variant_name }}</h4>
              <span>{{ variant.channel }} · {{ variant.format }}</span>
            </header>
            <p class="insight-proposal-card__headline">{{ variant.headline }}</p>
            <p>{{ variant.body }}</p>
            <p class="insight-proposal-card__note"><strong>What changed:</strong> {{ variant.rationale }}</p>
            <p class="insight-proposal-card__note"><strong>Hypothesis:</strong> {{ variant.hypothesis }}</p>
          </article>
        </div>
        <div class="card-actions">
          <AppButton :loading="store.applying" @click="apply">Apply redesign → open in Designer</AppButton>
          <AppButton variant="danger" size="sm" @click="store.discardDraft()">Discard</AppButton>
        </div>
      </div>
    </template>
  </AppCard>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import AppLoader from "@/components/common/AppLoader.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import { useInsightStore } from "@/stores/insightStore";

const props = defineProps({
  campaignId: { type: String, required: true },
});

const store = useInsightStore();
const router = useRouter();
const draftMessage = ref("");
const threadEl = ref(null);

async function start() {
  try {
    await store.start(props.campaignId);
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

async function apply() {
  try {
    const result = await store.applyProposal();
    if (result?.designer_session?.id) {
      router.push({ name: "designer-session", params: { sessionId: result.designer_session.id } });
    }
  } catch {
    // store.error already holds a user-facing message
  }
}

watch(
  () => store.messages.length,
  async () => {
    await nextTick();
    if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight;
  },
);

// Reaching this panel for a different campaign than the one currently loaded
// (e.g. navigating report -> report without a full remount) must not keep
// showing the previous campaign's session.
watch(
  () => props.campaignId,
  (next) => {
    if (store.sessionId && store.campaignId !== next) store.reset();
  },
);
</script>

<style scoped>
.insight-panel__intro {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.insight-panel__thread {
  max-height: 22rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-right: 0.25rem;
}

.insight-panel__empty {
  color: var(--color-text-subtle);
  font-size: 0.85rem;
}

.insight-message {
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-md);
  background: var(--color-surface-muted);
  max-width: 90%;
}

.insight-message--user {
  align-self: flex-end;
  background: var(--color-accent-soft);
}

.insight-message--thinking p {
  opacity: 0.6;
}

.insight-message__role {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-subtle);
  margin-bottom: 0.2rem;
}

.insight-panel__composer {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.9rem;
}

.insight-panel__composer textarea {
  flex: 1;
  resize: vertical;
}

.insight-panel__draft {
  margin-top: 1.25rem;
  border-top: 1px solid var(--color-border);
  padding-top: 1rem;
}

.insight-proposal-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.insight-proposal-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.9rem;
}

.insight-proposal-card header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.insight-proposal-card__headline {
  font-weight: 600;
}

.insight-proposal-card__note {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}
</style>
