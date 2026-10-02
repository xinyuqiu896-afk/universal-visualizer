<template>
  <div class="scroll-area">
    <h3 class="module-title">⚡ 批量处理</h3>
    <div class="card-box">
      <el-upload drag multiple :show-file-list="false" :before-upload="pick" accept=".docx,.doc,.pptx,.pdf,.txt,.md,.csv,.xlsx,.xls">
        <el-icon size="32" style="color:var(--primary)"><Files /></el-icon>
        <div style="margin-top:4px">批量选择文件（可多选）</div>
      </el-upload>
      <div v-if="queue.length" class="hint" style="margin:8px 0">已加入 {{ queue.length }} 个文件</div>
      <el-button type="primary" size="small" style="margin-top:8px" :disabled="!queue.length || running"
                 :loading="running" @click="runAll">开始批量生成可视化</el-button>
    </div>

    <div v-for="(item, i) in queue" :key="i" class="card-box">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:13px;font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ item.name }}</span>
        <el-tag size="small" :type="statusType(item.status)">{{ item.status }}</el-tag>
      </div>
      <el-progress v-if="item.status !== '等待'" :percentage="item.pct" :status="item.status === '失败' ? 'exception' : undefined" style="margin-top:6px" />
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { Files } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const queue = ref([]), running = ref(false)

function pick(f) { queue.value.push({ file: f, name: f.name, status: '等待', pct: 0, fileId: '' }); return false }

function statusType(s) { return s === '完成' ? 'success' : s === '失败' ? 'danger' : s === '处理中' ? 'warning' : 'info' }

async function runAll() {
  running.value = true
  let okCount = 0
  try {
    for (const item of queue.value) {
      if (item.status === '完成') continue
      item.status = '处理中'; item.pct = 15
      try {
        const up = await api.uploadFile(item.file)
        item.fileId = up.file_id; item.pct = 45
        // 批量主题使用当前主题中心的选择；任务制生成 + 逐项进度
        const res = await api.generateWait(
          { file_id: up.file_id, theme: state.theme, model_id: state.modelId || null },
          (p) => { item.pct = Math.max(45, p) })
        item.pct = 100; item.status = '完成'; okCount++
        // 最后一个完成的结果载入预览
        state.previewSrc = api.previewUrl(res.id)
        state.currentRecordId = res.id
        window.__refreshRecent?.()
      } catch (e) {
        item.status = '失败'; item.pct = 100
      }
    }
    ElMessage.success(`批量处理结束：成功 ${okCount} / ${queue.value.length}`)
  } finally { running.value = false }
}
</script>
