<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { Calendar, MagicStick, SwitchButton, Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
// @ts-ignore
import { Editor } from '@bytemd/vue-next'
// @ts-ignore
import gfm from '@bytemd/plugin-gfm'
// @ts-ignore
import highlight from '@bytemd/plugin-highlight'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/vs.css'

const API_BASE = 'http://localhost:8000/api' // Adjust according to your env or use process.env.VITE_API_BASE
const plugins = [gfm(), highlight()]

// Status
const selectedDate = ref(new Date())
const content = ref('')
const isSaving = ref(false)
const saveTimeout = ref<number | null>(null)
const datesWithNotes = ref<string[]>([])

// Reference drawer
const showReferences = ref(true)
const activeTab = ref('capsule')
const searchQuery = ref('')
const recentCapsules = ref<any[]>([])
const recentFeeds = ref<any[]>([])
const searchTimeout = ref<number | null>(null)

// Multi-select for AI
const selectedCapsuleIds = ref<number[]>([])
const selectedFeedIds = ref<number[]>([])
const selectedOriginalIds = ref<number[]>([])

// AI Writer
const showAIPanel = ref(false)
const aiGenerating = ref(false)
const aiFormat = ref('polish')

onMounted(() => {
  fetchDates()
  fetchNote(formatDate(selectedDate.value))
  fetchRecentCapsules()
  fetchRecentFeeds()
})

const formatDate = (date: Date) => {
  const d = new Date(date)
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().split('T')[0]
}

const fetchDates = async () => {
  try {
    const res = await axios.get(`${API_BASE}/daily-notes/dates`)
    datesWithNotes.value = res.data.dates
  } catch (e) {
    console.error('Failed to fetch dates', e)
  }
}

const fetchNote = async (dateStr: string) => {
  try {
    const res = await axios.get(`${API_BASE}/daily-notes/${dateStr}`)
    content.value = res.data.content || ''
  } catch (e) {
    console.error('Failed to fetch note', e)
    content.value = ''
  }
}

const fetchRecentCapsules = async () => {
  try {
    const params = searchQuery.value ? { keyword: searchQuery.value, limit: 20 } : { limit: 20 }
    const res = await axios.get(`${API_BASE}/capsules/`, { params })
    recentCapsules.value = res.data.items || res.data || []
  } catch (e) {
    console.error('Failed to fetch capsules', e)
  }
}

const fetchRecentFeeds = async () => {
  try {
    // 假设后端 /api/feed/list 支持搜索，如果没有直接拉取列表并在前端过滤
    const res = await axios.get(`${API_BASE}/feed/list`, { params: { limit: 20 } })
    let feeds = res.data || []
    if (searchQuery.value) {
      feeds = feeds.filter((f: any) => f.title?.toLowerCase().includes(searchQuery.value.toLowerCase()) || f.skim_summary?.toLowerCase().includes(searchQuery.value.toLowerCase()))
    }
    recentFeeds.value = feeds
  } catch (e) {
    console.error('Failed to fetch feeds', e)
  }
}

const handleSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  searchTimeout.value = window.setTimeout(() => {
    if (activeTab.value === 'capsule') {
      fetchRecentCapsules()
    } else {
      fetchRecentFeeds()
    }
  }, 500)
}

watch(activeTab, () => {
  searchQuery.value = ''
  if (activeTab.value === 'capsule') {
    fetchRecentCapsules()
  } else {
    fetchRecentFeeds()
  }
})

const saveNote = async () => {
  if (isSaving.value) return
  isSaving.value = true
  try {
    await axios.put(`${API_BASE}/daily-notes/${formatDate(selectedDate.value)}`, {
      content: content.value
    })
    if (!datesWithNotes.value.includes(formatDate(selectedDate.value)) && content.value.trim() !== '') {
      datesWithNotes.value.push(formatDate(selectedDate.value))
    }
  } catch (e) {
    console.error('Failed to save note', e)
  } finally {
    isSaving.value = false
  }
}

const handleEditorChange = (v: string) => {
  content.value = v
  
  // Auto-save debounce
  if (saveTimeout.value) {
    clearTimeout(saveTimeout.value)
  }
  saveTimeout.value = window.setTimeout(() => {
    saveNote()
  }, 2000)
}

watch(selectedDate, (newDate) => {
  fetchNote(formatDate(newDate))
})

const handleDragStartCapsule = (e: DragEvent, capsule: any) => {
  if (e.dataTransfer) {
    e.dataTransfer.setData('text/plain', `> [!quote] ${capsule.title || '闪念胶囊'}\n> ${capsule.content}\n\n[[capsule:${capsule.id}]]\n`)
  }
}

const handleDragStartFeed = (e: DragEvent, feed: any) => {
  if (e.dataTransfer) {
    e.dataTransfer.setData('text/plain', `> [!info] ${feed.title || '精读文献'}\n> ${feed.skim_summary || feed.summary || '暂无摘要'}\n\n[[feed:${feed.id}]]\n`)
  }
}

const handleDragStartOriginal = (e: DragEvent, feed: any) => {
  if (e.dataTransfer) {
    e.dataTransfer.setData('text/plain', `> [!abstract] ${feed.title || '文献原文'}\n> ${feed.skim_summary || '查看原文详细内容'}\n\n[[original:${feed.id}]]\n`)
  }
}

const totalSelectedItems = computed(() => {
  return selectedCapsuleIds.value.length + selectedFeedIds.value.length + selectedOriginalIds.value.length
})

const handleQuickAI = () => {
  showAIPanel.value = true
}

const triggerAIRewrite = async () => {
  // 如果没有勾选素材，也没有写草稿，则提示
  const totalSelected = selectedCapsuleIds.value.length + selectedFeedIds.value.length + selectedOriginalIds.value.length
  if (!content.value.trim() && totalSelected === 0) {
    ElMessage.warning('请先写点草稿，或者在右侧勾选一些素材再呼叫 AI')
    return
  }
  
  aiGenerating.value = true
  
  // 从编辑器文本中通过正则提取出的隐式引用 ID
  const capsuleIdRegex = /\[\[capsule:(\d+)\]\]/g
  const feedIdRegex = /\[\[feed:(\d+)\]\]/g
  const originalIdRegex = /\[\[original:(\d+)\]\]/g
  
  const refCapsuleIds = new Set<number>(selectedCapsuleIds.value)
  const refFeedIds = new Set<number>(selectedFeedIds.value)
  const refOriginalIds = new Set<number>(selectedOriginalIds.value)
  
  let match
  while ((match = capsuleIdRegex.exec(content.value)) !== null) refCapsuleIds.add(parseInt(match[1]))
  while ((match = feedIdRegex.exec(content.value)) !== null) refFeedIds.add(parseInt(match[1]))
  while ((match = originalIdRegex.exec(content.value)) !== null) refOriginalIds.add(parseInt(match[1]))
  
  try {
    // Show an initial engaging message while waiting for TTFT (Time To First Token)
    content.value += '\n\n---\n**🧠 AI 正在深度阅读并构思文章框架，请稍候...**\n\n'
    
    const response = await fetch(`${API_BASE}/daily-notes/ai-rewrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_content: content.value,
        reference_capsule_ids: Array.from(refCapsuleIds),
        reference_feed_ids: Array.from(refFeedIds),
        reference_original_ids: Array.from(refOriginalIds),
        format_type: aiFormat.value
      })
    })

    if (!response.ok) {
      const errText = await response.text()
      throw new Error(`请求失败 (${response.status}): ${errText}`)
    }
    
    if (!response.body) throw new Error('No response body')
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    
    let firstTokenReceived = false

    const processLines = (lines: string[]) => {
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (!dataStr) continue
          try {
            const data = JSON.parse(dataStr)
            if (data.event === 'message') {
              if (!firstTokenReceived) {
                // Remove the waiting message when the first token arrives
                content.value = content.value.replace('\n\n---\n**🧠 AI 正在深度阅读并构思文章框架，请稍候...**\n\n', '\n\n---\n**AI 生成结果：**\n\n')
                firstTokenReceived = true
              }
              content.value += data.answer
            }
          } catch (e) {
            // ignore JSON parse error on partial chunks
          }
        }
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        if (buffer) {
          processLines(buffer.split('\n'))
        }
        break
      }
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      processLines(lines)
    }
    
    saveNote() // Save the AI result
    
  } catch (e: any) {
      console.error(e)
      ElMessage.error(`AI 生成失败: ${e.message || e}`)
    } finally {
    aiGenerating.value = false
    showAIPanel.value = false
  }
}
</script>

<template>
  <div class="h-full flex overflow-hidden bg-white">
    <!-- 左侧日历栏 -->
    <div class="w-80 border-r border-gray-200 bg-gray-50/50 flex flex-col">
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <el-icon><Calendar /></el-icon> 日历漫游
        </h2>
      </div>
      <div class="flex-1 overflow-y-auto p-4 custom-calendar">
        <el-calendar v-model="selectedDate">
          <template #date-cell="{ data }">
            <div class="h-full w-full flex flex-col items-center justify-center relative">
              <span class="text-sm" :class="{'text-indigo-600 font-bold': data.isSelected}">{{ data.day.split('-')[2] }}</span>
              <div v-if="datesWithNotes.includes(data.day)" class="w-1.5 h-1.5 rounded-full bg-indigo-500 absolute bottom-1"></div>
            </div>
          </template>
        </el-calendar>
      </div>
    </div>

    <!-- 中间主编辑器区 -->
    <div class="flex-1 flex flex-col relative bg-white">
      <div class="h-14 border-b border-gray-100 flex items-center justify-between px-6">
        <div class="flex items-center gap-4">
          <h1 class="text-xl font-bold text-gray-800">{{ formatDate(selectedDate) }}</h1>
          <span v-if="isSaving" class="text-xs text-gray-400">保存中...</span>
          <span v-else class="text-xs text-gray-400">已保存</span>
        </div>
        <div class="flex gap-2">
          <el-button @click="showAIPanel = true" type="primary" plain size="small">
            <el-icon class="mr-1"><MagicStick /></el-icon> AI 创作
          </el-button>
          <el-button @click="showReferences = !showReferences" size="small">
            <el-icon class="mr-1"><SwitchButton /></el-icon> 素材库
          </el-button>
        </div>
      </div>
      
      <div class="flex-1 overflow-hidden relative">
        <Editor
          :value="content"
          :plugins="plugins"
          @change="handleEditorChange"
          class="h-full typora-editor"
          placeholder="在此记录今日的所思所想... 支持 Markdown，支持拖拽右侧胶囊引入素材。"
        />
        
        <!-- AI 浮窗 -->
        <div v-if="showAIPanel" class="absolute top-4 right-4 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 p-4 z-50">
          <h3 class="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <el-icon class="text-purple-500"><MagicStick /></el-icon> AI 魔法棒
          </h3>
          <div class="space-y-3">
            <el-radio-group v-model="aiFormat" class="w-full">
              <el-radio-button label="polish" class="flex-1">润色</el-radio-button>
              <el-radio-button label="card" class="flex-1">卡片</el-radio-button>
              <el-radio-button label="blog" class="flex-1">博客</el-radio-button>
            </el-radio-group>
            <el-button @click="triggerAIRewrite" type="primary" class="w-full" :loading="aiGenerating">
              {{ aiGenerating ? '正在生成...' : '开始魔法重写' }}
            </el-button>
            <el-button @click="showAIPanel = false" class="w-full !ml-0" size="small">关闭</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧引用库 -->
    <div v-if="showReferences" class="w-80 border-l border-gray-200 bg-gray-50 flex flex-col">
      <div class="p-4 border-b border-gray-200">
        <h3 class="font-semibold text-gray-700 mb-3">知识素材库</h3>
        <el-input
          v-model="searchQuery"
          placeholder="搜索素材..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          class="mb-3"
        />
        <el-radio-group v-model="activeTab" size="small" class="w-full">
          <el-radio-button label="capsule" class="flex-1">闪念胶囊</el-radio-button>
          <el-radio-button label="feed" class="flex-1">文献摘要</el-radio-button>
          <el-radio-button label="original" class="flex-1">文献原文</el-radio-button>
        </el-radio-group>
        <p class="text-xs text-gray-500 mt-3">拖拽或勾选卡片，召唤 AI 写作</p>
      </div>
      
      <div class="flex-1 overflow-y-auto p-4 space-y-3 pb-20">
        <!-- 胶囊列表 -->
        <template v-if="activeTab === 'capsule'">
          <div v-if="recentCapsules.length === 0" class="text-sm text-gray-400 text-center py-4">无匹配胶囊</div>
          <div 
            v-for="capsule in recentCapsules" 
            :key="'cap-'+capsule.id"
            draggable="true"
            @dragstart="handleDragStartCapsule($event, capsule)"
            class="bg-white p-3 rounded-lg border border-gray-200 shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all flex items-start gap-2"
          >
            <el-checkbox v-model="selectedCapsuleIds" :label="capsule.id" :value="capsule.id" size="small" class="mt-0.5"><span class="hidden"></span></el-checkbox>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-gray-800 mb-1 line-clamp-1">{{ capsule.title || '无标题胶囊' }}</div>
              <div class="text-xs text-gray-500 line-clamp-3">{{ capsule.content }}</div>
            </div>
          </div>
        </template>
        
        <!-- 文献摘要列表 -->
        <template v-if="activeTab === 'feed'">
          <div v-if="recentFeeds.length === 0" class="text-sm text-gray-400 text-center py-4">无匹配文献</div>
          <div 
            v-for="feed in recentFeeds" 
            :key="'feed-'+feed.id"
            draggable="true"
            @dragstart="handleDragStartFeed($event, feed)"
            class="bg-white p-3 rounded-lg border border-gray-200 shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all flex items-start gap-2"
          >
            <el-checkbox v-model="selectedFeedIds" :label="feed.id" :value="feed.id" size="small" class="mt-0.5"><span class="hidden"></span></el-checkbox>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-gray-800 mb-1 line-clamp-2 leading-snug">{{ feed.title }}</div>
              <div class="text-xs text-gray-500 line-clamp-3">{{ feed.skim_summary || feed.summary || '暂无摘要' }}</div>
            </div>
          </div>
        </template>

        <!-- 文献原文列表 -->
        <template v-if="activeTab === 'original'">
          <div v-if="recentFeeds.length === 0" class="text-sm text-gray-400 text-center py-4">无匹配文献</div>
          <div 
            v-for="feed in recentFeeds" 
            :key="'orig-'+feed.id"
            draggable="true"
            @dragstart="handleDragStartOriginal($event, feed)"
            class="bg-white p-3 rounded-lg border border-gray-200 shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all flex items-start gap-2"
          >
            <el-checkbox v-model="selectedOriginalIds" :label="feed.id" :value="feed.id" size="small" class="mt-0.5"><span class="hidden"></span></el-checkbox>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-gray-800 mb-1 line-clamp-2 leading-snug">{{ feed.title }}</div>
              <div class="text-xs text-indigo-500 font-medium">包含完整深度解析原文</div>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部悬浮操作栏 -->
      <div v-if="totalSelectedItems > 0" class="absolute bottom-4 right-4 w-72 bg-gray-800 text-white rounded-xl shadow-2xl p-3 flex items-center justify-between z-40 transition-all">
        <div class="text-sm font-medium">已选择 {{ totalSelectedItems }} 项素材</div>
        <el-button type="primary" size="small" @click="handleQuickAI">
          <el-icon class="mr-1"><MagicStick /></el-icon> AI 创作
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-calendar :deep(.el-calendar-table .el-calendar-day) {
  height: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.custom-calendar :deep(.el-calendar__header) {
  padding: 8px 0;
  border-bottom: none;
}
.custom-calendar :deep(.el-calendar__body) {
  padding: 0;
}

/* Typora-like editor styling */
.typora-editor :deep(.bytemd) {
  height: 100%;
  border: none;
  background: transparent;
}
.typora-editor :deep(.bytemd-fullscreen) {
  background: white !important;
  z-index: 9999 !important;
}
.typora-editor :deep(.bytemd-toolbar) {
  border-bottom: 1px solid #f3f4f6;
  background: white;
}
.typora-editor :deep(.CodeMirror) {
  background: transparent;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  padding: 20px 40px;
}
.typora-editor :deep(.markdown-body) {
  padding: 20px 40px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
</style>