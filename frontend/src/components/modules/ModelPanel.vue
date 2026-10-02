<template>
  <div class="scroll-area">
    <h3 class="module-title">🤖 Agent 模型接入</h3>

    <div class="card-box" style="border-left:3px solid var(--primary)">
      <div style="font-weight:700;font-size:13.5px">{{ builtin.provider }}（内置默认）</div>
      <div class="hint" style="margin:6px 0">Base URL：{{ builtin.base_url }}</div>
      <div class="hint">默认模型：{{ builtin.default_model }} · 快速模型：{{ builtin.fast_model }}</div>
      <el-link type="primary" :href="'https://agnes-ai.com/zh-Hans/docs/overview'" target="_blank" style="font-size:12px">官方文档 ↗</el-link>
    </div>

    <div style="font-weight:600;font-size:13px;margin:14px 0 8px">已接入模型</div>
    <div v-for="m in models" :key="m.id" class="model-card" :class="{ default: m.is_default }">
      <div style="display:flex;align-items:center;gap:6px">
        <span style="font-weight:600;font-size:13px;flex:1">{{ m.name }}</span>
        <el-tag v-if="m.builtin" size="small">内置</el-tag>
        <el-tag v-if="m.is_default" size="small" type="success">默认</el-tag>
      </div>
      <div class="hint" style="margin:4px 0">{{ m.base_url }} · {{ m.api_key }}</div>
      <div style="display:flex;gap:6px">
        <el-button size="small" @click="use(m)">使用此模型</el-button>
        <el-button v-if="!m.is_default" size="small" plain @click="makeDefault(m)">设为默认</el-button>
        <el-button v-if="!m.builtin" size="small" type="danger" plain @click="del(m)">删除</el-button>
      </div>
    </div>

    <div class="card-box" style="margin-top:14px">
      <div style="font-weight:600;font-size:13px;margin-bottom:8px">➕ 添加自定义模型（OpenAI 兼容协议）</div>
      <el-input v-model="form.name" size="small" placeholder="模型名称，如 gpt-4o / deepseek-chat" style="margin-bottom:6px" />
      <el-input v-model="form.base_url" size="small" placeholder="Base URL，如 https://api.openai.com/v1" style="margin-bottom:6px" />
      <el-input v-model="form.api_key" size="small" placeholder="API Key" show-password style="margin-bottom:6px" />
      <div style="display:flex;gap:6px">
        <el-button size="small" :loading="probing" @click="probe">测试连通</el-button>
        <el-button size="small" type="primary" @click="add">添加</el-button>
      </div>
      <div v-if="probeResult" class="hint" style="margin-top:6px">✅ 连通成功，远端模型：{{ probeResult.join(', ') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api'

const state = inject('appState')
const models = ref([]), builtin = ref({}), probing = ref(false), probeResult = ref('')
const form = reactive({ name: '', base_url: '', api_key: '' })

async function load() {
  models.value = await api.listModels()
  builtin.value = await api.builtinInfo()
}
async function add() {
  await api.addModel({ ...form }); ElMessage.success('已添加')
  Object.assign(form, { name: '', base_url: '', api_key: '' }); load()
}
async function del(m) { await api.delModel(m.id); ElMessage.success('已删除'); load() }
async function makeDefault(m) { await api.setDefault(m.id); load() }
function use(m) { state.modelId = m.id; ElMessage.success(`已切换为使用「${m.name}」`) }
async function probe() {
  probing.value = true; probeResult.value = ''
  try {
    const res = await api.probe({ base_url: form.base_url, api_key: form.api_key })
    probeResult.value = res.remote_models
  } finally { probing.value = false }
}
onMounted(load)
</script>

<style scoped>
.model-card { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; background: #fff; }
.model-card.default { border-color: #22c55e; }
</style>
