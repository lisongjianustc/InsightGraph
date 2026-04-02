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
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#3b82f6]"></span> 原文文档 (Original)</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#10b981]"></span> 泛读摘要 (Skim)</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#f59e0b]"></span> 精读对话 (Deep)</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#8b5cf6]"></span> 闪念胶囊 (Capsule)</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#ef4444]"></span> 实体标签 (Tag)</div>
        </div>
      </el-card>
    </div>

    <!-- ECharts 容器 -->
    <div ref="chartRef" class="flex-1 w-full" v-loading="loading"></div>

    <!-- 节点详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="selectedNode?.name"
      size="40%"
      destroy-on-close
    >
      <div class="p-4" v-if="selectedNode">
        <div class="mb-4 flex gap-2">
          <el-tag :type="getTagType(selectedNode.type)">{{ selectedNode.type.toUpperCase() }}</el-tag>
          <el-tag type="info">ID: {{ selectedNode.id }}</el-tag>
        </div>
        <div class="bg-gray-50 p-4 rounded-lg">
          <h3 class="font-bold text-gray-700 mb-2">内容预览：</h3>
          <div class="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto custom-scrollbar">
            {{ selectedNode.content || '无内容' }}
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, markRaw } from 'vue'
import { Connection, Refresh, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const loading = ref(false)
const building = ref(false)

const drawerVisible = ref(false)
const selectedNode = ref<any>(null)

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
      }
    })
  }

  const nodes = data.nodes.map((node: any) => ({
    id: node.id,
    name: node.type === 'tag' ? node.name : (node.name.length > 15 ? node.name.substring(0, 15) + '...' : node.name),
    fullName: node.name,
    type: node.type,
    content: node.content,
    symbolSize: node.type === 'tag' ? 20 : (node.type === 'original' ? 40 : 30),
    itemStyle: {
      color: colorMap[node.type] || '#9ca3af'
    }
  }))

  const edges = data.edges.map((edge: any) => ({
    source: edge.source,
    target: edge.target,
    lineStyle: {
      width: 2,
      curveness: 0.2,
      opacity: 0.7
    }
  }))

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
        edges: edges,
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
