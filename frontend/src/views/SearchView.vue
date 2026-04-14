<template>
  <div class="h-full flex flex-col bg-app max-w-5xl mx-auto w-full">
    <!-- Search Header -->
    <div class="bg-card p-6 rounded-xl border border-border shadow-sm mb-6 shrink-0">
      <h2 class="text-2xl font-bold text-primary mb-4 flex items-center gap-2">
        <el-icon class="text-orange-500"><Search /></el-icon>
        主动文献检索
      </h2>
      <div class="flex gap-4">
        <el-input
          v-model="searchQuery"
          placeholder="输入研究方向或关键词 (例如: deep learning)..."
          size="large"
          clearable
          @keyup.enter="handleSearch"
          class="flex-1"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" size="large" :loading="isSearching" @click="handleSearch" class="px-8 font-bold">
          检索 arXiv
        </el-button>
      </div>
      <div class="flex items-center justify-between mt-3">
        <p class="text-xs text-secondary flex items-center gap-1">
          <el-icon><InfoFilled /></el-icon>
          支持双引号精确短语匹配 (如: "large language models" agent)。也可直接使用 arXiv API 高级语法 (如 au:bengio AND cat:cs.AI)
        </p>
        <div v-if="hasSearched && results.length > 0" class="flex items-center gap-2">
          <span class="text-xs text-secondary">结果排序:</span>
          <el-select v-model="sortBy" size="small" class="w-28" @change="sortResults">
            <el-option label="提交时间" value="submittedDate" />
            <el-option label="相关度" value="relevance" />
          </el-select>
          <el-select v-model="sortOrder" size="small" class="w-24" @change="sortResults">
            <el-option label="降序" value="descending" />
            <el-option label="升序" value="ascending" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- Search Results -->
    <div class="flex-1 overflow-auto custom-scrollbar pr-2 pb-6">
      <div v-if="!hasSearched" class="h-full flex flex-col items-center justify-center text-secondary">
        <el-icon :size="64" class="mb-4 opacity-20"><Trophy /></el-icon>
        <p>探索浩瀚学术星海</p>
      </div>
      
      <div v-else-if="results.length === 0 && !isSearching" class="text-center py-12">
        <el-empty description="没有找到相关的文献" />
      </div>

      <div v-else class="space-y-4">
        <el-card 
          v-for="(item, index) in results" 
          :key="index" 
          shadow="hover" 
          class="rounded-xl border border-border transition-shadow relative"
          :class="{'bg-app/50': item.is_imported}"
        >
          <div class="absolute left-4 top-4 z-10">
            <el-checkbox v-model="item.selected" size="large" />
          </div>
          
          <div class="flex justify-between items-start gap-4 pl-8">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <el-tag size="small" type="warning" effect="dark">arXiv</el-tag>
                <span class="text-xs text-secondary font-mono">{{ formatDate(item.published) }}</span>
              </div>
              <h3 class="text-lg font-bold text-primary leading-tight mb-2 hover:text-orange-600 transition-colors cursor-pointer">
                <a :href="item.url" target="_blank">{{ item.title }}</a>
              </h3>
              <p class="text-sm text-secondary mb-3 line-clamp-1 italic">
                <el-icon><User /></el-icon> {{ item.authors.join(', ') }}
              </p>
              <div class="text-sm text-secondary line-clamp-3 leading-relaxed">
                {{ item.summary }}
              </div>
            </div>
            
            <div class="shrink-0 flex flex-col items-end gap-2 w-32">
              <el-button 
                v-if="!item.is_imported" 
                type="primary" 
                plain 
                :loading="importingStates[item.url]"
                @click="importItem(item)"
                class="w-full"
              >
                <el-icon class="mr-1"><Download /></el-icon>
                加入知识库
              </el-button>
              
              <template v-else>
                <!-- 泛读按钮 -->
                <el-button 
                  type="success" 
                  plain 
                  class="w-full"
                  :disabled="!item.skim_summary"
                  @click="openSkimDialog(item)"
                >
                  <el-icon class="mr-1"><Document /></el-icon>
                  泛读摘要
                </el-button>
                
                <!-- 精读模式按钮 -->
                <el-button 
                  type="warning" 
                  plain 
                  @click="openDeepReadDrawer(item)"
                  class="w-full !ml-0"
                >
                  <el-icon class="mr-1"><Reading /></el-icon>
                  精读模式
                </el-button>
              </template>
              
              <el-tooltip content="在 arXiv 官网打开" placement="top">
                <a :href="item.url" target="_blank" class="text-secondary hover:text-orange-500 mt-2 inline-block p-2">
                  <el-icon :size="18"><TopRight /></el-icon>
                </a>
              </el-tooltip>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 加载更多按钮 -->
      <div v-if="results.length > 0" class="flex justify-center mt-6">
        <el-button 
          plain
          round
          size="large"
          class="w-48 text-secondary border-gray-300 hover:text-orange-500 hover:border-orange-500"
          :loading="isLoadingMore" 
          @click="loadMoreResults"
        >
          <el-icon class="mr-1"><Download /></el-icon>
          加载更多文献
        </el-button>
      </div>
    </div>
    
    <!-- 悬浮批量操作栏 -->
    <div v-if="selectedItems.length > 0" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-card/90 backdrop-blur-md px-6 py-4 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-border flex items-center gap-6 z-50 transition-all">
      <span class="text-secondary font-medium">已选择 <span class="text-orange-600 font-bold text-lg">{{ selectedItems.length }}</span> 篇文献</span>
      <div class="h-6 w-px bg-gray-300"></div>
      <el-button type="primary" size="large" :loading="isBatchImporting" @click="handleBatchImport" class="px-8 font-bold shadow-md shadow-orange-500/20">
        <el-icon class="mr-2"><Download /></el-icon>
        批量加入知识库
      </el-button>
      <el-button link @click="clearSelection" class="text-secondary hover:text-secondary">取消选择</el-button>
    </div>

    <!-- 泛读摘要弹窗 -->
    <el-dialog v-model="skimDialogVisible" title="🤖 AI 泛读摘要 (Key Takeaways)" width="50%" destroy-on-close>
      <div v-if="currentSkimContent" class="prose max-w-none text-gray-700 leading-relaxed text-sm bg-app p-6 rounded-lg border border-border" v-html="renderMarkdown(currentSkimContent)">
      </div>
      <div v-else class="flex flex-col items-center justify-center py-12 text-secondary">
        <el-icon class="is-loading text-4xl mb-4 text-blue-400"><Loading /></el-icon>
        <p>大模型正在后台努力阅读并生成摘要，请稍候再来看...</p>
      </div>
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
          <h4 class="font-bold text-primary text-xl truncate flex-1 pr-4">
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
          class="p-6 overflow-y-auto bg-app flex flex-col transition-all duration-300"
          :class="deepLayoutMode === 'split' ? 'w-1/2 border-r border-border' : 'w-full'"
        >
          <div class="bg-card p-8 rounded-xl shadow-sm border border-border min-h-full flex flex-col relative">
            
            <!-- 可折叠的顶部信息区 -->
            <div class="transition-all duration-300 ease-in-out overflow-hidden" 
                 :class="isHeaderCollapsed ? 'max-h-0 opacity-0 mb-0 pb-0 border-0' : 'max-h-[300px] opacity-100 mb-6 pb-6 border-b border-border'">
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <h1 class="text-2xl font-bold text-primary mb-4">{{ currentDeepFeed?.title }}</h1>
                  <div class="flex items-center gap-3 text-sm text-secondary">
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
                class="shadow-sm border-border"
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
                <div v-else class="prose max-w-none text-primary leading-relaxed whitespace-pre-wrap text-lg font-serif min-h-[200px]">
                  {{ translatedContent || '正在翻译中...' }}
                </div>
              </template>
              <template v-else>
                <div class="prose max-w-none text-primary leading-relaxed whitespace-pre-wrap text-lg font-serif min-h-[200px]">
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
              ? 'w-1/2 flex flex-col bg-card border-l border-border' 
              : 'absolute bottom-6 right-6 w-[400px] h-[650px] max-h-[85vh] bg-card shadow-[0_10px_40px_-10px_rgba(0,0,0,0.3)] rounded-2xl flex flex-col z-50 border border-border overflow-hidden transition-all duration-300 transform',
            deepLayoutMode === 'full' && !isChatFloatingVisible ? 'translate-y-[120%] opacity-0 pointer-events-none' : 'translate-y-0 opacity-100'
          ]"
        >
          <!-- 悬浮窗 Header (仅全屏模式显示) -->
          <div v-if="deepLayoutMode === 'full'" class="flex justify-between items-center p-4 border-b border-border bg-app flex-shrink-0">
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
          <div v-if="deepLayoutMode === 'split'" class="flex justify-between items-center p-4 border-b border-border bg-app flex-shrink-0">
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
          <div class="flex-1 p-6 overflow-y-auto bg-app">
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
                      :class="msg.role === 'user' ? 'bg-blue-500 text-white rounded-tr-sm' : 'bg-card border border-border text-primary rounded-tl-sm'">
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
                  <div class="px-4 py-3 bg-card border border-border rounded-2xl rounded-tl-sm shadow-sm text-secondary flex items-center gap-2">
                    <el-icon class="is-loading"><Refresh /></el-icon> 正在思考...
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入区 -->
          <div class="p-4 border-t border-border bg-card">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="3"
              placeholder="输入你的问题，按 Enter 键发送 (Shift+Enter 换行)..."
              resize="none"
              @keydown.enter.exact.prevent="sendChatMessage"
            />
            <div class="flex justify-between items-center mt-3">
              <span class="text-xs text-secondary">💡 提示：将存入 DIFY_DATASET_DEEP_ID</span>
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

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, InfoFilled, Trophy, Download, User, TopRight, Document, DataLine, Loading, Reading, Close, FullScreen, ArrowDown, ArrowUp, Refresh, Warning, ChatDotRound, MoreFilled, DocumentAdd, Delete, DocumentCopy, Position } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const API_BASE = 'http://localhost:8000/api'

const searchQuery = ref('')
const sortBy = ref('relevance')
const sortOrder = ref('descending')
const isSearching = ref(false)
const isLoadingMore = ref(false)
const currentStart = ref(0)
const hasSearched = ref(false)
const results = ref<any[]>([])

// 记录各个条目的入库 Loading 状态，key 为 URL
const importingStates = ref<Record<string, boolean>>({})
const isBatchImporting = ref(false)

// 泛读弹窗相关
const skimDialogVisible = ref(false)
const currentSkimContent = ref('')

// 精读弹窗相关
const deepReadDrawerVisible = ref(false)
const currentDeepFeed = ref<any>(null)
const chatInput = ref('')
const chatLoading = ref(false)
const conversationId = ref('')
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

const getSourceTagType = (source: string) => {
  const s = source.toLowerCase()
  if (s === 'github') return 'success'
  if (s === 'arxiv') return 'warning'
  return 'info'
}

const selectedItems = computed(() => {
  return results.value.filter(item => item.selected && !item.is_imported)
})

// 保存原始返回的结果，用于还原排序
const originalResults = ref<any[]>([])

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'Unknown Date'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

// 前端本地重排逻辑
const sortResults = () => {
  if (results.value.length === 0) return
  
  if (sortBy.value === 'relevance') {
    // 恢复默认检索顺序 (arXiv API 的默认打分顺序)
    results.value = [...originalResults.value]
    if (sortOrder.value === 'ascending') {
      results.value.reverse()
    }
    return
  }

  // 否则按时间排序
  results.value.sort((a, b) => {
    const dateA = new Date(a.published).getTime() || 0
    const dateB = new Date(b.published).getTime() || 0
    let comparison = dateA - dateB
    
    if (sortOrder.value === 'descending') {
      return comparison > 0 ? -1 : (comparison < 0 ? 1 : 0)
    } else {
      return comparison > 0 ? 1 : (comparison < 0 ? -1 : 0)
    }
  })
}

const renderMarkdown = (text: string) => {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text) as string)
}

const handleSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query) {
    ElMessage.warning('请输入检索词')
    return
  }
  
  isSearching.value = true
  hasSearched.value = true
  currentStart.value = 0
  results.value = []
  
  try {
    // 强制使用 relevance 检索作为基础数据，以便前端能进行双向排序
    const res = await axios.get(`${API_BASE}/search/external`, {
      params: { 
        query, 
        start: currentStart.value,
        max_results: 15,
        sort_by: 'relevance',
        sort_order: 'descending'
      }
    })
    
    // 初始化 selected 状态
    const dataWithSelection = res.data.map((item: any) => ({
      ...item,
      selected: false
    }))
    
    originalResults.value = [...dataWithSelection] // 保存原始副本
    results.value = dataWithSelection
    
    // 如果用户设置了其他默认排序，检索后立刻应用
    if (sortBy.value !== 'relevance' || sortOrder.value !== 'descending') {
      sortResults()
    }
  } catch (error: any) {
      if (error.response && error.response.data && error.response.data.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('检索失败，请检查网络或稍后重试')
      }
    } finally {
    isSearching.value = false
  }
}

const loadMoreResults = async () => {
  const query = searchQuery.value.trim()
  if (!query) return
  
  isLoadingMore.value = true
  currentStart.value += 15
  
  try {
    const res = await axios.get(`${API_BASE}/search/external`, {
      params: { 
        query, 
        start: currentStart.value,
        max_results: 15,
        sort_by: 'relevance',
        sort_order: 'descending'
      }
    })
    
    if (res.data.length === 0) {
      ElMessage.info('没有更多文献了')
      return
    }
    
    const newDataWithSelection = res.data.map((item: any) => ({
      ...item,
      selected: false
    }))
    
    originalResults.value.push(...newDataWithSelection)
    results.value.push(...newDataWithSelection)
    
    // 如果当前有特殊排序，重新排一下
    if (sortBy.value !== 'relevance' || sortOrder.value !== 'descending') {
      sortResults()
    }
  } catch (error) {
    ElMessage.error('加载更多失败，请检查网络或稍后重试')
    currentStart.value -= 15 // 回滚
  } finally {
    isLoadingMore.value = false
  }
}

const importItem = async (item: any) => {
  importingStates.value[item.url] = true
  try {
    const payload = {
      title: item.title,
      summary: item.summary,
      url: item.url,
      authors: item.authors
    }
    const res = await axios.post(`${API_BASE}/search/import`, payload)
    if (res.data.status === 'success') {
      ElMessage.success('成功加入知识库！后台正在生成摘要。')
      item.is_imported = true
      item.local_id = res.data.id
    }
  } catch (error) {
    ElMessage.error('入库失败')
  } finally {
    importingStates.value[item.url] = false
  }
}

const clearSelection = () => {
  results.value.forEach(item => item.selected = false)
}

const handleBatchImport = async () => {
  const itemsToImport = selectedItems.value
  if (itemsToImport.length === 0) return
  
  isBatchImporting.value = true
  try {
    const payload = {
      items: itemsToImport.map(item => ({
        title: item.title,
        summary: item.summary,
        url: item.url,
        authors: item.authors
      }))
    }
    const res = await axios.post(`${API_BASE}/search/import_batch`, payload)
    if (res.data.status === 'success') {
      ElMessage.success(`成功批量加入 ${res.data.imported_count} 篇文献！`)
      
      // 更新前端状态
      res.data.items.forEach((importedItem: any) => {
        const match = results.value.find(r => r.url === importedItem.url)
        if (match) {
          match.is_imported = true
          match.local_id = importedItem.local_id
          match.selected = false
        }
      })
    }
  } catch (error) {
    ElMessage.error('批量入库失败')
  } finally {
    isBatchImporting.value = false
  }
}

const openSkimDialog = async (item: any) => {
  currentSkimContent.value = ''
  skimDialogVisible.value = true
  
  if (item.skim_summary) {
    currentSkimContent.value = item.skim_summary
    return
  }
  
  // 如果没有缓存（说明还在生成或生成失败），尝试去拿一次最新的
  try {
    const res = await axios.get(`${API_BASE}/feed/${item.local_id}`)
    if (res.data.skim_summary) {
      item.skim_summary = res.data.skim_summary
      currentSkimContent.value = item.skim_summary
    } else {
      currentSkimContent.value = '' // 依然在生成中
    }
  } catch (error) {
    ElMessage.error('无法获取摘要')
  }
}

// handleDeepRead has been replaced by openDeepReadDrawer

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

const openDeepReadDrawer = async (feed: any) => {
  if (!feed.local_id) {
    ElMessage.warning('请先加入知识库再进行精读')
    return
  }
  
  // 从后端获取该 Feed 的完整信息，因为 search 页的 item 是外部数据
  try {
    const res = await axios.get(`${API_BASE}/feed/${feed.local_id}`)
    currentDeepFeed.value = res.data
  } catch (error) {
    ElMessage.error('无法加载文献详情')
    return
  }
  
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
  if (currentDeepFeed.value.source === 'arxiv' && currentDeepFeed.value.url) {
    readingViewType.value = 'pdf'
  } else {
    readingViewType.value = 'translation'
  }
  
  // 恢复状态
  isHeaderCollapsed.value = false
  
  try {
    const res = await axios.get(`${API_BASE}/reader/feed/${currentDeepFeed.value.id}/deep_read`)
    if (res.data.status === 'success') {
      if (res.data.deep_chat_history && res.data.deep_chat_history.length > 0) {
        chatMessages.value = res.data.deep_chat_history
        conversationId.value = res.data.deep_conversation_id
      } else {
        chatMessages.value.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: `你好！我是针对《${currentDeepFeed.value.title}》的精读助手。你可以随时向我提问关于这篇文档的任何问题。`
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
      
      // 如果之前没有生成知识图谱，这里静默触发一下
      if (!currentDeepFeed.value.is_saved_to_kb) {
        axios.post(`${API_BASE}/feed/${currentDeepFeed.value.id}/save_to_kb`).then(() => {
          feed.status = 'deep_read'
          feed.is_saved_to_kb = true
          currentDeepFeed.value.is_saved_to_kb = true
        })
      }
    }
  } catch (error) {
    ElMessage.error('无法加载精读状态')
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
      combinedContent += `**QA ${idx + 1}:**\n${msg.content}\n\n`
    })
    
    const title = `[精读合集] ${currentDeepFeed.value.title.slice(0, 30)}...`
    await axios.post(`${API_BASE}/knowledge/save`, {
      title: title,
      content: combinedContent,
      kb_type: 'deep',
      ref_id: currentDeepFeed.value.id
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
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
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
