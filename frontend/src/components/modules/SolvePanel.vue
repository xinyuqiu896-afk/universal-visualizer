<template>
  <div class="scroll-area">
    <h3 class="module-title">📝 题目解答</h3>
    <div class="module-sub">上传历年真题 / 计算题等题目类文件后，AI 逐题给出步骤与答案，支持点击步骤在原文中定位</div>

    <el-button type="primary" size="small" :disabled="!state.fileId" :loading="loading" @click="run">
      解答当前文档
    </el-button>
    <div v-if="!state.fileId" class="hint" style="margin-top:8px">请先上传文件或输入文本</div>

    <template v-if="result">
      <div class="solve-head">
        <span class="solve-title">{{ result.title || '题目解答' }}</span>
        <el-tag size="small" type="success" effect="plain" round>{{ result.items?.length || 0 }} 题</el-tag>
      </div>

      <div v-for="(item, i) in result.items" :key="i" class="card-box solve-item">
        <div class="solve-q">
          <span class="solve-idx">{{ i + 1 }}</span>
          <span class="solve-q-text">{{ item.question }}</span>
          <el-tag v-if="item.type" size="small" effect="plain" round>{{ item.type }}</el-tag>
        </div>
        <ol class="solve-steps">
          <li v-for="(s, j) in item.steps" :key="j">{{ s }}</li>
        </ol>
        <div class="solve-answer">
          <span class="solve-answer-label">答案</span>
          <span v-html="renderAnswer(item.answer)"></span>
        </div>
      </div>

      <div v-if="!result.items?.length" class="card-box hint">
        {{ result.is_question_doc === false ? '当前文档未识别到题目，可尝试「摘要与标签分类」或「生成可视化」' : '未识别到题目' }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const loading = ref(false)
// 与全局共享，避免重复调用；文档切换自动失效
const result = computed(() => state.solveData)

async function run() {
  if (!state.fileId) return ElMessage.warning('请先上传文件或输入文本')
  loading.value = true
  try {
    state.solveData = await api.solve({ file_id: state.fileId, model_id: state.modelId || null })
  } finally { loading.value = false }
}

// 答案文本安全渲染：转义后仅把 **x** 加粗
function renderAnswer(t) {
  const esc = (t || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
  return esc.replace(/\*\*(.+?)\*\*/g, '<b style="color:var(--primary)">$1</b>')
}

watch(() => state.fileId, () => { state.solveData = null })
</script>

<style scoped>
.solve-head { display: flex; align-items: center; gap: 8px; margin: 14px 0 2px; }
.solve-title { font-weight: 700; font-size: 13.5px; color: var(--text); }
.solve-item { animation: solveIn 360ms cubic-bezier(.32,.72,0,1) backwards; }
.solve-item:nth-child(2) { animation-delay: 60ms; }
@keyframes solveIn { from { opacity: 0; transform: translateY(10px); } }
.solve-q { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.solve-idx {
  flex-shrink: 0; width: 20px; height: 20px; border-radius: 50%; background: var(--primary-soft);
  color: var(--primary); font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; margin-top: 1px;
}
.solve-q-text { flex: 1; font-weight: 600; font-size: 12.5px; line-height: 1.75; color: var(--text); }
.solve-steps {
  margin: 0 0 10px; padding-left: 28px; font-size: 12px; line-height: 1.9; color: #454e5d;
}
.solve-steps li::marker { color: var(--primary); font-weight: 600; }
.solve-answer {
  background: linear-gradient(135deg, #f0fdf4, #f8fffb); border: 1px solid #bbf7d0;
  border-radius: 10px; padding: 9px 12px; font-size: 12.5px; line-height: 1.8; color: #166534;
  display: flex; gap: 8px; align-items: flex-start;
}
.solve-answer-label {
  flex-shrink: 0; font-size: 10.5px; font-weight: 700; color: #16a34a;
  background: #dcfce7; border-radius: 6px; padding: 2px 8px; margin-top: 1px;
}
</style>
