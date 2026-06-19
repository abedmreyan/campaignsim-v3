import { ref } from "vue";

const STORAGE_KEY = "cs-theme";
const theme = ref("dark");

function apply(value) {
  theme.value = value;
  document.documentElement.setAttribute("data-theme", value);
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {}
}

export function useTheme() {
  function init() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") {
      apply(saved);
    } else {
      apply("dark"); // default to dark
    }
  }

  function toggle() {
    apply(theme.value === "dark" ? "light" : "dark");
  }

  return { theme, toggle, init };
}
