<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-brand" @click="goHome">
        <span class="logo-icon">&#9670;</span>
        <span class="logo-text">Project Helper</span>
        <span class="logo-sub">项目学习助手</span>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link v-if="route.params.id" :to="`/analysis/${route.params.id}`" class="nav-link">分析报告</router-link>
        <router-link v-if="route.params.id" :to="`/qa/${route.params.id}`" class="nav-link">智能问答</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 60px;
  background: var(--surface-1);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}
.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}
.logo-icon {
  font-size: 24px;
  color: var(--accent);
  filter: drop-shadow(0 0 8px var(--accent-glow));
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-1);
  letter-spacing: -0.3px;
}
.logo-sub {
  font-size: 12px;
  color: var(--text-3);
  background: var(--surface-2);
  padding: 2px 8px;
  border-radius: 10px;
}
.header-nav {
  display: flex;
  gap: 8px;
}
.nav-link {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-2);
  text-decoration: none;
  transition: all 0.2s;
}
.nav-link:hover {
  color: var(--text-1);
  background: var(--surface-2);
}
.nav-link.router-link-active {
  color: var(--accent);
  background: var(--accent-bg);
}
.app-main {
  flex: 1;
  padding: 0;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
