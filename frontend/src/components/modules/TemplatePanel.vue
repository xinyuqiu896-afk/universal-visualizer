<template>
  <div class="scroll-area">
    <h3 class="module-title">🎨 模板与主题中心</h3>
    <div class="hint" style="margin-bottom:12px">选择生成页面的视觉主题。「智能选型」由 AI 根据内容主题自动匹配最合适的风格。</div>
    <div v-for="t in themes" :key="t.key"
         class="theme-card" :class="{ active: state.theme === t.key }" @click="state.theme = t.key">
      <div class="swatch" :style="{ background: t.bg }">
        <span v-for="c in t.dots" :key="c" class="dot" :style="{ background: c }"></span>
      </div>
      <div>
        <div style="font-weight:600;font-size:13px">{{ t.name }}</div>
        <div class="hint">{{ t.desc }}</div>
      </div>
      <el-icon v-if="state.theme === t.key" color="var(--primary)" style="margin-left:auto"><Check /></el-icon>
    </div>
    <el-input v-model="state.extraReq" type="textarea" :rows="3" size="small"
              style="margin-top:12px" placeholder="附加要求（可选）：如“重点突出数据表格”“加入时间线”…" />
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { Check } from '@element-plus/icons-vue'
const state = inject('appState')
const themes = [
  { key: 'auto',        name: '🎯 智能选型', desc: 'AI 根据内容主题自动匹配最佳风格', bg: 'linear-gradient(135deg,#667eea,#764ba2)', dots: ['#fff','#ffd'] },
  { key: 'tech-blue',   name: '科技蓝', desc: '深蓝底 + 电光蓝，玻璃拟态', bg: 'linear-gradient(135deg,#0B1220,#1D4ED8)', dots: ['#3B82F6','#93C5FD'] },
  { key: 'biz-gold',    name: '商务黑金', desc: '炭黑 + 香槟金，衬线标题', bg: 'linear-gradient(135deg,#111,#3a2f0b)', dots: ['#C9A227','#E7C873'] },
  { key: 'fresh-green', name: '清新自然', desc: '米白 + 森林绿', bg: 'linear-gradient(135deg,#F7F5EF,#2F6B4F)', dots: ['#2F6B4F','#86C99B'] },
  { key: 'warm-orange', name: '暖橙活力', desc: '奶油白 + 珊瑚橙', bg: 'linear-gradient(135deg,#FFF8F0,#E8622C)', dots: ['#E8622C','#FFB380'] },
  { key: 'minimal',     name: '极简杂志', desc: '纯白 + 留白 + 一处强调色', bg: 'linear-gradient(135deg,#fff,#e5e5e5)', dots: ['#111','#E11D48'] },
  { key: 'dark-neon',   name: '暗黑霓虹', desc: '深底 + 霓虹紫青渐变', bg: 'linear-gradient(135deg,#0A0A12,#7C3AED)', dots: ['#A78BFA','#22D3EE'] },
]
</script>

<style scoped>
.theme-card {
  display: flex; gap: 12px; align-items: center; padding: 10px 12px; border: 1.5px solid var(--border);
  border-radius: 10px; margin-bottom: 8px; cursor: pointer; transition: all .15s; background: #fff;
}
.theme-card:hover { border-color: #c3cdf5; }
.theme-card.active { border-color: var(--primary); background: var(--primary-soft); }
.swatch { width: 52px; height: 36px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: flex-end; gap: 4px; padding: 5px; }
.dot { width: 9px; height: 9px; border-radius: 50%; }
</style>
