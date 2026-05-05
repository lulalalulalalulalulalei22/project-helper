<script setup>
defineProps({
  projects: { type: Array, default: () => [] },
})
const emit = defineEmits(['select', 'refresh'])

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="repo-list">
    <div v-if="projects.length === 0" class="empty-state card">
      <div class="empty-icon">&#128269;</div>
      <p>还没有分析过任何项目</p>
      <p class="empty-hint">在上方输入 GitHub 地址开始分析</p>
    </div>
    <div v-for="p in projects" :key="p.id" class="repo-item card" @click="emit('select', p)">
      <div class="repo-info">
        <h3 class="repo-name">{{ p.project_name || p.repo_url }}</h3>
        <p class="repo-url">{{ p.repo_url }}</p>
        <div class="repo-meta">
          <span v-for="tech in (typeof p.tech_stack === 'string' ? JSON.parse(p.tech_stack || '[]') : (p.tech_stack || []))" :key="tech" class="badge">{{ tech }}</span>
        </div>
      </div>
      <div class="repo-actions" @click.stop>
        <span class="repo-date">{{ formatDate(p.created_at) }}</span>
        <button class="btn btn-secondary btn-sm" @click="emit('select', p)">查看</button>
        <button class="btn btn-secondary btn-sm" @click="emit('refresh')">刷新</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.repo-list { display: flex; flex-direction: column; gap: 10px; }
.empty-state { text-align: center; padding: 50px 20px; }
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { color: var(--text-2); }
.empty-hint { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.repo-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 22px; cursor: pointer; transition: border-color 0.2s;
}
.repo-item:hover { border-color: var(--border-light); }
.repo-name { font-size: 15px; font-weight: 600; margin-bottom: 2px; }
.repo-url { font-size: 12px; color: var(--text-3); font-family: var(--font-mono); margin-bottom: 8px; }
.repo-meta { display: flex; gap: 6px; flex-wrap: wrap; }
.repo-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.repo-date { font-size: 12px; color: var(--text-3); }
.btn-sm { padding: 6px 14px; font-size: 12px; }
</style>
