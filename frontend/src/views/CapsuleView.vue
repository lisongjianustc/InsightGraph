<template>
  <div class="h-screen bg-gray-50 flex flex-col items-center pt-10 px-4 relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute top-0 w-full h-64 bg-gradient-to-b from-purple-100 to-transparent pointer-events-none"></div>

    <div class="max-w-3xl w-full z-10 flex flex-col h-full">
      <!-- 头部 -->
      <div class="text-center mb-4 shrink-0">
        <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-2">⚡️ 闪念胶囊</h1>
        <p class="text-sm text-gray-500">记录一闪而过的灵感碎片，自动构建专属知识网络</p>
      </div>

      <!-- 紧凑型输入区 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 transition-all duration-300 focus-within:shadow-md focus-within:border-purple-300 mb-6 shrink-0 overflow-hidden relative">
        <el-input
          v-model="capsuleInput"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 8 }"
          placeholder="写下你的想法 (支持 Markdown)，或直接 Ctrl+V 粘贴截图..."
          resize="none"
          class="compact-textarea text-base"
          @keydown.ctrl.enter="submitCapsule"
          @keydown.meta.enter="submitCapsule"
          @paste="handlePaste"
        />
        <div class="flex justify-between items-center px-4 py-3 bg-gray-50/80 border-t border-gray-100">
          <div class="flex items-center gap-2">
            <el-upload
              :action="uploadUrl"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              name="file"
              class="inline-flex items-center"
            >
              <el-button size="small" class="!border-gray-200 hover:!border-purple-300 hover:!text-purple-600 transition-colors" plain>
                <el-icon class="mr-1 text-base"><DocumentAdd /></el-icon>
                <span class="hidden sm:inline">上传文档/图文</span>
              </el-button>
            </el-upload>
            <span v-if="isUploading" class="text-xs text-purple-600 flex items-center gap-1 bg-purple-100/50 px-2 py-1 rounded">
              <el-icon class="is-loading"><Loading /></el-icon> AI 解析中...
            </span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400 hidden sm:inline">Ctrl + Enter 发送</span>
            <el-button 
              type="primary" 
              class="!rounded-lg font-bold px-6 shadow-sm"
              :loading="isSubmitting"
              :disabled="!capsuleInput.trim()"
              @click="submitCapsule"
            >
              封存想法
              <el-icon class="ml-1"><Position /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

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

      <div class="flex-1 overflow-auto pb-4 custom-scrollbar">
        <div v-loading="isLoading" class="space-y-4">
          <el-empty v-if="!isLoading && capsules.length === 0" description="没有找到匹配的胶囊" />
          
          <el-card 
            v-for="cap in capsules" 
            :key="cap.id" 
            shadow="never" 
            class="rounded-lg border border-gray-100 hover:shadow-md transition-shadow group relative"
          >
            <div class="flex justify-between items-start mb-2">
              <span class="text-xs text-gray-400 font-mono">{{ formatDate(cap.created_at) }}</span>
              <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <el-button size="small" text type="primary" @click="openEditDialog(cap)"><el-icon><Edit /></el-icon></el-button>
                <el-button size="small" text type="danger" @click="confirmDelete(cap)"><el-icon><Delete /></el-icon></el-button>
                <el-tag size="small" type="info" effect="plain">已入库</el-tag>
              </div>
            </div>
            <div class="prose max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed text-sm break-words overflow-hidden" style="max-height: 300px; overflow-y: auto;">
              {{ cap.content }}
            </div>
          </el-card>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="shrink-0 flex justify-center py-4 bg-gray-50/80 backdrop-blur-sm z-10 border-t border-gray-100">
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
    
    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑胶囊" width="50%" destroy-on-close>
      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium text-gray-700 mb-1 block">标题 (可选)</label>
          <el-input v-model="editingCapsule.title" placeholder="给胶囊起个名字..." />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700 mb-1 block">内容</label>
          <el-input v-model="editingCapsule.content" type="textarea" :rows="10" placeholder="修改你的想法..." />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isSavingEdit" @click="saveEdit">
            保存修改
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Position, Collection, Refresh, DocumentAdd, Loading, Search, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'
const uploadUrl = `${API_BASE}/capsules/upload`

const capsuleInput = ref('')
const isSubmitting = ref(false)
const isLoading = ref(false)
const isUploading = ref(false)
const capsules = ref<any[]>([])
const totalCapsules = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

const editDialogVisible = ref(false)
const isSavingEdit = ref(false)
const editingCapsule = ref<any>({})

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

const openEditDialog = (cap: any) => {
  editingCapsule.value = { ...cap }
  editDialogVisible.value = true
}

const saveEdit = async () => {
  isSavingEdit.value = true
  try {
    await axios.put(`${API_BASE}/capsules/${editingCapsule.value.id}`, {
      content: editingCapsule.value.content,
      title: editingCapsule.value.title || null
    })
    ElMessage.success('胶囊修改成功')
    editDialogVisible.value = false
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
})
</script>

<style scoped>
.compact-textarea :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 16px 16px 12px 16px;
  background: transparent;
}
.compact-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
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
</style>
