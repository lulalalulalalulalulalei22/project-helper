<script setup>
import { computed } from 'vue'

const props = defineProps({
  progress: { type: Array, default: () => [] },
  error: { type: String, default: '' },
})

const steps = [
  { key: 'clone', label: '克隆代码' },
  { key: 'tree', label: '生成目录树' },
  { key: 'key_files', label: '识别关键文件' },
  { key: 'analysis', label: 'AI 深度分析' },
  { key: 'summary', label: '生成报告' },
]

const progressMap = computed(() => {
  const map = {}
  for (const p of props.progress) {
    map[p.step] = p
  }
  return map
})

function stepStatus(key) {
  const s = progressMap.value[key]
  if (!s) return 'pending'
  if (s.status === 'error') return 'error'
  if (s.status === 'done') return 'done'
  return 'running'
}

function stepMessage(key) {
  const s = progressMap.value[key]
  return s?.message || ''
}
</script>

<template>
  <div class="progress-panel card" style="max-width: 600px; margin: 60px auto;">
    <h2 class="progress-title">正在分析项目...</h2>
    <div class="step-list">
      <div
        v-for="step in steps" :key="step.key"
        class="step-item"
        :class="stepStatus(step.key)"
      >
        <div class="step-indicator">
          <span v-if="stepStatus(step.key) === 'done'" class="step-check">&#10003;</span>
          <span v-else-if="stepStatus(step.key) === 'running'" class="spinner"></span>
          <span v-else-if="stepStatus(step.key) === 'error'" class="step-error">&#10007;</span>
          <span v-else class="step-pending">&#9679;</span>
        </div>
        <div class="step-content">
          <span class="step-label">{{ step.label }}</span>
          <span v-if="stepMessage(step.key)" class="step-msg">{{ stepMessage(step.key) }}</span>
        </div>
      </div>
    </div>
    <div v-if="error" class="progress-error">{{ error }}</div>
  </div>
</template>

<style scoped>
.progress-title {
  font-size: 18px; font-weight: 700; margin-bottom: 24px; text-align: center;
}
.step-list { display: flex; flex-direction: column; gap: 4px; }
.step-item {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px; border-radius: var(--radius-sm);
  transition: background 0.2s;
}
.step-item.running { background: var(--accent-bg); }
.step-item.done { opacity: 0.7; }
.step-indicator { width: 24px; display: flex; justify-content: center; flex-shrink: 0; }
.step-check { color: var(--accent-2); font-weight: bold; }
.step-error { color: var(--danger); }
.step-pending { color: var(--border); font-size: 10px; }
.step-content { display: flex; flex-direction: column; }
.step-label { font-size: 14px; font-weight: 600; }
.step-msg { font-size: 12px; color: var(--text-3); margin-top: 1px; }
.progress-error {
  margin-top: 16px; padding: 12px; background: rgba(255, 92, 122, 0.1);
  border-radius: var(--radius-sm); color: var(--danger); font-size: 13px;
  text-align: center;
}
</style>
