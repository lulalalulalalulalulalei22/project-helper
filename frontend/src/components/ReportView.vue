<script setup>
import { computed } from 'vue'
import { Marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'

const props = defineProps({
  report: { type: String, default: '' },
  projectName: { type: String, default: '' },
})

const marked = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value
        } catch {}
      }
      try {
        return hljs.highlightAuto(code).value
      } catch {}
      return code
    },
  })
)

const renderedHtml = computed(() => {
  if (!props.report) return ''
  return marked.parse(props.report)
})

function downloadMarkdown() {
  const name = props.projectName || 'project'
  const filename = `${name}_源码分析.md`
  const blob = new Blob([props.report], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="report-view">
    <div class="report-toolbar">
      <button v-if="report" class="btn-download" @click="downloadMarkdown" title="下载为 Markdown 文件">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        <span>下载 Markdown</span>
      </button>
    </div>
    <div v-if="!report" class="empty-report card">
      <p>报告中...</p>
    </div>
    <div v-else class="markdown-body" v-html="renderedHtml"></div>
  </div>
</template>

<style scoped>
.report-view {
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 36px 40px;
}
.report-toolbar {
  display: flex; justify-content: flex-end; margin-bottom: 8px;
}
.btn-download {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: 1px solid var(--border);
  border-radius: 6px; padding: 5px 12px;
  color: var(--text-2); font-size: 12px; font-family: inherit;
  cursor: pointer; transition: border-color 0.2s, color 0.2s;
}
.btn-download:hover {
  border-color: var(--border-light); color: var(--text-1);
}
.empty-report { text-align: center; padding: 60px; color: var(--text-2); }
</style>
