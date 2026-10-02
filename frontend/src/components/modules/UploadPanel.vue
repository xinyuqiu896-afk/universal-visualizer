<template>
  <div class="scroll-area">
    <h3 class="module-title">📤 文件上传与在线输入</h3>

    <div class="card-box">
      <el-upload drag :show-file-list="false" :before-upload="handleUpload"
                 accept=".docx,.doc,.pptx,.pdf,.txt,.md,.csv,.xlsx,.xls,.json,.html,.png,.jpg,.jpeg,.webp,.bmp,.gif,.zip">
        <el-icon size="40" style="color:var(--primary)"><UploadFilled /></el-icon>
        <div style="margin-top:6px">拖拽文件到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="hint" style="margin-top:8px">
            支持 Word / PPT / PDF / TXT / Markdown / CSV / Excel / JSON / HTML / <b>zip 压缩包</b>，≤30MB<br>
            🖼️ 图片自动 OCR 识别：长图自动切片有序合并不漏字，低清图自动增强后识别<br>
            📦 zip 自动解析包内全部文档 · exe/镜像等程序文件无法解析，将给出友好提示
          </div>
        </template>
      </el-upload>
    </div>

    <div class="card-box">
      <div style="font-weight:600;font-size:13px;margin-bottom:8px">✍️ 在线输入文本</div>
      <el-input v-model="title" placeholder="可选：给文本起个标题" size="small" style="margin-bottom:8px" />
      <el-input v-model="text" type="textarea" :rows="6" placeholder="粘贴任意文本内容，粘贴后同样可生成可视化…" />
      <el-button type="primary" size="small" style="margin-top:10px" :loading="loading" @click="submitText">解析文本</el-button>
    </div>

    <div v-if="meta.ext" class="card-box">
      <div style="font-weight:600;font-size:13px;margin-bottom:6px">✅ 解析成功</div>
      <div class="hint">
        {{ meta.file_name }} · {{ meta.ext }} · {{ meta.char_count }} 字
        <template v-if="meta.ocr"><br>OCR 识别<span v-if="meta.long_image"> · 长图已切 {{ meta.slices }} 段合并</span><span v-if="meta.enhanced"> · 低清已增强</span></template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as api from '../../api'

const state = inject('appState')
const text = ref(''), title = ref(''), loading = ref(false)
const meta = ref({})

async function handleUpload(file) {
  loading.value = true
  try {
    const res = await api.uploadFile(file)
    applyResult(res)
  } finally { loading.value = false }
  return false // 阻止 el-upload 默认上传
}

async function submitText() {
  if (!text.value.trim()) return ElMessage.warning('请输入文本')
  loading.value = true
  try {
    const res = await api.parseText(text.value, title.value)
    applyResult(res)
  } finally { loading.value = false }
}

function applyResult(res) {
  state.fileId = res.file_id
  state.docText = res.text
  state.docMeta = res.meta
  meta.value = res.meta
  ElMessage.success('解析完成，可在中间栏查看原文')
}
</script>
