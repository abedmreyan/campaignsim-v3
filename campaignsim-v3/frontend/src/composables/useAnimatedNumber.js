import { onBeforeUnmount, ref, unref, watch } from "vue";

/**
 * Smooth count-up for numeric metric displays (presentation only).
 */
export function useAnimatedNumber(source, duration = 420) {
  const display = ref(0);
  let frameId = null;

  function animateTo(target) {
    if (!Number.isFinite(target)) return;
    const from = display.value;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - progress) ** 3;
      display.value = Math.round(from + (target - from) * eased);
      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      }
    };

    if (frameId) cancelAnimationFrame(frameId);
    frameId = requestAnimationFrame(step);
  }

  watch(
    () => {
      const raw = unref(source);
      const num = Number(raw);
      return Number.isFinite(num) ? num : null;
    },
    (value) => {
      if (value === null) return;
      animateTo(value);
    },
    { immediate: true },
  );

  onBeforeUnmount(() => {
    if (frameId) cancelAnimationFrame(frameId);
  });

  return display;
}
