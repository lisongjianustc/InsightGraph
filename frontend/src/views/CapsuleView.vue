<template>
  <div class="min-h-screen bg-gray-50 flex flex-col items-center pt-10 px-4 relative overflow-auto custom-scrollbar">
    <!-- 背景装饰 -->
    <div class="absolute top-0 w-full h-64 bg-gradient-to-b from-purple-100 to-transparent pointer-events-none"></div>

    <div class="max-w-3xl w-full z-10 flex flex-col flex-1">
      <!-- 头部 -->
      <div class="text-center mb-8 shrink-0">
        <h1 class="text-4xl font-extrabold text-gray-800 tracking-tight mb-2">⚡️ 闪念胶囊</h1>
        <p class="text-gray-500">记录一闪而过的灵感、文档或碎片化信息，自动构建专属知识网络</p>
      </div>

      <!-- 原版大输入区 -->
      <el-card shadow="hover" class="rounded-xl border-0 overflow-visible mb-8 shrink-0">
        <div class="relative">
          <el-upload
            class="w-full"
            drag
            :action="uploadUrl"
            :headers="authHeaders"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            name="file"
          >
            <div v-if="!isUploading" class="el-upload__text text-gray-400 p-4">
              <el-icon class="text-3xl mb-2 text-gray-300"><DocumentAdd /></el-icon>
              <div>拖拽文档到此处上传解析</div>
              <div class="text-xs mt-1">支持 图文 / PDF / Word / Excel / PPT / MD / TXT</div>
            </div>
            <div v-else class="el-upload__text text-gray-400 p-4 flex flex-col items-center justify-center">
              <el-icon class="text-3xl mb-2 text-blue-400 is-loading"><Loading /></el-icon>
              <div>正在解析文档，请稍候...</div>
            </div>
          </el-upload>
          
          <div class="mt-4 relative">
            <el-input
              v-model="capsuleInput"
              type="textarea"
              :rows="4"
              placeholder="或者写下你的想法 (支持 Markdown)，或直接 Ctrl+V 粘贴截图..."
              resize="none"
              class="custom-textarea text-lg"
              @keydown.ctrl.enter="submitCapsule"
              @keydown.meta.enter="submitCapsule"
              @paste="handlePaste"
            />
            <div class="absolute bottom-3 right-3 flex items-center gap-3">
              <span class="text-xs text-gray-400">Ctrl + Enter 发送</span>
              <el-button 
                type="primary" 
                class="!rounded-lg font-bold px-6 shadow-md"
                :loading="isSubmitting"
                :disabled="!capsuleInput.trim()"
                @click="submitCapsule"
              >
                封存想法
                <el-icon class="ml-2"><Position /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 历史胶囊列表 -->
      <div class="flex justify-between items-center mb-4 shrink-0">
        <h2 class="text-lg font-bold text-gray-700 flex items-center">
          <el-icon class="mr-2 text-purple-500"><Collection /></el-icon>
          胶囊库 ({{ totalCapsules }})
        </h2>
        <div class="flex items-center gap-3">
          <el-input
            v-model="searchQuery"
            placeholder="搜索胶囊内容..."
            :prefix-icon="Search"
            clearable
            class="w-64"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
          <el-button link @click="fetchCapsules">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="flex-1 pb-20">
        <div v-loading="isLoading" class="space-y-4">
          <el-empty v-if="!isLoading && capsules.length === 0" description="没有找到匹配的胶囊" />
          
          <el-card 
            v-for="cap in capsules" 
            :key="cap.id" 
            :id="'capsule-' + cap.id"
            shadow="hover" 
            class="rounded-lg border border-gray-100 hover:shadow-md transition-all group relative cursor-pointer"
            :class="{'highlight-flash': highlightedCapsuleId === cap.id}"
            @click="openCapsuleDetail(cap)"
          >
            <div class="flex justify-between items-start mb-2">
              <span class="text-xs text-gray-400 font-mono">{{ formatDate(cap.created_at) }}</span>
              <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
                <el-button size="small" text type="primary" @click="openCapsuleDetail(cap, true)"><el-icon><Edit /></el-icon></el-button>
                <el-button size="small" text type="danger" @click="confirmDelete(cap)"><el-icon><Delete /></el-icon></el-button>
                <el-tag size="small" type="info" effect="plain">已入库</el-tag>
              </div>
            </div>
            <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed break-words overflow-hidden relative" style="max-height: 200px;">
              <div v-html="renderMarkdown(cap.content)"></div>
              <!-- 渐变遮罩 (用于内容过长时提示) -->
              <div class="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-white to-transparent"></div>
            </div>
          </el-card>
        </div>
      </div>
      
      <!-- 分页 (悬浮吸底) -->
      <div class="fixed bottom-0 left-0 w-full flex justify-center py-4 bg-gray-50/90 backdrop-blur-md z-20 border-t border-gray-200/50 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          background
          layout="total, sizes, prev, pager, next"
          :total="totalCapsules"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 全屏查看/编辑抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="editingMode ? '编辑胶囊' : '查看胶囊'"
      size="60%"
      destroy-on-close
      class="custom-drawer"
    >
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <h3 class="font-bold text-lg text-gray-800">{{ editingMode ? '编辑模式' : '沉浸阅读' }}</h3>
            <!-- 切换器：仅在查看模式且有附件时显示 -->
            <el-radio-group v-if="!editingMode && editingCapsule.file_url" v-model="capsuleViewMode" size="small">
              <el-radio-button label="file"><el-icon class="mr-1"><Document /></el-icon>原文件预览</el-radio-button>
              <el-radio-button label="text"><el-icon class="mr-1"><DocumentCopy /></el-icon>解析文本</el-radio-button>
            </el-radio-group>
          </div>
          <div class="flex gap-2">
            <el-button v-if="!editingMode" type="primary" plain size="small" @click="editingMode = true; capsuleViewMode = 'text'">
              <el-icon class="mr-1"><Edit /></el-icon> 编辑
            </el-button>
            <el-button v-if="editingMode" type="info" plain size="small" @click="editingMode = false; capsuleViewMode = editingCapsule.file_url ? 'file' : 'text'">
              <el-icon class="mr-1"><Reading /></el-icon> 预览
            </el-button>
          </div>
        </div>
      </template>

      <div class="h-full flex flex-col p-2">
        <div v-if="editingMode" class="flex-1 flex flex-col space-y-4">
          <div class="shrink-0">
            <el-input v-model="editingCapsule.title" placeholder="给胶囊起个名字 (可选)..." size="large" />
          </div>
          <div class="flex-1 min-h-0 relative bytemd-wrapper">
            <Editor
              :value="editingCapsule.content || ''"
              :plugins="plugins"
              @change="handleEditorChange"
              class="h-full custom-bytemd-editor"
              placeholder="在此修改你的 Markdown 内容..."
            />
          </div>
          <div class="shrink-0 flex justify-end gap-3 pt-4 border-t border-gray-100">
            <el-button @click="detailDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="isSavingEdit" @click="saveEdit">
              保存修改
            </el-button>
          </div>
        </div>

        <div v-else class="flex-1 flex flex-col min-h-0 bg-white">
          <!-- 有文件附件且处于文件预览模式时渲染 -->
          <div v-if="editingCapsule.file_url && capsuleViewMode === 'file'" class="flex-1 bg-gray-50 border border-gray-200 rounded-lg overflow-hidden flex flex-col h-full">
            <template v-if="getFileType(editingCapsule.file_type) === 'pdf'">
              <iframe :src="getFullUrl(editingCapsule.file_url)" class="w-full h-full border-0"></iframe>
            </template>
            <template v-else-if="getFileType(editingCapsule.file_type) === 'docx'">
              <vue-office-docx :src="getFullUrl(editingCapsule.file_url)" class="w-full h-full" />
            </template>
            <template v-else-if="getFileType(editingCapsule.file_type) === 'excel'">
              <vue-office-excel :src="getFullUrl(editingCapsule.file_url)" class="w-full h-full" />
            </template>
            <template v-else-if="getFileType(editingCapsule.file_type) === 'pptx'">
              <vue-office-pptx :src="getFullUrl(editingCapsule.file_url)" class="w-full h-full" />
            </template>
            <template v-else>
              <div class="p-8 text-center text-gray-500">该格式暂不支持直接预览，请<a :href="getFullUrl(editingCapsule.file_url)" target="_blank" class="text-blue-500 hover:underline">点击下载</a></div>
            </template>
          </div>

          <!-- 解析文本模式 -->
          <div v-else class="flex-1 overflow-auto custom-scrollbar">
            <div class="max-w-4xl mx-auto px-8 py-10" @mouseup="handleTextSelection">
              <h1 v-if="editingCapsule.title" class="text-4xl font-bold mb-8 text-gray-900 border-b pb-6">{{ editingCapsule.title }}</h1>
              <div class="markdown-body text-lg leading-loose">
                <Viewer
                  :value="editingCapsule.content"
                  :plugins="plugins"
                />
              </div>
              <div class="mt-16 pt-8 border-t border-gray-100 text-sm text-gray-400 text-center font-mono">
                记录于 {{ formatDate(editingCapsule.created_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 高亮悬浮菜单 -->
      <div 
        v-if="showHighlightMenu" 
        :style="{ top: highlightMenuPos.top + 'px', left: highlightMenuPos.left + 'px' }" 
        class="highlight-menu fixed z-50 bg-gray-800 text-white px-3 py-2 rounded-lg shadow-lg cursor-pointer hover:bg-gray-700 transition-colors flex items-center gap-2 text-sm font-medium"
        @mousedown.prevent="extractHighlight"
      >
        <el-icon><MagicStick /></el-icon> 提取为高亮胶囊
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

let ipcRenderer: any = null
try {
  if (typeof window !== 'undefined' && window.require) {
    ipcRenderer = window.require('electron').ipcRenderer
  }
} catch (e) {}
import { Position, Collection, Refresh, DocumentAdd, Loading, Search, Delete, Edit, Reading, Document, DocumentCopy, MagicStick } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
// @ts-ignore
import { Editor, Viewer } from '@bytemd/vue-next'
// @ts-ignore
import gfm from '@bytemd/plugin-gfm'
// @ts-ignore
import highlight from '@bytemd/plugin-highlight'
// @ts-ignore
import breaks from '@bytemd/plugin-breaks'
// @ts-ignore
import math from '@bytemd/plugin-math'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/vs.css'
import 'juejin-markdown-themes/dist/juejin.min.css' 
import VueOfficeDocx from '@vue-office/docx'
import VueOfficeExcel from '@vue-office/excel'
import VueOfficePptx from '@vue-office/pptx'
import '@vue-office/docx/lib/index.css'
import '@vue-office/excel/lib/index.css'

const plugins = [
  gfm(),
  highlight(),
  breaks(),
  math()
]

const route = useRoute()
const router = useRouter()

const API_BASE = 'http://localhost:8000/api'
const uploadUrl = `${API_BASE}/capsules/upload`

const capsuleInput = ref('')
const isSubmitting = ref(false)
const isLoading = ref(false)
const isUploading = ref(false)
const capsules = ref<any[]>([])

const authHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}
const totalCapsules = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const highlightedCapsuleId = ref<number | null>(null)

const detailDrawerVisible = ref(false)
const editingMode = ref(false)
const capsuleViewMode = ref('text') // 'text' or 'file'
const isSavingEdit = ref(false)
const editingCapsule = ref<any>({})

// 高亮提取闪念胶囊
const showHighlightMenu = ref(false)
const highlightMenuPos = ref({ top: 0, left: 0 })
const selectedText = ref('')

const handleTextSelection = () => {
  if (editingMode.value) return // 编辑模式下不弹悬浮窗
  const selection = window.getSelection()
  if (selection && selection.toString().trim().length > 0) {
    const text = selection.toString().trim()
    if (text.length > 5) {
      selectedText.value = text
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()
      highlightMenuPos.value = {
        top: rect.top - 45,
        left: rect.left + (rect.width / 2) - 60
      }
      showHighlightMenu.value = true
    } else {
      showHighlightMenu.value = false
    }
  } else {
    showHighlightMenu.value = false
  }
}

const extractHighlight = async () => {
  if (!selectedText.value || !editingCapsule.value) return
  try {
    const sourceLink = `[《${editingCapsule.value.title || '闪念胶囊'}》](/capsules)`
    const content = `> ${selectedText.value}\n> \n> — 摘自：${sourceLink}`
    
    await axios.post(`${API_BASE}/capsules`, {
      content: content,
      visibility: 'private'
    })
    
    ElMessage.success('✨ 已成功提取为高亮胶囊！')
    showHighlightMenu.value = false
    window.getSelection()?.removeAllRanges()
    fetchCapsules() // 刷新列表
  } catch (error) {
    ElMessage.error('提取高亮胶囊失败')
  }
}

const getFullUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `http://localhost:8000${path}`
}

const getFileType = (type: string) => {
  if (!type) return 'text'
  if (type.includes('pdf')) return 'pdf'
  if (type.includes('word') || type.includes('document')) return 'docx'
  if (type.includes('excel') || type.includes('spreadsheet')) return 'excel'
  if (type.includes('powerpoint') || type.includes('presentation')) return 'pptx'
  return 'text'
}

const renderMarkdown = (text: string) => {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text) as string)
}

const handleSearch = () => {
  currentPage.value = 1
  fetchCapsules()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchCapsules()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchCapsules()
}

const openCapsuleDetail = (cap: any, edit = false) => {
  editingCapsule.value = { ...cap }
  editingMode.value = edit
  capsuleViewMode.value = cap.file_url && !edit ? 'file' : 'text'
  detailDrawerVisible.value = true
}

const handleEditorChange = (v: string) => {
  editingCapsule.value.content = v
}

const saveEdit = async () => {
  isSavingEdit.value = true
  try {
    await axios.put(`${API_BASE}/capsules/${editingCapsule.value.id}`, {
      content: editingCapsule.value.content,
      title: editingCapsule.value.title || null
    })
    ElMessage.success('胶囊修改成功')
    editingMode.value = false // return to view mode
    fetchCapsules()
  } catch (error) {
    ElMessage.error('修改失败')
  } finally {
    isSavingEdit.value = false
  }
}

const confirmDelete = (cap: any) => {
  ElMessageBox.confirm('删除该胶囊会同时删除知识图谱中的关联节点，是否继续？', '警告', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`${API_BASE}/capsules/${cap.id}`)
      ElMessage.success('删除成功')
      // If deleting the last item on a page, go to previous page
      if (capsules.value.length === 1 && currentPage.value > 1) {
        currentPage.value--
      } else {
        fetchCapsules()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const beforeUpload = (_file: File) => {
  isUploading.value = true
  return true
}

const handleUploadSuccess = (response: any, file: any) => {
  isUploading.value = false
  if (response.status === 'success') {
    ElMessage.success(`文件 ${file.name} 已成功解析并入库！`)
    fetchCapsules()
  } else {
    ElMessage.error(response.message || '文件解析失败')
  }
}

const handleUploadError = (_error: any, file: any) => {
  isUploading.value = false
  ElMessage.error(`文件 ${file.name} 上传失败`)
}

const fetchCapsules = async () => {
  isLoading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const params: any = { skip, limit: pageSize.value }
    if (searchQuery.value) {
      params.keyword = searchQuery.value
    }
    const res = await axios.get(`${API_BASE}/capsules`, { params })
    // Backward compatibility if backend isn't updated yet
    if (Array.isArray(res.data)) {
      capsules.value = res.data
      totalCapsules.value = res.data.length
    } else {
      capsules.value = res.data.items
      totalCapsules.value = res.data.total
    }
    
    // Check for highlight parameter
    if (route.query.highlight_id) {
      highlightedCapsuleId.value = parseInt(route.query.highlight_id as string)
      nextTick(() => {
        const el = document.getElementById('capsule-' + highlightedCapsuleId.value)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' })
          // Remove query param without refreshing
          router.replace({ query: {} })
          // Remove highlight after 3 seconds
          setTimeout(() => {
            highlightedCapsuleId.value = null
          }, 3000)
        }
      })
    }
  } catch (error) {
    ElMessage.error('获取历史记录失败')
  } finally {
    isLoading.value = false
  }
}

const submitCapsule = async () => {
  if (!capsuleInput.value.trim() || isSubmitting.value) return
  
  isSubmitting.value = true
  try {
    // 自动提取第一行作为标题（最多20个字符）
    const lines = capsuleInput.value.split('\n').filter(l => l.trim())
    const title = lines.length > 0 ? lines[0].substring(0, 20) : '未命名胶囊'
    
    await axios.post(`${API_BASE}/capsules`, {
      content: capsuleInput.value,
      title: title
    })
    
    ElMessage.success('💡 灵感已封存并同步至知识库')
    capsuleInput.value = ''
    await fetchCapsules()
  } catch (error) {
    ElMessage.error('保存失败，请检查网络')
  } finally {
    isSubmitting.value = false
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

const handlePaste = async (e: ClipboardEvent) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const file = items[i].getAsFile()
      if (file) {
        e.preventDefault()
        await uploadImageFile(file)
        break
      }
    }
  }
}

const uploadImageFile = async (file: File) => {
  if (!beforeUpload(file)) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await axios.post(uploadUrl, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    handleUploadSuccess(res.data, file)
  } catch (error: any) {
    handleUploadError(error, file)
  }
}

onMounted(() => {
  fetchCapsules()
  
  if (ipcRenderer) {
    ipcRenderer.on('refresh-data', (_event: any, type: string) => {
      if (type === 'capsules') {
        fetchCapsules()
      }
    })
  }

  document.addEventListener('mousedown', (e) => {
    const target = e.target as HTMLElement
    if (target.closest('.highlight-menu')) return
    
    setTimeout(() => {
      const selection = window.getSelection()
      if (!selection || selection.toString().trim().length === 0) {
        showHighlightMenu.value = false
      }
    }, 100)
  })
})

onUnmounted(() => {
  if (ipcRenderer) {
    ipcRenderer.removeAllListeners('refresh-data')
  }
})

</script>

<style scoped>
.custom-textarea :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 16px 16px 48px 16px;
  background: transparent;
}
.custom-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}
:deep(.el-upload-dragger) {
  padding: 20px;
  border-radius: 12px;
  background-color: #f9fafb;
}
:deep(.el-upload-dragger:hover) {
  background-color: #f3f4f6;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-drawer .el-drawer__header {
  margin-bottom: 0;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
}
.custom-full-textarea :deep(.el-textarea__inner) {
  height: 100% !important;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 14px;
  line-height: 1.6;
  padding: 16px;
  border-radius: 8px;
}

/* ByteMD Style overrides */
.bytemd-wrapper :deep(.bytemd) {
  height: 100%;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}
.bytemd-wrapper :deep(.bytemd-preview) {
  padding: 24px;
}
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji';
}
</style>
<style>
@keyframes flashHighlight {
  0% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.7); border-color: #f97316; }
  50% { box-shadow: 0 0 0 10px rgba(249, 115, 22, 0); border-color: #f97316; }
  100% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0); }
}
.highlight-flash {
  animation: flashHighlight 1.5s ease-out 2;
  border-color: #f97316 !important;
}
</style>
