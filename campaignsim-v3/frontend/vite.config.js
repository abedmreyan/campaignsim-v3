import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-three": ["three"],
          "vendor-gsap":  ["gsap"],
          "vendor-vue":   ["vue", "vue-router", "pinia"],
        },
      },
    },
  },
  server: {
    port: 3006,
    open: false,
    host: true,
    allowedHosts: ["campaignsim-v3.aethersystems.co", "localhost", "127.0.0.1"],
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
      "/health": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    port: 3006,
    host: true,
    allowedHosts: ["campaignsim-v3.aethersystems.co", "localhost", "127.0.0.1"],
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
      "/health": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
