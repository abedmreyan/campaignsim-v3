<template>
  <AppCard title="Persona insights" eyebrow="Step 5">
    <div v-if="!personas.length">
      <EmptyState message="Select a persona and ask about campaign results after the report is ready." />
    </div>
    <div v-else class="interview-layout">
      <aside class="persona-picker">
        <input v-model.trim="pickerSearch" type="search" placeholder="Search personas…" />
        <div class="persona-picker__list">
          <button
            v-for="persona in filteredPersonas"
            :key="persona.user_id"
            type="button"
            class="persona-picker__item"
            :class="{ 'is-active': personaId === persona.user_id }"
            @click="personaId = persona.user_id"
          >
            <strong>{{ persona.name }}</strong>
            <span style="display: block; font-size: 0.75rem; color: var(--color-text-muted)">
              {{ persona.segment }}
            </span>
          </button>
        </div>
      </aside>

      <div class="interview-panel">
        <div class="suggested-questions">
          <button
            v-for="suggestion in suggestions"
            :key="suggestion"
            type="button"
            @click="question = suggestion"
          >
            {{ suggestion }}
          </button>
        </div>

        <div ref="chatLogRef" class="chat-log" role="log" aria-live="polite">
          <TransitionGroup name="chat-msg" tag="div" class="chat-log__messages">
            <div
              v-for="message in messages"
              :key="`${message.created_at}-${message.role}-${message.content?.slice(0, 12)}`"
              class="chat-message"
              :class="`chat-message--${message.role}`"
            >
              <span
                v-if="message.role === 'assistant'"
                class="persona-card__avatar"
                style="width: 2rem; height: 2rem; font-size: 0.7rem"
              >
                {{ personaInitials }}
              </span>
              <div class="chat-message__bubble">
                <strong v-if="message.persona_name" style="display: block; margin-bottom: 0.25rem; font-size: 0.75rem">
                  {{ message.persona_name }}
                </strong>
                <p>{{ message.content }}</p>
              </div>
            </div>
            <div v-if="loading" key="typing" class="chat-message chat-message--assistant">
              <span class="persona-card__avatar" style="width: 2rem; height: 2rem; font-size: 0.7rem">
                {{ personaInitials }}
              </span>
              <div class="chat-typing chat-typing--glass" aria-label="Persona is typing">
                <span /><span /><span />
              </div>
            </div>
          </TransitionGroup>
        </div>

        <form class="interview-form interview-form--sticky" @submit.prevent="ask">
          <input v-model.trim="question" type="text" placeholder="Ask why this persona reacted a certain way" />
          <AppButton type="submit" :loading="loading">Send</AppButton>
        </form>
        <ErrorState v-if="error" :message="error" />
      </div>
    </div>
  </AppCard>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";

const props = defineProps({
  personas: {
    type: Array,
    default: () => [],
  },
  messages: {
    type: Array,
    default: () => [],
  },
});
const emit = defineEmits(["ask"]);

const suggestions = [
  "Why did you engage with the winning variant?",
  "Why did you ignore the email campaign?",
  "Which channel feels most natural to you?",
  "What would make this ad more convincing?",
  "Would you buy after seeing this campaign?",
];

const personaId = ref(props.personas[0]?.user_id || null);
const pickerSearch = ref("");
const question = ref("");
const loading = ref(false);
const error = ref("");
const chatLogRef = ref(null);

const filteredPersonas = computed(() => {
  const q = pickerSearch.value.toLowerCase();
  if (!q) return props.personas;
  return props.personas.filter((p) =>
    [p.name, p.segment, p.profession].some((field) => String(field || "").toLowerCase().includes(q)),
  );
});

const personaInitials = computed(() => {
  const persona = props.personas.find((p) => p.user_id === personaId.value);
  return (
    persona?.name
      ?.split(" ")
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "P"
  );
});

async function scrollChatToBottom() {
  await nextTick();
  const el = chatLogRef.value;
  if (!el) return;
  el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
}

watch(
  () => props.personas,
  (personas) => {
    if (!personaId.value && personas.length) personaId.value = personas[0].user_id;
  },
  { immediate: true },
);

watch(
  () => [props.messages.length, loading.value],
  () => scrollChatToBottom(),
);

async function ask() {
  if (!personaId.value || !question.value) {
    error.value = "Choose a persona and enter a question.";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await emit("ask", { personaId: personaId.value, question: question.value });
    question.value = "";
    await scrollChatToBottom();
  } catch (err) {
    error.value = err?.message || "Could not ask the persona.";
  } finally {
    loading.value = false;
  }
}
</script>
