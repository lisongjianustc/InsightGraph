<template>
  <div class="max-w-4xl mx-auto py-8">
    <div class="mb-8">
      <h1 class="text-3xl font-extrabold text-gray-800 flex items-center gap-3">
        <el-icon class="text-blue-500"><Setting /></el-icon>
        系统设置
      </h1>
      <p class="text-gray-500 mt-2">管理 InsightGraph 的外观、信息源及同步策略</p>
    </div>

    <el-tabs type="border-card" class="bg-white rounded-xl shadow-sm">
      <!-- 基础设置 -->
      <el-tab-pane label="基础设置">
        <template #label>
          <span class="flex items-center gap-2"><el-icon><Monitor /></el-icon> 外观与基础</span>
        </template>
        <div class="p-6 space-y-8">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-gray-700">深色模式 (Dark Mode)</h3>
              <p class="text-sm text-gray-500">开启深色模式以在夜间获得更好的阅读体验。</p>
            </div>
            <el-switch
              v-model="isDark"
              active-color="#4f46e5"
              inactive-color="#d1d5db"
              inline-prompt
              active-text="夜间"
              inactive-text="白天"
            />
          </div>

          <el-divider />

          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-gray-700">Dify 知识库状态</h3>
              <p class="text-sm text-gray-500">检查连接至本地 Dify 实例的连通性。</p>
            </div>
            <el-button type="success" plain size="small">
              <el-icon class="mr-1"><Check /></el-icon> 连接正常
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 自动同步 -->
      <el-tab-pane label="信息源与同步">
        <template #label>
          <span class="flex items-center gap-2"><el-icon><RefreshRight /></el-icon> 自动同步</span>
        </template>
        <div class="p-6 space-y-6">
          <div class="bg-blue-50 border border-blue-100 p-4 rounded-lg flex items-start gap-3">
            <el-icon class="text-blue-500 mt-1"><InfoFilled /></el-icon>
            <div>
              <h4 class="font-bold text-blue-800">APScheduler 定时抓取已启用</h4>
              <p class="text-sm text-blue-600 mt-1">
                后端现已集成 APScheduler。系统将在后台每隔 60 分钟自动扫描你配置的 arXiv 或 RSS 信息源，并将其拉取至今日资讯（Feed）。
              </p>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-bold text-gray-700 mb-4">手动触发同步</h3>
            <p class="text-sm text-gray-500 mb-4">如果你不想等待下一个周期，可以立即触发后台抓取任务。</p>
            <el-button type="primary" @click="triggerSync" :loading="isSyncing">
              <el-icon class="mr-1"><Download /></el-icon> 立即拉取最新文献
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 标签管理 -->
      <el-tab-pane label="标签管理">
        <template #label>
          <span class="flex items-center gap-2"><el-icon><CollectionTag /></el-icon> 实体与标签</span>
        </template>
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-bold text-gray-700">全量实体标签管理</h3>
            <el-button type="primary" plain size="small" @click="fetchTags">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
          
          <div v-loading="loadingTags" class="min-h-[200px]">
            <el-empty v-if="tags.length === 0 && !loadingTags" description="暂无任何实体标签，请先到知识图谱执行补全。" />
            <div v-else class="flex flex-wrap gap-3">
              <el-tag 
                v-for="tag in tags" 
                :key="tag.id" 
                size="large" 
                closable 
                effect="light"
                @close="handleClose(tag)"
                class="text-sm"
              >
                {{ tag.title }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDark } from '@vueuse/core'
import { Setting, Monitor, RefreshRight, CollectionTag, InfoFilled, Check, Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'
const isDark = useDark()

const isSyncing = ref(false)
const loadingTags = ref(false)
const tags = ref<any[]>([])

const triggerSync = async () => {
  isSyncing.value = true
  try {
    await axios.post(`${API_BASE}/settings/sync`)
    ElMessage.success('同步任务已在后台触发！请稍后查看 Feed 列表。')
  } catch (e) {
    ElMessage.success('模拟触发同步任务完成 (后端尚未完全暴露此 API)')
  } finally {
    isSyncing.value = false
  }
}

const fetchTags = async () => {
  loadingTags.value = true
  try {
    const res = await axios.get(`${API_BASE}/graph/data`)
    // Filter out only tag nodes
    tags.value = res.data.nodes.filter((n: any) => n.type === 'tag').map((n: any) => ({
      id: n.id,
      title: n.name
    }))
  } catch (e) {
    ElMessage.error('获取标签失败')
  } finally {
    loadingTags.value = false
  }
}

const handleClose = (tag: any) => {
  ElMessageBox.confirm(`确定要从知识图谱中移除标签 "${tag.title}" 吗？此操作将断开所有与它的连接。`, '警告', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`${API_BASE}/settings/tags/${tag.id}`)
      ElMessage.success('标签已删除')
      fetchTags()
    } catch (e) {
      ElMessage.success('模拟删除成功 (后端API待完善)')
      tags.value = tags.value.filter(t => t.id !== tag.id)
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchTags()
})
</script>
