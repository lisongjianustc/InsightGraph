<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Calendar, MagicStick, SwitchButton } from '@element-plus/icons-vue'
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
const recentCapsules = ref<any[]>([])

// AI Writer
const showAIPanel = ref(false)
const aiGenerating = ref(false)
const aiFormat = ref('polish')

onMounted(() => {
  fetchDates()
  fetchNote(formatDate(selectedDate.value))
  fetchRecentCapsules()
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
    const res = await axios.get(`${API_BASE}/capsules/`)
    recentCapsules.value = res.data.slice(0, 10)
  } catch (e) {
    console.error('Failed to fetch capsules', e)
  }
}

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

const handleDragStart = (e: DragEvent, capsule: any) => {
  if (e.dataTransfer) {
    e.dataTransfer.setData('text/plain', `> [!quote] ${capsule.title || '胶囊'}\n> ${capsule.content}\n\n[[capsule:${capsule.id}]]\n`)
  }
}

const triggerAIRewrite = async () => {
  if (!content.value.trim()) {
    ElMessage.warning('请先写点内容再呼叫 AI')
    return
  }
  
  aiGenerating.value = true
  
  // Extract capsule IDs from content
  const capsuleIdRegex = /\[\[capsule:(\d+)\]\]/g
  const refIds = []
  let match
  while ((match = capsuleIdRegex.exec(content.value)) !== null) {
    refIds.push(parseInt(match[1]))
  }
  
  try {
    const response = await fetch(`${API_BASE}/daily-notes/ai-rewrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_content: content.value,
        reference_capsule_ids: refIds,
        format_type: aiFormat.value
      })
    })

    if (!response.body) throw new Error('No response body')
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    
    // Clear content or append, depending on UX. Let's append for now to not lose draft.
    content.value += '\n\n---\n**AI 生成结果：**\n\n'

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
              content.value += data.answer
            }
          } catch (e) {
            // ignore JSON parse error on partial chunks
          }
        }
      }
    }
    
    saveNote() // Save the AI result
    
  } catch (e) {
    console.error(e)
    ElMessage.error('AI 生成失败')
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
        <h3 class="font-semibold text-gray-700">闪念胶囊库</h3>
        <p class="text-xs text-gray-500 mt-1">将下方卡片拖拽至左侧编辑器中即可引用</p>
      </div>
      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <div 
          v-for="capsule in recentCapsules" 
          :key="capsule.id"
          draggable="true"
          @dragstart="handleDragStart($event, capsule)"
          class="bg-white p-3 rounded-lg border border-gray-200 shadow-sm cursor-move hover:border-indigo-300 hover:shadow-md transition-all"
        >
          <div class="font-medium text-sm text-gray-800 mb-1 line-clamp-1">{{ capsule.title || '无标题胶囊' }}</div>
          <div class="text-xs text-gray-500 line-clamp-3">{{ capsule.content }}</div>
        </div>
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