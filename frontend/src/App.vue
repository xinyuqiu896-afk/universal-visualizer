<template>
  <div class="layout">
    <!-- 左侧功能栏 -->
    <div class="pane pane-left">
      <div class="brand">
        <div class="logo">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6" rx="1"/><rect x="12" y="8" width="3" height="10" rx="1"/><rect x="17" y="4" width="3" height="14" rx="1"/>
          </svg>
        </div>
        <div>
          <div class="brand-name">万能可视化</div>
          <div class="brand-sub">UNIVERSAL VISUALIZER</div>
        </div>
      </div>
      <div class="pane-body nav-list">
        <div class="nav-group">文件与输入</div>
        <div v-for="m in modules.slice(0, 3)" :key="m.key"
             class="nav-item" :class="{ active: activeModule === m.key }"
             @click="activeModule = m.key">
          <span class="nav-icon">{{ m.icon }}</span>{{ m.label }}
        </div>
        <div class="nav-group">分析与设计</div>
        <div v-for="m in modules.slice(3, 7)" :key="m.key"
             class="nav-item" :class="{ active: activeModule === m.key }"
             @click="activeModule = m.key">
          <span class="nav-icon">{{ m.icon }}</span>{{ m.label }}
        </div>
        <div class="nav-group">管理与输出</div>
        <div v-for="m in modules.slice(7)" :key="m.key"
             class="nav-item" :class="{ active: activeModule === m.key }"
             @click="activeModule = m.key">
          <span class="nav-icon">{{ m.icon }}</span>{{ m.label }}
        </div>
      </div>
      <!-- 模型状态条：圆点 → 胶囊 → 信息卡 三态形变（效果 1 / 2 / 7） -->
      <div class="model-strip">
        <div v-if="msState === 'card'" class="ms-card">
          <div class="ms-card-head">
            <span class="dot dot-lg"></span>
            <b class="ms-card-name">{{ currentModelName }}</b>
          </div>
          <div class="ms-card-sub">连接正常 · 开箱即用默认模型</div>
          <div class="ms-card-actions">
            <el-button size="small" type="primary" round @click="openModelsModule">模型管理</el-button>
            <el-button size="small" round @click="msCollapse">收起</el-button>
          </div>
        </div>
        <button class="ms-btn" :class="{ open: msState !== 'dot' }" title="模型状态"
                @click="msState === 'pill' ? (msState = 'card') : (msState = 'pill')">
          <span class="dot"></span>
          <span class="ms-text">已接入：{{ currentModelName }}</span>
        </button>
      </div>
      <!-- 作者署名入口（左下角）：点击弹出署名卡 -->
      <div class="author-strip">
        <div v-if="authorOpen" class="author-card">
          <div class="author-pen"><span class="author-avatar">QXY</span>
            <div><b>笔名：QXY</b><span>Universal Visualizer</span></div>
          </div>
          <div class="author-row" @click="copyQQ">
            <span class="author-label">QQ</span>
            <span class="author-qq">1181426980</span>
            <span class="author-copy">{{ qqCopied ? '✓ 已复制' : '复制' }}</span>
          </div>
        </div>
        <button class="author-btn" :class="{ open: authorOpen }" @click="authorOpen = !authorOpen">
          <span class="author-pen-icon">✍</span>
          <span class="author-name">QXY</span>
        </button>
      </div>
    </div>
    <div class="pane pane-mid">
      <div class="pane-head">
        <el-icon><Grid /></el-icon>功能面板
      </div>
      <div class="pane-body">
        <!-- 效果 ⑨：模块视图切换——旧视图下移淡出，新视图自下方 12px 淡入归位 -->
        <Transition name="view" mode="out-in">
          <component :is="moduleComponents[activeModule]" :key="activeModule" />
        </Transition>
      </div>
    </div>

    <!-- 中间：原文展示（宽度响应式，供效果 6 的 container query 触发内容重排） -->
    <div class="pane pane-mid doc-pane">
      <div class="pane-head">
        <el-icon><Document /></el-icon>解析原文
        <el-tag v-if="docMeta.ext" size="small" type="info" effect="plain" round style="margin-left:auto">{{ docMeta.ext }}</el-tag>
      </div>
      <div class="pane-body">
        <template v-if="docText">
          <div class="doc-toolbar">
            <div class="doc-meta">
              <span class="doc-name">{{ docMeta.file_name }}</span>
              <span class="doc-stat">{{ docMeta.char_count }} 字<span v-if="docMeta.total"> · {{ Number(docMeta.total).toLocaleString() }} 条数据</span></span>
            </div>
            <el-button size="small" round :disabled="genLoading" @click="briefRef?.open()">简要概括</el-button>
            <el-button size="small" type="primary" round :loading="genLoading" @click="doGenerate">生成可视化</el-button>
          </div>
          <BriefSummaryCard ref="briefRef" :active-point="activePoint"
                            @locate="locatePoint" @open-full="activeModule = 'summary'" />
          <!-- eslint-disable-next-line vue/no-v-html -->
          <pre class="doc-text" ref="docTextRef" v-html="docHtml"></pre>
        </template>
        <div v-else class="empty-state">
          <div class="empty-icon">📄</div>
          <div class="empty-title">尚未解析文件</div>
          <div class="empty-hint">从左侧「文件上传 / 在线输入」开始<br>支持 Word · PPT · PDF · Excel · 图片 OCR</div>
        </div>
      </div>
    </div>

    <!-- 右侧：可视化预览（最大区域） -->
    <div class="pane pane-right">
      <div class="pane-head">
        <el-icon><MagicStick /></el-icon>可视化结果
        <div class="toolbar" :class="{ compact: tbCompact }">
          <el-select v-model="currentRecordId" size="small" style="width:170px" placeholder="历史结果"
                     @change="loadRecord(currentRecordId)">
            <el-option v-for="r in recentRecords" :key="r.id" :value="r.id" :label="r.title" />
          </el-select>
          <el-button-group size="small">
            <el-button @click="zoom(0.9)">−</el-button>
            <el-button style="width:58px;font-variant-numeric:tabular-nums" @click="zoom(0)">{{ Math.round(scale * 100) }}%</el-button>
            <el-button @click="zoom(1.1)">+</el-button>
          </el-button-group>
          <!-- 效果 3：紧凑态 ↔ 完整控制面板 -->
          <div class="tb-extra">
            <el-button size="small" @click="reloadFrame">刷新</el-button>
            <el-button size="small" @click="openLocal">本地预览</el-button>
            <el-button size="small" @click="exportPdf" :disabled="!previewSrc">导出 PDF</el-button>
            <el-button size="small" @click="openBlank">新窗口</el-button>
            <el-button size="small" type="primary" :loading="shareLoading" @click="makeShare">公开链接</el-button>
          </div>
          <el-button size="small" round class="tb-toggle" @click="tbCompact = !tbCompact">
            {{ tbCompact ? '更多 ▾' : '收起 ▴' }}
          </el-button>
        </div>
      </div>
      <div class="preview-wrap">
        <iframe v-if="previewSrc" ref="frameRef" :src="previewSrc + '?t=' + frameKey" class="preview-frame"
                :style="{ width: (100 / scale) + '%', height: (100 / scale) + '%', transform: `scale(${scale})` }"></iframe>

        <!-- 生成进度遮罩 -->
        <div v-if="genLoading" class="gen-overlay">
          <div class="gen-card">
            <div class="gen-ring" :style="{ background: `conic-gradient(var(--primary) ${genProgress * 3.6}deg, #e8ecf5 0deg)` }">
              <div class="gen-ring-inner">
                <span class="gen-pct">{{ genProgress }}<small>%</small></span>
              </div>
            </div>
            <div class="gen-stage">{{ genMessage }}</div>
            <div class="gen-time">
              已用时 <b>{{ genElapsedText }}</b>
              <template v-if="genProgress > 3 && genProgress < 99 && genElapsed > 15"> · 预计还需 {{ genEtaText }}</template>
            </div>
            <div class="gen-bar"><div class="gen-bar-fill" :style="{ width: genProgress + '%' }"></div></div>
            <div class="gen-tips">AI 正在逐段设计版式、配色与图表，完成后自动展示 · 请勿关闭页面</div>
          </div>
        </div>

        <div v-else-if="!previewSrc" class="empty-state" style="height:100%">
          <div class="empty-icon">✨</div>
          <div class="empty-title">生成的可视化 HTML 将展示在这里</div>
          <div class="empty-hint">智能选型主题 · 缩放 · 本地预览 · 导出 PDF · 公开分享</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, provide, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, Document, MagicStick } from '@element-plus/icons-vue'
import * as api from './api'

import UploadPanel from './components/modules/UploadPanel.vue'
import ConvertPanel from './components/modules/ConvertPanel.vue'
import CasesPanel from './components/modules/CasesPanel.vue'
import HistoryPanel from './components/modules/HistoryPanel.vue'
import BatchPanel from './components/modules/BatchPanel.vue'
import TemplatePanel from './components/modules/TemplatePanel.vue'
import SummaryPanel from './components/modules/SummaryPanel.vue'
import InsightPanel from './components/modules/InsightPanel.vue'
import ExportPanel from './components/modules/ExportPanel.vue'
import FavPanel from './components/modules/FavPanel.vue'
import TrashPanel from './components/modules/TrashPanel.vue'
import ModelPanel from './components/modules/ModelPanel.vue'
import SettingsPanel from './components/modules/SettingsPanel.vue'
import SolvePanel from './components/modules/SolvePanel.vue'
import BriefSummaryCard from './components/BriefSummaryCard.vue'

const modules = [
  { key: 'upload',   icon: '📤', label: '文件上传与在线输入' },
  { key: 'batch',    icon: '⚡', label: '批量处理' },
  { key: 'convert',  icon: '🔄', label: '格式转换' },
  { key: 'template', icon: '🎨', label: '模板与主题中心' },
  { key: 'summary',  icon: '🧠', label: '摘要与标签分类' },
  { key: 'insight',  icon: '📊', label: '图表洞察' },
  { key: 'solve',    icon: '📝', label: '题目解答' },
  { key: 'history',  icon: '🕘', label: '历史记录' },
  { key: 'fav',      icon: '⭐', label: '收藏' },
  { key: 'trash',    icon: '🗑️', label: '回收站' },
  { key: 'export',   icon: '🔗', label: '导出与分享' },
  { key: 'model',    icon: '🤖', label: 'Agent 模型接入' },
  { key: 'cases',    icon: '📚', label: '案例查看' },
  { key: 'settings', icon: '⚙️', label: '系统设置' },
]
const moduleComponents = {
  upload: UploadPanel, batch: BatchPanel, convert: ConvertPanel, template: TemplatePanel,
  summary: SummaryPanel, insight: InsightPanel, solve: SolvePanel, history: HistoryPanel, fav: FavPanel,
  trash: TrashPanel, export: ExportPanel, model: ModelPanel, cases: CasesPanel, settings: SettingsPanel,
}

const activeModule = ref('upload')
// ---- 全局共享状态 ----
const state = reactive({
  fileId: '', docText: '', docMeta: {},
  theme: 'auto', modelId: '', extraReq: '',
  previewSrc: '', currentRecordId: '',
  recentRecords: [], settings: {},
  summaryData: null,   // 「简要概括」与「摘要与标签分类」共享的分析结果
  solveData: null,     // 「题目解答」结果缓存
})
provide('appState', state)

const currentModelName = computed(() => state.modelId || 'Agnes 大模型（默认）')

// ---- 模型状态三态形变（效果 1/2/7）：dot → pill → card，反向沿原路径收回 ----
const msState = ref('dot')
function msCollapse() {
  if (msState.value === 'card') {
    msState.value = 'pill'                       // 先收回信息卡
    setTimeout(() => { msState.value = 'dot' }, 280)  // 再收回胶囊，绿点保留为完成标记
  } else {
    msState.value = 'dot'
  }
}
function openModelsModule() {
  msState.value = 'dot'
  activeModule.value = 'model'
}

// ---- 可视化工具栏紧凑态切换（效果 3） ----
const tbCompact = ref(true)

// ---- 作者署名 ----
const authorOpen = ref(false)
const qqCopied = ref(false)
function copyQQ() {
  navigator.clipboard?.writeText('1181426980').catch(() => {})
  qqCopied.value = true
  setTimeout(() => { qqCopied.value = false }, 2000)
}
// 模板作用域代理（state 内字段需显式暴露给 template）
const docText = computed(() => state.docText)
const docMeta = computed(() => state.docMeta)
const previewSrc = computed(() => state.previewSrc)
const currentRecordId = computed({
  get: () => state.currentRecordId,
  set: v => { state.currentRecordId = v },
})
const recentRecords = computed(() => state.recentRecords)
const scale = ref(1)
const frameKey = ref(Date.now())
const genLoading = ref(false)
const shareLoading = ref(false)
const frameRef = ref(null)
const briefRef = ref(null)
const docTextRef = ref(null)

// ---- 简要概括 · 原文关键句定位高亮 ----
const activePoint = ref(-1)
const activeMark = ref('')

function escapeHtml(s) {
  return s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
}
const docHtml = computed(() => {
  const t = state.docText
  if (!activeMark.value) return escapeHtml(t)
  const idx = t.indexOf(activeMark.value)
  if (idx < 0) return escapeHtml(t)
  return escapeHtml(t.slice(0, idx)) + '<mark class="kp-mark">' + escapeHtml(activeMark.value) +
         '</mark>' + escapeHtml(t.slice(idx + activeMark.value.length))
})

async function locatePoint(point, index) {
  activePoint.value = index
  const t = state.docText
  let found = ''
  // 依次尝试：整句 → 前 20 字 → 前 12 字（容忍空白差异）
  for (const cand of [point.trim(), point.trim().slice(0, 20), point.trim().slice(0, 12)]) {
    if (!cand) continue
    if (t.includes(cand)) { found = cand; break }
    const re = new RegExp(cand.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').split('').join('\\s*'))
    const m = t.match(re)
    if (m) { found = m[0]; break }
  }
  activeMark.value = found
  if (!found) return
  await nextTick()
  docTextRef.value?.querySelector('.kp-mark')?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

// ---- 生成进度状态 ----
const genProgress = ref(0)
const genMessage = ref('')
const genElapsed = ref(0)

const genElapsedText = computed(() => {
  const s = Math.round(genElapsed.value)
  return s >= 60 ? `${Math.floor(s / 60)} 分 ${s % 60} 秒` : `${s} 秒`
})
const genEtaText = computed(() => {
  // 按当前进度线性外推剩余时间
  if (genProgress.value <= 3) return '计算中…'
  const remain = Math.max(0, (100 - genProgress.value) / genProgress.value * genElapsed.value)
  const s = Math.round(remain)
  return s >= 60 ? `${Math.floor(s / 60)} 分 ${s % 60} 秒` : `${s} 秒`
})

function zoom(dir) {
  scale.value = dir === 0 ? 1 : Math.min(2, Math.max(0.4, +(scale.value * (dir > 0 ? dir : dir)).toFixed(2)))
}
function reloadFrame() { frameKey.value = Date.now() }
function openLocal() {
  // 本地预览：直接以独立标签页打开预览地址
  if (!state.previewSrc) return ElMessage.warning('暂无可预览结果')
  window.open(state.previewSrc, '_blank')
}
function openBlank() { openLocal() }

// 导出 PDF：对 iframe 同源文档直接调起打印（版式与页面显示一致）
function exportPdf() {
  const win = frameRef.value?.contentWindow
  if (!win) return ElMessage.warning('请先生成或选择一个可视化结果')
  try {
    win.focus()
    win.__uvExportPdf ? win.__uvExportPdf() : win.print()
    ElMessage.info('已调起打印，在弹窗中选择「另存为 PDF」')
  } catch {
    window.open(state.previewSrc, '_blank')
    ElMessage.info('已在新窗口打开，点击页面右下角「导出 PDF」按钮')
  }
}

async function doGenerate() {
  if (!state.fileId) return ElMessage.warning('请先上传文件或输入文本')
  genLoading.value = true
  genProgress.value = 2
  genMessage.value = '任务创建中…'
  genElapsed.value = 0
  try {
    const res = await api.generateWait(
      { file_id: state.fileId, theme: state.theme, model_id: state.modelId || null, extra_req: state.extraReq },
      (p, msg, elapsed) => {
        genProgress.value = Math.max(genProgress.value, p)
        genMessage.value = msg || genMessage.value
        genElapsed.value = elapsed || genElapsed.value
      })
    genProgress.value = 100
    state.previewSrc = api.previewUrl(res.id)
    state.currentRecordId = res.id
    frameKey.value = Date.now()
    // 零成本回填：生成时已并行产出摘要，若概括卡片还是空的直接补上
    if (!state.summaryData && (res.summary || res.suggested_theme)) {
      state.summaryData = {
        summary: res.summary || '', key_points: [], keywords: [],
        category: res.category || '', tags: res.tags || [],
        suggested_theme: res.suggested_theme || '',
      }
    }
    ElMessage.success('生成完成：' + (res.suggested_theme ? `智能选型「${res.suggested_theme}」` : 'OK'))
    refreshRecent()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '生成失败')
  } finally { genLoading.value = false }
}

async function makeShare() {
  if (!state.currentRecordId) return ElMessage.warning('请先生成或选择一个结果')
  shareLoading.value = true
  try {
    const res = await api.share(state.currentRecordId)
    const full = location.origin + res.share_url
    await ElMessageBox.alert(
      `<a href="${full}" target="_blank" style="word-break:break-all">${full}</a>`,
      '公开访问链接（已复制入口）', { dangerouslyUseHTMLString: true })
    navigator.clipboard?.writeText(full).catch(() => {})
  } finally { shareLoading.value = false }
}

async function loadRecord(id) {
  state.previewSrc = api.previewUrl(id)
  state.currentRecordId = id
  frameKey.value = Date.now()
}

async function refreshRecent() {
  try {
    state.recentRecords = (await api.history()).slice(0, 30)
  } catch { /* ignore */ }
}

onMounted(async () => {
  refreshRecent()
  try { state.settings = await api.getSettings() } catch { /* ignore */ }
})
onMounted(() => { window.__refreshRecent = refreshRecent })
</script>

<style scoped>
.brand { display: flex; gap: 11px; align-items: center; padding: 18px 16px; border-bottom: 1px solid var(--border); }
.logo {
  width: 38px; height: 38px; border-radius: 11px; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #4f6ef7, #8b5cf6); color: #fff;
  box-shadow: 0 4px 14px rgba(79, 110, 247, .35);
}
.brand-name {
  font-weight: 700; font-size: 15px; letter-spacing: .5px;
  background: linear-gradient(120deg, #1f2733 30%, #4f6ef7 75%, #8b5cf6);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.brand-sub { font-size: 9px; color: var(--text-sub); letter-spacing: 1.6px; font-weight: 500; }

.nav-list { padding: 10px 10px; }
.nav-group {
  font-size: 10.5px; font-weight: 600; color: #9aa4b5; letter-spacing: 1.5px;
  padding: 12px 10px 6px; user-select: none;
}
.nav-item {
  position: relative;
  display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 9px;
  font-size: 13px; cursor: pointer; color: #3c4557; margin-bottom: 2px;
  transition: background .18s, color .18s, transform .18s;
}
.nav-item:hover { background: #f0f3fa; transform: translateX(2px); }
.nav-item.active { background: var(--primary-soft); color: var(--primary); font-weight: 600; }
/* 激活项左侧渐变指示条 */
.nav-item.active::before {
  content: ''; position: absolute; left: -10px; top: 20%; bottom: 20%; width: 3px;
  border-radius: 99px; background: linear-gradient(180deg, #4f6ef7, #8b5cf6);
}
.nav-icon { width: 20px; text-align: center; font-size: 14px; }
.model-strip {
  position: relative; padding: 11px 16px; border-top: 1px solid var(--border); font-size: 12px;
  display: flex; align-items: center; gap: 7px; z-index: 5;
}
/* 效果 1：圆点水平展开为可读胶囊 */
.ms-btn {
  display: flex; align-items: center; border: 0; background: transparent; cursor: pointer;
  padding: 5px 8px; margin: -5px -8px; border-radius: 999px; max-width: calc(100% - 0px);
  transition: background .3s, box-shadow .3s; font-family: inherit;
}
.ms-btn:hover { background: #f0f3fa; }
.ms-btn.open { background: var(--primary-soft); box-shadow: inset 0 0 0 1px #dfe5ff; }
.ms-btn .ms-text {
  display: block; overflow: hidden; white-space: nowrap; text-overflow: clip; text-align: left;
  max-width: 0; opacity: 0; color: var(--text-sub);
  transition: max-width .38s cubic-bezier(.32,.72,0,1), opacity .28s, margin-left .38s;
}
.ms-btn.open .ms-text { max-width: 170px; opacity: 1; margin-left: 7px; color: var(--primary); font-weight: 600; }
/* 效果 2：胶囊向上托出信息卡 */
.ms-card {
  position: absolute; bottom: calc(100% + 10px); left: 12px; right: 12px; z-index: 20;
  background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
  box-shadow: var(--shadow-lg); padding: 14px 15px 12px;
  transform-origin: bottom left; animation: msCardIn .38s cubic-bezier(.32,.72,0,1);
}
@keyframes msCardIn { from { opacity: 0; transform: translateY(10px) scale(.92); } }
.ms-card-head { display: flex; align-items: center; gap: 9px; }
.ms-card-name { font-size: 13px; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dot-lg { width: 9px; height: 9px; }
.ms-card-sub { font-size: 11px; color: var(--text-sub); margin: 8px 0 10px 18px; }
.ms-card-actions { display: flex; gap: 6px; justify-content: flex-end; }
.ms-card-actions .el-button { margin-left: 0; }

/* ---- 作者署名（左下角空白区） ---- */
.author-strip { position: relative; padding: 10px 16px 13px; margin-top: auto; }
.author-btn {
  display: flex; align-items: center; gap: 7px; border: 0; background: transparent; cursor: pointer;
  padding: 6px 10px; margin: -6px -10px; border-radius: 999px; font-family: inherit;
  transition: background .25s var(--ease-mat, cubic-bezier(.4,0,.2,1));
}
.author-btn:hover { background: #f0f3fa; }
.author-pen-icon { font-size: 13px; opacity: .75; }
.author-name { font-size: 12px; font-weight: 600; color: var(--text-sub); letter-spacing: .5px; }
.author-btn.open .author-name { color: var(--primary); }
.author-card {
  position: absolute; bottom: calc(100% + 2px); left: 12px; right: 12px; z-index: 30;
  background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
  box-shadow: var(--shadow-lg); padding: 14px 15px;
  transform-origin: bottom left; animation: authorIn .4s cubic-bezier(.32,.72,0,1);
}
@keyframes authorIn { from { opacity: 0; transform: translateY(10px) scale(.92); } }
.author-pen { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.author-avatar {
  width: 36px; height: 36px; border-radius: 12px; flex-shrink: 0;
  background: linear-gradient(135deg, #4f6ef7, #8b5cf6); color: #fff;
  font-size: 11px; font-weight: 700; letter-spacing: .5px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(79,110,247,.32);
}
.author-pen b { display: block; font-size: 13px; color: var(--text); }
.author-pen span { font-size: 10px; color: var(--text-sub); letter-spacing: .6px; }
.author-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 10px;
  background: #f6f8fc; cursor: pointer; transition: background .2s;
}
.author-row:hover { background: var(--primary-soft); }
.author-label { font-size: 10.5px; font-weight: 700; color: var(--text-sub); }
.author-qq { flex: 1; font-size: 13px; font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
.author-copy { font-size: 10.5px; color: var(--primary); font-weight: 600; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,.18); animation: pulse 2.2s infinite; flex-shrink: 0; }
@keyframes pulse { 50% { box-shadow: 0 0 0 5px rgba(34,197,94,.06); } }

.doc-toolbar {
  padding: 10px 14px; border-bottom: 1px solid var(--border);
  display: flex; gap: 10px; align-items: center; position: sticky; top: 0; background: var(--panel); z-index: 2;
  flex-wrap: wrap; row-gap: 6px;
}
/* 效果 6：容器宽度变化时，文件信息与操作按钮在 上下↔左右 之间平滑重排 */
.doc-pane { width: clamp(300px, 26vw, 420px); container-type: inline-size; }
@container (max-width: 352px) {
  .doc-toolbar .doc-meta { flex-basis: 100%; }
}
.doc-toolbar .doc-meta { transition: flex-basis .35s; }
.doc-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.doc-name { font-size: 12.5px; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-stat { font-size: 11px; color: var(--text-sub); font-variant-numeric: tabular-nums; }
.doc-text {
  margin: 0; padding: 14px 16px; white-space: pre-wrap; word-break: break-word;
  font-family: inherit; font-size: 12.5px; line-height: 1.85; color: #39414e;
}
/* 关键句原文定位高亮 */
.doc-text :deep(.kp-mark) {
  background: #ffe89a; color: inherit; border-radius: 3px; padding: 1px 0;
  box-shadow: 0 0 0 2px #ffe89a; transition: background 1.2s;
}
.preview-wrap { flex: 1; overflow: hidden; position: relative; }
.preview-frame {
  border: 0; background: #fff; transform-origin: top left;
  box-shadow: 0 4px 24px rgba(0,0,0,.10); border-radius: 6px 0 0 0; position: absolute; left: 0; top: 0;
}
.toolbar { margin-left: auto; display: flex; gap: 8px; align-items: center; justify-content: flex-end; }
/* 效果 3：完整控制面板从「更多」按钮位置平滑展开/收起 */
.tb-extra {
  display: flex; align-items: center; gap: 8px; overflow: hidden;
  max-width: 0; opacity: 0; transform: translateX(10px);
  transition: max-width .42s cubic-bezier(.32,.72,0,1), opacity .3s, transform .42s cubic-bezier(.32,.72,0,1);
}
.toolbar:not(.compact) .tb-extra { max-width: 560px; opacity: 1; transform: none; }
.tb-extra .el-button + .el-button { margin-left: 0; }   /* 间距交给 gap，收起时不留残影 */
.tb-toggle { flex-shrink: 0; }

/* ---- 生成进度遮罩 ---- */
.gen-overlay {
  position: absolute; inset: 0; z-index: 10;
  background: rgba(244, 246, 250, .82); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
}
.gen-card {
  width: 400px; padding: 36px 40px 30px; border-radius: 18px; background: var(--panel);
  box-shadow: var(--shadow-lg); border: 1px solid var(--border); text-align: center;
  animation: cardIn .45s cubic-bezier(.32,.72,0,1);
}
@keyframes cardIn { from { opacity: 0; transform: translateY(18px) scale(.97); } }
.gen-ring {
  width: 116px; height: 116px; border-radius: 50%; margin: 0 auto 20px;
  display: flex; align-items: center; justify-content: center;
  transition: background .8s ease;
}
.gen-ring-inner {
  width: 92px; height: 92px; border-radius: 50%; background: var(--panel);
  display: flex; align-items: center; justify-content: center;
  box-shadow: inset 0 1px 4px rgba(20,30,60,.06);
}
.gen-pct { font-size: 26px; font-weight: 700; color: var(--primary); font-variant-numeric: tabular-nums; }
.gen-pct small { font-size: 13px; font-weight: 600; margin-left: 1px; }
.gen-stage { font-size: 13.5px; font-weight: 600; color: var(--text); margin-bottom: 8px; line-height: 1.6; }
.gen-time { font-size: 12px; color: var(--text-sub); margin-bottom: 14px; font-variant-numeric: tabular-nums; }
.gen-time b { color: var(--primary); font-weight: 600; }
.gen-bar { height: 6px; border-radius: 99px; background: #edf0f7; overflow: hidden; }
.gen-bar-fill {
  height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, #4f6ef7, #8b5cf6);
  transition: width .8s cubic-bezier(.32,.72,0,1);
}
.gen-tips { margin-top: 14px; font-size: 11.5px; color: #9aa4b5; line-height: 1.7; }

.empty-state { height: 100%; }
.empty-icon { font-size: 42px; opacity: .45; filter: saturate(.8); }
.empty-title { font-size: 14px; font-weight: 600; color: #5b6472; letter-spacing: .3px; }
.empty-hint { font-size: 12px; color: var(--text-sub); line-height: 1.9; }
</style>
