<template>
  <div class="h-screen bg-gray-50 flex flex-col items-center pt-10 px-4 relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute top-0 w-full h-64 bg-gradient-to-b from-purple-100 to-transparent pointer-events-none"></div>

    <div class="max-w-3xl w-full z-10 flex flex-col h-full">
      <!-- 头部 -->
      <div class="text-center mb-8 shrink-0">
        <h1 class="text-4xl font-extrabold text-gray-800 tracking-tight mb-2">⚡️ 闪念胶囊</h1>
        <p class="text-gray-500">记录一闪而过的灵感、文档或碎片化信息，自动构建专属知识网络</p>
      </div>

      <!-- 输入区 -->
      <el-card shadow="hover" class="rounded-xl border-0 overflow-visible mb-8 shrink-0">
        <div class="relative">
          <el-upload
            class="w-full"
            drag
            :action="uploadUrl"
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
              placeholder="或者写下你的想法 (支持 Markdown)..."
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
          最近封存
        </h2>
        <el-button link @click="fetchCapsules">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>

      <div class="flex-1 overflow-auto pb-8 custom-scrollbar">
        <div v-loading="isLoading" class="space-y-4">
          <el-empty v-if="!isLoading && capsules.length === 0" description="还没有记录任何灵感" />
          
          <el-card 
            v-for="cap in capsules" 
            :key="cap.id" 
            shadow="never" 
            class="rounded-lg border border-gray-100 hover:shadow-md transition-shadow group"
          >
            <div class="flex justify-between items-start mb-2">
              <span class="text-xs text-gray-400 font-mono">{{ formatDate(cap.created_at) }}</span>
              <el-tag size="small" type="info" effect="plain" class="opacity-0 group-hover:opacity-100 transition-opacity">已入库</el-tag>
            </div>
            <div class="prose max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed text-sm break-words overflow-hidden" style="max-height: 300px; overflow-y: auto;">
              {{ cap.content }}
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Position, Collection, Refresh, DocumentAdd, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'
const uploadUrl = `${API_BASE}/capsules/upload`

const capsuleInput = ref('')
const isSubmitting = ref(false)
const isLoading = ref(false)
const isUploading = ref(false)
const capsules = ref<any[]>([])

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
    const res = await axios.get(`${API_BASE}/capsules`)
    capsules.value = res.data
  } catch (error) {
    ElMessage.error('获取胶囊历史失败')
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
</style>
