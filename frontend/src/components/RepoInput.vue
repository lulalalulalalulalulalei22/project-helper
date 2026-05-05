<script setup>
import { ref } from 'vue'

const emit = defineEmits(['submit'])
const repoUrl = ref('')
const error = ref('')

function submit() {
  const url = repoUrl.value.trim()
  if (!url) return
  if (!url.includes('github.com')) {
    error.value = '请输入有效的 GitHub 仓库地址'
    return
  }
  error.value = ''
  emit('submit', url)
}
</script>

<template>
  <div class="repo-input-wrapper">
    <div class="input-group">
      <span class="input-prefix">https://github.com/</span>
      <input
        v-model="repoUrl"
        type="text"
        class="input repo-input"
        placeholder="username/repo"
        @keyup.enter="submit"
      />
      <button class="btn btn-primary" @click="submit">
        <span>&#9654;</span>
        开始分析
      </button>
    </div>
    <p v-if="error" class="input-error">{{ error }}</p>
    <p class="input-hint">支持任何公开的 GitHub 仓库，例如: facebook/react, fastapi/fastapi</p>
  </div>
</template>

<style scoped>
.repo-input-wrapper {
  max-width: 620px; margin: 0 auto;
}
.input-group {
  display: flex; align-items: stretch;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius); overflow: hidden;
  transition: border-color 0.2s;
}
.input-group:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-bg);
}
.input-prefix {
  display: flex; align-items: center;
  padding: 0 14px; font-size: 13px;
  color: var(--text-3); background: var(--surface-3);
  border-right: 1px solid var(--border);
  font-family: var(--font-mono); white-space: nowrap;
}
.repo-input {
  flex: 1; border: none; background: transparent;
  padding: 14px 16px; border-radius: 0;
}
.repo-input:focus { box-shadow: none; outline: none; }
.btn { border-radius: 0; padding: 0 24px; white-space: nowrap; }
.input-error { color: var(--danger); font-size: 13px; margin-top: 8px; }
.input-hint { color: var(--text-3); font-size: 12px; margin-top: 8px; }
</style>
