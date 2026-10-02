<template>
  <div class="scroll-area">
    <h3 class="module-title">🔄 格式转换</h3>
    <div class="card-box">
      <el-upload drag :show-file-list="false" :before-upload="pick" accept=".docx,.doc,.pptx,.pdf,.txt,.md,.csv,.xlsx,.xls">
        <el-icon size="32" style="color:var(--primary)"><UploadFilled /></el-icon>
        <div style="margin-top:4px">选择要转换的文件</div>
      </el-upload>
      <div v-if="file" class="hint" style="margin:8px 0">已选择：{{ file.name }}</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
        <el-button v-for="t in targets" :key="t" size="small" :disabled="!file || loading"
                   :loading="loading" @click="convert(t)">转为 {{ t }}</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const file = ref(null), loading = ref(false)
const targets = ['.txt', '.docx', '.pdf', '.xlsx', '.csv']

function pick(f) { file.value = f; return false }
async function convert(target) {
  loading.value = true
  try {
    const blob = await api.convertFile(file.value, target)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = file.value.name.replace(/\.[^.]+$/, '') + '_converted' + target
    a.click(); URL.revokeObjectURL(url)
    ElMessage.success('转换完成，已开始下载')
  } finally { loading.value = false }
}
</script>
