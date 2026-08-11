<template>
  <div class="designer-session-view view-stack stagger-in">
    <PageHeader
      title="Campaign Designer"
      eyebrow="Iteration draft"
      description="Review, edit through chat, or remove proposed variants, then launch this iteration."
    />

    <AppLoader v-if="store.starting" label="Loading designer session…" />
    <ErrorState v-else-if="store.error && !store.sessionId" :message="store.error" />

    <template v-else>
      <div class="designer-session-view__layout">
        <AppCard eyebrow="Chat" title="Refine with the strategist">
          <div ref="threadEl" class="designer-session-view__thread">
            <div
              v-for="(message, index) in visibleMessages"
              :key="index"
              class="designer-session-view__message"
              :class="`designer-session-view__message--${message.role}`"
            >
              <span class="designer-session-view__role">{{ message.role === "user" ? "You" : "Strategist" }}</span>
              <p>{{ message.content }}</p>
            </div>
            <div v-if="store.sending" class="designer-session-view__message designer-session-view__message--assistant">
              <span class="designer-session-view__role">Strategist</span>
              <p>Thinking…</p>
            </div>
          </div>
          <ErrorState v-if="store.error" :message="store.error" />
          <form class="designer-session-view__composer" @submit.prevent="submit">
            <textarea
              v-model="draftMessage"
              rows="2"
              placeholder="e.g. Swap the CTA on the second variant to something more urgent."
              :disabled="store.sending || store.status !== 'active'"
            ></textarea>
            <AppButton type="submit" :loading="store.sending" :disabled="!draftMessage.trim() || store.status !== 'active'">
              Send
            </AppButton>
          </form>
        </AppCard>

        <AppCard eyebrow="Draft" title="Variants to launch">
          <EmptyState v-if="!store.draft?.variants?.length" title="No variants in this draft" message="Ask the strategist to propose or restore variants." />
          <div v-else class="designer-session-view__variants">
            <article v-for="(variant, index) in store.draft.variants" :key="index" class="designer-session-view__variant-card">
              <header>
                <h4>{{ variant.variant_name }}</h4>
                <span>{{ variant.channel }} · {{ variant.format }}</span>
              </header>
              <p class="designer-session-view__headline">{{ variant.headline }}</p>
              <p>{{ variant.body }}</p>
              <p v-if="variant.rationale" class="designer-session-view__note"><strong>Rationale:</strong> {{ variant.rationale }}</p>
              <p v-if="variant.hypothesis" class="designer-session-view__note"><strong>Hypothesis:</strong> {{ variant.hypothesis }}</p>
              <div class="card-actions">
                <AppButton variant="danger" size="sm" @click="removeVariant(index)">Remove</AppButton>
              </div>
            </article>
          </div>
          <div class="card-actions" style="margin-top: 1rem">
            <AppButton
              size="lg"
              :loading="launching"
              :disabled="!store.draft?.variants?.length || store.status !== 'active'"
              @click="launch"
            >
              Launch this iteration
            </AppButton>
          </div>
          <ErrorState v-if="launchError" :message="launchError" />
        </AppCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import AppLoader from "@/components/common/AppLoader.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import { useDesignerStore } from "@/stores/designerStore";
import { startAbTest } from "@/api/campaignApi";

const route = useRoute();
const router = useRouter();
const store = useDesignerStore();
const draftMessage = ref("");
const threadEl = ref(null);
const launching = ref(false);
const launchError = ref(null);

const visibleMessages = computed(() =>
  store.messages.filter((m) => (m.role === "user" || m.role === "assistant") && m.content),
);

async function submit() {
  const message = draftMessage.value;
  draftMessage.value = "";
  try {
    await store.sendMessage(message);
  } catch {
    // store.error already holds a user-facing message
  }
}

async function removeVariant(index) {
  try {
    await store.removeDraftVariant(index);
  } catch (err) {
    launchError.value = err?.message || "Could not remove that variant.";
  }
}

async function launch() {
  launching.value = true;
  launchError.value = null;
  try {
    const payload = await store.commit();
    const result = await startAbTest(payload);
    const newCampaignId = result.campaign_id;
    router.push({ name: "CampaignReport", params: { campaignId: newCampaignId } });
  } catch (err) {
    launchError.value = err?.message || "Could not launch this iteration.";
  } finally {
    launching.value = false;
  }
}

watch(
  () => store.messages.length,
  async () => {
    await nextTick();
    if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight;
  },
);

onMounted(() => {
  store.resume(route.params.sessionId);
});

watch(
  () => route.params.sessionId,
  (next) => {
    if (next && next !== store.sessionId) store.resume(next);
  },
);
</script>

<style scoped>
.designer-session-view__layout {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 900px) {
  .designer-session-view__layout {
    grid-template-columns: 1fr;
  }
}

.designer-session-view__thread {
  max-height: 24rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-right: 0.25rem;
  margin-bottom: 0.75rem;
}

.designer-session-view__message {
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-md);
  background: var(--color-surface-muted);
  max-width: 90%;
}

.designer-session-view__message--user {
  align-self: flex-end;
  background: var(--color-accent-soft);
}

.designer-session-view__role {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-subtle);
  margin-bottom: 0.2rem;
}

.designer-session-view__composer {
  display: flex;
  gap: 0.5rem;
}

.designer-session-view__composer textarea {
  flex: 1;
  resize: vertical;
}

.designer-session-view__variants {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.designer-session-view__variant-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.9rem;
}

.designer-session-view__variant-card header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.designer-session-view__headline {
  font-weight: 600;
}

.designer-session-view__note {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}
</style>
