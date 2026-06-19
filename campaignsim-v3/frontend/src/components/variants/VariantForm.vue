<template>
  <form class="variant-form" @submit.prevent="submit">
    <div class="form-grid">
      <label>
        <span>Variant name</span>
        <input v-model.trim="form.variant_name" type="text" placeholder="Instagram Video Ad" />
      </label>
      <label>
        <span>Channel</span>
        <select v-model="form.channel">
          <option value="">Select channel</option>
          <option v-for="channel in channels" :key="channel" :value="channel">{{ channel }}</option>
        </select>
      </label>
      <label>
        <span>Format</span>
        <select v-model="form.format">
          <option value="">Select format</option>
          <option v-for="format in formats" :key="format" :value="format">{{ format }}</option>
        </select>
      </label>
      <label>
        <span>Tone</span>
        <select v-model="form.tone">
          <option value="">Select tone</option>
          <option v-for="tone in tones" :key="tone" :value="tone">{{ tone }}</option>
        </select>
      </label>
      <label>
        <span>Headline</span>
        <input v-model.trim="form.headline" type="text" placeholder="Zero Sugar. Zero Wait." />
      </label>
      <label>
        <span>CTA</span>
        <input v-model.trim="form.cta" type="text" placeholder="Try it now" />
      </label>
      <label v-if="form.channel === 'email'">
        <span>Email subject</span>
        <input v-model.trim="form.email_subject" type="text" placeholder="Your mornings just got better" />
      </label>
      <label>
        <span>Target segment</span>
        <input v-model.trim="form.target_segment" type="text" placeholder="Urban Professionals" />
      </label>
      <label>
        <span>Max rounds</span>
        <input v-model.number="form.max_rounds" type="number" min="1" max="50" />
      </label>
    </div>
    <label>
      <span>Body</span>
      <textarea v-model.trim="form.body" rows="3" placeholder="Premium cold brew ready in 30 seconds."></textarea>
    </label>
    <label>
      <span>Visual description</span>
      <textarea v-model.trim="form.visual_desc" rows="2" placeholder="Fast-paced morning commute video."></textarea>
    </label>
    <div v-if="errors.length" class="form-errors">
      <p v-for="error in errors" :key="error">{{ error }}</p>
    </div>
    <div class="form-actions">
      <AppButton variant="primary" type="submit">{{ editing ? "Save variant" : "Add variant" }}</AppButton>
      <AppButton v-if="editing" variant="secondary" @click="$emit('cancel')">Cancel</AppButton>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref, watch } from "vue";
import AppButton from "@/components/common/AppButton.vue";

const props = defineProps({
  editing: Boolean,
  modelValue: Object,
});
const emit = defineEmits(["submit", "cancel"]);

const channels = ["instagram", "email", "tiktok", "linkedin"];
const formats = ["VideoAd", "CarouselPost", "EmailNewsletter", "ShortFormVideo", "SponsoredPost"];
const tones = ["playful", "professional", "urgent", "neutral"];
const errors = ref([]);

const emptyForm = () => ({
  variant_name: "",
  channel: "",
  format: "",
  headline: "",
  body: "",
  cta: "",
  visual_desc: "",
  email_subject: "",
  tone: "neutral",
  target_segment: "",
  max_rounds: 10,
});

const form = reactive(emptyForm());

function hydrate(value) {
  Object.assign(form, emptyForm(), {
    ...value,
    format: value?.content?.format || value?.format || "",
    headline: value?.content?.headline || value?.headline || "",
    body: value?.content?.body || value?.body || "",
    cta: value?.content?.cta || value?.cta || "",
    visual_desc: value?.content?.visual_desc || value?.visual_desc || "",
    email_subject: value?.content?.email_subject || value?.email_subject || "",
    tone: value?.content?.tone || value?.tone || "neutral",
  });
}

watch(
  () => props.modelValue,
  (value) => hydrate(value),
  { immediate: true },
);

function validate() {
  const next = [];
  ["variant_name", "channel", "format", "headline", "body", "cta"].forEach((field) => {
    if (!form[field]) next.push(`${field.replace("_", " ")} is required.`);
  });
  if (form.channel === "email" && !form.email_subject) next.push("email subject is required for email.");
  if (Number(form.max_rounds) < 1 || Number(form.max_rounds) > 50) {
    next.push("max rounds must be between 1 and 50.");
  }
  errors.value = next;
  return next.length === 0;
}

function submit() {
  if (!validate()) return;
  emit("submit", { ...form });
  hydrate(null);
  errors.value = [];
}
</script>
