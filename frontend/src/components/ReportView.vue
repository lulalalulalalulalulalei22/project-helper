<script setup>
import { computed } from 'vue'
import { Marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'

const props = defineProps({
  report: { type: String, default: '' },
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
</script>

<template>
  <div class="report-view">
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
.empty-report { text-align: center; padding: 60px; color: var(--text-2); }
</style>
