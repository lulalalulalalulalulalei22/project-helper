<script setup>
import { ref, nextTick, onUnmounted, computed } from 'vue'
import { Marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'

const props = defineProps({
  projectId: { type: [Number, String], required: true },
})

const marked = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try { return hljs.highlight(code, { language: lang }).value } catch {}
      }
      try { return hljs.highlightAuto(code).value } catch {}
      return code
    },
  })
)

const messages = ref([])
const input = ref('')
const sending = ref(false)
const eventSource = ref(null)
const chatContainer = ref(null)
const streamBuffer = ref('')
const toolCalls = ref([])

function addMessage(role, content) {
  messages.value.push({ role, content, id: Date.now() })
}

function renderMd(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

async function send() {
  const question = input.value.trim()
  if (!question || sending.value) return

  input.value = ''
  addMessage('user', question)
  sending.value = true
  streamBuffer.value = ''
  toolCalls.value = []

  // Add a placeholder assistant message
  const aiMsgId = Date.now()
  messages.value.push({ role: 'assistant', content: '', id: aiMsgId, streaming: true })
  await scrollToBottom()

  try {
    const es = new EventSource(
      `/api/chat?project_id=${props.projectId}&question=${encodeURIComponent(question)}`
    )
    eventSource.value = es

    es.addEventListener('chat', (e) => {
      const data = JSON.parse(e.data)

      if (data.type === 'text') {
        streamBuffer.value += data.content
        // Update the last message
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.content = streamBuffer.value
        }
        scrollToBottom()
      } else if (data.type === 'tool_start') {
        toolCalls.value.push({ name: data.content, status: 'running' })
      } else if (data.type === 'tool_result') {
        if (toolCalls.value.length > 0) {
          toolCalls.value[toolCalls.value.length - 1].status = 'done'
          toolCalls.value[toolCalls.value.length - 1].result = data.content
        }
      } else if (data.type === 'done') {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg) lastMsg.streaming = false
        sending.value = false
        es.close()
      } else if (data.type === 'error') {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg) {
          lastMsg.content += `\n\n> 错误: ${data.content}`
          lastMsg.streaming = false
        }
        sending.value = false
        es.close()
      }
    })

    es.addEventListener('error', (e) => {
      try {
        const data = JSON.parse(e.data)
        streamBuffer.value += `\n\n> 错误: ${data.message}`
      } catch {}
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg) lastMsg.streaming = false
      sending.value = false
      es.close()
    })

    es.onerror = () => {
      if (sending.value) {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg) lastMsg.streaming = false
        sending.value = false
      }
      es.close()
    }
  } catch (e) {
    addMessage('assistant', `请求失败: ${e.message}`)
    sending.value = false
  }
}

onUnmounted(() => {
  if (eventSource.value) eventSource.value.close()
})
</script>

<template>
  <div class="chat-panel card">
    <div class="chat-messages" ref="chatContainer">
      <div v-if="messages.length === 0" class="chat-welcome">
        <div class="welcome-icon">&#9741;</div>
        <h3>智能问答</h3>
        <p>针对该项目源码提问，AI 会查找代码来回答你的问题</p>
      </div>

      <div
        v-for="msg in messages" :key="msg.id"
        class="chat-msg"
        :class="msg.role"
      >
        <div class="msg-avatar">
          {{ msg.role === 'user' ? '?' : 'AI' }}
        </div>
        <div class="msg-body">
          <div
            v-if="msg.role === 'assistant'"
            class="markdown-body msg-md"
            v-html="renderMd(msg.content)"
          ></div>
          <div v-else class="msg-text">{{ msg.content }}</div>

          <!-- Streaming cursor -->
          <span v-if="msg.streaming" class="stream-cursor">|</span>

          <!-- Tool calls indicator -->
          <div v-if="msg.role === 'assistant' && toolCalls.length > 0" class="tool-calls">
            <div v-for="tc in toolCalls" :key="tc.name" class="tool-call-item">
              <span class="tool-dot" :class="tc.status"></span>
              <span class="tool-name">工具调用: {{ tc.name }}</span>
              <span v-if="tc.result" class="tool-result">{{ tc.result }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <textarea
        v-model="input"
        class="input chat-input"
        placeholder="输入问题，例如: 这个项目的认证流程是怎么实现的？"
        rows="2"
        @keyup.enter.exact="send"
        :disabled="sending"
      ></textarea>
      <button
        class="btn btn-primary chat-send"
        @click="send"
        :disabled="!input.trim() || sending"
      >
        <span v-if="sending" class="spinner"></span>
        <span v-else>&#9654;</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex; flex-direction: column;
  height: calc(100vh - 140px); min-height: 500px; padding: 0;
}
.chat-messages {
  flex: 1; overflow-y: auto; padding: 24px;
}
.chat-welcome { text-align: center; padding: 60px 20px; }
.welcome-icon { font-size: 40px; margin-bottom: 12px; }
.chat-welcome h3 { font-size: 18px; margin-bottom: 6px; }
.chat-welcome p { font-size: 14px; color: var(--text-2); }
.chat-msg { display: flex; gap: 12px; margin-bottom: 20px; }
.chat-msg.user { flex-direction: row-reverse; }
.msg-avatar {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.chat-msg.user .msg-avatar { background: var(--accent-bg); color: var(--accent); }
.chat-msg.assistant .msg-avatar { background: var(--accent-2-bg); color: var(--accent-2); }
.msg-body {
  max-width: 80%; min-width: 0;
  position: relative;
}
.chat-msg.user .msg-body {
  background: var(--accent-bg); border-radius: 12px 4px 12px 12px;
  padding: 10px 14px;
}
.msg-text { font-size: 14px; line-height: 1.6; word-break: break-word; }
.msg-md { font-size: 14px; }
.msg-md :deep(h1), .msg-md :deep(h2), .msg-md :deep(h3) { font-size: 1.1em; margin: 12px 0 6px; }
.msg-md :deep(pre) { padding: 10px 14px; margin: 8px 0; }
.msg-md :deep(pre code) { font-size: 12px; }
.stream-cursor {
  animation: pulse 0.6s infinite; color: var(--accent); font-weight: bold;
}
.tool-calls {
  margin-top: 6px; padding: 8px 12px;
  background: var(--surface-2); border-radius: 8px;
  font-size: 12px;
}
.tool-call-item { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.tool-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.tool-dot.running { background: var(--warning); }
.tool-dot.done { background: var(--accent-2); }
.tool-name { color: var(--text-2); }
.tool-result { color: var(--text-3); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.chat-input-area {
  display: flex; gap: 10px; padding: 16px 20px;
  border-top: 1px solid var(--border);
}
.chat-input {
  flex: 1; resize: none; font-family: inherit;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: 12px;
  color: var(--text-1); font-size: 14px;
  line-height: 1.5;
}
.chat-input:focus { outline: none; border-color: var(--accent); }
.chat-send { flex-shrink: 0; align-self: flex-end; }
</style>
