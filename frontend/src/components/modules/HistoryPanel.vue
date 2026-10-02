<template>
  <div class="scroll-area">
    <h3 class="module-title">🕘 历史记录</h3>
    <div style="display:flex;gap:8px;margin-bottom:10px">
      <el-input v-model="keyword" size="small" placeholder="搜索标题/摘要/文件名" clearable @input="load" />
      <el-button size="small" @click="load">搜索</el-button>
    </div>
    <el-empty v-if="!list.length" description="暂无历史记录" :image-size="70" />
    <div v-for="r in list" :key="r.id" class="rec-card">
      <div style="display:flex;align-items:center;gap:6px">
        <span style="font-weight:600;font-size:13px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ r.title }}</span>
        <el-icon v-if="r.favorite" color="#f59e0b"><StarFilled /></el-icon>
      </div>
      <div class="hint" style="margin:4px 0">{{ r.category }} · {{ r.source_type }} · {{ r.created_at?.slice(0, 16).replace('T', ' ') }}</div>
      <div class="tag-line">
        <el-tag v-for="t in r.tags?.slice(0, 3)" :key="t" size="small" type="info">{{ t }}</el-tag>
      </div>
      <div style="display:flex;gap:6px;margin-top:8px">
        <el-button size="small" type="primary" @click="view(r)">查看</el-button>
        <el-button size="small" @click="fav(r)">{{ r.favorite ? '取消收藏' : '收藏' }}</el-button>
        <el-button size="small" type="danger" plain @click="del(r)">删除</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { StarFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const list = ref([]), keyword = ref('')

async function load() { list.value = await api.history({ keyword: keyword.value }) }
async function view(r) {
  state.previewSrc = api.previewUrl(r.id)
  state.currentRecordId = r.id
  if (!state.recentRecords.find(x => x.id === r.id)) state.recentRecords.unshift(r)
}
async function fav(r) { await api.toggleFav(r.id); load() }
async function del(r) {
  await ElMessageBox.confirm('移入回收站？', '提示', { type: 'warning' })
  await api.toTrash(r.id); ElMessage.success('已移入回收站'); load()
}
onMounted(load)
</script>

<style scoped>
.rec-card { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; background: #fff; }
</style>
