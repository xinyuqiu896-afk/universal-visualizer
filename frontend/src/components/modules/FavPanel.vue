<template>
  <div class="scroll-area">
    <h3 class="module-title">⭐ 收藏</h3>
    <el-empty v-if="!list.length" description="暂无收藏" :image-size="70" />
    <div v-for="r in list" :key="r.id" class="rec-card">
      <div style="font-weight:600;font-size:13px">{{ r.title }}</div>
      <div class="hint" style="margin:4px 0">{{ r.category }} · {{ r.created_at?.slice(0, 10) }}</div>
      <el-button size="small" type="primary" @click="view(r)">查看</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import * as api from '../../api'

const state = inject('appState')
const list = ref([])
async function load() { list.value = await api.history({ favorite: 1 }) }
function view(r) {
  state.previewSrc = api.previewUrl(r.id)
  state.currentRecordId = r.id
}
onMounted(load)
</script>

<style scoped>
.rec-card { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; background: #fff; }
</style>
