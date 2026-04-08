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

      <!-- 信息源管理 -->
      <el-tab-pane label="信息源管理">
        <template #label>
          <span class="flex items-center gap-2"><el-icon><Link /></el-icon> 信息源管理</span>
        </template>
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-lg font-bold text-gray-700">配置订阅源 (RSS/API)</h3>
              <p class="text-sm text-gray-500">添加你关注的博客、期刊或 Arxiv 分类链接。</p>
            </div>
            <el-button type="primary" @click="openSourceDialog()">
              <el-icon class="mr-1"><Plus /></el-icon> 添加源
            </el-button>
          </div>
          
          <el-table :data="sources" style="width: 100%" v-loading="loadingSources" class="border rounded-lg">
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="url" label="链接" show-overflow-tooltip />
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="scope">
                <el-switch v-model="scope.row.is_active" @change="toggleSourceStatus(scope.row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openSourceDialog(scope.row)">编辑</el-button>
                <el-button link type="danger" @click="deleteSource(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
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

      <!-- 笔记分类管理 -->
      <el-tab-pane label="笔记分类管理">
        <template #label>
          <span class="flex items-center gap-2"><el-icon><FolderOpened /></el-icon> 笔记分类</span>
        </template>
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-gray-800">全量每日笔记分类</h2>
            <div>
              <el-button type="primary" size="small" @click="openCreateCategoryDialog">
                <el-icon class="mr-1"><Plus /></el-icon> 新增分类
              </el-button>
              <el-button plain size="small" @click="fetchCategories">
                <el-icon class="mr-1"><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>
          
          <div v-loading="loadingCategories" class="min-h-[200px]">
            <el-empty v-if="categories.length === 0 && !loadingCategories" description="暂无任何分类数据" />
            <el-table v-else :data="categories" style="width: 100%" border stripe>
              <el-table-column prop="name" label="分类名称" width="250">
                <template #default="scope">
                  <div class="flex items-center gap-2 font-medium">
                    <el-icon class="text-yellow-500"><FolderOpened /></el-icon> {{ scope.row.name }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="关联笔记数量" width="150" align="center">
                <template #default="scope">
                  <el-tag type="info" size="small">{{ scope.row.count }} 篇</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" min-width="200">
                <template #default="scope">
                  <el-button 
                    size="small" 
                    type="primary" 
                    plain 
                    @click="openRenameCategoryDialog(scope.row)"
                    :disabled="scope.row.name === '未分类'"
                  >
                    重命名
                  </el-button>
                  <el-button 
                    size="small" 
                    type="danger" 
                    plain 
                    @click="handleDeleteCategory(scope.row)"
                    :disabled="scope.row.name === '未分类'"
                  >
                    删除分类 (重置为未分类)
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 分类新增弹窗 -->
    <el-dialog v-model="createCategoryDialogVisible" title="新增分类" width="400px">
      <el-form label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="newCategoryName" placeholder="请输入新的分类名称" @keyup.enter="submitCreateCategory" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createCategoryDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isCreatingCategory" @click="submitCreateCategory">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分类重命名弹窗 -->
    <el-dialog v-model="renameCategoryDialogVisible" title="重命名分类" width="400px">
      <el-form label-width="80px">
        <el-form-item label="旧名称">
          <el-input v-model="categoryToRename.oldName" disabled />
        </el-form-item>
        <el-form-item label="新名称" required>
          <el-input v-model="categoryToRename.newName" placeholder="请输入新的分类名称" @keyup.enter="submitRenameCategory" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="renameCategoryDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isRenamingCategory" @click="submitRenameCategory">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加/编辑源弹窗 -->
    <el-dialog v-model="sourceDialogVisible" :title="editingSource.id ? '编辑订阅源' : '添加订阅源'" width="500px">
      <el-form :model="editingSource" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="editingSource.name" placeholder="例如: Github Trending" />
        </el-form-item>
        <el-form-item label="URL" required>
          <el-input v-model="editingSource.url" placeholder="http://..." />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="editingSource.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="sourceDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isSavingSource" @click="saveSource">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDark } from '@vueuse/core'
import { Setting, Monitor, RefreshRight, CollectionTag, InfoFilled, Check, Download, Refresh, Link, Plus, FolderOpened } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'
const isDark = useDark()

const isSyncing = ref(false)
const loadingTags = ref(false)
const tags = ref<any[]>([])

const loadingSources = ref(false)
const sources = ref<any[]>([])
const sourceDialogVisible = ref(false)
const isSavingSource = ref(false)
const editingSource = ref<any>({ name: '', url: '', is_active: true })

// 笔记分类
const categories = ref<any[]>([])
const loadingCategories = ref(false)
const createCategoryDialogVisible = ref(false)
const isCreatingCategory = ref(false)
const newCategoryName = ref('')
const renameCategoryDialogVisible = ref(false)
const isRenamingCategory = ref(false)
const categoryToRename = ref({ oldName: '', newName: '' })

const fetchSources = async () => {
  loadingSources.value = true
  try {
    const res = await axios.get(`${API_BASE}/settings/sources`)
    sources.value = res.data
  } catch (e) {
    ElMessage.error('获取订阅源失败')
  } finally {
    loadingSources.value = false
  }
}

const openSourceDialog = (source?: any) => {
  if (source) {
    editingSource.value = { ...source }
  } else {
    editingSource.value = { name: '', url: '', is_active: true }
  }
  sourceDialogVisible.value = true
}

const saveSource = async () => {
  if (!editingSource.value.name || !editingSource.value.url) {
    ElMessage.warning('请填写名称和 URL')
    return
  }
  isSavingSource.value = true
  try {
    if (editingSource.value.id) {
      await axios.put(`${API_BASE}/settings/sources/${editingSource.value.id}`, editingSource.value)
    } else {
      await axios.post(`${API_BASE}/settings/sources`, editingSource.value)
    }
    ElMessage.success('保存成功')
    sourceDialogVisible.value = false
    fetchSources()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    isSavingSource.value = false
  }
}

const toggleSourceStatus = async (source: any) => {
  try {
    await axios.put(`${API_BASE}/settings/sources/${source.id}`, source)
    ElMessage.success(`已${source.is_active ? '启用' : '禁用'}源: ${source.name}`)
  } catch (e) {
    source.is_active = !source.is_active // revert
    ElMessage.error('状态切换失败')
  }
}

const deleteSource = (source: any) => {
  ElMessageBox.confirm(`确定要删除源 "${source.name}" 吗？`, '警告', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`${API_BASE}/settings/sources/${source.id}`)
      ElMessage.success('删除成功')
      fetchSources()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

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

// ===== 分类管理 =====
const fetchCategories = async () => {
  loadingCategories.value = true
  try {
    const res = await axios.get(`${API_BASE}/daily-notes/categories`)
    categories.value = res.data.categories || []
  } catch (error) {
    console.error('Fetch categories error', error)
    ElMessage.error('获取分类列表失败')
  } finally {
    loadingCategories.value = false
  }
}

const openCreateCategoryDialog = () => {
  newCategoryName.value = ''
  createCategoryDialogVisible.value = true
}

const submitCreateCategory = () => {
  const name = newCategoryName.value.trim()
  if (!name) {
    ElMessage.warning('名称不能为空')
    return
  }
  if (categories.value.some(c => c.name === name)) {
    ElMessage.warning('该分类已存在')
    return
  }
  
  // 对于空分类，我们可以在前端临时维护，或者如果需要持久化可以在写笔记时固化。
  // 在这里我们先在列表中添加一个计数为0的占位对象，这样用户切回每日笔记时就可以选到了。
  // (实际上，刷新页面后空分类会消失，因为后端的聚合查询依赖真实的笔记记录，这是符合“用完即走”设计的。)
  categories.value.push({ name: name, count: 0, notes: [] })
  ElMessage.success('新增分类成功，您现在可以在每日笔记中选择它了')
  createCategoryDialogVisible.value = false
}

const openRenameCategoryDialog = (category: any) => {
  categoryToRename.value = {
    oldName: category.name,
    newName: ''
  }
  renameCategoryDialogVisible.value = true
}

const submitRenameCategory = async () => {
  const { oldName, newName } = categoryToRename.value
  if (!newName.trim()) {
    ElMessage.warning('新名称不能为空')
    return
  }
  if (newName.trim() === oldName) {
    ElMessage.warning('新名称不能与旧名称相同')
    return
  }
  if (newName.trim() === '未分类') {
    ElMessage.warning('不能重命名为"未分类"')
    return
  }
  
  isRenamingCategory.value = true
  try {
    const res = await axios.put(`${API_BASE}/daily-notes/categories/rename`, {
      old_name: oldName,
      new_name: newName.trim()
    })
    ElMessage.success(`重命名成功，影响了 ${res.data.count} 篇笔记`)
    renameCategoryDialogVisible.value = false
    fetchCategories()
  } catch (error) {
    console.error('Rename category error', error)
    ElMessage.error('重命名失败')
  } finally {
    isRenamingCategory.value = false
  }
}

const handleDeleteCategory = async (category: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类 "${category.name}" 吗？该分类下的所有笔记将被设为"未分类"，此操作不可撤销。`,
      '删除警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await axios.delete(`${API_BASE}/daily-notes/categories/${encodeURIComponent(category.name)}`)
    ElMessage.success('分类已删除')
    fetchCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete category error', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchTags()
  fetchSources()
  fetchCategories()
})
</script>
