<template>
  <section class="home-journey" aria-labelledby="home-journey-title">
    <div class="home-section-label" aria-hidden="true">02 — How it works</div>
    <div class="home-journey__head">
      <h2 id="home-journey-title">Five steps from brief to decision</h2>
      <p>Each stage builds on the last—upload once, then move through the pipeline without re-entering context.</p>
    </div>
    <div class="home-journey__track">
      <div class="home-journey__connector" aria-hidden="true" />
      <article v-for="step in steps" :key="step.n" class="home-journey__step">
        <em class="home-journey__num">{{ step.n }}</em>
        <strong class="home-journey__title">{{ step.title }}</strong>
        <span class="home-journey__detail">{{ step.detail }}</span>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({ steps: { type: Array, required: true } });
</script>
