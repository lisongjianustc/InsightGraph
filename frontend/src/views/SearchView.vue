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
      <div class="flex items-center justify-between mt-3">
        <p class="text-xs text-gray-400 flex items-center gap-1">
          <el-icon><InfoFilled /></el-icon>
          支持双引号精确短语匹配 (如: "large language models" agent)。也可直接使用 arXiv API 高级语法 (如 au:bengio AND cat:cs.AI)
        </p>
        <div v-if="hasSearched && results.length > 0" class="flex items-center gap-2">
          <span class="text-xs text-gray-500">结果排序:</span>
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
          class="rounded-xl border border-gray-100 transition-shadow relative"
          :class="{'bg-gray-50/50': item.is_imported}"
        >
          <div class="absolute left-4 top-4 z-10">
            <el-checkbox v-model="item.selected" size="large" />
          </div>
          
          <div class="flex justify-between items-start gap-4 pl-8">
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
                
                <!-- 精读按钮 -->
                <el-button 
                  v-if="item.status === 'deep_read'" 
                  type="info" 
                  disabled 
                  class="w-full !ml-0"
                >
                  <el-icon class="mr-1"><Check /></el-icon>
                  已深度入库
                </el-button>
                <el-button 
                  v-else 
                  type="warning" 
                  plain 
                  :loading="deepReadingStates[item.local_id]"
                  @click="handleDeepRead(item)"
                  class="w-full !ml-0"
                >
                  <el-icon class="mr-1"><DataLine /></el-icon>
                  精读入图谱
                </el-button>
              </template>
              
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
    
    <!-- 悬浮批量操作栏 -->
    <div v-if="selectedItems.length > 0" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-md px-6 py-4 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-gray-200 flex items-center gap-6 z-50 transition-all">
      <span class="text-gray-600 font-medium">已选择 <span class="text-orange-600 font-bold text-lg">{{ selectedItems.length }}</span> 篇文献</span>
      <div class="h-6 w-px bg-gray-300"></div>
      <el-button type="primary" size="large" :loading="isBatchImporting" @click="handleBatchImport" class="px-8 font-bold shadow-md shadow-orange-500/20">
        <el-icon class="mr-2"><Download /></el-icon>
        批量加入知识库
      </el-button>
      <el-button link @click="clearSelection" class="text-gray-400 hover:text-gray-600">取消选择</el-button>
    </div>

    <!-- 泛读摘要弹窗 -->
    <el-dialog v-model="skimDialogVisible" title="🤖 AI 泛读摘要 (Key Takeaways)" width="50%" destroy-on-close>
      <div v-if="currentSkimContent" class="prose max-w-none text-gray-700 leading-relaxed text-sm bg-gray-50 p-6 rounded-lg border border-gray-100" v-html="renderMarkdown(currentSkimContent)">
      </div>
      <div v-else class="flex flex-col items-center justify-center py-12 text-gray-400">
        <el-icon class="is-loading text-4xl mb-4 text-blue-400"><Loading /></el-icon>
        <p>大模型正在后台努力阅读并生成摘要，请稍候再来看...</p>
      </div>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, InfoFilled, Trophy, Download, Check, User, TopRight, Document, DataLine, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const API_BASE = 'http://localhost:8000/api'

const searchQuery = ref('')
const sortBy = ref('submittedDate')
const sortOrder = ref('descending')
const isSearching = ref(false)
const hasSearched = ref(false)
const results = ref<any[]>([])

// 记录各个条目的入库 Loading 状态，key 为 URL
const importingStates = ref<Record<string, boolean>>({})
const deepReadingStates = ref<Record<number, boolean>>({})
const isBatchImporting = ref(false)

// 泛读弹窗相关
const skimDialogVisible = ref(false)
const currentSkimContent = ref('')

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
  results.value = []
  
  try {
    // 强制使用 relevance 检索作为基础数据，以便前端能进行双向排序
    const res = await axios.get(`${API_BASE}/search/external`, {
      params: { 
        query, 
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

const handleDeepRead = async (item: any) => {
  if (!item.local_id) return
  
  deepReadingStates.value[item.local_id] = true
  try {
    const res = await axios.post(`${API_BASE}/feed/${item.local_id}/save_to_kb`)
    if (res.data.status === 'success') {
      ElMessage.success('精读并入库成功，已生成知识图谱节点！')
      item.status = 'deep_read'
      item.is_saved_to_kb = true
    }
  } catch (error) {
    ElMessage.error('精读失败')
  } finally {
    deepReadingStates.value[item.local_id] = false
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
