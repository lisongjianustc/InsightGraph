<template>
  <div class="h-full w-full bg-white relative flex flex-col">
    <!-- Header -->
    <div class="absolute top-4 left-4 z-10">
      <el-card shadow="hover" class="rounded-xl bg-white/90 backdrop-blur-sm border-0">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold text-gray-800 mb-1 flex items-center gap-2">
              <el-icon class="text-blue-500"><Connection /></el-icon>
              知识图谱网络
            </h2>
            <p class="text-xs text-gray-500">连接文章、胶囊和核心实体标签</p>
          </div>
          <div class="flex flex-col gap-2">
            <el-button type="primary" size="small" plain @click="fetchGraphData" :loading="loading">
              <el-icon><Refresh /></el-icon> 刷新网络
            </el-button>
            <el-button type="warning" size="small" plain @click="triggerBuild" :loading="building">
              <el-icon><MagicStick /></el-icon> 补全关系
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图例 -->
    <div class="absolute bottom-4 left-4 z-10">
      <el-card shadow="hover" class="rounded-xl bg-white/90 backdrop-blur-sm border-0">
        <div class="text-sm font-bold text-gray-700 mb-2">节点类型</div>
        <div class="flex flex-col gap-2 text-xs">
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#ef4444]"></span> 实体概念 (Tag)</div>
          <div class="text-gray-400 mt-1 italic">（点击概念展开相关文献与胶囊）</div>
        </div>
      </el-card>
    </div>

    <!-- ECharts 容器 -->
    <div ref="chartRef" class="flex-1 w-full" v-loading="loading"></div>

    <!-- 节点详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`概念标签: ${selectedNode?.name}`"
      size="40%"
      destroy-on-close
    >
      <div class="p-4" v-if="selectedNode">
        <div class="mb-4">
          <el-tag type="danger" effect="dark" size="large" class="font-bold text-lg"># {{ selectedNode.name }}</el-tag>
        </div>

        <!-- 概念释义区 -->
        <div class="bg-indigo-50 border border-indigo-100 p-4 rounded-lg mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-bold text-indigo-800 flex items-center gap-2">
              <el-icon><InfoFilled /></el-icon> 概念释义
            </h3>
            <el-button 
              v-if="!loadingDefinition && (tagDefinition.includes('获取定义失败') || tagDefinition === '暂无释义' || !tagDefinition)" 
              size="small" type="primary" plain round @click="fetchTagDefinition(selectedNode, true)">
              <el-icon class="mr-1"><Refresh /></el-icon> 重新获取
            </el-button>
          </div>
          <div v-if="loadingDefinition" class="flex items-center gap-2 text-indigo-400 text-sm py-2">
            <el-icon class="is-loading"><Loading /></el-icon> 正在由 AI 生成专业释义...
          </div>
          <div v-else class="text-sm text-indigo-900 leading-relaxed whitespace-pre-wrap">
            {{ tagDefinition || '暂无释义' }}
          </div>
        </div>

        <div class="bg-gray-50 p-4 rounded-lg">
          <h3 class="font-bold text-gray-700 mb-4 flex items-center gap-2">
            <el-icon><Connection /></el-icon> 相关文献 / 胶囊 ({{ selectedNode.docs?.length || 0 }})
          </h3>
          <div v-if="selectedNode.docs?.length > 0" class="space-y-3">
            <div v-for="(doc, index) in selectedNode.docs" :key="index" 
                 class="bg-white p-3 rounded border border-gray-200 shadow-sm transition-colors"
                 :class="{'hover:border-indigo-300 cursor-pointer': doc.type === 'skim' || doc.type === 'deep'}"
                 @click="(doc.type === 'skim' || doc.type === 'deep') ? openDoc(doc) : null">
              <div class="flex items-start justify-between gap-2">
                <span class="text-sm font-medium text-gray-800 line-clamp-2 leading-snug transition-colors" :class="{'hover:text-indigo-600': doc.type === 'skim' || doc.type === 'deep'}">{{ doc.name }}</span>
                <el-tag :type="getTagType(doc.type)" size="small" class="shrink-0">{{ doc.type.toUpperCase() }}</el-tag>
              </div>
              <div v-if="doc.type === 'capsule'" class="mt-2 text-xs text-gray-500 line-clamp-3 bg-gray-50 p-2 rounded cursor-pointer hover:bg-gray-100 transition-colors" @click="openDoc(doc)">
                {{ doc.content }}
              </div>
              
              <!-- 胶囊/原文类型的操作栏 -->
              <div v-if="doc.type === 'capsule' || doc.type === 'original'" class="mt-3 flex flex-wrap gap-2 pt-2 border-t border-gray-100">
                <template v-if="doc.type === 'original'">
                  <el-button v-if="doc.url" size="small" text bg type="primary" @click="openDoc(doc, 'url')">
                    <el-icon class="mr-1"><Link /></el-icon>查看来源网页
                  </el-button>
                  <el-button v-if="doc.pdf_url" size="small" text bg type="warning" @click="openDoc(doc, 'pdf')">
                    <el-icon class="mr-1"><Document /></el-icon>打开原PDF
                  </el-button>
                </template>
                <template v-if="doc.type === 'capsule'">
                  <el-button size="small" text bg type="primary" @click="openDoc(doc)">
                    <el-icon class="mr-1"><Link /></el-icon>查看胶囊
                  </el-button>
                  <el-button v-if="doc.file_url" size="small" text bg type="warning" @click="openDoc(doc, 'pdf')">
                    <el-icon class="mr-1"><Document /></el-icon>打开原文件
                  </el-button>
                </template>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无关联文档" :image-size="60" />
        </div>
      </div>
    </el-drawer>

    <!-- 知识沉淀卡片 (用于展示精读/泛读节点详情) -->
    <el-dialog
      v-model="knowledgeDialogVisible"
      :title="knowledgeDialogData?.type === 'skim' ? '📖 泛读沉淀' : '🧠 精读知识点'"
      width="60%"
      destroy-on-close
      class="knowledge-dialog"
    >
      <div v-if="knowledgeDialogData" class="knowledge-card">
        <h2 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">{{ knowledgeDialogData.name }}</h2>
        <div class="prose max-w-none prose-lg text-gray-700 leading-relaxed bg-orange-50/30 p-8 rounded-xl border border-orange-100 shadow-inner whitespace-pre-wrap" v-html="renderMarkdown(knowledgeDialogData.content)">
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, markRaw } from 'vue'
import { Connection, Refresh, MagicStick, InfoFilled, Loading, Link, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const API_BASE = 'http://localhost:8000/api'
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const loading = ref(false)
const building = ref(false)
const knowledgeDialogVisible = ref(false)
const knowledgeDialogData = ref<any>(null)

const renderMarkdown = (text: string) => {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text) as string)
}

const drawerVisible = ref(false)
const selectedNode = ref<any>(null)
const tagDefinition = ref('')
const loadingDefinition = ref(false)

// 颜色映射
const colorMap: Record<string, string> = {
  original: '#3b82f6',
  skim: '#10b981',
  deep: '#f59e0b',
  capsule: '#8b5cf6',
  tag: '#ef4444'
}

const getTagType = (type: string) => {
  if (type === 'original') return 'primary'
  if (type === 'skim') return 'success'
  if (type === 'deep') return 'warning'
  if (type === 'capsule') return 'danger'
  return 'info'
}

const openDoc = (doc: any, action?: string) => {
  if (doc.type === 'original') {
    if (action === 'pdf' && doc.pdf_url) {
      window.open(doc.pdf_url, '_blank')
    } else if (doc.url) {
      window.open(doc.url, '_blank')
    }
  } else if (doc.type === 'capsule') {
    if (action === 'pdf' && doc.file_url) {
      // 如果直接打开原文件，拼接完整路径
      const fileUrl = doc.file_url.startsWith('http') ? doc.file_url : `${API_BASE.replace('/api', '')}${doc.file_url}`
      window.open(fileUrl, '_blank')
    } else {
      // Navigate to capsule view and auto-highlight
      window.open(`/capsule?highlight_id=${doc.ref_id}`, '_blank')
    }
  } else if (doc.type === 'skim' || doc.type === 'deep') {
    knowledgeDialogData.value = doc
    knowledgeDialogVisible.value = true
  } else {
    ElMessage.info('该类型节点暂不支持直接跳转')
  }
}

const fetchTagDefinition = async (node: any, force = false) => {
  if (!force && node.content && !node.content.startsWith('Tag:') && !node.content.includes('获取定义失败')) {
    tagDefinition.value = node.content
    return
  }
  loadingDefinition.value = true
  tagDefinition.value = ''
  try {
    const res = await axios.get(`${API_BASE}/graph/tag/${node.id}/definition`, { params: { force: force ? true : undefined } })
    tagDefinition.value = res.data.definition
    node.content = res.data.definition // update local cache
  } catch (error) {
    tagDefinition.value = '获取定义失败，请检查网络或 Dify 配置'
    node.content = tagDefinition.value
  } finally {
    loadingDefinition.value = false
  }
}

const fetchGraphData = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/graph/data`)
    renderChart(res.data)
  } catch (error) {
    ElMessage.error('获取图谱数据失败')
  } finally {
    loading.value = false
  }
}

const triggerBuild = async () => {
  building.value = true
  try {
    await axios.post(`${API_BASE}/graph/build`)
    ElMessage.success('已触发后台大模型抽取关系任务，请稍后刷新查看')
  } catch (error) {
    ElMessage.error('触发关系补全失败')
  } finally {
    building.value = false
  }
}

const renderChart = (data: any) => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = markRaw(echarts.init(chartRef.value))
    
    // 绑定点击事件
    chartInstance.on('click', (params: any) => {
      if (params.dataType === 'node') {
        selectedNode.value = params.data
        drawerVisible.value = true
        fetchTagDefinition(params.data)
      }
    })
  }

  const rawNodes = data.nodes || []
  const rawEdges = data.edges || []

  // 1. Separate tags and documents
  const tags = rawNodes.filter((n: any) => n.type === 'tag')
  const docs = rawNodes.filter((n: any) => n.type !== 'tag')

  // 2. Map doc ID -> doc Object
  const docMap = new Map(docs.map((d: any) => [d.id, d]))

  // 3. Map tag ID -> Array of related docs
  const tagDocsMap = new Map()
  tags.forEach((t: any) => tagDocsMap.set(t.id, []))

  rawEdges.forEach((e: any) => {
    const sourceIsTag = tagDocsMap.has(e.source)
    const targetIsTag = tagDocsMap.has(e.target)

    if (sourceIsTag && docMap.has(e.target)) {
      tagDocsMap.get(e.source).push(docMap.get(e.target))
    } else if (targetIsTag && docMap.has(e.source)) {
      tagDocsMap.get(e.target).push(docMap.get(e.source))
    }
  })

  // 4. Generate Tag-to-Tag co-occurrence edges
  const tagEdges: any[] = []
  const edgeSet = new Set()

  docs.forEach((doc: any) => {
    // Find all tags connected to this doc
    const docTags = tags.filter((t: any) => {
      const relatedDocs = tagDocsMap.get(t.id) || []
      return relatedDocs.some((d: any) => d.id === doc.id)
    })

    // Create combinations of tags that share this doc
    for (let i = 0; i < docTags.length; i++) {
      for (let j = i + 1; j < docTags.length; j++) {
        const t1 = docTags[i].id
        const t2 = docTags[j].id
        const key = t1 < t2 ? `${t1}-${t2}` : `${t2}-${t1}`
        
        if (!edgeSet.has(key)) {
          edgeSet.add(key)
          tagEdges.push({
            source: t1,
            target: t2,
            lineStyle: {
              width: 1,
              curveness: 0.1,
              opacity: 0.2
            }
          })
        }
      }
    }
  })

  // 5. Build final nodes (Only Tags)
  const nodes = tags.map((node: any) => {
    const relatedDocs = tagDocsMap.get(node.id) || []
    return {
      id: node.id,
      name: node.name,
      fullName: node.name,
      type: node.type,
      docs: relatedDocs,
      // Node size based on how many docs are connected to this tag
      symbolSize: 20 + Math.min(relatedDocs.length * 5, 40),
      itemStyle: {
        color: colorMap[node.type] || '#9ca3af'
      }
    }
  })

  const option = {
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          return `<b>${params.data.type.toUpperCase()}</b><br/>${params.data.fullName}`
        }
        return ''
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        nodes: nodes,
        edges: tagEdges,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          color: '#4b5563',
          fontSize: 12
        },
        force: {
          repulsion: 300,
          edgeLength: 100,
          gravity: 0.1
        },
        lineStyle: {
          color: '#cbd5e1'
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          }
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  fetchGraphData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
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
