<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { EditPen, Refresh, TopRight, Check, Download, Document, DocumentCopy, Reading, ChatDotRound, Position, Warning, FullScreen, DataLine, Close, ArrowUp, ArrowDown, Delete, DocumentAdd, MoreFilled } from '@element-plus/icons-vue'

const API_BASE = '/api'

interface FeedItem {
  id: number
  source: string
  title: string
  content: string
  url: string
  raw_data?: any
  is_saved_to_kb: boolean
  skim_summary?: string
  full_text?: string
  translated_pdf_url?: string
  translated_pdf_url_mono?: string
  created_at: string
}

const feeds = ref<FeedItem[]>([])
const loading = ref(false)
const activeTab = ref('all')

const skimDialogVisible = ref(false)
const skimLoading = ref(false)
const currentSkimFeed = ref<FeedItem | null>(null)
const currentSkimSummary = ref<string>('')

// 精读模式状态
const deepReadDrawerVisible = ref(false)
const currentDeepFeed = ref<FeedItem | null>(null)
const chatInput = ref('')
const chatLoading = ref(false)
const conversationId = ref('')
// 默认开启翻译
const translating = ref(false)
const translatedContent = ref('')
const translatedPdfUrl = ref('')
const translatedPdfUrlMono = ref('')
const deepLayoutMode = ref<'split' | 'full'>('split')
const isChatFloatingVisible = ref(false)
const readingViewType = ref<string>('translation')
const isHeaderCollapsed = ref(false)

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  saved?: boolean
}
const chatMessages = ref<ChatMessage[]>([])

const quickNoteContent = ref('')
const savingNote = ref(false)

const saveQuickNote = async () => {
  if (!quickNoteContent.value.trim()) return
  
  savingNote.value = true
  try {
    const title = `[胶囊] ${quickNoteContent.value.slice(0, 15)}...`
    await axios.post(`${API_BASE}/knowledge/save`, {
      title: title,
      content: quickNoteContent.value,
      kb_type: 'capsule'
    })
    
    ElMessage.success('闪念胶囊已存入知识库')
    quickNoteContent.value = ''
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingNote.value = false
  }
}

const fetchFeeds = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/feed/list`)
    feeds.value = res.data
  } catch (error) {
    ElMessage.error('获取资讯失败，请检查后端是否启动')
  } finally {
    loading.value = false
  }
}

const saveToKb = async (feed: FeedItem) => {
  if (feed.is_saved_to_kb) return
  
  try {
    const res = await axios.post(`${API_BASE}/feed/${feed.id}/save_to_kb`)
    if (res.data.status === 'processing' || res.data.status === 'success') {
      ElMessage.success('已加入知识库队列')
      feed.is_saved_to_kb = true
    }
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

const getSourceTagType = (source: string) => {
  if (source.toLowerCase() === 'github') return 'success'
  if (source.toLowerCase() === 'arxiv') return 'warning'
  return 'info'
}

const getKeywords = (feed: FeedItem): string[] => {
  const keywords: string[] = []
  if (!feed.raw_data) return keywords
  
  // Extract topics/keywords depending on the source
  if (feed.source.toLowerCase() === 'github' && Array.isArray(feed.raw_data.topics)) {
    keywords.push(...feed.raw_data.topics)
  } else if (feed.source.toLowerCase() === 'arxiv') {
    if (feed.raw_data.categories) {
      const cats = typeof feed.raw_data.categories === 'string' 
        ? feed.raw_data.categories.split(',') 
        : feed.raw_data.categories
      if (Array.isArray(cats)) keywords.push(...cats)
    }
    if (feed.raw_data.keywords) {
      const kw = typeof feed.raw_data.keywords === 'string'
        ? feed.raw_data.keywords.split(',')
        : feed.raw_data.keywords
      if (Array.isArray(kw)) keywords.push(...kw)
    }
  }
  return keywords.map(k => k.trim()).filter(k => k)
}

const getKeywordTagType = (index: number) => {
  const types = ['primary', 'success', 'info', 'warning', 'danger']
  return types[index % types.length]
}

const filteredFeeds = computed(() => {
  if (activeTab.value === 'all') return feeds.value
  return feeds.value.filter(feed => feed.source.toLowerCase() === activeTab.value)
})

const openSkimDialog = async (feed: FeedItem, forceRegenerate: boolean = false) => {
  currentSkimFeed.value = feed
  skimDialogVisible.value = true
  
  if (!forceRegenerate && feed.skim_summary) {
    currentSkimSummary.value = feed.skim_summary
    skimLoading.value = false
    // 已经有缓存，直接展示，不发起请求
    return
  }
  
  currentSkimSummary.value = ''
  skimLoading.value = true
  
  try {
    const res = await axios.post(`${API_BASE}/reader/skim?feed_id=${feed.id}&force_regenerate=${forceRegenerate}`)
    if (res.data.status === 'success') {
      currentSkimSummary.value = res.data.summary
      // 更新本地状态，以便下一次打开时知道已经有缓存
      feed.skim_summary = res.data.summary
      if (res.data.cached && !forceRegenerate) {
        ElMessage.success('已加载历史泛读总结')
      }
    }
  } catch (error) {
    ElMessage.error('获取泛读总结失败')
    if (!currentSkimSummary.value) {
      currentSkimSummary.value = '大模型服务暂不可用或接口报错。'
    }
  } finally {
    skimLoading.value = false
  }
}

const saveSkimSummaryToKb = async () => {
  if (!currentSkimFeed.value || !currentSkimSummary.value) return
  
  try {
    const title = `[泛读] ${currentSkimFeed.value.title}`
    const content = `# ${title}\n\n## 泛读总结\n${currentSkimSummary.value}\n\n## 原文内容\n${currentSkimFeed.value.content}\n\nSource URL: ${currentSkimFeed.value.url || 'None'}`
    
    await axios.post(`${API_BASE}/knowledge/save`, {
      title: title,
      content: content,
      kb_type: 'skim',
      ref_id: currentSkimFeed.value.id
    })
    
    ElMessage.success('笔记已成功发送至知识库队列')
    skimDialogVisible.value = false
  } catch (error) {
    ElMessage.error('保存笔记失败')
  }
}

// ==================== 精读模式逻辑 ====================
const syncChatHistory = async () => {
  if (!currentDeepFeed.value) return
  try {
    await axios.post(`${API_BASE}/reader/feed/${currentDeepFeed.value.id}/chat_history`, {
      conversation_id: conversationId.value,
      history: chatMessages.value
    })
  } catch (e) {
    console.error('Failed to sync history', e)
  }
}

const toggleTranslation = async (forceRefresh = false) => {
  if ((readingViewType.value === 'translation' || readingViewType.value === 'translation_mono') && 
      (!translatedContent.value && !translatedPdfUrl.value && !translatedPdfUrlMono.value || forceRefresh) && 
      currentDeepFeed.value) {
    translating.value = true
    
    // 如果是强制刷新，先清空本地状态
    if (forceRefresh) {
      translatedPdfUrl.value = ''
      translatedPdfUrlMono.value = ''
      translatedContent.value = ''
      if (currentDeepFeed.value) {
        currentDeepFeed.value.translated_pdf_url = ''
        currentDeepFeed.value.translated_pdf_url_mono = ''
      }
    }
    
    try {
      const res = await axios.post(`${API_BASE}/reader/feed/${currentDeepFeed.value.id}/translate?force_refresh=${forceRefresh}`)
      if (res.data.status === 'success') {
        if (res.data.translated_pdf_url) {
          translatedPdfUrl.value = res.data.translated_pdf_url
          if (currentDeepFeed.value) {
            currentDeepFeed.value.translated_pdf_url = res.data.translated_pdf_url
          }
        }
        if (res.data.translated_pdf_url_mono) {
          translatedPdfUrlMono.value = res.data.translated_pdf_url_mono
          if (currentDeepFeed.value) {
            currentDeepFeed.value.translated_pdf_url_mono = res.data.translated_pdf_url_mono
          }
        }
        
        if (!res.data.translated_pdf_url && !res.data.translated_pdf_url_mono && res.data.translated_content) {
          translatedContent.value = res.data.translated_content
        }
      }
    } catch (e) {
      ElMessage.error('获取翻译失败')
      readingViewType.value = 'text' // 回退到原文
    } finally {
      translating.value = false
    }
  }
}

const handleViewTypeChange = async (val: string) => {
  if (val === 'translation' || val === 'translation_mono') {
    await toggleTranslation()
  }
}

const openDeepReadDrawer = async (feed: FeedItem) => {
  currentDeepFeed.value = feed
  chatMessages.value = []
  chatInput.value = ''
  conversationId.value = ''
  translatedContent.value = ''
  translatedPdfUrl.value = ''
  translatedPdfUrlMono.value = ''
  deepReadDrawerVisible.value = true
  deepLayoutMode.value = 'split'
  isChatFloatingVisible.value = false
  
  // 默认视图逻辑：如果是 arxiv 且有链接则默认看 PDF，否则看翻译
  if (feed.source === 'arxiv' && feed.url) {
    readingViewType.value = 'pdf'
  } else {
    readingViewType.value = 'translation'
  }
  
  // 恢复状态
  isHeaderCollapsed.value = false
  
  try {
    const res = await axios.get(`${API_BASE}/reader/feed/${feed.id}/deep_read`)
    if (res.data.status === 'success') {
      if (res.data.deep_chat_history && res.data.deep_chat_history.length > 0) {
        chatMessages.value = res.data.deep_chat_history
        conversationId.value = res.data.deep_conversation_id
      } else {
        chatMessages.value.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: `你好！我是针对《${feed.title}》的精读助手。你可以随时向我提问关于这篇文档的任何问题。`
        })
      }
      
      if (res.data.translated_pdf_url) {
        translatedPdfUrl.value = res.data.translated_pdf_url
      }
      if (res.data.translated_pdf_url_mono) {
        translatedPdfUrlMono.value = res.data.translated_pdf_url_mono
      }
      if (res.data.translated_content) {
        translatedContent.value = res.data.translated_content
      }
      
      if (!translatedPdfUrl.value && !translatedPdfUrlMono.value && !translatedContent.value && (readingViewType.value === 'translation' || readingViewType.value === 'translation_mono')) {
        // 如果没有缓存翻译且默认打开翻译开关，则自动触发翻译请求
        await toggleTranslation()
      }
      
      // 更新全文本
      if (res.data.full_text) {
        feed.full_text = res.data.full_text
      }
    }
  } catch (e) {
    // 接口报错 fallback
    chatMessages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: `你好！我是针对《${feed.title}》的精读助手。你可以随时向我提问关于这篇文档的任何问题。`
    })
  }
}

const sendChatMessage = async (presetQuery?: string) => {
  const userMsg = typeof presetQuery === 'string' ? presetQuery : chatInput.value.trim()
  if (!userMsg || !currentDeepFeed.value || chatLoading.value) return
  
  if (typeof presetQuery !== 'string') {
    chatInput.value = ''
    chatMessages.value.push({
      id: Date.now().toString() + '_user',
      role: 'user',
      content: userMsg
    })
  }
  
  chatLoading.value = true
  try {
    const payload = {
      feed_id: currentDeepFeed.value.id,
      query: userMsg,
      conversation_id: conversationId.value || null
    }
    
    const res = await axios.post(`${API_BASE}/reader/chat`, payload)
    if (res.data.status === 'success') {
      chatMessages.value.push({
        id: Date.now().toString() + '_assistant',
        role: 'assistant',
        content: res.data.answer,
        saved: false
      })
      if (res.data.conversation_id) {
        conversationId.value = res.data.conversation_id
      }
      await syncChatHistory()
    }
  } catch (error) {
    chatMessages.value.push({
      id: Date.now().toString() + '_error',
      role: 'assistant',
      content: '❌ 对话请求失败，请检查后端或大模型服务状态。'
    })
  } finally {
    chatLoading.value = false
  }
}

const deleteChatMessage = async (msgId: string) => {
  chatMessages.value = chatMessages.value.filter(m => m.id !== msgId)
  await syncChatHistory()
  ElMessage.success('消息已删除')
}

const regenerateResponse = async (msgId: string) => {
  const index = chatMessages.value.findIndex(m => m.id === msgId)
  if (index === -1) return
  
  let userMsg = ''
  for (let i = index - 1; i >= 0; i--) {
    if (chatMessages.value[i].role === 'user') {
      userMsg = chatMessages.value[i].content
      break
    }
  }
  
  if (!userMsg) {
    ElMessage.warning('找不到对应的用户提问')
    return
  }
  
  chatMessages.value.splice(index, 1)
  await sendChatMessage(userMsg)
}

const clearAllChatHistory = () => {
  if (!currentDeepFeed.value) return
  chatMessages.value = [{
    id: Date.now().toString(),
    role: 'assistant',
    content: `你好！我是针对《${currentDeepFeed.value.title}》的精读助手。你可以随时向我提问关于这篇文档的任何问题。`
  }]
  conversationId.value = ''
  syncChatHistory().then(() => {
    ElMessage.success('聊天记录已清空')
  })
}

const exportChatHistory = () => {
  if (!currentDeepFeed.value || chatMessages.value.length === 0) return
  
  let mdContent = `# 精读对话记录：${currentDeepFeed.value.title}\n\n`
  chatMessages.value.forEach(msg => {
    if (msg.role === 'assistant' && msg.content.includes('你好！我是针对')) return
    mdContent += `### ${msg.role === 'user' ? '🧑‍💻 我' : '🤖 精读助手'}\n${msg.content}\n\n---\n\n`
  })
  
  const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `精读记录_${currentDeepFeed.value.title.slice(0, 15)}.md`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const batchSaveChatToKb = async () => {
  if (!currentDeepFeed.value) return
  
  const assistantMsgs = chatMessages.value.filter(m => m.role === 'assistant' && !m.content.includes('你好！我是针对') && !m.saved)
  if (assistantMsgs.length === 0) {
    ElMessage.info('没有新的助手消息需要保存')
    return
  }
  
  const loading = ElMessage({
    message: '正在批量存入精读知识库...',
    type: 'info',
    duration: 0
  })
  
  try {
    let combinedContent = `针对《${currentDeepFeed.value.title}》的精读对话合集：\n\n`
    assistantMsgs.forEach((msg, idx) => {
      combinedContent += `**AI 回答 ${idx + 1}：**\n${msg.content}\n\n---\n\n`
    })
    
    const title = `[精读合集] ${currentDeepFeed.value.title.slice(0, 30)}...`
    
    await axios.post(`${API_BASE}/knowledge/save`, {
      title: title,
      content: combinedContent,
      kb_type: 'deep',
      source_url: currentDeepFeed.value.url
    })
    
    assistantMsgs.forEach(msg => { msg.saved = true })
    await syncChatHistory()
    
    loading.close()
    ElMessage.success('批量入库成功！')
  } catch (error) {
    loading.close()
    ElMessage.error('批量入库失败')
  }
}

const saveChatMsgToKb = async (msg: ChatMessage) => {
  if (!currentDeepFeed.value || msg.saved) return
  
  try {
    const title = `[精读问答] ${currentDeepFeed.value.title.slice(0, 30)}...`
    const content = `针对《${currentDeepFeed.value.title}》的精读对话：\n\n**AI回答：**\n${msg.content}`
    
    await axios.post(`${API_BASE}/knowledge/save`, {
      title: title,
      content: content,
      kb_type: 'deep',
      ref_id: currentDeepFeed.value.id
    })
    
    msg.saved = true
    ElMessage.success('问答已存入知识库')
  } catch (error) {
    ElMessage.error('保存问答失败')
  }
}

onMounted(() => {
  fetchFeeds()
})
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- 快捷录入区 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
      <h3 class="text-lg font-medium text-gray-800 mb-4 flex items-center gap-2">
        <el-icon><EditPen /></el-icon> 闪念胶囊 (Quick Note)
      </h3>
      <el-input
        v-model="quickNoteContent"
        type="textarea"
        :rows="3"
        placeholder="记录下刚才的灵感或碎片知识，一键送入知识库..."
        class="mb-4"
      />
      <div class="flex justify-end">
        <el-button type="primary" :disabled="!quickNoteContent.trim()" :loading="savingNote" @click="saveQuickNote">
          存入知识库
        </el-button>
      </div>
    </div>

    <!-- 资讯流 Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xl font-bold text-gray-800">今日资讯 (Feeds)</h3>
      <el-button :icon="Refresh" circle @click="fetchFeeds" :loading="loading" />
    </div>

    <!-- 分栏 / 分 Tab 展示区 -->
    <el-tabs v-model="activeTab" class="mb-6">
      <el-tab-pane label="全部 (All)" name="all" />
      <el-tab-pane label="arXiv 论文" name="arxiv" />
      <el-tab-pane label="GitHub 趋势" name="github" />
    </el-tabs>

    <el-skeleton :loading="loading" animated :count="3" class="space-y-4">
      <template #template>
        <div class="bg-white p-6 rounded-xl border border-gray-100 mb-4">
          <el-skeleton-item variant="h3" style="width: 50%" />
          <el-skeleton-item variant="text" style="width: 100%; margin-top: 16px" />
          <el-skeleton-item variant="text" style="width: 80%" />
        </div>
      </template>
      
      <template #default>
        <div v-if="filteredFeeds.length === 0" class="text-center py-12 text-gray-400">
          <el-empty description="暂无资讯，请检查抓取任务或切换分类" />
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div v-for="feed in filteredFeeds" :key="feed.id" 
               class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden transition-all hover:shadow-md flex flex-col">
            <div class="p-6 flex-1 flex flex-col">
              <div class="flex items-center justify-between mb-3">
                <el-tag :type="getSourceTagType(feed.source)" size="small" class="uppercase">
                  {{ feed.source }}
                </el-tag>
                <span class="text-xs text-gray-400">{{ formatDate(feed.created_at) }}</span>
              </div>
              
              <h4 class="text-lg font-bold text-gray-800 mb-3 line-clamp-2">
                <a v-if="feed.url" :href="feed.url" target="_blank" class="hover:text-blue-600 transition-colors">
                  {{ feed.title }}
                </a>
                <span v-else>{{ feed.title }}</span>
              </h4>

              <!-- 关键字 Tags -->
              <div v-if="getKeywords(feed).length > 0" class="flex flex-wrap gap-2 mb-3">
                <el-tag 
                  v-for="(kw, idx) in getKeywords(feed).slice(0, 6)" 
                  :key="idx" 
                  :type="getKeywordTagType(idx)" 
                  size="small" 
                  effect="light"
                  round>
                  {{ kw }}
                </el-tag>
                <el-tag v-if="getKeywords(feed).length > 6" type="info" size="small" round>...</el-tag>
              </div>
              
              <p class="text-gray-600 text-sm whitespace-pre-line leading-relaxed mb-6 flex-1 line-clamp-4">
                {{ feed.content }}
              </p>
              
              <div class="flex items-center justify-between pt-4 border-t border-gray-50 mt-auto">
                <a v-if="feed.url" :href="feed.url" target="_blank" class="text-sm text-blue-500 hover:underline flex items-center gap-1">
                  查看原文 <el-icon><TopRight /></el-icon>
                </a>
                <span v-else></span>
                
                <div class="flex gap-2">
                  <el-button 
                    type="primary" 
                    plain
                    size="small"
                    @click="openSkimDialog(feed)">
                    <template #icon><Document /></template>
                    AI 泛读
                  </el-button>

                  <el-button 
                    type="success" 
                    plain
                    size="small"
                    @click="openDeepReadDrawer(feed)">
                    <template #icon><Reading /></template>
                    精读模式
                  </el-button>

                  <el-button 
                    :type="feed.is_saved_to_kb ? 'info' : 'primary'" 
                    :plain="feed.is_saved_to_kb"
                    :disabled="feed.is_saved_to_kb"
                    size="small"
                    @click="saveToKb(feed)">
                    <template #icon>
                      <el-icon v-if="feed.is_saved_to_kb"><Check /></el-icon>
                      <el-icon v-else><Download /></el-icon>
                    </template>
                    {{ feed.is_saved_to_kb ? '原文已入库' : '原文入库' }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </el-skeleton>

    <!-- 泛读模式弹窗 -->
    <el-dialog
      v-model="skimDialogVisible"
      title="AI 泛读模式 (Skim Reading)"
      width="60%"
      destroy-on-close
    >
      <div v-if="currentSkimFeed" class="mb-4 pb-4 border-b border-gray-200">
        <h4 class="font-bold text-gray-800 text-lg mb-2">{{ currentSkimFeed.title }}</h4>
        <p class="text-gray-500 text-sm">来源: {{ currentSkimFeed.source.toUpperCase() }}</p>
      </div>
      
      <div v-loading="skimLoading" element-loading-text="大模型正在分析文章主旨要义..." class="min-h-[150px]">
        <div v-if="!skimLoading" class="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-line bg-gray-50 p-4 rounded-lg">
          {{ currentSkimSummary }}
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="skimDialogVisible = false">关闭</el-button>
          <el-button :disabled="skimLoading" @click="openSkimDialog(currentSkimFeed!, true)">重新生成</el-button>
          <el-button type="primary" :disabled="skimLoading || !currentSkimSummary" @click="saveSkimSummaryToKb">
            <el-icon class="mr-1"><DocumentCopy /></el-icon> 保存总结至知识库
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 精读模式全屏视图 -->
    <el-drawer
      v-model="deepReadDrawerVisible"
      size="100%"
      direction="rtl"
      :show-close="false"
      destroy-on-close
      class="deep-read-drawer"
    >
      <template #header>
        <div class="flex justify-between items-center w-full">
          <h4 class="font-bold text-gray-800 text-xl truncate flex-1 pr-4">
            <el-icon class="mr-2"><Reading /></el-icon>
            {{ currentDeepFeed?.title }}
          </h4>
          <div class="flex-shrink-0 flex gap-4 items-center mr-8">
            <el-radio-group v-model="deepLayoutMode" size="small">
              <el-radio-button label="split"><el-icon><DataLine /></el-icon> 左右分栏</el-radio-button>
              <el-radio-button label="full"><el-icon><FullScreen /></el-icon> 全屏沉浸</el-radio-button>
            </el-radio-group>
          </div>
          <el-button link @click="deepReadDrawerVisible = false" class="absolute right-4 top-4">
            <el-icon class="text-xl"><Close /></el-icon>
          </el-button>
        </div>
      </template>
      
      <div class="flex h-full -mt-5 -mx-5 relative overflow-hidden">
        <!-- 左侧：原文内容区 -->
        <div 
          class="p-6 overflow-y-auto bg-gray-50 flex flex-col transition-all duration-300"
          :class="deepLayoutMode === 'split' ? 'w-1/2 border-r border-gray-200' : 'w-full'"
        >
          <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-100 min-h-full flex flex-col relative">
            
            <!-- 可折叠的顶部信息区 -->
            <div class="transition-all duration-300 ease-in-out overflow-hidden" 
                 :class="isHeaderCollapsed ? 'max-h-0 opacity-0 mb-0 pb-0 border-0' : 'max-h-[300px] opacity-100 mb-6 pb-6 border-b border-gray-100'">
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <h1 class="text-2xl font-bold text-gray-900 mb-4">{{ currentDeepFeed?.title }}</h1>
                  <div class="flex items-center gap-3 text-sm text-gray-500">
                    <el-tag :type="getSourceTagType(currentDeepFeed?.source || '')" size="small" class="uppercase">
                      {{ currentDeepFeed?.source }}
                    </el-tag>
                    <span>发布于 {{ currentDeepFeed ? formatDate(currentDeepFeed.created_at) : '' }}</span>
                    <a v-if="currentDeepFeed?.url" :href="currentDeepFeed.url" target="_blank" class="text-blue-500 hover:underline flex items-center gap-1 ml-auto">
                      在原网站打开 <el-icon><TopRight /></el-icon>
                    </a>
                    <!-- 提供直接下载或在新标签页查看 PDF 的链接 -->
                    <a v-if="currentDeepFeed?.source === 'arxiv' && currentDeepFeed?.url" 
                       :href="currentDeepFeed.url.replace('abs', 'pdf') + '.pdf'" 
                       target="_blank" 
                       class="text-red-500 hover:underline flex items-center gap-1 ml-2">
                      <el-icon><Document /></el-icon> 在新标签页打开 PDF
                    </a>
                  </div>
                </div>
                <div class="flex-shrink-0 ml-4">
                  <el-radio-group v-model="readingViewType" size="small" @change="handleViewTypeChange">
                    <el-radio-button label="pdf" v-if="currentDeepFeed?.source === 'arxiv'">原版 PDF</el-radio-button>
                    <el-radio-button label="translation">双语对照翻译</el-radio-button>
                    <el-radio-button label="translation_mono">纯中文翻译</el-radio-button>
                    <el-radio-button label="text">提取的全文</el-radio-button>
                  </el-radio-group>
                  
                  <el-button 
                    v-if="readingViewType === 'translation' || readingViewType === 'translation_mono'"
                    class="ml-2"
                    size="small"
                    circle
                    :disabled="translating"
                    @click="toggleTranslation(true)"
                    title="重新翻译此文档"
                  >
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 折叠控制按钮 -->
            <div class="absolute right-8" :class="isHeaderCollapsed ? 'top-4' : 'top-[auto] mt-[-20px]'">
              <el-button 
                size="small" 
                circle
                class="shadow-sm border-gray-200"
                @click="isHeaderCollapsed = !isHeaderCollapsed"
                :title="isHeaderCollapsed ? '展开信息' : '折叠信息以扩大阅读区'"
              >
                <el-icon><ArrowDown v-if="isHeaderCollapsed"/><ArrowUp v-else/></el-icon>
              </el-button>
            </div>
            
            <!-- 内容展示区 -->
            <div class="flex-1 flex flex-col" :class="isHeaderCollapsed ? 'mt-4' : ''">
              <template v-if="readingViewType === 'pdf'">
                <iframe 
                  v-if="currentDeepFeed?.url"
                  :src="currentDeepFeed.url.replace('abs', 'pdf') + '.pdf'" 
                  class="w-full min-h-[600px] flex-1 border-0 rounded-md"
                ></iframe>
              </template>
              <template v-else-if="readingViewType === 'translation' || readingViewType === 'translation_mono'">
                <div v-if="translating" v-loading="translating" element-loading-text="正在为您翻译全文并保持原排版，这可能需要几分钟的时间，请耐心等待..." class="w-full min-h-[600px] flex items-center justify-center"></div>
                <iframe 
                  v-else-if="readingViewType === 'translation' && translatedPdfUrl"
                  :src="`http://localhost:8000${translatedPdfUrl}`" 
                  class="w-full min-h-[600px] flex-1 border-0 rounded-md"
                ></iframe>
                <iframe 
                  v-else-if="readingViewType === 'translation_mono' && translatedPdfUrlMono"
                  :src="`http://localhost:8000${translatedPdfUrlMono}`" 
                  class="w-full min-h-[600px] flex-1 border-0 rounded-md"
                ></iframe>
                <div v-else class="prose max-w-none text-gray-800 leading-relaxed whitespace-pre-wrap text-lg font-serif min-h-[200px]">
                  {{ translatedContent || '正在翻译中...' }}
                </div>
              </template>
              <template v-else>
                <div class="prose max-w-none text-gray-800 leading-relaxed whitespace-pre-wrap text-lg font-serif min-h-[200px]">
                  {{ currentDeepFeed?.full_text || currentDeepFeed?.content }}
                  <div v-if="!currentDeepFeed?.full_text && currentDeepFeed?.source === 'arxiv'" class="mt-4 p-4 bg-yellow-50 text-yellow-800 rounded-md text-sm">
                    <el-icon><Warning /></el-icon> 当前展示的仅为网页摘要。系统正在后台尝试抓取并解析 PDF 全文，请稍后再试或切换到原版 PDF 视图。
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- AI 对话交互区 (通过 class 切换 split 还是 float) -->
        <div 
          :class="[
            deepLayoutMode === 'split' 
              ? 'w-1/2 flex flex-col bg-white border-l border-gray-200' 
              : 'absolute bottom-6 right-6 w-[400px] h-[650px] max-h-[85vh] bg-white shadow-[0_10px_40px_-10px_rgba(0,0,0,0.3)] rounded-2xl flex flex-col z-50 border border-gray-200 overflow-hidden transition-all duration-300 transform',
            deepLayoutMode === 'full' && !isChatFloatingVisible ? 'translate-y-[120%] opacity-0 pointer-events-none' : 'translate-y-0 opacity-100'
          ]"
        >
          <!-- 悬浮窗 Header (仅全屏模式显示) -->
          <div v-if="deepLayoutMode === 'full'" class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50 flex-shrink-0">
            <div class="font-bold text-gray-700 flex items-center gap-2">
              <el-icon><ChatDotRound /></el-icon> 精读助手
            </div>
            <div class="flex items-center gap-2">
              <el-dropdown trigger="click">
                <el-button link type="info">
                  <el-icon class="text-lg"><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="batchSaveChatToKb"><el-icon><DocumentAdd /></el-icon> 批量入库</el-dropdown-item>
                    <el-dropdown-item @click="exportChatHistory"><el-icon><Download /></el-icon> 导出记录</el-dropdown-item>
                    <el-dropdown-item divided @click="clearAllChatHistory" class="text-red-500"><el-icon><Delete /></el-icon> 清空对话</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button link @click="isChatFloatingVisible = false">
                <el-icon class="text-xl"><Close /></el-icon>
              </el-button>
            </div>
          </div>
          
          <!-- 分栏模式的 Header -->
          <div v-if="deepLayoutMode === 'split'" class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50 flex-shrink-0">
            <div class="font-bold text-gray-700 flex items-center gap-2">
              <el-icon><ChatDotRound /></el-icon> 精读助手
            </div>
            <div class="flex items-center gap-2">
              <el-button size="small" @click="batchSaveChatToKb"><el-icon><DocumentAdd /></el-icon> 批量入库</el-button>
              <el-button size="small" @click="exportChatHistory"><el-icon><Download /></el-icon> 导出</el-button>
              <el-button size="small" type="danger" plain @click="clearAllChatHistory"><el-icon><Delete /></el-icon> 清空</el-button>
            </div>
          </div>

          <!-- 聊天记录区 -->
          <div class="flex-1 p-6 overflow-y-auto bg-gray-50">
            <div class="space-y-6">
              <div v-for="msg in chatMessages" :key="msg.id" 
                   class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                
                <div class="max-w-[85%] flex gap-3" :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'">
                  <!-- 头像 -->
                  <div class="flex-shrink-0">
                    <div v-if="msg.role === 'user'" class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white">
                      U
                    </div>
                    <div v-else class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white">
                      AI
                    </div>
                  </div>
                  
                  <!-- 消息内容 -->
                  <div class="flex flex-col" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
                    <div 
                      class="px-4 py-3 rounded-2xl shadow-sm"
                      :class="msg.role === 'user' ? 'bg-blue-500 text-white rounded-tr-sm' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'">
                      <div class="prose prose-sm max-w-none whitespace-pre-wrap" :class="msg.role === 'user' ? 'text-white' : ''">
                        {{ msg.content }}
                      </div>
                    </div>
                    
                    <!-- 消息操作按钮 -->
                    <div class="mt-2 flex items-center gap-2">
                      <template v-if="msg.role === 'assistant'">
                        <el-button 
                          size="small" 
                          text 
                          :type="msg.saved ? 'success' : 'primary'"
                          :disabled="msg.saved"
                          @click="saveChatMsgToKb(msg)">
                          <el-icon class="mr-1"><DocumentCopy /></el-icon>
                          {{ msg.saved ? '已存入知识库' : '存入精读库' }}
                        </el-button>
                        
                        <el-button 
                          size="small" 
                          text 
                          type="info"
                          @click="regenerateResponse(msg.id)">
                          <el-icon class="mr-1"><Refresh /></el-icon>
                          重新生成
                        </el-button>
                      </template>
                      
                      <el-button 
                        size="small" 
                        text 
                        type="danger"
                        class="!px-2"
                        @click="deleteChatMessage(msg.id)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Loading 状态 -->
              <div v-if="chatLoading" class="flex justify-start">
                <div class="flex gap-3">
                  <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white">AI</div>
                  <div class="px-4 py-3 bg-white border border-gray-200 rounded-2xl rounded-tl-sm shadow-sm text-gray-500 flex items-center gap-2">
                    <el-icon class="is-loading"><Refresh /></el-icon> 正在思考...
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入区 -->
          <div class="p-4 border-t border-gray-200 bg-white">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="3"
              placeholder="输入你的问题，按 Enter 键发送 (Shift+Enter 换行)..."
              resize="none"
              @keydown.enter.exact.prevent="sendChatMessage"
            />
            <div class="flex justify-between items-center mt-3">
              <span class="text-xs text-gray-400">💡 提示：将存入 DIFY_DATASET_DEEP_ID</span>
              <el-button type="primary" :disabled="!chatInput.trim() || chatLoading" @click="sendChatMessage">
                发送 <el-icon class="ml-1"><Position /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 悬浮唤醒按钮 (全屏模式下，且对话框被收起时显示) -->
        <div 
          v-if="deepLayoutMode === 'full'"
          class="absolute bottom-8 right-8 z-40 transition-all duration-300"
          :class="isChatFloatingVisible ? 'translate-y-[150%] opacity-0' : 'translate-y-0 opacity-100'"
        >
          <el-button type="primary" size="large" circle class="shadow-xl w-14 h-14" @click="isChatFloatingVisible = true">
            <el-icon class="text-2xl"><ChatDotRound /></el-icon>
          </el-button>
        </div>

      </div>
    </el-drawer>
  </div>
</template>

<style>
.deep-read-drawer .el-drawer__header {
  margin-bottom: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
}
.deep-read-drawer .el-drawer__body {
  padding: 20px;
  overflow: hidden;
}
</style>
