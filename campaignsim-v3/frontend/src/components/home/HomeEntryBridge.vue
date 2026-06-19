<template>
  <section class="home-bridge" aria-labelledby="home-bridge-title">
    <div class="home-bridge__card">
      <div class="home-bridge__main">
        <h2 id="home-bridge-title">Ready to test your campaign brief?</h2>
        <p class="home-bridge__text">
          Upload your brand materials on Step 1—PDF, Markdown, or plain text. The workflow
          builds your graph, personas, variants, and ranked report from there.
        </p>
        <ul class="home-bridge__hints" aria-label="Supported file types on Step 1">
          <li>PDF</li>
          <li>Markdown</li>
          <li>Plain text</li>
        </ul>
        <button
          type="button"
          class="app-button app-button--primary home-bridge__cta"
          @click="goToBriefUpload"
        >
          Continue to upload
        </button>
      </div>

      <div v-if="recentItems.length" class="home-bridge__recent">
        <div class="home-bridge__recent-head">
          <span class="home-bridge__recent-label">Recent on this device</span>
          <RouterLink class="home-bridge__recent-link" to="/history">All history</RouterLink>
        </div>
        <ul class="home-bridge__recent-list">
          <li v-for="item in recentItems" :key="item.simulation_id">
            <span class="home-bridge__recent-name">{{ item.project_name }}</span>
            <span class="home-bridge__recent-meta">
              <StatusBadge :status="item.status" />
              <span v-if="item.top_variant_name" class="home-bridge__recent-winner">
                {{ item.top_variant_name }}
              </span>
              <time v-if="item.updated_at" :datetime="item.updated_at">
                {{ formatDate(item.updated_at) }}
              </time>
            </span>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import StatusBadge from "@/components/common/StatusBadge.vue";
import { useCampaignStore } from "@/stores/campaignStore";
import {
  formatHistoryPreviewDate,
  getRecentHistoryPreview,
} from "@/utils/homeHistoryPreview.js";

const router = useRouter();
const store = useCampaignStore();

const recentItems = ref([]);

function formatDate(iso) {
  return formatHistoryPreviewDate(iso);
}

function goToBriefUpload() {
  store.currentStep = 1;
  store.persist();
  router.push({ name: "process" });
}

onMounted(() => {
  recentItems.value = getRecentHistoryPreview(3);
});
</script>
