<template>
  <div class="h-full w-full bg-white relative flex flex-col items-center">
    <!-- Header -->
    <div class="w-full h-16 shrink-0 flex items-center justify-between px-6 border-b border-gray-100 bg-white/80 backdrop-blur-sm z-10 sticky top-0">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md">
          <el-icon size="20"><ChatDotRound /></el-icon>
        </div>
        <div>
          <h2 class="text-lg font-bold text-gray-800 leading-tight">Insight 智能助理</h2>
          <p class="text-xs text-gray-500">连接所有原文、笔记与闪念胶囊的全局知识库</p>
        </div>
      </div>
      <el-button v-if="conversationId" type="info" text bg size="small" @click="startNewChat">
        <el-icon class="mr-1"><Plus /></el-icon> 新对话
      </el-button>
    </div>

    <!-- Chat Message List -->
    <div class="flex-1 w-full max-w-4xl overflow-y-auto p-6 space-y-6 custom-scrollbar" ref="chatScrollRef">
      <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400">
        <el-icon size="48" class="mb-4 text-indigo-100"><ChatLineSquare /></el-icon>
        <p class="text-lg font-medium text-gray-500">准备好探索你的知识库了吗？</p>
        <p class="text-sm mt-2">试着问我："最近我读过哪些关于大模型的论文？" 或 "总结一下我存的闪念胶囊"</p>
      </div>

      <div v-for="(msg, index) in messages" :key="index" class="flex gap-4" :class="{'flex-row-reverse': msg.role === 'user'}">
        <!-- Avatar -->
        <div class="w-8 h-8 shrink-0 rounded-full flex items-center justify-center mt-1"
             :class="msg.role === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-indigo-100 text-indigo-600'">
          <el-icon><User v-if="msg.role === 'user'" /><Cpu v-else /></el-icon>
        </div>
        
        <!-- Bubble -->
        <div class="max-w-[80%] rounded-2xl px-5 py-3 shadow-sm"
             :class="msg.role === 'user' ? 'bg-blue-500 text-white rounded-tr-sm' : 'bg-gray-50 border border-gray-100 text-gray-800 rounded-tl-sm'">
          <div class="prose prose-sm max-w-none" :class="{'prose-invert': msg.role === 'user'}" v-html="renderMarkdown(msg.content)"></div>
          
          <!-- Citations / References (If any) -->
          <div v-if="msg.role === 'assistant' && msg.citations && msg.citations.length > 0" class="mt-3 pt-3 border-t border-gray-200/50">
            <div class="text-xs text-gray-500 font-medium mb-2 flex items-center gap-1">
              <el-icon><Link /></el-icon> 引用来源：
            </div>
            <div class="flex flex-wrap gap-2">
              <el-tag v-for="(cite, cIdx) in msg.citations" :key="cIdx" size="small" type="info" effect="plain" class="max-w-[200px] truncate" :title="cite.title">
                {{ cite.title }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="isTyping" class="flex gap-4">
        <div class="w-8 h-8 shrink-0 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mt-1">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
        <div class="bg-gray-50 border border-gray-100 rounded-2xl rounded-tl-sm px-5 py-3 text-gray-500 text-sm flex items-center gap-2">
          正在思考检索知识库...
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="w-full max-w-4xl p-6 shrink-0 bg-white">
      <div class="relative shadow-sm rounded-xl border border-gray-200 bg-white overflow-hidden transition-shadow focus-within:shadow-md focus-within:border-indigo-300">
        <!-- Uploaded Files Preview -->
        <div v-if="uploadedFiles.length > 0" class="flex flex-wrap gap-2 p-3 bg-gray-50 border-b border-gray-100">
          <div v-for="(f, idx) in uploadedFiles" :key="idx" class="flex items-center gap-1 bg-white border border-gray-200 rounded-md px-2 py-1 text-xs text-gray-600 shadow-sm relative group">
            <el-icon v-if="f.type === 'image'" class="text-blue-500"><Picture /></el-icon>
            <el-icon v-else class="text-orange-500"><Document /></el-icon>
            <span class="max-w-[100px] truncate" :title="f.name">{{ f.name }}</span>
            <el-icon class="cursor-pointer text-gray-400 hover:text-red-500 ml-1" @click="removeFile(idx)"><Close /></el-icon>
          </div>
        </div>

        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="向你的专属知识库提问 (支持粘贴图文, Shift + Enter 换行)..."
          resize="none"
          class="chat-input"
          @keydown.enter.exact.prevent="sendMessage"
          @paste="handlePaste"
        />
        <div class="absolute bottom-2 left-2">
          <el-upload
            :action="`${API_BASE}/chat/upload`"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            name="file"
          >
            <el-button text circle size="small" :loading="isUploading" class="!text-gray-400 hover:!text-indigo-500">
              <el-icon size="18"><Paperclip /></el-icon>
            </el-button>
          </el-upload>
        </div>
        <div class="absolute bottom-2 right-2">
          <el-button 
            type="primary" 
            circle 
            class="!w-8 !h-8 !bg-indigo-500 !border-none hover:!bg-indigo-600 shadow-md transition-transform active:scale-95"
            :disabled="!userInput.trim() || isTyping"
            @click="sendMessage"
          >
            <el-icon><Top /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="text-center mt-2 text-[10px] text-gray-400">
        Insight Assistant may produce inaccurate information about people, places, or facts.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ChatDotRound, ChatLineSquare, User, Cpu, Plus, Top, Loading, Link, Paperclip, Picture, Document, Close } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE = 'http://localhost:8000/api'

interface Citation {
  title: string
  dataset_id?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

const messages = ref<Message[]>([])
const userInput = ref('')
const isTyping = ref(false)
const isUploading = ref(false)
const uploadedFiles = ref<{id: string, type: string, name: string}[]>([])
const conversationId = ref('')
const chatScrollRef = ref<HTMLElement | null>(null)

const beforeUpload = () => {
  isUploading.value = true
  return true
}

const handleUploadSuccess = (response: any, file: any) => {
  isUploading.value = false
  if (response.status === 'success') {
    uploadedFiles.value.push({
      id: response.file_id,
      type: response.type,
      name: response.name || file.name
    })
  } else {
    ElMessage.error(response.message || '文件上传失败')
  }
}

const handleUploadError = (_error: any, file: any) => {
  isUploading.value = false
  ElMessage.error(`文件 ${file.name} 上传失败`)
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const handlePaste = async (e: ClipboardEvent) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1 || items[i].type.indexOf('application/pdf') !== -1) {
      const file = items[i].getAsFile()
      if (file) {
        e.preventDefault()
        isUploading.value = true
        const formData = new FormData()
        formData.append('file', file)
        try {
          const res = await axios.post(`${API_BASE}/chat/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          handleUploadSuccess(res.data, file)
        } catch (error: any) {
          handleUploadError(error, file)
        }
        break
      }
    }
  }
}

const renderMarkdown = (text: string) => {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text) as string)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatScrollRef.value) {
      chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
    }
  })
}

const startNewChat = () => {
  messages.value = []
  conversationId.value = ''
  userInput.value = ''
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isTyping.value) return
  
  const query = userInput.value.trim()
  const filesToUpload = uploadedFiles.value.map(f => ({
    type: f.type,
    transfer_method: 'local_file',
    upload_file_id: f.id
  }))
  
  // Create user message content
  let userDisplayContent = query
  if (uploadedFiles.value.length > 0) {
    const fileNames = uploadedFiles.value.map(f => `📎 ${f.name}`).join('\n')
    userDisplayContent = `${fileNames}\n\n${query}`
  }
  
  messages.value.push({ role: 'user', content: userDisplayContent })
  userInput.value = ''
  uploadedFiles.value = [] // Clear uploaded files
  isTyping.value = true
  scrollToBottom()

  // Create a placeholder for assistant's response
  messages.value.push({ role: 'assistant', content: '', citations: [] })
  const currentMsgIndex = messages.value.length - 1

  try {
    const response = await fetch(`${API_BASE}/chat/global`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        conversation_id: conversationId.value,
        files: filesToUpload
      })
    })

    if (!response.body) throw new Error('No response body')

    isTyping.value = false // Hide typing indicator once stream starts
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (!dataStr) continue
          
          try {
            const data = JSON.parse(dataStr)
            
            // Handle Dify streaming events
            if (data.event === 'message') {
              messages.value[currentMsgIndex].content += data.answer
              if (data.conversation_id && !conversationId.value) {
                conversationId.value = data.conversation_id
              }
              scrollToBottom()
            } 
            else if (data.event === 'message_end') {
              // Parse citations if retriever_resources exists
              if (data.metadata && data.metadata.retriever_resources) {
                const resources = data.metadata.retriever_resources
                const uniqueCitations = new Map()
                resources.forEach((r: any) => {
                  if (r.document_name && !uniqueCitations.has(r.document_name)) {
                    uniqueCitations.set(r.document_name, {
                      title: r.document_name,
                      dataset_id: r.dataset_id
                    })
                  }
                })
                messages.value[currentMsgIndex].citations = Array.from(uniqueCitations.values())
              }
            }
            else if (data.event === 'error') {
              messages.value[currentMsgIndex].content += `\n\n**[Error]**: ${data.message}`
            }
          } catch (e) {
            // Ignore JSON parse errors for incomplete chunks
          }
        }
      }
    }
  } catch (error) {
    console.error('Chat error:', error)
    messages.value[currentMsgIndex].content += '\n\n**[网络错误]**: 无法连接到全局对话服务。'
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-input :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 12px 48px 12px 16px;
  background: transparent;
}
.chat-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
</style>
