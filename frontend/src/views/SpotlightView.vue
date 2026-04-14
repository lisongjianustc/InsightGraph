<template>
  <div class="w-full h-full flex flex-col justify-center bg-transparent items-center p-4" style="-webkit-app-region: drag">
    <div class="w-full max-w-2xl bg-gray-900/90 backdrop-blur-xl rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-gray-700/50 overflow-hidden flex flex-col px-4 relative" style="-webkit-app-region: no-drag">
      <div class="flex items-center w-full">
        <el-icon class="text-indigo-400 mr-3" :size="24"><MagicStick /></el-icon>
        <input 
          ref="inputRef"
          v-model="content"
          @keyup.enter="submit"
          @keyup.esc="hide"
          @paste="handlePaste"
          type="text"
          placeholder="记录闪念胶囊... (支持 Ctrl+V 粘贴截图或网址)"
          class="flex-1 bg-transparent border-none outline-none text-white text-xl py-5 placeholder-gray-500 font-medium"
          :disabled="loading"
        />
        <div class="flex items-center ml-2 mr-2">
          <el-switch
            v-model="isPrivate"
            inline-prompt
            active-text="私密"
            inactive-text="公开"
            style="--el-switch-on-color: #6366f1; --el-switch-off-color: #10b981"
          />
        </div>
        <div v-if="pastedImage" class="h-12 w-12 rounded bg-gray-800 border border-gray-600 overflow-hidden flex items-center justify-center p-1 relative ml-2">
          <img :src="pastedImagePreview" class="max-w-full max-h-full object-contain" />
          <button @click="clearImage" class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] hover:bg-red-600">×</button>
        </div>
        <div v-if="loading" class="flex items-center justify-center w-8 h-8 ml-2">
          <svg class="animate-spin h-5 w-5 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <div v-else-if="success" class="flex items-center justify-center w-8 h-8 ml-2 text-green-400">
          <el-icon :size="20"><Check /></el-icon>
        </div>
      </div>
      <div v-if="detectedUrl" class="w-full text-xs text-gray-400 pb-2 flex items-center gap-1">
        <el-icon><Link /></el-icon> 将自动抓取链接内容入库
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { MagicStick, Check, Link } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE = 'http://localhost:8000/api'
const content = ref('')
const loading = ref(false)
const success = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const isPrivate = ref(true)

const pastedImage = ref<File | null>(null)
const pastedImagePreview = ref<string>('')
const detectedUrl = ref(false)

let ipcRenderer: any = null
try {
  // Use window.require to bypass Vite's dependency resolution since nodeIntegration is true
  if (typeof window !== 'undefined' && window.require) {
    ipcRenderer = window.require('electron').ipcRenderer
  }
} catch (e) {
  console.warn('Not in electron environment')
}

watch(content, (newVal) => {
  // 简单判断是否是 http 链接
  const urlRegex = /^(https?:\/\/[^\s]+)$/
  detectedUrl.value = urlRegex.test(newVal.trim())
})

const hide = () => {
  if (ipcRenderer) {
    ipcRenderer.send('hide-spotlight')
  }
}

const clearImage = () => {
  pastedImage.value = null
  pastedImagePreview.value = ''
}

const handlePaste = (e: ClipboardEvent) => {
  if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
    const file = e.clipboardData.files[0]
    if (file.type.startsWith('image/')) {
      e.preventDefault()
      pastedImage.value = file
      pastedImagePreview.value = URL.createObjectURL(file)
      // 如果只粘贴了图片，没有任何文字，可以直接回车提交
      if (!content.value) {
        content.value = `[图片: ${file.name}]`
      }
    }
  }
}

const submit = async () => {
  if (!content.value.trim() && !pastedImage.value) return
  
  loading.value = true
  success.value = false
  
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.warning('请先在主窗口登录')
      hide()
      return
    }

    const visibility = isPrivate.value ? 'private' : 'public'

    if (pastedImage.value) {
      // 走文件上传接口 (图片 OCR)
      const formData = new FormData()
      formData.append('file', pastedImage.value)
      formData.append('visibility', visibility)
      await axios.post(`${API_BASE}/capsules/upload`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })
    } else if (detectedUrl.value) {
      // 检测到单 URL，触发专门的链接抓取接口（此为A3需求，由后端自动爬取网页）
      await axios.post(`${API_BASE}/capsules/url`, 
        { url: content.value.trim(), visibility },
        { headers: { Authorization: `Bearer ${token}` } }
      )
    } else {
      // 纯文本接口
      await axios.post(`${API_BASE}/capsules`, 
        { content: content.value, visibility },
        { headers: { Authorization: `Bearer ${token}` } }
      )
    }
    
    success.value = true
    content.value = ''
    clearImage()
    
    // 通知主窗口刷新胶囊列表
    if (ipcRenderer) {
      ipcRenderer.send('refresh-main-window', 'capsules')
    }
    
    setTimeout(() => {
      success.value = false
      hide()
    }, 800)
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Focus the input whenever the window gains focus
  window.addEventListener('focus', () => {
    inputRef.value?.focus()
  })
  // Initial focus
  setTimeout(() => inputRef.value?.focus(), 100)
})
</script>

<style scoped>
/* Hide the scrollbar for spotlight */
::-webkit-scrollbar {
  display: none;
}
</style>
