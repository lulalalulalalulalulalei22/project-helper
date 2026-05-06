<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ProgressPanel from '../components/ProgressPanel.vue'
import ReportView from '../components/ReportView.vue'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const report = ref('')
const tree = ref({})
const progress = ref([])
const analyzing = ref(false)
const loading = ref(false)
const error = ref('')
const eventSource = ref(null)

const displayState = computed(() => {
  if (error.value && !report.value) return 'error'
  if (report.value && !analyzing.value) return 'report'
  if (analyzing.value) return 'analyzing'
  if (loading.value) return 'loading'
  return 'empty'
})

function startAnalysis(repoUrl) {
  analyzing.value = true
  error.value = ''
  progress.value = []
  report.value = ''
  project.value = null

  const es = new EventSource(
    `/api/analyze?repo_url=${encodeURIComponent(repoUrl)}&force=false`
  )
  eventSource.value = es

  es.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data)
    progress.value.push(data)

    if (data.step === 'error') {
      error.value = data.message || '分析过程出错'
      analyzing.value = false
      es.close()
      return
    }
    if (data.step === 'cached' && data.status === 'done') {
      const cached = data.data
      let stack = cached.tech_stack
      if (typeof stack === 'string') stack = JSON.parse(stack)
      project.value = {
        id: cached.id,
        repo_url: cached.repo_url,
        project_name: cached.project_name,
        tech_stack: stack,
      }
      report.value = cached.report
      tree.value = cached.tree || {}
      analyzing.value = false
      es.close()
      router.replace(`/analysis/${cached.id}`)
    }
    if (data.step === 'summary' && data.status === 'done') {
      const d = data.data
      project.value = {
        id: d.project_id,
        project_name: d.project_name,
        tech_stack: d.tech_stack,
        repo_url: repoUrl,
      }
      report.value = d.report
      tree.value = d.tree || {}
      analyzing.value = false
      es.close()
      router.replace(`/analysis/${d.project_id}`)
    }
  })

  es.addEventListener('done', (e) => {
    const data = JSON.parse(e.data)
    if (data.project_id && !report.value) {
      loadProject(data.project_id)
    }
    es.close()
    analyzing.value = false
  })

  es.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.message) {
        error.value = data.message
      }
    } catch {
      // network errors have no parseable data — onerror will handle
    }
  })

  es.onerror = () => {
    if (!report.value) {
      if (!error.value) {
        error.value = '连接中断，请确认后端服务已启动'
      }
      analyzing.value = false
    }
    es.close()
  }
}

async function loadProject(id) {
  loading.value = true
  try {
    const res = await fetch(`/api/projects/${id}`)
    if (!res.ok) throw new Error('Project not found')
    project.value = await res.json()
    report.value = project.value.report
    tree.value = project.value.tree || {}
    router.replace(`/analysis/${id}`)
  } catch (e) {
    error.value = '加载项目失败: ' + e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const id = route.params.id
  const repoUrl = route.query.repo_url

  if (id) {
    loadProject(id)
  } else if (repoUrl) {
    startAnalysis(repoUrl)
  }
})

onUnmounted(() => {
  if (eventSource.value) {
    eventSource.value.close()
  }
})
</script>

<template>
  <div class="analysis-page container">
    <!-- Empty -->
    <div v-if="displayState === 'empty'" class="empty-state">
      <div class="empty-icon">&#128270;</div>
      <h2>输入 GitHub 仓库地址开始分析</h2>
      <p>在首页输入仓库地址，或点击上方"首页"返回</p>
    </div>

    <!-- Loading -->
    <div v-if="displayState === 'loading'" class="loading-state">
      <div class="spinner"></div>
      <p>加载项目数据...</p>
    </div>

    <!-- Analyzing -->
    <ProgressPanel
      v-if="displayState === 'analyzing'"
      :progress="progress"
      :error="error"
    />

    <!-- Error -->
    <div v-if="displayState === 'error'" class="error-card card">
      <div class="error-icon">&#9888;</div>
      <h3>分析失败</h3>
      <p>{{ error }}</p>
      <router-link to="/" class="btn btn-secondary">返回首页</router-link>
    </div>

    <!-- Report -->
    <div v-if="displayState === 'report'" class="report-section animate-in">
      <div class="report-header">
        <div>
          <h1 class="project-title">{{ project?.project_name || '' }}</h1>
          <p class="project-url">{{ project?.repo_url || '' }}</p>
        </div>
        <div class="report-actions">
          <span v-for="tech in (project?.tech_stack || [])" :key="tech" class="badge">{{ tech }}</span>
          <router-link v-if="project?.id" :to="`/qa/${project.id}`" class="btn btn-primary btn-qa">
            智能问答
          </router-link>
        </div>
      </div>

      <div class="report-layout">
        <ReportView :report="report" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-page { padding: 40px 24px; }
.empty-state { text-align: center; padding: 80px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state h2 { font-size: 22px; margin-bottom: 8px; }
.empty-state p { color: var(--text-2); }
.loading-state { text-align: center; padding: 80px 20px; }
.loading-state p { color: var(--text-2); margin-top: 20px; font-size: 14px; }
.spinner {
  width: 36px; height: 36px; margin: 0 auto;
  border: 3px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.report-section { max-width: 900px; margin: 0 auto; }
.report-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border);
  flex-wrap: wrap; gap: 16px;
}
.project-title { font-size: 28px; font-weight: 800; margin-bottom: 4px; }
.project-url { font-size: 13px; color: var(--text-3); font-family: var(--font-mono); }
.report-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.btn-qa { text-decoration: none; }
.error-card { text-align: center; padding: 40px; max-width: 500px; margin: 60px auto; }
.error-icon { font-size: 36px; margin-bottom: 12px; }
.error-card h3 { font-size: 18px; color: var(--danger); margin-bottom: 8px; }
.error-card p { color: var(--text-2); font-size: 14px; margin-bottom: 20px; }
</style>
