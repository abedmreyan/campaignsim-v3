import { onMounted, onUnmounted } from "vue";

const CLASS_MAP = {
  reveal:       "scroll-hidden",
  "reveal-left":  "scroll-hidden-left",
  "reveal-scale": "scroll-hidden-scale",
};

/**
 * Scroll-triggered reveal. Elements are visible by default.
 * On mount we mark them hidden, then reveal as they enter the viewport.
 * If JS is slow or IntersectionObserver unsupported, content stays visible.
 */
export function useScrollReveal(
  containerRef,
  selector = ".reveal, .reveal-left, .reveal-scale",
  options = { threshold: 0.08, rootMargin: "0px 0px -20px 0px" },
) {
  let observer = null;
  let targets = [];

  onMounted(() => {
    if (typeof IntersectionObserver === "undefined") return;

    const root = containerRef?.value ?? document;
    targets = Array.from(root.querySelectorAll(selector));
    if (!targets.length) return;

    observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          // Remove the hidden marker
          Object.values(CLASS_MAP).forEach((c) => el.classList.remove(c));
          el.classList.add("is-revealed");
          observer.unobserve(el);
        }
      });
    }, options);

    // Mark hidden then observe in the same microtask flush
    // so there's no visible flash
    requestAnimationFrame(() => {
      targets.forEach((el) => {
        // Determine which reveal type this element is
        for (const [revealClass, hiddenClass] of Object.entries(CLASS_MAP)) {
          if (el.classList.contains(revealClass)) {
            el.classList.add(hiddenClass);
            break;
          }
        }
        observer.observe(el);
      });
    });
  });

  onUnmounted(() => {
    observer?.disconnect();
    // Restore visibility on unmount
    targets.forEach((el) => {
      Object.values(CLASS_MAP).forEach((c) => el.classList.remove(c));
    });
  });
}
