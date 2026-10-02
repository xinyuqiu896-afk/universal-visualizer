<template>
  <div class="scroll-area">
    <h3 class="module-title">🧠 摘要与标签分类</h3>
    <el-button type="primary" size="small" :disabled="!state.fileId" :loading="loading" @click="run">
      分析当前文档
    </el-button>
    <div v-if="!state.fileId" class="hint" style="margin-top:8px">请先上传文件或输入文本</div>

    <template v-if="result">
      <div class="card-box" style="margin-top:14px">
        <div style="font-weight:700;font-size:15px">{{ result.title }}</div>
        <div class="tag-line">
          <el-tag size="small" type="warning">{{ result.category }}</el-tag>
          <el-tag v-for="t in result.tags" :key="t" size="small" type="info">{{ t }}</el-tag>
        </div>
        <p style="font-size:13px;line-height:1.8;color:#444">{{ result.summary }}</p>
        <ol v-if="result.key_points?.length" style="margin:0 0 8px;padding-left:20px;font-size:12.5px;line-height:1.9;color:#555">
          <li v-for="(p, i) in result.key_points" :key="i">{{ p }}</li>
        </ol>
        <div class="hint">关键词：{{ result.keywords?.join(' / ') }}　|　内容形态：{{ result.content_type }}　|　建议主题：{{ result.suggested_theme }}</div>
        <el-button size="small" style="margin-top:8px" @click="applyTheme">应用建议主题</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const loading = ref(false)

// 与中间栏「简要概括」卡片共享同一份分析结果，避免重复调用大模型
const result = computed(() => state.summaryData)

async function run() {
  if (state.summaryData) {
    ElMessage.info('当前文档已分析过，直接展示缓存结果')
    return
  }
  loading.value = true
  try {
    state.summaryData = await api.summarize({ file_id: state.fileId, model_id: state.modelId || null })
  } finally { loading.value = false }
}
function applyTheme() {
  if (result.value?.suggested_theme) state.theme = result.value.suggested_theme
}
</script>
