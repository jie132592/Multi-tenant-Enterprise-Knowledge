<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 左侧会话列表 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <span>对话记录</span>
          <el-button type="primary" link @click="handleNewChat">
            <el-icon><Plus /></el-icon>
            新对话
          </el-button>
        </div>

        <div class="kb-selector">
          <el-select
            v-model="currentKbId"
            placeholder="选择知识库"
            size="default"
            @change="handleKbChange"
          >
            <el-option
              v-for="kb in kbList"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </div>

        <div class="session-list">
          <div
            v-for="session in sessionList"
            :key="session.id"
            :class="['session-item', { active: currentSessionId === session.id }]"
            @click="selectSession(session)"
          >
            <div class="session-title">{{ session.title }}</div>
            <div class="session-info">
              <span>{{ session.message_count }} 条消息</span>
            </div>
          </div>
          <el-empty v-if="sessionList.length === 0" description="暂无会话" :image-size="60" />
        </div>
      </div>

      <!-- 右侧对话区 -->
      <div class="chat-main">
        <!-- 未选择会话 -->
        <div v-if="!currentSessionId" class="chat-empty">
          <el-empty description="请选择或创建会话开始对话">
            <el-button type="primary" @click="handleNewChat">新建会话</el-button>
          </el-empty>
        </div>

        <!-- 聊天界面 -->
        <template v-else>
          <div class="chat-header">
            <span class="chat-title">{{ currentSession?.title || '新对话' }}</span>
            <div class="chat-actions">
              <el-button type="danger" link @click="handleClearHistory">
                <el-icon><Delete /></el-icon>
                清除历史
              </el-button>
            </div>
          </div>

          <div class="chat-messages" ref="messagesRef">
            <div
              v-for="(msg, index) in messageList"
              :key="index"
              :class="['message', msg.role]"
            >
              <div class="message-avatar">
                <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                <el-icon v-else><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text" :class="{ loading: msg.role === 'assistant' && !msg.content }">
                  <template v-if="msg.role === 'assistant' && !msg.content">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    AI 正在思考...
                  </template>
                  <template v-else>
                    {{ msg.content }}<span v-if="msg.role === 'assistant' && !msg.meta?.citations?.length" class="typing-cursor">|</span>
                  </template>
                </div>
                <div v-if="msg.meta?.citations?.length && (citationProgress[msg.id] || 0) > 0" class="message-citations">
                  <div class="citations-title">引用：</div>
                  <div
                    v-for="(cit, i) in msg.meta.citations.slice(0, citationProgress[msg.id])"
                    :key="i"
                    class="citation-item"
                  >
                    <span class="citation-doc">{{ cit.document_name }}</span>
                    <span class="citation-content">{{ cit.content }}</span>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <div class="chat-input">
            <div v-if="currentTokenUsage" class="token-info">
              <el-tag size="small" type="info">
                Tokens: {{ currentTokenUsage.total_tokens }} (Prompt: {{ currentTokenUsage.prompt_tokens }}, Completion: {{ currentTokenUsage.completion_tokens }})
              </el-tag>
            </div>
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              :disabled="!currentKbId || loading"
              :placeholder="currentKbId ? '输入问题...' : '请先选择知识库'"
              resize="none"
              @keydown.enter.ctrl="handleSend"
            />
            <el-button
              type="primary"
              :disabled="!inputText.trim() || !currentKbId || loading"
              @click="handleSend"
            >
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, User, ChatDotRound, Promotion, Loading } from '@element-plus/icons-vue'
import { chatApi, type ChatSession, type ChatMessage } from '../api/chat'
import { knowledgeApi, type KnowledgeBase } from '../api/knowledge'

const kbList = ref<KnowledgeBase[]>([])
const currentKbId = ref<number | null>(null)
const sessionList = ref<ChatSession[]>([])
const currentSessionId = ref<number | null>(null)
const currentSession = ref<ChatSession | null>(null)
const citationProgress = reactive<Record<number, number>>({}) // msgId -> number of visible citations
const messageList = ref<ChatMessage[]>([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref()
const currentTokenUsage = ref<{ prompt_tokens: number; completion_tokens: number; total_tokens: number } | null>(null)

const loadKbList = async () => {
  try {
    const data = await knowledgeApi.list({ page_size: 100 })
    kbList.value = data || []
    if (kbList.value.length > 0 && !currentKbId.value) {
      currentKbId.value = kbList.value[0].id
    }
  } catch (error) {
    console.error(error)
  }
}

const loadSessionList = async () => {
  if (!currentKbId.value) return
  try {
    const data = await chatApi.listSessions({ kb_id: currentKbId.value })
    sessionList.value = data || []
  } catch (error) {
    console.error(error)
  }
}

const selectSession = async (session: ChatSession) => {
  currentSessionId.value = session.id
  currentSession.value = session
  await loadMessages()
}

const loadMessages = async () => {
  if (!currentSessionId.value) return
  try {
    const data = await chatApi.getSession(currentSessionId.value)
    messageList.value = data.messages || []
    scrollToBottom()
  } catch (error) {
    console.error(error)
  }
}

const handleNewChat = async () => {
  if (!currentKbId.value) {
    ElMessage.warning('请先选择知识库')
    return
  }
  try {
    const session = await chatApi.createSession({
      kb_id: currentKbId.value,
      title: '新对话'
    })
    currentSessionId.value = session.id
    currentSession.value = session
    messageList.value = []
    await loadSessionList()
  } catch (error) {
    console.error(error)
  }
}

const handleKbChange = async () => {
  currentSessionId.value = null
  currentSession.value = null
  messageList.value = []
  await loadSessionList()
}

const handleSend = async () => {
  if (!inputText.value.trim() || !currentSessionId.value || !currentKbId.value) return

  const text = inputText.value.trim()
  inputText.value = ''
  loading.value = true

  // 添加用户消息
  messageList.value.push({
    id: Date.now(),
    session_id: currentSessionId.value!,
    role: 'user',
    content: text,
    meta: {},
    created_at: new Date().toISOString()
  })

  // 添加 AI 消息占位
  const aiMessage = {
    id: Date.now() + 1,
    session_id: currentSessionId.value!,
    role: 'assistant' as const,
    content: '',
    meta: { citations: [], token_usage: null },
    created_at: new Date().toISOString()
  }
  const msgIndex = messageList.value.length
  messageList.value.push(aiMessage)

  scrollToBottom()

  try {
    // 使用流式 API
    let pendingContent = ''
    let flushTimer: number | null = null

    const flushContent = () => {
      if (pendingContent) {
        messageList.value[msgIndex].content += pendingContent
        pendingContent = ''
        scrollToBottom()
      }
      flushTimer = null
    }

    const result = await chatApi.sendMessageStream(
      currentSessionId.value,
      { content: text, kb_id: currentKbId.value! },
      (chunk) => {
        // 累积内容，40ms 后批量显示（打字机效果）
        pendingContent += chunk
        if (!flushTimer) {
          flushTimer = window.setTimeout(flushContent, 40)
        }
      }
    )

    const { citations, tokenUsage } = result

    // 刷新剩余内容
    if (flushTimer) {
      clearTimeout(flushTimer)
      flushContent()
    }

    // 完成后存储引用和 token 到消息 meta
    messageList.value[msgIndex].meta.citations = citations
    if (tokenUsage) {
      currentTokenUsage.value = tokenUsage
      messageList.value[msgIndex].meta.token_usage = tokenUsage
    }
    loading.value = false

    // 打字机效果：逐条显示引用（通过独立 reactive 触发响应式）
    const msgId = messageList.value[msgIndex].id
    citationProgress[msgId] = 0
    let citIndex = 0
    const timer = setInterval(() => {
      if (citIndex < citations.length) {
        citationProgress[msgId] = citIndex + 1
        citIndex++
        scrollToBottom()
      } else {
        clearInterval(timer)
      }
    }, 300)

    // 更新会话标题
    if (currentSession.value) {
      currentSession.value.title = text.slice(0, 50) + (text.length > 50 ? '...' : '')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('发送消息失败')
    loading.value = false
    // 移除失败的 AI 消息
    messageList.value.pop()
  }
}

const handleClearHistory = async () => {
  if (!currentSessionId.value) return
  try {
    await chatApi.clearHistory(currentSessionId.value)
    messageList.value = []
    if (currentSession.value) {
      currentSession.value.title = '新对话'
    }
    ElMessage.success('已清除历史')
  } catch (error) {
    console.error(error)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

onMounted(async () => {
  await loadKbList()
  await loadSessionList()
})
</script>

<style lang="scss" scoped>
.chat-page {
  height: 100%;
  padding: 0;
}

.chat-container {
  display: flex;
  height: 100%;
  background: #fff;
}

.sidebar {
  width: 280px;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;

  .sidebar-header {
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e6e6e6;

    span {
      font-weight: 500;
      font-size: 16px;
    }
  }

  .kb-selector {
    padding: 12px 16px;
    border-bottom: 1px solid #e6e6e6;

    .el-select {
      width: 100%;
    }
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .session-item {
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 4px;
    transition: background 0.2s;

    &:hover {
      background: #f5f7fa;
    }

    &.active {
      background: #ecf5ff;
    }

    .session-title {
      font-size: 14px;
      font-weight: 500;
      color: #333;
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .session-info {
      font-size: 12px;
      color: #999;
    }
  }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;

  .chat-empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .chat-header {
    padding: 16px 20px;
    border-bottom: 1px solid #e6e6e6;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .chat-title {
      font-size: 16px;
      font-weight: 500;
    }
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .message {
    display: flex;
    gap: 12px;
    max-width: 80%;

    &.user {
      align-self: flex-end;
      flex-direction: row-reverse;

      .message-content {
        background: #409eff;
        color: #fff;
      }
    }

    &.assistant {
      align-self: flex-start;
    }

    .message-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #f0f2f5;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
    }

    .message-content {
      background: #f5f7fa;
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 14px;
      line-height: 1.6;

      .message-text {
        &.loading {
          color: #999;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .typing-cursor {
          display: inline-block;
          animation: blink 0.8s infinite;
          color: #409eff;
          font-weight: bold;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      }

      .message-citations {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(0, 0, 0, 0.1);

        .citations-title {
          font-size: 12px;
          font-weight: 500;
          margin-bottom: 8px;
          color: inherit;
          opacity: 0.8;
        }

        .citation-item {
          font-size: 12px;
          margin-bottom: 6px;
          padding: 6px 8px;
          background: rgba(0, 0, 0, 0.05);
          border-radius: 4px;

          .citation-doc {
            font-weight: 500;
            margin-right: 6px;
          }

          .citation-content {
            opacity: 0.8;
          }
        }
      }
    }
  }

  .chat-input {
    padding: 16px 20px;
    border-top: 1px solid #e6e6e6;
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: flex-end;

    .token-info {
      align-self: flex-start;
    }

    .el-textarea {
      flex: 1;
      width: 100%;
    }

    .el-button {
      align-self: flex-end;
    }
  }
}
</style>
