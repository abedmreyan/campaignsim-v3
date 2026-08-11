import { defineStore } from "pinia";
import {
  commitDesignerSession,
  createDesignerSession,
  getDesignerSession,
  sendDesignerMessage,
  updateDesignerDraft,
} from "@/api/designerApi";

function normalizeError(error, fallback = "Something went wrong.") {
  if (error?.error?.message) return error.error.message;
  return error?.message || fallback;
}

export const useDesignerStore = defineStore("designer", {
  state: () => ({
    sessionId: null,
    status: "idle", // idle | active | committed | abandoned
    messages: [],
    draft: null,
    starting: false,
    sending: false,
    error: null,
  }),

  getters: {
    // Chat bubbles only — system prompt and raw tool-call/tool-result turns
    // aren't meant for the transcript view.
    visibleMessages: (state) =>
      state.messages.filter((m) => (m.role === "user" || m.role === "assistant") && m.content),
  },

  actions: {
    async start(simulationId) {
      if (this.sessionId) return; // one session per builder visit is enough
      this.starting = true;
      this.error = null;
      try {
        const session = await createDesignerSession({ simulationId });
        this.sessionId = session.id;
        this.status = session.status;
        this.messages = session.messages || [];
        this.draft = session.draft || null;
      } catch (error) {
        this.error = normalizeError(error, "Could not start the designer session.");
        throw error;
      } finally {
        this.starting = false;
      }
    },

    async reload() {
      if (!this.sessionId) return;
      const session = await getDesignerSession(this.sessionId);
      this.status = session.status;
      this.messages = session.messages || [];
      this.draft = session.draft || null;
    },

    // Resume an existing session by id — used when a session was created
    // elsewhere (e.g. applying an Insight redesign proposal) rather than
    // started fresh from this store.
    async resume(sessionId) {
      this.reset();
      this.sessionId = sessionId;
      this.starting = true;
      this.error = null;
      try {
        await this.reload();
      } catch (error) {
        this.error = normalizeError(error, "Could not load the designer session.");
        throw error;
      } finally {
        this.starting = false;
      }
    },

    async removeDraftVariant(index) {
      if (!this.draft?.variants) return;
      const variants = this.draft.variants.filter((_, i) => i !== index);
      const updated = await updateDesignerDraft(this.sessionId, { ...this.draft, variants });
      this.draft = updated.draft;
    },

    async commit() {
      if (!this.sessionId) return null;
      const result = await commitDesignerSession(this.sessionId);
      this.status = "committed";
      return result.payload;
    },

    async sendMessage(text) {
      const message = (text || "").trim();
      if (!message || !this.sessionId) return null;

      this.sending = true;
      this.error = null;
      // Optimistic echo so the chat feels responsive while the agent thinks.
      this.messages = [...this.messages, { role: "user", content: message }];
      try {
        const result = await sendDesignerMessage(this.sessionId, message);
        this.messages = result.session?.messages || this.messages;
        this.draft = result.draft || this.draft;
        return result;
      } catch (error) {
        this.error = normalizeError(error, "The designer agent could not respond.");
        throw error;
      } finally {
        this.sending = false;
      }
    },

    discardDraft() {
      this.draft = null;
    },

    reset() {
      this.sessionId = null;
      this.status = "idle";
      this.messages = [];
      this.draft = null;
      this.starting = false;
      this.sending = false;
      this.error = null;
    },
  },
});
