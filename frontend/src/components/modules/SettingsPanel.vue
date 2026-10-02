<template>
  <div class="scroll-area">
    <h3 class="module-title">⚙️ 系统设置</h3>
    <div class="card-box">
      <div style="margin-bottom:12px">
        <div style="font-size:13px;font-weight:600;margin-bottom:6px">默认主题</div>
        <el-select v-model="s.theme" size="small" style="width:100%">
          <el-option label="智能选型（推荐）" value="auto" />
          <el-option v-for="t in ['tech-blue','biz-gold','fresh-green','warm-orange','minimal','dark-neon']"
                     :key="t" :label="t" :value="t" />
        </el-select>
      </div>
      <div style="margin-bottom:12px">
        <div style="font-size:13px;font-weight:600;margin-bottom:6px">生成温度：{{ s.temperature }}</div>
        <el-slider v-model="s.temperature" :min="0" :max="1.5" :step="0.05" />
      </div>
      <div style="margin-bottom:12px">
        <div style="font-size:13px;font-weight:600;margin-bottom:6px">送入模型的最大原文长度：{{ s.max_context_chars }} 字</div>
        <el-slider v-model="s.max_context_chars" :min="2000" :max="30000" :step="1000" />
      </div>
      <div style="margin-bottom:12px;display:flex;align-items:center;gap:8px">
        <el-switch v-model="s.auto_summary" />
        <span style="font-size:13px">生成时自动附带摘要与分类</span>
      </div>
      <el-button type="primary" size="small" @click="save">保存设置</el-button>
    </div>
    <div class="card-box hint">
      数据存储：本地 SQLite（backend/data/app.db）；生成的 HTML 位于 backend/generated/；
      公开分享链接依赖后端服务可达（/share/{id}）。
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted, inject } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const s = reactive({ theme: 'auto', temperature: 0.65, max_context_chars: 14000, auto_summary: true })

onMounted(async () => { Object.assign(s, await api.getSettings()) })
async function save() {
  await api.saveSettings({ ...s })
  Object.assign(state.settings, s)
  ElMessage.success('已保存')
}
</script>
