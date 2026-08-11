import { defineStore } from "pinia";
import {
  applyInsightProposal,
  createInsightSession,
  getInsightSession,
  sendInsightMessage,
} from "@/api/insightApi";

function normalizeError(error, fallback = "Something went wrong.") {
  if (error?.error?.message) return error.error.message;
  return error?.message || fallback;
}

export const useInsightStore = defineStore("insight", {
  state: () => ({
    sessionId: null,
    campaignId: null,
    status: "idle", // idle | active
    messages: [],
    draft: null,
    starting: false,
    sending: false,
    applying: false,
    error: null,
  }),

  getters: {
    // The seeded report message (first assistant turn) and system prompt
    // aren't part of the back-and-forth transcript view.
    visibleMessages: (state) => (state.messages || []).slice(2).filter((m) => m.content),
    reportMessage: (state) => state.messages?.[1]?.content || "",
  },

  actions: {
    async start(campaignId) {
      if (this.sessionId && this.campaignId === campaignId) return;
      this.reset();
      this.campaignId = campaignId;
      this.starting = true;
      this.error = null;
      try {
        const session = await createInsightSession(campaignId);
        this.sessionId = session.id;
        this.status = session.status;
        this.messages = session.messages || [];
        this.draft = session.draft || null;
      } catch (error) {
        this.error = normalizeError(error, "Could not start the insight session.");
        throw error;
      } finally {
        this.starting = false;
      }
    },

    async reload() {
      if (!this.sessionId) return;
      const session = await getInsightSession(this.sessionId);
      this.status = session.status;
      this.messages = session.messages || [];
      this.draft = session.draft || null;
    },

    async sendMessage(text) {
      const message = (text || "").trim();
      if (!message || !this.sessionId) return null;

      this.sending = true;
      this.error = null;
      this.messages = [...this.messages, { role: "user", content: message }];
      try {
        const result = await sendInsightMessage(this.sessionId, message);
        this.messages = result.session?.messages || this.messages;
        this.draft = result.draft || this.draft;
        return result;
      } catch (error) {
        this.error = normalizeError(error, "The insight agent could not respond.");
        throw error;
      } finally {
        this.sending = false;
      }
    },

    async applyProposal() {
      if (!this.sessionId || !this.draft?.variants?.length) return null;
      this.applying = true;
      this.error = null;
      try {
        return await applyInsightProposal(this.sessionId);
      } catch (error) {
        this.error = normalizeError(error, "Could not apply the redesign.");
        throw error;
      } finally {
        this.applying = false;
      }
    },

    discardDraft() {
      this.draft = null;
    },

    reset() {
      this.sessionId = null;
      this.campaignId = null;
      this.status = "idle";
      this.messages = [];
      this.draft = null;
      this.starting = false;
      this.sending = false;
      this.applying = false;
      this.error = null;
    },
  },
});
