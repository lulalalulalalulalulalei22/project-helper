<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import RepoInput from '../components/RepoInput.vue'
import RepoList from '../components/RepoList.vue'

const router = useRouter()
const projects = ref([])

async function loadProjects() {
  try {
    const res = await fetch('/api/projects')
    const data = await res.json()
    projects.value = data.projects || []
  } catch (e) {
    console.error('Failed to load projects:', e)
  }
}

function onRepoSubmit(repoUrl) {
  // Navigate to analysis page with repo_url as query param
  const fullUrl = repoUrl.startsWith('https://') ? repoUrl : `https://github.com/${repoUrl}`
  router.push(`/analysis?repo_url=${encodeURIComponent(fullUrl)}`)
}

function onSelectProject(project) {
  router.push(`/analysis/${project.id}`)
}

onMounted(loadProjects)
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="container">
        <div class="hero-badge">
          <span class="pulse-dot"></span>
          Powered by DeepSeek V4
        </div>
        <h1 class="hero-title">
          秒懂任何开源项目
        </h1>
        <p class="hero-desc">
          输入 GitHub 仓库地址，AI 自动克隆并深度分析源码，
          生成人人都能看懂的完整分析报告。支持交互式问答，像聊天一样读懂代码。
        </p>
        <RepoInput @submit="onRepoSubmit" />
      </div>
    </section>

    <section class="projects-section container">
      <div class="section-header">
        <h2>已分析的项目</h2>
        <span class="count-badge">{{ projects.length }}</span>
      </div>
      <RepoList :projects="projects" @select="onSelectProject" @refresh="loadProjects" />
    </section>

    <section class="features container">
      <h2 class="section-title">为什么用 Project Helper？</h2>
      <div class="feature-grid">
        <div class="feature-card card">
          <div class="feature-icon">&#9881;</div>
          <h3>智能分析</h3>
          <p>AI 深度遍历源码，提取项目结构、核心模块、数据流和设计模式</p>
        </div>
        <div class="feature-card card">
          <div class="feature-icon">&#9741;</div>
          <h3>交互式问答</h3>
          <p>像和作者对话一样，随时提问项目中的任何代码逻辑</p>
        </div>
        <div class="feature-card card">
          <div class="feature-icon">&#9733;</div>
          <h3>自动缓存</h3>
          <p>分析过的项目版本自动缓存，下次秒开，无需重复等待</p>
        </div>
        <div class="feature-card card">
          <div class="feature-icon">&#9776;</div>
          <h3>通俗易懂</h3>
          <p>用简单语言解释复杂代码，编程新手也能快速上手</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  padding: 80px 0 60px;
  text-align: center;
  background: radial-gradient(ellipse 60% 60% at 50% 0%, rgba(108, 140, 255, 0.08), transparent);
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 16px; border-radius: 20px;
  background: var(--surface-2); border: 1px solid var(--border);
  font-size: 13px; color: var(--text-2); margin-bottom: 24px;
}
.pulse-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-2);
  animation: pulse 2s infinite;
  display: inline-block;
}
.hero-title {
  font-size: 48px; font-weight: 800; letter-spacing: -1px;
  background: linear-gradient(135deg, #fff 30%, var(--accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 16px;
}
.hero-desc {
  font-size: 17px; color: var(--text-2); max-width: 580px;
  margin: 0 auto 36px; line-height: 1.7;
}
.projects-section {
  padding: 20px 0 60px;
}
.section-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
}
.section-header h2 {
  font-size: 20px; font-weight: 700;
}
.count-badge {
  font-size: 12px; padding: 2px 10px;
  background: var(--surface-2); border-radius: 12px; color: var(--text-3);
}
.features {
  padding: 20px 0 80px;
}
.section-title {
  font-size: 22px; font-weight: 700; margin-bottom: 28px; text-align: center;
}
.feature-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.feature-card {
  text-align: center; padding: 28px 20px; transition: border-color 0.2s;
}
.feature-card:hover { border-color: var(--border-light); }
.feature-icon { font-size: 32px; margin-bottom: 12px; }
.feature-card h3 { font-size: 16px; margin-bottom: 8px; }
.feature-card p { font-size: 13px; color: var(--text-2); line-height: 1.6; }
</style>
