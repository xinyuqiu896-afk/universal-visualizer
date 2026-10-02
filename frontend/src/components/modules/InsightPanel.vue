<template>
  <div class="scroll-area">
    <h3 class="module-title">📊 图表洞察</h3>
    <el-button type="primary" size="small" :disabled="!state.fileId" :loading="loading" @click="run">
      从当前文档提取图表
    </el-button>
    <div v-if="!state.fileId" class="hint" style="margin-top:8px">请先上传文件或输入文本</div>

    <template v-for="(c, i) in charts" :key="i">
      <div class="card-box" style="margin-top:12px">
        <div style="font-weight:600;font-size:13.5px">{{ c.title }}</div>
        <div :ref="el => setChartRef(el, i)" style="height:260px;margin-top:6px"></div>
        <div class="hint">{{ c.note }}</div>
      </div>
    </template>

    <div v-if="insights.length" class="card-box" style="margin-top:12px">
      <div style="font-weight:600;font-size:13px;margin-bottom:6px">💡 洞察结论</div>
      <div v-for="(s, i) in insights" :key="i" style="font-size:13px;line-height:1.8">· {{ s }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, nextTick } from 'vue'
import * as echarts from 'echarts'
import * as api from '../../api'

const state = inject('appState')
const loading = ref(false)
const charts = ref([])
const insights = ref([])
const chartEls = {}

function setChartRef(el, i) { if (el) chartEls[i] = el }

async function run() {
  loading.value = true
  charts.value = []; insights.value = []
  try {
    const res = await api.insight({ file_id: state.fileId, model_id: state.modelId || null })
    charts.value = res.charts || []
    insights.value = res.insights || []
    await nextTick()
    charts.value.forEach((c, i) => {
      if (chartEls[i]) echarts.init(chartEls[i]).setOption(c.option)
    })
  } finally { loading.value = false }
}
</script>
