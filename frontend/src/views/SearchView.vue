<template>
  <div class="h-full flex flex-col bg-gray-50 max-w-5xl mx-auto w-full">
    <!-- Search Header -->
    <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mb-6 shrink-0">
      <h2 class="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
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
      <p class="text-xs text-gray-400 mt-3 flex items-center gap-1">
        <el-icon><InfoFilled /></el-icon>
        可直接输入自然语言，后台自动转换。也支持 arXiv API 高级语法 (如 au:bengio AND cat:cs.AI)
      </p>
    </div>

    <!-- Search Results -->
    <div class="flex-1 overflow-auto custom-scrollbar pr-2 pb-6">
      <div v-if="!hasSearched" class="h-full flex flex-col items-center justify-center text-gray-400">
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
          class="rounded-xl border border-gray-100 transition-shadow"
          :class="{'opacity-60 bg-gray-50': item.is_imported}"
        >
          <div class="flex justify-between items-start gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <el-tag size="small" type="warning" effect="dark">arXiv</el-tag>
                <span class="text-xs text-gray-400 font-mono">{{ formatDate(item.published) }}</span>
              </div>
              <h3 class="text-lg font-bold text-gray-800 leading-tight mb-2 hover:text-orange-600 transition-colors cursor-pointer">
                <a :href="item.url" target="_blank">{{ item.title }}</a>
              </h3>
              <p class="text-sm text-gray-500 mb-3 line-clamp-1 italic">
                <el-icon><User /></el-icon> {{ item.authors.join(', ') }}
              </p>
              <div class="text-sm text-gray-600 line-clamp-3 leading-relaxed">
                {{ item.summary }}
              </div>
            </div>
            
            <div class="shrink-0 flex flex-col items-end gap-2">
              <el-button 
                v-if="!item.is_imported" 
                type="primary" 
                plain 
                :loading="importingStates[item.url]"
                @click="importItem(item)"
              >
                <el-icon class="mr-1"><Download /></el-icon>
                加入知识库
              </el-button>
              <el-button v-else type="success" plain disabled>
                <el-icon class="mr-1"><Check /></el-icon>
                已入库
              </el-button>
              
              <el-tooltip content="在 arXiv 官网打开" placement="top">
                <a :href="item.url" target="_blank" class="text-gray-400 hover:text-orange-500 mt-2 inline-block p-2">
                  <el-icon :size="18"><TopRight /></el-icon>
                </a>
              </el-tooltip>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search, InfoFilled, Trophy, Download, Check, User, TopRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

const searchQuery = ref('')
const isSearching = ref(false)
const hasSearched = ref(false)
const results = ref<any[]>([])

// 记录各个条目的入库 Loading 状态，key 为 URL
const importingStates = ref<Record<string, boolean>>({})

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'Unknown Date'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const handleSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query) {
    ElMessage.warning('请输入检索词')
    return
  }
  
  isSearching.value = true
  hasSearched.value = true
  results.value = []
  
  try {
    const res = await axios.get(`${API_BASE}/search/external`, {
      params: { query, max_results: 15 }
    })
    results.value = res.data
  } catch (error) {
    ElMessage.error('检索失败，请检查网络或稍后重试')
  } finally {
    isSearching.value = false
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
    }
  } catch (error) {
    ElMessage.error('入库失败')
  } finally {
    importingStates.value[item.url] = false
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
</style>
