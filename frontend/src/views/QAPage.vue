<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import ChatPanel from '../components/ChatPanel.vue'

const route = useRoute()
const projectId = route.params.id
const project = ref(null)
const loading = ref(true)
const error = ref('')

async function loadProject() {
  try {
    const res = await fetch(`/api/projects/${projectId}`)
    if (!res.ok) throw new Error('项目未找到')
    project.value = await res.json()
  } catch (e) {
    error.value = '加载项目失败: ' + e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadProject)
</script>

<template>
  <div class="qa-page container">
    <div v-if="loading" class="loading-state">
      <div class="spinner" style="width: 32px; height: 32px;"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-card card">{{ error }}</div>

    <div v-else class="qa-layout animate-in">
      <div class="qa-sidebar">
        <div class="project-info-card card">
          <h3>{{ project.project_name }}</h3>
          <p class="pi-url">{{ project.repo_url }}</p>
          <div class="pi-tech">
            <span v-for="tech in project.tech_stack" :key="tech" class="badge">{{ tech }}</span>
          </div>
          <router-link to="/" class="btn btn-secondary btn-back">返回首页</router-link>
        </div>
        <div class="tips-card card">
          <h4>提问技巧</h4>
          <ul>
            <li>问具体模块: "用户认证是怎么实现的？"</li>
            <li>问数据流: "一个请求从前端到数据库的完整流程？"</li>
            <li>问设计: "这个项目用了哪些设计模式？"</li>
            <li>问特定文件: "src/main.py 做了什么？"</li>
          </ul>
        </div>
      </div>

      <div class="qa-main">
        <ChatPanel :project-id="projectId" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.qa-page { padding: 32px 24px; }
.loading-state { text-align: center; padding: 60px; }
.loading-state p { margin-top: 16px; color: var(--text-2); }
.qa-layout { display: grid; grid-template-columns: 260px 1fr; gap: 24px; max-width: 1000px; margin: 0 auto; align-items: start; }
.qa-sidebar { position: sticky; top: 80px; display: flex; flex-direction: column; gap: 16px; }
.qa-main { min-height: 70vh; }
.project-info-card h3 { font-size: 16px; margin-bottom: 4px; }
.pi-url { font-size: 12px; color: var(--text-3); font-family: var(--font-mono); margin-bottom: 10px; word-break: break-all; }
.pi-tech { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
.btn-back { width: 100%; justify-content: center; font-size: 13px; text-decoration: none; }
.tips-card h4 { font-size: 14px; margin-bottom: 8px; color: var(--text-2); }
.tips-card ul { font-size: 12px; color: var(--text-2); padding-left: 18px; }
.tips-card li { margin-bottom: 6px; }
.error-card { text-align: center; padding: 40px; color: var(--danger); }

@media (max-width: 768px) {
  .qa-layout { grid-template-columns: 1fr; }
  .qa-sidebar { position: static; }
}
</style>
