import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import i18n from "./i18n/index.js";
import "./styles/base.css";
import "./styles/dashboard.css";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(i18n);

// Attempt to restore auth state from cookie before mounting.
// The router guard also calls fetchMe() but doing it here avoids
// a flash of unauthenticated state on first render.
import("@/stores/authStore").then(({ useAuthStore }) => {
  const auth = useAuthStore();
  auth.fetchMe().finally(() => {
    app.mount("#app");
  });
});
