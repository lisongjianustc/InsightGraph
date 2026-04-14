<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { Calendar, MagicStick, SwitchButton, Search, Folder, FolderOpened, Document, Loading, Link } from '@element-plus/icons-vue'
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
const category = ref('未分类')
const noteTags = ref<string[]>([])
const allGlobalTags = ref<string[]>([])
const aiSuggestions = ref<string[]>([])
const isSaving = ref(false)
const isCategorizing = ref(false)
const saveTimeout = ref<number | null>(null)
const datesWithNotes = ref<string[]>([])
const viewMode = ref('calendar') // 'calendar' | 'category'
const categoriesData = ref<any[]>([])

// Reference drawer
const showReferences = ref(true)
const activeTab = ref('recommend')
const searchQuery = ref('')
const recentCapsules = ref<any[]>([])
const recentFeeds = ref<any[]>([])
const recommendations = ref<any[]>([])
const loadingRecommendations = ref(false)
const searchTimeout = ref<number | null>(null)
const recommendTimeout = ref<number | null>(null)

// Multi-select for AI
const selectedCapsuleIds = ref<number[]>([])
const selectedFeedIds = ref<number[]>([])
const selectedOriginalIds = ref<number[]>([])

// AI Writer
const showAIPanel = ref(false)
const aiGenerating = ref(false)
const aiMode = ref('template') // 'template' | 'custom'
const aiFormat = ref('polish') // corresponds to template_id
const aiCustomPrompt = ref('') // optional additional instruction
const showAdvanced = ref(false) // toggle for custom prompt in template mode

const aiTemplateGroups = [
  {
    label: '写作',
    options: [
      { value: 'polish', label: '润色' },
      { value: 'rewrite', label: '改写' },
      { value: 'expand', label: '扩写' },
      { value: 'shorten', label: '压缩' },
      { value: 'blog', label: '博客' },
      { value: 'card', label: '卡片' }
    ]
  },
  {
    label: '结构化',
    options: [
      { value: 'outline', label: '大纲' },
      { value: 'keypoints', label: '要点' },
      { value: 'action_items', label: '待办' }
    ]
  },
  {
    label: '知识管理',
    options: [
      { value: 'qa', label: '问答(Q&A)' },
      { value: 'flashcards', label: '记忆卡片' }
    ]
  }
]

// Tree computing and Dnd
const treeData = computed(() => {
  return categoriesData.value.map(cat => ({
    id: `cat_${cat.name}`,
    label: `${cat.name} (${cat.count})`,
    type: 'category',
    name: cat.name,
    children: cat.notes.map((note: any) => ({
      id: `note_${note.date}`,
      label: note.title,
      type: 'note',
      date: note.date
    }))
  }))
})

const allowDrag = (node: any) => {
  return node.data.type === 'note'
}

const allowDrop = (draggingNode: any, dropNode: any, type: string) => {
  if (draggingNode.data.type !== 'note') return false
  if (dropNode.data.type === 'category' && type === 'inner') return true
  if (dropNode.data.type === 'note' && (type === 'prev' || type === 'next')) return true
  return false
}

const handleDrop = async (draggingNode: any, dropNode: any, dropType: string, _ev: any) => {
  const noteDate = draggingNode.data.date
  let targetCategory = '未分类'
  
  if (dropType === 'inner') {
    targetCategory = dropNode.data.name
  } else {
    targetCategory = dropNode.parent.data?.name || '未分类'
  }
  
  try {
    await axios.patch(`${API_BASE}/daily-notes/${noteDate}/category`, {
      category: targetCategory
    })
    ElMessage.success(`已移动至 [${targetCategory}]`)
    if (formatDate(selectedDate.value) === noteDate) {
       category.value = targetCategory
    }
    fetchCategories()
  } catch (e) {
    console.error(e)
    ElMessage.error('移动失败')
    fetchCategories() // revert tree
  }
}

const handleNodeClick = (data: any) => {
  if (data.type === 'note') {
    selectedDate.value = new Date(data.date)
  }
}

onMounted(() => {
  fetchDates()
  fetchCategories()
  fetchAllTags()
  fetchNote(formatDate(selectedDate.value))
  fetchRecentCapsules()
  fetchRecentFeeds()
})

const fetchAllTags = async () => {
  try {
    const res = await axios.get(`${API_BASE}/graph/data`)
    const tags = res.data.nodes.filter((n: any) => n.node_type === 'tag').map((n: any) => n.title)
    allGlobalTags.value = [...new Set(tags)] as string[]
  } catch (e) {
    console.error('Failed to fetch global tags', e)
  }
}

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

const fetchCategories = async () => {
  try {
    const res = await axios.get(`${API_BASE}/daily-notes/categories`)
    categoriesData.value = res.data.categories || []
  } catch (e) {
    console.error('Failed to fetch categories', e)
  }
}

const fetchNote = async (dateStr: string) => {
  try {
    const res = await axios.get(`${API_BASE}/daily-notes/${dateStr}`)
    content.value = res.data.content || ''
    category.value = res.data.category || '未分类'
    noteTags.value = res.data.tags || []
  } catch (e) {
    console.error('Failed to fetch note', e)
    content.value = ''
    category.value = '未分类'
    noteTags.value = []
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

const fetchRecommendations = async () => {
  if (!content.value || content.value.trim().length < 5) {
    recommendations.value = []
    return
  }
  loadingRecommendations.value = true
  try {
    const res = await axios.post(`${API_BASE}/daily-notes/recommendations`, {
      text: content.value.trim(),
      top_k: 3
    })
    recommendations.value = res.data.items || []
  } catch (e) {
    console.error('Failed to fetch recommendations:', e)
  } finally {
    loadingRecommendations.value = false
  }
}

watch(content, (newVal, oldVal) => {
  if (isSaving.value) return // 阻止因为自身格式化导致循环保存
  if (newVal === oldVal) return
  
  // 检测是否输入了 (( 触发块级引用
  if (newVal.endsWith('((')) {
    showBlockRefDialog.value = true
    blockRefSearch.value = ''
    searchBlockRefs()
  }

  if (saveTimeout.value) clearTimeout(saveTimeout.value)
  saveTimeout.value = window.setTimeout(() => {
    saveNote()
  }, 1500)

  // 触发 AI Librarian 推荐
  if (recommendTimeout.value) clearTimeout(recommendTimeout.value)
  recommendTimeout.value = window.setTimeout(() => {
    if (activeTab.value === 'recommend') {
      fetchRecommendations()
    }
  }, 2000)
})

const handleSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  searchTimeout.value = window.setTimeout(() => {
    if (activeTab.value === 'capsule') {
      fetchRecentCapsules()
    } else if (activeTab.value === 'feed' || activeTab.value === 'original') {
      fetchRecentFeeds()
    }
  }, 500)
}

watch(activeTab, (newVal) => {
  searchQuery.value = ''
  if (newVal === 'capsule') fetchRecentCapsules()
  else if (newVal === 'feed' || newVal === 'original') fetchRecentFeeds()
  else if (newVal === 'recommend') fetchRecommendations()
})

const saveNote = async () => {
  if (isSaving.value) return
  isSaving.value = true
  try {
    await axios.put(`${API_BASE}/daily-notes/${formatDate(selectedDate.value)}`, {
      content: content.value,
      category: category.value,
      tags: noteTags.value
    })
    if (!datesWithNotes.value.includes(formatDate(selectedDate.value)) && content.value.trim() !== '') {
      datesWithNotes.value.push(formatDate(selectedDate.value))
    }
    // Refresh categories in background to keep counts/names updated
    fetchCategories()
    
    // Auto categorize if applicable
    if (category.value === '未分类' && content.value.length > 50 && !isCategorizing.value) {
      autoCategorize()
    }
  } catch (e) {
    console.error('Failed to save note', e)
  } finally {
    isSaving.value = false
  }
}

const autoCategorize = async () => {
  isCategorizing.value = true
  try {
    const existingCategories = categoriesData.value.map(c => c.name).filter(n => n !== '未分类')
    const res = await axios.post(`${API_BASE}/daily-notes/auto-categorize`, {
      content: content.value,
      existing_categories: existingCategories
    })
    
    if (res.data.primary && res.data.primary !== '未分类') {
      category.value = res.data.primary
      aiSuggestions.value = res.data.suggestions || []
      
      // Save again with new category
      await axios.put(`${API_BASE}/daily-notes/${formatDate(selectedDate.value)}`, {
        content: content.value,
        category: category.value
      })
      fetchCategories()
      ElMessage.success(`AI 自动分类为：${category.value}`)
    }
  } catch (e) {
    console.error('Auto categorization failed', e)
  } finally {
    isCategorizing.value = false
  }
}

// 块级引用逻辑 (Block-level Reference)
const showBlockRefDialog = ref(false)
const blockRefSearch = ref('')
const blockRefResults = ref<any[]>([])
const loadingBlockRefs = ref(false)

const searchBlockRefs = async () => {
  loadingBlockRefs.value = true
  try {
    const res = await axios.get(`${API_BASE}/capsules`, {
      params: { search: blockRefSearch.value, limit: 15 }
    })
    blockRefResults.value = res.data.items || []
  } catch (e) {
    console.error('Search block refs failed', e)
  } finally {
    loadingBlockRefs.value = false
  }
}

const insertBlockRef = (capsule: any) => {
  // 替换掉最后输入的 ((
  const lastIndex = content.value.lastIndexOf('((')
  let baseContent = content.value
  let afterContent = ''
  if (lastIndex !== -1) {
    baseContent = content.value.substring(0, lastIndex)
    afterContent = content.value.substring(lastIndex + 2)
  }
  
  // 如果引用的本身就是高亮块（自带了 > 和 来源），就不用再套一层引用块了
  let refText = ''
  if (capsule.content.includes('摘自文献') || capsule.content.includes('摘自：')) {
    refText = `\n${capsule.content}\n`
  } else {
    refText = `\n> ${capsule.content}\n> — 引用自 [[capsule:${capsule.id}]]\n`
  }
  
  content.value = baseContent + refText + afterContent
  showBlockRefDialog.value = false
  triggerSave()
}

const handleCategoryChange = (val: string) => {
  category.value = val
  triggerSave()
}

const handleTagsChange = () => {
  triggerSave()
}

const triggerSave = () => {
  if (saveTimeout.value) clearTimeout(saveTimeout.value)
  saveTimeout.value = window.setTimeout(() => {
    saveNote()
  }, 1000)
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
    
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE}/daily-notes/ai-rewrite`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        draft_content: content.value,
        reference_capsule_ids: Array.from(refCapsuleIds),
        reference_feed_ids: Array.from(refFeedIds),
        reference_original_ids: Array.from(refOriginalIds),
        mode: aiMode.value,
        template_id: aiFormat.value,
        custom_prompt: aiCustomPrompt.value
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
  <div class="h-full flex overflow-hidden bg-card">
    <!-- 左侧侧边栏 (日历/分类 切换) -->
    <div class="w-80 border-r border-border bg-app/50 flex flex-col shrink-0">
      <div class="p-4 border-b border-border">
        <el-radio-group v-model="viewMode" class="w-full flex">
          <el-radio-button label="calendar" class="flex-1 text-center"><el-icon class="mr-1"><Calendar /></el-icon>日历</el-radio-button>
          <el-radio-button label="category" class="flex-1 text-center"><el-icon class="mr-1"><Folder /></el-icon>分类</el-radio-button>
        </el-radio-group>
      </div>
      
      <!-- 日历视图 -->
      <div v-show="viewMode === 'calendar'" class="flex-1 overflow-y-auto p-4 custom-calendar">
        <el-calendar v-model="selectedDate">
          <template #date-cell="{ data }">
            <div class="h-full w-full flex flex-col items-center justify-center relative">
              <span class="text-sm" :class="{'text-indigo-600 font-bold': data.isSelected}">{{ data.day.split('-')[2] }}</span>
              <div v-if="datesWithNotes.includes(data.day)" class="w-1.5 h-1.5 rounded-full bg-indigo-500 absolute bottom-1"></div>
            </div>
          </template>
        </el-calendar>
      </div>

      <!-- 分类视图 -->
      <div v-show="viewMode === 'category'" class="flex-1 overflow-y-auto p-2">
        <el-tree
          v-if="treeData.length > 0"
          :data="treeData"
          draggable
          :allow-drop="allowDrop"
          :allow-drag="allowDrag"
          @node-drop="handleDrop"
          @node-click="handleNodeClick"
          node-key="id"
          default-expand-all
          :expand-on-click-node="false"
          class="bg-transparent"
        >
          <template #default="{ node, data }">
            <div class="flex items-center gap-2 w-full pr-2 text-sm transition-colors py-1" 
                 :class="{'text-indigo-600 font-bold bg-indigo-50 px-2 rounded': data.type === 'note' && formatDate(selectedDate) === data.date}">
              <el-icon v-if="data.type === 'category'" class="text-yellow-500"><FolderOpened /></el-icon>
              <el-icon v-else class="text-secondary"><Document /></el-icon>
              <span class="truncate flex-1" :class="{'font-medium text-gray-700': data.type === 'category'}">{{ node.label }}</span>
            </div>
          </template>
        </el-tree>
        <div v-else class="text-center text-secondary text-sm mt-10">暂无分类数据</div>
      </div>
    </div>

    <!-- 中间主编辑器区 -->
    <div class="flex-1 flex flex-col relative bg-card min-w-0">
      <div class="h-auto min-h-14 py-2 border-b border-border flex flex-col justify-center px-6 shrink-0 gap-2">
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center gap-4">
            <h1 class="text-xl font-bold text-primary">{{ formatDate(selectedDate) }}</h1>
            
            <el-select
              v-model="category"
              filterable
              allow-create
              default-first-option
              :reserve-keyword="false"
              placeholder="未分类"
              size="small"
              class="w-40"
              @change="handleCategoryChange"
            >
              <el-option-group v-if="aiSuggestions.length > 0" label="✨ AI 推荐分类">
                <el-option
                  v-for="sugg in aiSuggestions"
                  :key="'ai_' + sugg"
                  :label="sugg"
                  :value="sugg"
                >
                  <span class="flex items-center gap-2"><el-icon class="text-purple-500"><MagicStick /></el-icon>{{ sugg }}</span>
                </el-option>
              </el-option-group>
              
              <el-option-group label="📂 现有分类">
                <el-option
                  v-for="cat in categoriesData"
                  :key="cat.name"
                  :label="cat.name"
                  :value="cat.name"
                />
              </el-option-group>
            </el-select>
            
            <span v-if="isSaving" class="text-xs text-secondary transition-opacity">保存中...</span>
            <span v-else-if="isCategorizing" class="text-xs text-indigo-500 transition-opacity flex items-center gap-1"><el-icon class="is-loading"><Loading /></el-icon> AI 自动分类中...</span>
            <span v-else class="text-xs text-secondary transition-opacity">已保存</span>
          </div>
          <div class="flex gap-2 shrink-0">
            <el-button @click="showAIPanel = true" type="primary" plain size="small">
              <el-icon class="mr-1"><MagicStick /></el-icon> AI 创作
            </el-button>
            <el-button @click="showReferences = !showReferences" size="small">
              <el-icon class="mr-1"><SwitchButton /></el-icon> 素材库
            </el-button>
          </div>
        </div>
        
        <!-- Tags Editor Row -->
        <div class="flex items-center w-full">
          <el-select
            v-model="noteTags"
            multiple
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            placeholder="+ 添加图谱标签 (Tag)"
            size="small"
            class="w-full custom-tag-select"
            @change="handleTagsChange"
          >
            <el-option
              v-for="item in allGlobalTags"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
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
        <div v-if="showAIPanel" class="absolute top-4 right-4 w-96 bg-card rounded-xl shadow-2xl border border-border p-4 z-50 flex flex-col max-h-[80vh]">
          <h3 class="font-semibold text-primary mb-3 flex items-center justify-between">
            <span class="flex items-center gap-2"><el-icon class="text-purple-500"><MagicStick /></el-icon> AI 魔法棒</span>
            <el-radio-group v-model="aiMode" size="small">
              <el-radio-button label="template">模板</el-radio-button>
              <el-radio-button label="custom">自定义</el-radio-button>
            </el-radio-group>
          </h3>
          
          <div class="flex-1 overflow-y-auto space-y-4 pr-1">
            <template v-if="aiMode === 'template'">
              <div v-for="(group, idx) in aiTemplateGroups" :key="idx" class="space-y-1">
                <div class="text-xs text-secondary font-medium">{{ group.label }}</div>
                <div class="grid grid-cols-3 gap-2">
                  <div 
                    v-for="opt in group.options" 
                    :key="opt.value"
                    @click="aiFormat = opt.value"
                    class="cursor-pointer border rounded text-center py-1.5 text-xs transition-colors"
                    :class="aiFormat === opt.value ? 'bg-indigo-50 border-indigo-500 text-indigo-700 font-medium' : 'border-border text-secondary hover:bg-app'"
                  >
                    {{ opt.label }}
                  </div>
                </div>
              </div>
              
              <div>
                <div class="flex items-center justify-between text-xs text-secondary cursor-pointer py-1" @click="showAdvanced = !showAdvanced">
                  <span>高级指令 (可选)</span>
                  <span>{{ showAdvanced ? '收起' : '展开' }}</span>
                </div>
                <el-input
                  v-show="showAdvanced"
                  v-model="aiCustomPrompt"
                  type="textarea"
                  :rows="2"
                  placeholder="附加要求：例如'用更口语化的语气'..."
                  class="mt-1 text-xs"
                />
              </div>
            </template>

            <template v-else>
              <div class="space-y-2">
                <div class="text-xs text-secondary font-medium">自定义提示词</div>
                <el-input
                  v-model="aiCustomPrompt"
                  type="textarea"
                  :rows="6"
                  placeholder="输入你的具体写作要求：例如'把草稿提炼成一份带重点和行动项的周报，重点要突出'..."
                />
              </div>
            </template>
          </div>

          <div class="pt-4 mt-2 border-t border-border space-y-2 shrink-0">
            <el-button @click="triggerAIRewrite" type="primary" class="w-full" :loading="aiGenerating" :disabled="aiMode === 'custom' && !aiCustomPrompt.trim()">
              {{ aiGenerating ? '正在生成...' : '开始魔法生成' }}
            </el-button>
            <el-button @click="showAIPanel = false" class="w-full !ml-0" size="small">关闭</el-button>
          </div>
        </div>
        
        <!-- 块级引用搜索框 (Block-level Reference) -->
        <el-dialog v-model="showBlockRefDialog" title="插入高亮胶囊引用" width="500px" top="10vh" append-to-body :show-close="false" class="rounded-xl overflow-hidden shadow-2xl">
          <div class="space-y-4">
            <el-input
              v-model="blockRefSearch"
              placeholder="搜索你想引用的高亮块或胶囊内容..."
              :prefix-icon="Search"
              clearable
              autofocus
              @input="searchBlockRefs"
            />
            
            <div class="max-h-[400px] overflow-y-auto space-y-2 custom-scrollbar">
              <div v-if="loadingBlockRefs" class="py-8 flex justify-center">
                <el-icon class="is-loading text-secondary text-2xl"><Loading /></el-icon>
              </div>
              <div v-else-if="blockRefResults.length === 0" class="py-8 text-center text-secondary text-sm">
                没有找到匹配的块级引用
              </div>
              <div 
                v-else
                v-for="cap in blockRefResults" 
                :key="cap.id"
                class="p-3 border border-border rounded-lg hover:bg-indigo-50 hover:border-indigo-200 cursor-pointer transition-colors"
                @click="insertBlockRef(cap)"
              >
                <div v-if="cap.title" class="text-xs font-bold text-primary mb-1 line-clamp-1"><el-icon class="text-indigo-500 mr-1"><Link /></el-icon>{{ cap.title }}</div>
                <div class="text-sm text-secondary line-clamp-3 leading-relaxed">{{ cap.content }}</div>
                <div class="text-[10px] text-secondary mt-2 flex justify-between">
                  <span>{{ new Date(cap.created_at).toLocaleDateString() }}</span>
                  <span v-if="cap.content.includes('摘自文献') || cap.content.includes('摘自：')" class="text-indigo-400 font-medium">高亮片段</span>
                </div>
              </div>
            </div>
          </div>
        </el-dialog>
      </div>
    </div>

    <!-- 右侧引用库 -->
    <div v-if="showReferences" class="w-80 border-l border-border bg-app flex flex-col">
      <div class="p-4 border-b border-border">
        <h3 class="font-semibold text-gray-700 mb-3">知识素材库</h3>
        <el-input
          v-if="activeTab !== 'recommend'"
          v-model="searchQuery"
          placeholder="搜索素材..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          class="mb-3"
        />
        <el-radio-group v-model="activeTab" size="small" class="w-full flex-wrap gap-y-1">
          <el-radio-button label="recommend" class="flex-1">AI 推荐</el-radio-button>
          <el-radio-button label="capsule" class="flex-1">闪念胶囊</el-radio-button>
          <el-radio-button label="feed" class="flex-1">文献摘要</el-radio-button>
          <el-radio-button label="original" class="flex-1">文献原文</el-radio-button>
        </el-radio-group>
        <p v-if="activeTab === 'recommend'" class="text-xs text-indigo-500 mt-3 font-medium">✨ 根据您当前的书写内容，实时推荐可能相关的知识素材</p>
        <p v-else class="text-xs text-secondary mt-3">拖拽或勾选卡片，召唤 AI 写作</p>
      </div>
      
      <div class="flex-1 overflow-y-auto p-4 space-y-3 pb-20">
        <!-- AI 推荐列表 -->
        <template v-if="activeTab === 'recommend'">
          <div v-if="loadingRecommendations" class="text-sm text-secondary text-center py-4 flex items-center justify-center gap-2">
            <el-icon class="is-loading"><Loading /></el-icon> 正在检索相关记忆...
          </div>
          <div v-else-if="recommendations.length === 0" class="text-sm text-secondary text-center py-4">
            {{ content.length < 5 ? '多写一点内容，AI 将为您推荐相关素材' : '未找到强相关的历史素材' }}
          </div>
          <div 
            v-for="(item, index) in recommendations" 
            :key="'rec-'+index"
            class="bg-indigo-50 p-3 rounded-lg border border-indigo-100 shadow-sm transition-all flex items-start gap-2"
          >
            <div class="flex-1 min-w-0">
              <div class="text-xs font-semibold text-indigo-700 truncate mb-1">{{ item.title }}</div>
              <div class="text-xs text-secondary line-clamp-4 leading-relaxed">{{ item.content }}</div>
              <div class="text-[10px] text-indigo-400 mt-2 font-mono">相似度: {{ (item.score * 100).toFixed(1) }}%</div>
            </div>
          </div>
        </template>

        <!-- 胶囊列表 -->
        <template v-if="activeTab === 'capsule'">
          <div v-if="recentCapsules.length === 0" class="text-sm text-secondary text-center py-4">无匹配胶囊</div>
          <div 
            v-for="capsule in recentCapsules" 
            :key="'cap-'+capsule.id"
            draggable="true"
            @dragstart="handleDragStartCapsule($event, capsule)"
            class="bg-card p-3 rounded-lg border border-border shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all flex items-start gap-2"
          >
            <el-checkbox v-model="selectedCapsuleIds" :label="capsule.id" :value="capsule.id" size="small" class="mt-0.5"><span class="hidden"></span></el-checkbox>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-primary mb-1 line-clamp-1">{{ capsule.title || '无标题胶囊' }}</div>
              <div class="text-xs text-secondary line-clamp-3">{{ capsule.content }}</div>
            </div>
          </div>
        </template>
        
        <!-- 文献摘要列表 -->
        <template v-if="activeTab === 'feed'">
          <div v-if="recentFeeds.length === 0" class="text-sm text-secondary text-center py-4">无匹配文献</div>
          <div 
            v-for="feed in recentFeeds" 
            :key="'feed-'+feed.id"
            draggable="true"
            @dragstart="handleDragStartFeed($event, feed)"
            class="bg-card p-3 rounded-lg border border-border shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all flex items-start gap-2"
          >
            <el-checkbox v-model="selectedFeedIds" :label="feed.id" :value="feed.id" size="small" class="mt-0.5"><span class="hidden"></span></el-checkbox>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-primary mb-1 line-clamp-2 leading-snug">{{ feed.title }}</div>
              <div class="text-xs text-secondary line-clamp-3">{{ feed.skim_summary || feed.summary || '暂无摘要' }}</div>
            </div>
          </div>
        </template>

        <!-- 文献原文列表 -->
        <template v-if="activeTab === 'original'">
          <div v-if="recentFeeds.length === 0" class="text-sm text-secondary text-center py-4">无匹配文献</div>
          <div 
            v-for="feed in recentFeeds" 
            :key="'orig-'+feed.id"
            draggable="true"
            @dragstart="handleDragStartOriginal($event, feed)"
            class="bg-card p-3 rounded-lg border border-border shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all flex items-start gap-2"
          >
            <el-checkbox v-model="selectedOriginalIds" :label="feed.id" :value="feed.id" size="small" class="mt-0.5"><span class="hidden"></span></el-checkbox>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-primary mb-1 line-clamp-2 leading-snug">{{ feed.title }}</div>
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

.custom-tag-select :deep(.el-select__tags) {
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
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
