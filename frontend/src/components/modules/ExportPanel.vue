<template>
  <div class="scroll-area">
    <h3 class="module-title">🔗 导出与分享</h3>
    <div class="hint" style="margin-bottom:10px">对当前预览中的结果进行导出下载或生成公开访问链接。</div>
    <div class="card-box">
      <el-button type="primary" size="small" :disabled="!state.currentRecordId" @click="download">⬇️ 导出 HTML 文件</el-button>
      <el-button size="small" :disabled="!state.currentRecordId" :loading="sharing" @click="doShare">🔗 生成公开链接</el-button>
    </div>
    <div v-if="shareUrl" class="card-box">
      <div style="font-weight:600;font-size:13px;margin-bottom:6px">公开访问链接</div>
      <el-link type="primary" :href="shareUrl" target="_blank" style="word-break:break-all">{{ shareUrl }}</el-link>
      <el-button size="small" style="margin-top:8px" @click="copy">复制链接</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const shareUrl = ref(''), sharing = ref(false)

function download() {
  if (!state.currentRecordId) return
  window.open(api.exportUrl(state.currentRecordId), '_blank')
}
async function doShare() {
  sharing.value = true
  try {
    const res = await api.share(state.currentRecordId)
    shareUrl.value = location.origin + res.share_url
  } finally { sharing.value = false }
}
function copy() { navigator.clipboard?.writeText(shareUrl.value); ElMessage.success('已复制') }
</script>
