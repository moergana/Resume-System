<template>
  <div class="chat-container">
    <!-- 头部栏 -->
    <v-toolbar color="primary" class="flex-toolbar" density="compact">
      <v-toolbar-title class="text-center font-weight-bold text-h6 w-100">智能求职小助手</v-toolbar-title>
    </v-toolbar>

    <!-- 聊天内容区域 -->
    <div class="chat-content-wrapper">
      <v-card class="chat-messages pa-4" flat id="chatContent">
        <div v-for="(msg, index) in messages" :key="index" :id="'msg-' + index" class="d-flex mb-4 message-animate" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <template v-if="msg.content !== ''">
          <!-- 机器人头像 -->
          <v-avatar color="primary" size="40" class="mr-3" v-if="msg.role === 'bot'">
            <v-icon>mdi-robot</v-icon>
          </v-avatar>
          
          <!-- 聊天气泡 -->
          <v-sheet 
            :color="msg.role === 'user' ? 'primary' : 'white'"
            :class="msg.role === 'user' ? 'text-white' : 'text-black'"
            class="pa-3 rounded-lg flex-shrink-1 message-bubble"
            elevation="1"
          >
            <vue-markdown :source="msg.content" />
          </v-sheet>

          <!-- 用户头像 -->
          <v-avatar color="secondary" size="40" class="ml-3" v-if="msg.role === 'user'">
            <v-icon>mdi-account</v-icon>
          </v-avatar>
        </template>
      </div>

      <!-- 加载中动画 -->
      <div v-if="loading" class="d-flex justify-start mb-4">
        <v-avatar color="primary" size="40" class="mr-3">
          <v-icon>mdi-robot</v-icon>
        </v-avatar>
        <v-sheet color="white" class="pa-3 rounded-lg message-bubble" elevation="1">
          <v-progress-circular indeterminate size="24" width="2" color="primary"></v-progress-circular>
        </v-sheet>
      </div>
      </v-card>
    </div>

    <!-- 底部输入区域 -->
    <v-card class="flex-input w-100 pa-4 border-top" elevation="0">
      <div class="d-flex align-end">
        <v-textarea
          v-model="userInput"
          placeholder="请输入您的提示词... (Enter 发送，Shift+Enter 换行)"
          variant="outlined"
          density="comfortable"
          hide-details
          auto-grow
          rows="1"
          max-rows="10"
          class="mr-3"
          @keydown.enter.exact.prevent="sendMessage"
        ></v-textarea>
        <v-btn 
          color="primary" 
          height="48"
          :loading="loading"
          @click="sendMessage"
          append-icon="mdi-send"
          class="flex-shrink-0"
        >
          发送
        </v-btn>
      </div>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { AI_API_BASE_URL } from '@/utils/constants'
import VueMarkdown from 'vue-markdown-render'
import request from '@/utils/request'

const route = useRoute()

// 会话与请求所需的参数
const sessionId = ref('')
const analysisId = ref('') // 从路由query参数中读取
const userInput = ref('')
const loading = ref(false)

// 聊天记录数组，用于画面渲染
const messages = ref([
  { role: 'bot', content: '您好！我是您的智能助手，请问有什么可以帮您？' }
])

// 初始化生成当前会话的唯一ID
const generateSessionId = () => {
  return 'sess_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now()
}

onMounted(() => {
  sessionId.value = generateSessionId()
  // 从路由query参数中读取analysisId
  if (route.query.analysis_id) {
    analysisId.value = route.query.analysis_id
  }
  // 添加浏览器原生事件，监听用户直接关闭标签页或刷新窗口
  window.addEventListener('beforeunload', handleClearSession)
})

// 将清空会话的逻辑抽离成一个单独的方法
const handleClearSession = () => {
  if (!sessionId.value) return
  
  const targetAnalysisId = analysisId.value === '' ? `temp-${sessionId.value}` : analysisId.value
  const url = `${AI_API_BASE_URL}/chat/clear-session/${targetAnalysisId}`
  
  // 从cookie中读取token
  const token = getCookie('token')
  const headers = {
    'Content-Type': 'application/json'
  }
  if (token) {
    headers['Authorization'] = token
  }
  
  fetch(url, {
    method: 'DELETE',
    headers: headers,
    body: JSON.stringify({
      session_id: sessionId.value,
      analysis_id: targetAnalysisId,
      message: ''
    }),
    keepalive: true,
    credentials: 'include'
  }).catch(err => console.error('清除会话请求发送失败:', err))
}

// 网页内的路由跳转时触发（Vue 组件卸载时）
onBeforeUnmount(() => {
  handleClearSession()
  // 避免内存泄漏，移除事件监听器
  window.removeEventListener('beforeunload', handleClearSession)
})

// 从cookie中提取token的辅助函数
const getCookie = (name) => {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
}

// 处理并发送聊天信息 (使用fetch流式处理)
const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || loading.value) return

  // 1. 本地更新用户气泡
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  loading.value = true

  // 2. 预先推入一条空的机器人气泡，准备接收流式数据
  messages.value.push({ role: 'bot', content: '' })
  const botMessage = messages.value[messages.value.length - 1]

  try {
    // 构建请求头，包含JWT token以通过网关鉴权
    const headers = {
      'Content-Type': 'application/json'
    }
    
    // 从cookie中读取token并添加到Authorization header
    const token = getCookie('token')
    const role = getCookie('role')
    if (token) {
      headers['Authorization'] = token
    }
    if (role) {
      headers['Role'] = role
    }

    // 调用AI网关/chat接口，POST传送 ChatRequest 体
    const response = await fetch(`${AI_API_BASE_URL}/chat`, {
      method: 'POST',
      headers: headers,
      credentials: 'include', // 确保跨域请求时也会携带cookies
      body: JSON.stringify({
        session_id: sessionId.value,
        analysis_id: analysisId.value,
        message: text
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP 请求异常 Status: ${response.status}`)
    }

    // 3. 解析SSE(Server-Sent Events)数据流
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let done = false

    // 不断读取网络数据块
    while (!done) {
      const { value, done: readerDone } = await reader.read()
      done = readerDone

      if (value) {
        // 当前数据块解码
        const chunk = decoder.decode(value, { stream: true })
        // 数据流大多以 \n\n 切分，以辨别独立的数据包
        const lines = chunk.split('\n\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim() // 取出 JSON 字符串

            if (dataStr === '[DONE]') {
              break
            }

            if (dataStr) {
              try {
                // 将当前 JSON 解析，提取文本内容并累加显示到UI中
                const parsed = JSON.parse(dataStr)
                if (parsed.text) {
                  loading.value = false // 接收到有效数据块时隐藏加载动画
                  botMessage.content += parsed.text
                } else if (parsed.error) {
                  loading.value = false
                  botMessage.content += `\n[服务错误: ${parsed.error}]`
                }
              } catch (e) {
                console.error('SSE 流数据解析失败:', e, dataStr)
              }
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('网络请求或读取流数据时发生错误:', error)
    botMessage.content += `\n[系统提示: 连接智能助手失败]`
  } finally {
    loading.value = false // 无论成功失败均关闭 Loading
  }
}
</script>

<style scoped>
/* 整个Chat容器占满视口高度 */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  background: #fff;
  box-sizing: border-box;
}

/* 头部栏不伸缩 */
.flex-toolbar {
  flex-shrink: 0;
}

/* 中间内容区占满剩余空间 */
.chat-content-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;  /* 关键：允许子元素在超出内容时约束自身高度 */
}

/* 聊天消息内容区 */
.chat-messages {
  width: 100%;
  height: 100%;
  background-color: #f7f8fa;
  scroll-behavior: smooth;
  overflow-y: auto;
}

/* 底部输入区不伸缩 */
.flex-input {
  flex-shrink: 0;
}

/* 消息气泡的“从下到上浮入”动画 */
.message-animate {
  animation: floatIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 保证长文本能自动换行，且内部 Markdown 生效时不突兀 */
.message-bubble {
  max-width: 90%;  /* 放宽气泡宽度，给予表格和代码块更充裕的空间 */
  word-break: break-word;
  line-height: 1.6;
  overflow-x: auto; /* 对于极宽元素提供容器内部的滚动支持，不再撑破整体 UI */
}

/* 处理 vue-markdown-render 在深色白字情况下的标题等元素颜色继承 */
.message-bubble :deep(h1),
.message-bubble :deep(h2),
.message-bubble :deep(h3),
.message-bubble :deep(h4),
.message-bubble :deep(p),
.message-bubble :deep(li) {
  margin-bottom: 8px;
}
.message-bubble :deep(p:last-child) {
  margin-bottom: 0;
}

/* 解决 Markdown 中有序（ol）/无序（ul）列表的序号/黑点被截断出界的问题 */
.message-bubble :deep(ul),
.message-bubble :deep(ol) {
  padding-left: 24px;
  margin-top: 4px;
  margin-bottom: 8px;
}
.message-bubble :deep(li) {
  margin-bottom: 4px;
}

/* Markdown 内表格与代码块防溢出与基本样式优化 */
.message-bubble :deep(pre) {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto; /* 使超长的代码内容可滚动 */
  margin: 8px 0;
  font-family: Consolas, Monaco, monospace;
}
.text-white.message-bubble :deep(pre) {
  background-color: rgba(0, 0, 0, 0.25); /* 用户气泡(蓝色背景)里的代码块适配深色 */
}

.message-bubble :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  display: block;   /* 表格作为块级显示，以便溢出时可以出现滚动条 */
  overflow-x: auto;
}
.message-bubble :deep(th),
.message-bubble :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 12px;
  text-align: left;
}
.message-bubble :deep(th) {
  background-color: rgba(0, 0, 0, 0.05);
}

.border-top {
  border-top: 1px solid #eeeeee !important;
}
</style>
