<template>
  <div class="scroll-area">
    <h3 class="module-title">📚 案例查看</h3>
    <div class="hint" style="margin-bottom:10px">内置示例内容，一键载入后可直接生成可视化效果体验。</div>
    <div v-for="c in cases" :key="c.id" class="card-box">
      <div style="font-weight:600;font-size:13.5px">{{ c.name }}</div>
      <div class="hint" style="margin:4px 0 8px">{{ c.desc }}</div>
      <el-button size="small" type="primary" :loading="loadingId === c.id" @click="load(c)">载入并解析</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const cases = ref([]), loadingId = ref('')

onMounted(async () => { cases.value = await api.getCases() })

async function load(c) {
  loadingId.value = c.id
  try {
    const res = await api.parseText(c.text, c.name)
    state.fileId = res.file_id; state.docText = res.text; state.docMeta = res.meta
    ElMessage.success('案例已载入，可点击「生成可视化」体验')
  } finally { loadingId.value = '' }
}
</script>
