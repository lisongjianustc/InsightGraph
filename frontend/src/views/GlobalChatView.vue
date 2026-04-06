<template>
  <div class="h-full w-full bg-white relative flex overflow-hidden">
    <!-- Sidebar -->
    <div 
      class="w-64 bg-gray-50 border-r border-gray-200 flex flex-col transition-all duration-300 shrink-0"
      :class="isSidebarOpen ? 'ml-0' : '-ml-64'"
    >
      <div class="p-4 border-b border-gray-200 flex justify-between items-center bg-white">
        <el-button type="primary" plain class="w-full flex justify-start items-center gap-2" @click="startNewChat">
          <el-icon><Plus /></el-icon> 新的对话
        </el-button>
      </div>
      
      <div class="flex-1 overflow-y-auto p-3 custom-scrollbar space-y-6">
        <!-- 收藏的对话 -->
        <div v-if="favoriteConversations.length > 0">
          <div class="text-xs font-bold text-gray-400 mb-2 px-2 flex items-center gap-1">
            <el-icon><StarFilled /></el-icon> 收藏
          </div>
          <div class="space-y-1">
            <div 
              v-for="conv in favoriteConversations" 
              :key="conv.id"
              class="group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors"
              :class="currentConvId === conv.id ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-200'"
              @click="loadConversation(conv.id)"
            >
              <div class="flex items-center gap-2 overflow-hidden flex-1">
                <el-icon><ChatDotRound /></el-icon>
                <span class="truncate select-none" v-if="editingConvId !== conv.id">{{ conv.title }}</span>
                <el-input 
                  v-else 
                  v-model="editingTitle" 
                  size="small" 
                  class="flex-1"
                  @blur="saveTitle(conv)" 
                  @keyup.enter="saveTitle(conv)"
                  ref="editInputRef"
                  @click.stop
                />
              </div>
              <div class="hidden group-hover:flex items-center gap-1 shrink-0 ml-2" v-if="editingConvId !== conv.id">
                <el-icon class="hover:text-yellow-500" @click.stop="toggleFavorite(conv)"><StarFilled /></el-icon>
                <el-dropdown trigger="click" @command="(cmd: string) => handleConvCommand(cmd, conv)" @click.stop>
                  <el-icon class="hover:text-gray-800 outline-none"><MoreFilled /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit"><el-icon><EditPen /></el-icon> 重命名</el-dropdown-item>
                      <el-dropdown-item command="delete" class="text-red-500"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>

        <!-- 最近的对话 -->
        <div>
          <div class="text-xs font-bold text-gray-400 mb-2 px-2 flex items-center gap-1">
            <el-icon><Clock /></el-icon> 最近
          </div>
          <div class="space-y-1">
            <div 
              v-for="conv in recentConversations" 
              :key="conv.id"
              class="group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors"
              :class="currentConvId === conv.id ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-200'"
              @click="loadConversation(conv.id)"
            >
              <div class="flex items-center gap-2 overflow-hidden flex-1">
                <el-icon><ChatDotRound /></el-icon>
                <span class="truncate select-none" v-if="editingConvId !== conv.id">{{ conv.title }}</span>
                <el-input 
                  v-else 
                  v-model="editingTitle" 
                  size="small" 
                  class="flex-1"
                  @blur="saveTitle(conv)" 
                  @keyup.enter="saveTitle(conv)"
                  ref="editInputRef"
                  @click.stop
                />
              </div>
              <div class="hidden group-hover:flex items-center gap-1 shrink-0 ml-2" v-if="editingConvId !== conv.id">
                <el-icon class="hover:text-yellow-500" @click.stop="toggleFavorite(conv)"><Star /></el-icon>
                <el-dropdown trigger="click" @command="(cmd: string) => handleConvCommand(cmd, conv)" @click.stop>
                  <el-icon class="hover:text-gray-800 outline-none"><MoreFilled /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit"><el-icon><EditPen /></el-icon> 重命名</el-dropdown-item>
                      <el-dropdown-item command="delete" class="text-red-500"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-white relative min-w-0">
      <!-- Header -->
      <div class="w-full h-16 shrink-0 flex items-center justify-between px-6 border-b border-gray-100 bg-white/80 backdrop-blur-sm z-10 sticky top-0">
        <div class="flex items-center gap-3">
          <el-button text circle @click="isSidebarOpen = !isSidebarOpen" class="!text-gray-500 hover:!bg-gray-100">
            <el-icon size="20"><Expand v-if="!isSidebarOpen" /><Fold v-else /></el-icon>
          </el-button>
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md">
            <el-icon size="16"><ChatDotRound /></el-icon>
          </div>
          <div>
            <h2 class="text-base font-bold text-gray-800 leading-tight">
              {{ currentConvTitle || 'Insight 智能助理' }}
            </h2>
            <p class="text-xs text-gray-500" v-if="!currentConvId">连接所有原文、笔记与闪念胶囊的全局知识库</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <el-tooltip content="导出当前对话为 Markdown" placement="bottom">
            <el-button v-if="messages.length > 0" text circle @click="exportChat">
              <el-icon size="18"><Download /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <!-- Chat Message List -->
      <div class="flex-1 w-full overflow-y-auto p-6 custom-scrollbar" ref="chatScrollRef">
        <div class="max-w-4xl mx-auto space-y-6 pb-6">
          <div v-if="messages.length === 0" class="h-[60vh] flex flex-col items-center justify-center text-gray-400">
            <el-icon size="48" class="mb-4 text-indigo-100"><ChatLineSquare /></el-icon>
            <p class="text-lg font-medium text-gray-500">准备好探索你的知识库了吗？</p>
            <p class="text-sm mt-2">试着问我："最近我读过哪些关于大模型的论文？" 或 "总结一下我存的闪念胶囊"</p>
          </div>

          <div v-for="(msg, index) in messages" :key="index" class="flex gap-4 group" :class="{'flex-row-reverse': msg.role === 'user'}">
            <!-- Avatar -->
            <div class="w-8 h-8 shrink-0 rounded-full flex items-center justify-center mt-1"
                 :class="msg.role === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-indigo-100 text-indigo-600'">
              <el-icon><User v-if="msg.role === 'user'" /><Cpu v-else /></el-icon>
            </div>
            
            <!-- Bubble and Actions -->
            <div class="flex flex-col gap-1 max-w-[80%]" :class="{'items-end': msg.role === 'user'}">
              
              <!-- Editing Mode -->
              <div v-if="editingMsgIndex === index && msg.role === 'user'" class="w-full min-w-[300px] sm:min-w-[400px] bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <el-input
                  v-model="editMsgContent"
                  type="textarea"
                  :autosize="{ minRows: 2, maxRows: 6 }"
                  placeholder="编辑消息..."
                  class="mb-3"
                />
                <div class="flex justify-end gap-2">
                  <el-button size="small" @click="cancelEditMsg">取消</el-button>
                  <el-button type="primary" size="small" @click="saveAndResendMsg(index)">发送并重新生成</el-button>
                </div>
              </div>
              
              <!-- Normal Bubble -->
              <div v-else class="rounded-2xl px-5 py-3 shadow-sm relative"
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
              
              <!-- Action Buttons -->
              <div v-if="editingMsgIndex !== index" class="flex items-center gap-2 mt-1 text-gray-400 transition-opacity" :class="{'flex-row-reverse': msg.role === 'user', 'opacity-50': isTyping}">
                <el-tooltip v-if="msg.role === 'user' && !isTyping" content="编辑并重发" placement="bottom">
                  <el-button text circle size="small" @click="startEditMsg(index)" class="hover:text-indigo-600">
                    <el-icon><EditPen /></el-icon>
                  </el-button>
                </el-tooltip>
                
                <el-tooltip v-if="msg.role === 'assistant' && index === messages.length - 1 && !isTyping" content="重新生成" placement="bottom">
                  <el-button text circle size="small" @click="regenerateMsg" class="hover:text-indigo-600">
                    <el-icon><RefreshRight /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </div>
          
          <div v-if="isTyping" class="flex gap-4">
            <div class="w-8 h-8 shrink-0 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mt-1">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
            <div class="bg-gray-50 border border-gray-100 rounded-2xl rounded-tl-sm px-5 py-3 text-gray-500 text-sm flex flex-col gap-3 shadow-sm items-start">
              <div class="flex items-center gap-2">正在思考检索知识库...</div>
              <el-button size="small" type="danger" plain @click="stopGeneration">
                <el-icon class="mr-1"><VideoPause /></el-icon> 停止生成
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="w-full shrink-0 bg-white p-4 pt-0 relative">
        <div class="max-w-4xl mx-auto relative shadow-sm rounded-xl border border-gray-200 bg-white overflow-hidden transition-shadow focus-within:shadow-md focus-within:border-indigo-300">
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated, nextTick } from 'vue'
import { ChatDotRound, ChatLineSquare, User, Cpu, Plus, Top, Loading, Link, Paperclip, Picture, Document, Close, Expand, Fold, Star, StarFilled, MoreFilled, EditPen, Delete, Clock, Download, RefreshRight, VideoPause } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

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

interface Conversation {
  id: number
  title: string
  is_favorite: boolean
  dify_conversation_id: string
  updated_at: string
}

const isSidebarOpen = ref(true)
const conversations = ref<Conversation[]>([])
const currentConvId = ref<number | null>(null)
const currentConvTitle = ref('')
const difyConversationId = ref('')

const messages = ref<Message[]>([])
const userInput = ref('')
const isTyping = ref(false)
const isUploading = ref(false)
const uploadedFiles = ref<{id: string, type: string, name: string}[]>([])
const chatScrollRef = ref<HTMLElement | null>(null)

// 用于控制流式请求的中断
let abortController: AbortController | null = null

// 编辑相关 (Conversation Title)
const editingConvId = ref<number | null>(null)
const editingTitle = ref('')
const editInputRef = ref<any>(null)

// 消息编辑与重发相关
const editingMsgIndex = ref<number | null>(null)
const editMsgContent = ref('')

const favoriteConversations = computed(() => conversations.value.filter(c => c.is_favorite))
const recentConversations = computed(() => conversations.value.filter(c => !c.is_favorite))

const CURRENT_CONV_KEY = 'ig_current_global_chat_id'

// 定义组件名，供 keep-alive 使用
defineOptions({
  name: 'GlobalChatView'
})

onMounted(() => {
  initConversation()
})

onActivated(() => {
  // 从其他页面切换回来时，确保列表最新
  fetchConversations()
})

const initConversation = () => {
  fetchConversations().then(() => {
    // 恢复刷新前的对话状态
    const savedId = localStorage.getItem(CURRENT_CONV_KEY)
    if (savedId) {
      const id = parseInt(savedId, 10)
      // 确认这个 id 还在列表中（未被删除）
      if (conversations.value.some(c => c.id === id)) {
        loadConversation(id)
      } else {
        localStorage.removeItem(CURRENT_CONV_KEY)
      }
    }
  })
}

const fetchConversations = async () => {
  try {
    const res = await axios.get(`${API_BASE}/global-chat/conversations`)
    conversations.value = res.data
  } catch (error) {
    console.error('Failed to load conversations', error)
  }
}

const loadConversation = async (id: number) => {
  if (currentConvId.value === id) return
  
  // 切换对话时，如果有正在进行的请求，则中止它
  if (abortController) {
    abortController.abort()
    abortController = null
    isTyping.value = false
  }
  
  try {
    const res = await axios.get(`${API_BASE}/global-chat/conversations/${id}`)
    currentConvId.value = res.data.id
    currentConvTitle.value = res.data.title
    difyConversationId.value = res.data.dify_conversation_id || ''
    messages.value = res.data.history || []
    
    // 保存到 localStorage
    localStorage.setItem(CURRENT_CONV_KEY, res.data.id.toString())
    
    scrollToBottom()
  } catch (error) {
    ElMessage.error('加载对话失败')
  }
}

const startNewChat = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
    isTyping.value = false
  }

  currentConvId.value = null
  currentConvTitle.value = ''
  difyConversationId.value = ''
  messages.value = []
  userInput.value = ''
  localStorage.removeItem(CURRENT_CONV_KEY)
}

const syncConversation = async () => {
  if (!currentConvId.value) {
    // Create new
    try {
      const title = messages.value[0].content.substring(0, 20) + '...'
      const res = await axios.post(`${API_BASE}/global-chat/conversations`, {
        title: title,
        dify_conversation_id: difyConversationId.value,
        history: messages.value
      })
      currentConvId.value = res.data.id
      currentConvTitle.value = res.data.title
      
      // 保存新对话 ID 到 localStorage
      localStorage.setItem(CURRENT_CONV_KEY, res.data.id.toString())
      
      await fetchConversations()
      return // 创建时已经带了 history，不再需要后面的 PUT 请求
    } catch (e) {
      console.error(e)
      return
    }
  }
  
  // Update history
  try {
    await axios.put(`${API_BASE}/global-chat/conversations/${currentConvId.value}`, {
      history: messages.value,
      dify_conversation_id: difyConversationId.value
    })
  } catch (e) {
    console.error('Failed to sync history', e)
  }
}

const handleConvCommand = async (cmd: string, conv: Conversation) => {
  if (cmd === 'edit') {
    editingConvId.value = conv.id
    editingTitle.value = conv.title
    nextTick(() => {
      if (editInputRef.value && editInputRef.value[0]) {
        editInputRef.value[0].focus()
      }
    })
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm('确定要删除这条对话吗？此操作不可恢复。', '警告', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      })
      await axios.delete(`${API_BASE}/global-chat/conversations/${conv.id}`)
      ElMessage.success('已删除')
      if (currentConvId.value === conv.id) {
        startNewChat()
      }
      await fetchConversations()
    } catch (e) {
      // cancelled or error
    }
  }
}

const saveTitle = async (conv: Conversation) => {
  if (!editingConvId.value) return
  const newTitle = editingTitle.value.trim() || '未命名对话'
  try {
    await axios.put(`${API_BASE}/global-chat/conversations/${conv.id}`, { title: newTitle })
    conv.title = newTitle
    if (currentConvId.value === conv.id) {
      currentConvTitle.value = newTitle
    }
  } catch (e) {
    ElMessage.error('重命名失败')
  } finally {
    editingConvId.value = null
  }
}

const toggleFavorite = async (conv: Conversation) => {
  try {
    await axios.put(`${API_BASE}/global-chat/conversations/${conv.id}`, { is_favorite: !conv.is_favorite })
    conv.is_favorite = !conv.is_favorite
    ElMessage.success(conv.is_favorite ? '已收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const exportChat = () => {
  if (messages.value.length === 0) return
  
  let mdContent = `# 全局对话记录：${currentConvTitle.value || '未命名'}\n\n`
  messages.value.forEach(msg => {
    mdContent += `### ${msg.role === 'user' ? '🧑‍💻 我' : '🤖 Insight 智能助理'}\n${msg.content}\n\n---\n\n`
  })
  
  const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `对话_${currentConvTitle.value || '导出'}.md`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// ... upload and file handling
const beforeUpload = () => { isUploading.value = true; return true }
const handleUploadSuccess = (response: any, file: any) => {
  isUploading.value = false
  if (response.status === 'success') {
    uploadedFiles.value.push({ id: response.file_id, type: response.type, name: response.name || file.name })
  } else { ElMessage.error(response.message || '文件上传失败') }
}
const handleUploadError = (_error: any, file: any) => {
  isUploading.value = false
  ElMessage.error(`文件 ${file.name} 上传失败`)
}
const removeFile = (index: number) => { uploadedFiles.value.splice(index, 1) }

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
          const res = await axios.post(`${API_BASE}/chat/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
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

const stopGeneration = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
    isTyping.value = false
    const lastMsgIndex = messages.value.length - 1
    if (messages.value[lastMsgIndex] && messages.value[lastMsgIndex].role === 'assistant') {
      messages.value[lastMsgIndex].content += '\n\n**[已停止生成]**'
      syncConversation()
    }
  }
}

const startEditMsg = (index: number) => {
  editingMsgIndex.value = index
  editMsgContent.value = messages.value[index].content
}

const cancelEditMsg = () => {
  editingMsgIndex.value = null
  editMsgContent.value = ''
}

const saveAndResendMsg = async (index: number) => {
  if (!editMsgContent.value.trim() || isTyping.value) return
  
  // Truncate messages up to the edited one (exclusive)
  messages.value = messages.value.slice(0, index)
  
  userInput.value = editMsgContent.value.trim()
  editingMsgIndex.value = null
  editMsgContent.value = ''
  
  await sendMessage()
}

const regenerateMsg = async () => {
  if (isTyping.value || messages.value.length < 2) return
  
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg.role === 'assistant') {
    messages.value.pop()
  }
  
  const lastUserMsg = messages.value.pop()
  if (lastUserMsg) {
    // If the message contains file references, extract them (mock logic, for text we just pass text)
    // Actually, simple text regenerate is enough for now
    userInput.value = lastUserMsg.content
    await sendMessage()
  }
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isTyping.value) return
  
  const query = userInput.value.trim()
  const filesToUpload = uploadedFiles.value.map(f => ({
    type: f.type,
    transfer_method: 'local_file',
    upload_file_id: f.id
  }))
  
  let userDisplayContent = query
  if (uploadedFiles.value.length > 0) {
    const fileNames = uploadedFiles.value.map(f => `📎 ${f.name}`).join('\n')
    userDisplayContent = `${fileNames}\n\n${query}`
  }
  
  messages.value.push({ role: 'user', content: userDisplayContent })
  userInput.value = ''
  uploadedFiles.value = []
  isTyping.value = true
  scrollToBottom()

  // 核心修复1：用户发完消息立刻同步到数据库，确保历史记录先落库，不会因为切换而丢失
  await syncConversation()

  messages.value.push({ role: 'assistant', content: '', citations: [] })
  const currentMsgIndex = messages.value.length - 1

  // 初始化 AbortController 用于随时中断请求
  abortController = new AbortController()

  try {
    const response = await fetch(`${API_BASE}/chat/global`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        conversation_id: difyConversationId.value,
        files: filesToUpload
      }),
      signal: abortController.signal
    })

    if (!response.body) throw new Error('No response body')
    isTyping.value = false
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (!dataStr) continue
          
          try {
            const data = JSON.parse(dataStr)
            if (data.event === 'message') {
              // 核心修复2：如果用户已经点击了新对话清空了消息，此时必须立刻跳出循环，防止数组越界报错
              if (!messages.value[currentMsgIndex]) {
                if (abortController) {
                  abortController.abort()
                  abortController = null
                }
                return
              }
              messages.value[currentMsgIndex].content += data.answer
              if (data.conversation_id && !difyConversationId.value) {
                difyConversationId.value = data.conversation_id
              }
              scrollToBottom()
            } 
            else if (data.event === 'message_end') {
              if (data.metadata && data.metadata.retriever_resources) {
                const resources = data.metadata.retriever_resources
                const uniqueCitations = new Map()
                resources.forEach((r: any) => {
                  if (r.document_name && !uniqueCitations.has(r.document_name)) {
                    uniqueCitations.set(r.document_name, { title: r.document_name, dataset_id: r.dataset_id })
                  }
                })
                if (messages.value[currentMsgIndex]) {
                  messages.value[currentMsgIndex].citations = Array.from(uniqueCitations.values())
                }
              }
            }
            else if (data.event === 'error') {
              if (messages.value[currentMsgIndex]) {
                messages.value[currentMsgIndex].content += `\n\n**[Error]**: ${data.message}`
              }
            }
          } catch (e) {}
        }
      }
    }
    
    // 核心修复3：AI 回答完毕后，再次同步，把完整的回答更新到数据库
    // 并且如果发现用户已经切换了对话（messages 数组被清空），则不再执行同步，防止串台
    if (messages.value.length > currentMsgIndex) {
      await syncConversation()
    }
    
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('Chat request was aborted')
    } else {
      console.error('Chat error:', error)
      if (messages.value[currentMsgIndex]) {
        messages.value[currentMsgIndex].content += '\n\n**[网络错误]**: 无法连接到全局对话服务。'
      }
    }
  } finally {
    isTyping.value = false
    abortController = null
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
