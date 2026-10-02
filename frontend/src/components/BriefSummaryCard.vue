<template>
  <div class="brief-card" :class="{ expanded }">
    <!-- 折叠头：始终可见 -->
    <div class="brief-head" @click="themePop ? (themePop = false) : (expanded = !expanded)">
      <span class="brief-badge">✦</span>
      <span class="brief-title">简要概括</span>
      <template v-if="data">
        <span class="brief-peek">{{ firstSentence }}</span>
        <!-- 效果 7：反向收回后保留完成标记 -->
        <span v-if="!expanded" class="brief-done" title="概括已生成">✓</span>
        <el-tag v-if="data.suggested_theme" size="small" effect="plain" round
                class="brief-theme-tag" :class="{ active: themePop }"
                @click.stop="themePop = !themePop">
          {{ themeLabel(data.suggested_theme) }}
        </el-tag>
      </template>
      <span v-else class="brief-peek brief-peek-empty">一键提取原文核心摘要与关键句</span>
      <el-icon class="brief-chevron" :class="{ open: expanded }"><ArrowDown /></el-icon>
    </div>

    <!-- 效果 5：主题 tag 从原位向右下扩展为应用卡 -->
    <div v-if="themePop && data?.suggested_theme" class="theme-pop" @click.stop>
      <span class="tp-swatch" :style="{ background: themeColor }"></span>
      <div class="tp-info">
        <b>{{ themeLabel(data.suggested_theme) }}</b>
        <span>AI 推荐主题</span>
      </div>
      <el-button size="small" type="primary" round @click="applyTheme(); themePop = false">应用</el-button>
      <el-button size="small" text @click="themePop = false">✕</el-button>
    </div>

    <!-- 展开体 -->
    <el-collapse-transition>
      <div v-show="expanded" class="brief-body">
        <!-- 未生成 -->
        <div v-if="!data && !loading && !error" class="brief-empty">
          <div class="brief-empty-text">调用大模型提炼本文档的一句话摘要、3~5 条关键句与关键词</div>
          <el-button size="small" type="primary" round :disabled="!state.fileId" @click="run">生成概括</el-button>
          <div v-if="!state.fileId" class="brief-hint">请先上传文件或输入文本</div>
        </div>

        <!-- 加载骨架 -->
        <div v-else-if="loading" class="brief-skeleton">
          <div class="sk-line w80"></div>
          <div class="sk-line w60"></div>
          <div class="sk-line w70"></div>
          <div class="sk-line w50"></div>
          <div class="sk-tip">AI 正在阅读全文并提炼关键信息…</div>
        </div>

        <!-- 失败重试 -->
        <div v-else-if="error" class="brief-error">
          <span class="brief-error-text">⚠️ {{ error }}</span>
          <el-button size="small" type="primary" round @click="run">重试</el-button>
        </div>

        <!-- 已生成 -->
        <template v-else-if="data">
          <p class="brief-summary">{{ data.summary }}</p>
          <ol v-if="keyPoints.length" class="brief-points">
            <li v-for="(p, i) in keyPoints" :key="i"
                :class="{ located: activePoint === i }"
                title="点击在原文中定位"
                @click="$emit('locate', p, i)">{{ p }}</li>
          </ol>
          <div class="brief-keywords">
            <el-tag v-for="k in (data.keywords || []).slice(0, 6)" :key="k" size="small" effect="plain" round>{{ k }}</el-tag>
          </div>
          <div class="brief-actions">
            <el-button v-if="data.suggested_theme" size="small" text type="primary" @click="applyTheme">
              应用建议主题「{{ themeLabel(data.suggested_theme) }}」
            </el-button>
            <el-button size="small" text @click="$emit('open-full')">查看完整分析 →</el-button>
          </div>
        </template>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import * as api from '../api'

const props = defineProps({ activePoint: { type: Number, default: -1 } })
const emit = defineEmits(['locate', 'open-full'])

const state = inject('appState')
const loading = ref(false)
const expanded = ref(false)
const error = ref('')
const themePop = ref(false)

const THEME_COLORS = {
  'tech-blue': 'linear-gradient(135deg, #4f6ef7, #6d8bff)',
  'biz-gold': 'linear-gradient(135deg, #b8892d, #e8c169)',
  'fresh-green': 'linear-gradient(135deg, #16a34a, #4ade80)',
  'warm-orange': 'linear-gradient(135deg, #ea580c, #fb923c)',
  'minimal': 'linear-gradient(135deg, #64748b, #94a3b8)',
  'dark-neon': 'linear-gradient(135deg, #7c3aed, #c084fc)',
}

const data = computed(() => state.summaryData)
const keyPoints = computed(() => data.value?.key_points || [])
const firstSentence = computed(() => {
  const s = (data.value?.summary || '').replace(/\s+/g, '')
  return s.length > 46 ? s.slice(0, 46) + '…' : s
})

const THEME_LABELS = {
  'tech-blue': '科技蓝', 'biz-gold': '商务黑金', 'fresh-green': '清新绿',
  'warm-orange': '暖橙', 'minimal': '极简', 'dark-neon': '暗黑霓虹', 'auto': '智能选型',
}
const themeLabel = (t) => THEME_LABELS[t] || t
const themeColor = computed(() => THEME_COLORS[data.value?.suggested_theme] || 'var(--primary)')

// 文档切换后旧概括失效
watch(() => state.fileId, () => { state.summaryData = null; error.value = ''; themePop.value = false; expanded.value = false })

async function run() {
  if (!state.fileId) return ElMessage.warning('请先上传文件或输入文本')
  loading.value = true
  error.value = ''
  expanded.value = true
  try {
    state.summaryData = await api.summarize({ file_id: state.fileId, model_id: state.modelId || null })
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || '概括生成失败，请重试'
  } finally {
    loading.value = false
  }
}

function applyTheme() {
  if (data.value?.suggested_theme) {
    state.theme = data.value.suggested_theme
    ElMessage.success(`已切换主题：${themeLabel(data.value.suggested_theme)}`)
  }
}

// 供工具栏「简要概括」按钮调用：展开卡片，无结果时自动生成
function open() {
  expanded.value = true
  if (!data.value && !loading.value) run()
}
defineExpose({ open })
</script>

<style scoped>
.brief-card {
  position: relative;
  margin: 10px 14px 0; border: 1px solid var(--border);
  background: linear-gradient(180deg, #f8faff, #ffffff); overflow: visible;
  /* 效果 4：圆角形态过渡——折叠全圆胶囊 ↔ 展开卡片圆角，尺寸渐变中圆角平滑形变 */
  border-radius: 999px; transition: border-radius .42s cubic-bezier(.32,.72,0,1), box-shadow .25s;
}
.brief-card.expanded { border-radius: 14px; box-shadow: var(--shadow); }
.brief-head {
  display: flex; align-items: center; gap: 8px; padding: 9px 12px; cursor: pointer;
  user-select: none; min-width: 0;
}
.brief-head:hover { background: #f5f8ff; }
.brief-badge { color: var(--primary); font-size: 13px; flex-shrink: 0; }
.brief-title { font-size: 12.5px; font-weight: 700; color: var(--text); flex-shrink: 0; letter-spacing: .3px; }
.brief-peek {
  flex: 1; min-width: 0; font-size: 11.5px; color: var(--text-sub);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.brief-peek-empty { font-style: normal; opacity: .8; }
.brief-theme-tag { flex-shrink: 0; color: var(--primary); border-color: #dfe5ff; background: var(--primary-soft); cursor: pointer; transition: transform .25s, box-shadow .25s; }
.brief-theme-tag:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(79,110,247,.25); }
.brief-theme-tag.active { background: var(--primary); color: #fff; border-color: var(--primary); }
/* 效果 7：反向收回后保留完成标记 */
.brief-done {
  flex-shrink: 0; width: 16px; height: 16px; border-radius: 50%; background: #22c55e; color: #fff;
  font-size: 10px; font-weight: 700; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 0 3px rgba(34,197,94,.16); animation: doneIn .4s cubic-bezier(.34,1.56,.64,1);
}
@keyframes doneIn { from { transform: scale(0); } }

/* 效果 5：从 tag 原位向右下扩展的应用卡 */
.theme-pop {
  position: absolute; top: calc(100% + 6px); right: 14px; z-index: 30;
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
  box-shadow: var(--shadow-lg);
  transform-origin: top left; animation: tpIn .38s cubic-bezier(.32,.72,0,1);
}
@keyframes tpIn { from { opacity: 0; transform: translate(-10px, -6px) scale(.6); } }
.tp-swatch { width: 30px; height: 30px; border-radius: 9px; flex-shrink: 0; box-shadow: inset 0 0 0 1px rgba(0,0,0,.06); }
.tp-info { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.tp-info b { font-size: 12.5px; color: var(--text); }
.tp-info span { font-size: 10.5px; color: var(--text-sub); }
.theme-pop .el-button + .el-button { margin-left: 0; }
.brief-chevron { color: #9aa4b5; font-size: 12px; transition: transform .25s; flex-shrink: 0; }
.brief-chevron.open { transform: rotate(180deg); }

.brief-body { padding: 2px 14px 12px; border-top: 1px dashed var(--border); overflow: hidden; border-radius: 0 0 13px 13px; }
.brief-summary {
  margin: 10px 0 10px; font-size: 12.5px; line-height: 1.85; color: #39414e;
  padding-left: 10px; border-left: 3px solid var(--primary-soft);
}
.brief-points { margin: 0 0 10px; padding-left: 4px; list-style: none; counter-reset: kp; }
.brief-points li {
  counter-increment: kp; position: relative; padding: 5px 6px 5px 26px; border-radius: 8px;
  font-size: 12px; line-height: 1.75; color: #454e5d; cursor: pointer; transition: background .18s, color .18s;
}
.brief-points li::before {
  content: counter(kp); position: absolute; left: 4px; top: 7px;
  width: 16px; height: 16px; border-radius: 50%; background: var(--primary-soft); color: var(--primary);
  font-size: 10px; font-weight: 700; display: flex; align-items: center; justify-content: center;
}
.brief-points li:hover { background: #f0f3fa; }
.brief-points li.located { background: #fff7e0; color: #8a6200; }
.brief-keywords { display: flex; flex-wrap: wrap; gap: 5px; }
.brief-keywords .el-tag { color: #5b6472; border-color: var(--border); background: #f6f8fc; }
.brief-actions { display: flex; gap: 4px; margin-top: 6px; }
.brief-actions .el-button + .el-button { margin-left: 4px; }

.brief-empty { padding: 4px 0 2px; display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.brief-error { padding: 12px 0 4px; display: flex; align-items: center; gap: 10px; }
.brief-error-text { flex: 1; font-size: 12px; color: #b45309; line-height: 1.6; }
.brief-empty-text { font-size: 11.5px; color: var(--text-sub); line-height: 1.7; }
.brief-hint { font-size: 11px; color: #c0c7d4; }

.brief-skeleton { padding: 12px 0 4px; }
/* 效果 ⑩：1.2s 微光周期，加载超 300ms 才启动，避免快网闪烁 */
.sk-line { height: 11px; border-radius: 6px; margin-bottom: 9px; background: linear-gradient(90deg, #eef1f7 25%, #f7f9fd 50%, #eef1f7 75%); background-size: 200% 100%; animation: skShine 1.2s infinite linear 300ms; }
.w80 { width: 80%; } .w60 { width: 60%; } .w70 { width: 70%; } .w50 { width: 50%; }
@keyframes skShine { from { background-position: 200% 0; } to { background-position: -200% 0; } }
.sk-tip { font-size: 11px; color: #9aa4b5; margin-top: 4px; }

/* 数据落地：内容与骨架同位置 cross-fade，交错 60ms 入场 */
.brief-summary, .brief-points, .brief-keywords, .brief-actions {
  animation: briefIn 320ms cubic-bezier(.32,.72,0,1) backwards;
}
.brief-points { animation-delay: 60ms; }
.brief-keywords { animation-delay: 120ms; }
.brief-actions { animation-delay: 180ms; }
@keyframes briefIn { from { opacity: 0; transform: translateY(8px); } }
</style>
