<template>
  <DrawerPanel :open="open" title="Create a custom channel" eyebrow="Channel registry" @close="$emit('close')">
    <div class="create-channel">
      <p class="create-channel__intro">
        Describe the marketing channel in plain language — an AI drafts the action
        vocabulary, engagement weights, and content framing. Review and edit
        before saving.
      </p>

      <form v-if="!draft" class="create-channel__describe" @submit.prevent="requestDraft">
        <label>
          <span>Channel description</span>
          <textarea
            v-model.trim="description"
            rows="3"
            placeholder="e.g. a podcast pre-roll ad read by the host, delivered to subscribers who follow the show"
          ></textarea>
        </label>
        <p v-if="error" class="create-channel__error">{{ error }}</p>
        <AppButton type="submit" :loading="drafting">Draft with AI</AppButton>
      </form>

      <div v-else class="create-channel__review">
        <label>
          <span>Key</span>
          <input v-model.trim="draft.key" type="text" placeholder="podcast_ad" />
        </label>
        <label>
          <span>Name</span>
          <input v-model.trim="draft.name" type="text" placeholder="Podcast Ad" />
        </label>
        <label>
          <span>Kind</span>
          <select v-model="draft.kind">
            <option value="feed">Feed — agents see and react to shared posts</option>
            <option value="direct">Direct — private, no social propagation</option>
          </select>
        </label>
        <label>
          <span>Formats (comma-separated)</span>
          <input :value="(draft.formats || []).join(', ')" type="text" @input="setFormats($event.target.value)" />
        </label>
        <label>
          <span>Framing template</span>
          <input v-model.trim="draft.framing_template" type="text" placeholder="[Channel {format}] {headline}" />
        </label>
        <div class="create-channel__weights">
          <span class="create-channel__weights-label">Action weights</span>
          <div v-for="action in draft.available_actions || []" :key="action" class="create-channel__weight-row">
            <code>{{ action }}</code>
            <input
              type="number"
              step="0.05"
              min="-1"
              max="1"
              :value="draft.action_weights?.[action] ?? 0"
              @input="setWeight(action, $event.target.value)"
            />
          </div>
        </div>
        <p v-if="draft.weights_rationale" class="create-channel__rationale">{{ draft.weights_rationale }}</p>
        <p v-if="error" class="create-channel__error">{{ error }}</p>
        <div class="create-channel__actions">
          <AppButton variant="secondary" type="button" @click="draft = null">Start over</AppButton>
          <AppButton type="button" :loading="saving" @click="save">Save channel</AppButton>
        </div>
      </div>
    </div>
  </DrawerPanel>
</template>

<script setup>
import { ref } from "vue";
import DrawerPanel from "@/components/common/DrawerPanel.vue";
import AppButton from "@/components/common/AppButton.vue";
import { draftChannel, createChannel } from "@/api/campaignApi";

defineProps({ open: Boolean });
const emit = defineEmits(["close", "created"]);

const description = ref("");
const draft = ref(null);
const drafting = ref(false);
const saving = ref(false);
const error = ref("");

async function requestDraft() {
  if (!description.value) return;
  drafting.value = true;
  error.value = "";
  try {
    draft.value = await draftChannel({ description: description.value });
  } catch (err) {
    error.value = err?.message || "Could not draft a channel definition.";
  } finally {
    drafting.value = false;
  }
}

function setFormats(value) {
  draft.value.formats = value.split(",").map((f) => f.trim()).filter(Boolean);
}

function setWeight(action, value) {
  draft.value.action_weights = { ...draft.value.action_weights, [action]: Number(value) };
}

async function save() {
  if (!draft.value?.key || !draft.value?.name) {
    error.value = "Key and name are required.";
    return;
  }
  saving.value = true;
  error.value = "";
  try {
    const channel = await createChannel(draft.value);
    emit("created", channel);
    reset();
    emit("close");
  } catch (err) {
    error.value = err?.message || "Could not save this channel.";
  } finally {
    saving.value = false;
  }
}

function reset() {
  description.value = "";
  draft.value = null;
  error.value = "";
}

defineExpose({ reset });
</script>

<style scoped>
.create-channel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.create-channel__intro {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  line-height: 1.5;
}

.create-channel__describe,
.create-channel__review {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.create-channel__error {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin: 0;
}

.create-channel__weights {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm);
}

.create-channel__weights-label {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.create-channel__weight-row {
  display: grid;
  grid-template-columns: 1fr 6rem;
  align-items: center;
  gap: 0.75rem;
}

.create-channel__weight-row code {
  font-size: 0.8rem;
}

.create-channel__rationale {
  font-size: 0.8125rem;
  color: var(--color-text-subtle);
  font-style: italic;
}

.create-channel__actions {
  display: flex;
  gap: 0.75rem;
}
</style>
