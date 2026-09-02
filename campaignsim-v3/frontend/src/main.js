import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/base.css";
import "./styles/dashboard.css";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// Attempt to restore auth state from cookie before mounting.
// The router guard also calls fetchMe() but doing it here avoids
// a flash of unauthenticated state on first render.
import("@/stores/authStore").then(({ useAuthStore }) => {
  const auth = useAuthStore();
  auth.fetchMe().finally(() => {
    app.mount("#app");
  });
});
