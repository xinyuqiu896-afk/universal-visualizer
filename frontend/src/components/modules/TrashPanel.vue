<template>
  <div class="scroll-area">
    <h3 class="module-title">🗑️ 回收站</h3>
    <el-empty v-if="!list.length" description="回收站为空" :image-size="70" />
    <div v-for="r in list" :key="r.id" class="rec-card">
      <div style="font-weight:600;font-size:13px">{{ r.title }}</div>
      <div class="hint" style="margin:4px 0">{{ r.created_at?.slice(0, 16).replace('T', ' ') }}</div>
      <div style="display:flex;gap:6px">
        <el-button size="small" type="primary" plain @click="restore(r)">恢复</el-button>
        <el-button size="small" type="danger" @click="purge(r)">彻底删除</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '../../api'

const list = ref([])
async function load() { list.value = await api.trashList() }
async function restore(r) { await api.restore(r.id); ElMessage.success('已恢复'); load() }
async function purge(r) {
  await ElMessageBox.confirm('彻底删除后不可恢复，确认？', '警告', { type: 'error' })
  await api.purge(r.id); ElMessage.success('已彻底删除'); load()
}
onMounted(load)
</script>

<style scoped>
.rec-card { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; background: #fff; }
</style>
