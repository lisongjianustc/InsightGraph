<template>
  <div class="max-w-5xl mx-auto py-8">
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-extrabold text-gray-800 flex items-center gap-3">
          <el-icon class="text-indigo-500"><User /></el-icon>
          用户管理
        </h1>
        <p class="text-gray-500 mt-2">仅管理员可查看与管理用户状态、重置密码</p>
      </div>
      <div class="flex items-center gap-2">
        <el-input v-model="keyword" placeholder="搜索用户名/昵称/邮箱" clearable style="width: 260px" @keyup.enter="fetchUsers" />
        <el-button type="primary" @click="fetchUsers" :loading="loading">查询</el-button>
      </div>
    </div>

    <el-table :data="users" v-loading="loading" class="border rounded-lg bg-white" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" width="160" />
      <el-table-column prop="display_name" label="昵称" width="160" show-overflow-tooltip />
      <el-table-column prop="email" label="邮箱" show-overflow-tooltip />
      <el-table-column prop="is_active" label="状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.username === 'admin'" type="success">管理员</el-tag>
          <el-tag v-else :type="scope.row.is_active ? 'success' : 'danger'">{{ scope.row.is_active ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="must_change_password" label="需改密" width="120">
        <template #default="scope">
          <el-tag :type="scope.row.must_change_password ? 'warning' : 'info'">{{ scope.row.must_change_password ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="scope">
          <el-button link type="primary" :disabled="scope.row.username === 'admin'" @click="onResetPassword(scope.row)">重置密码</el-button>
          <el-button link :type="scope.row.is_active ? 'danger' : 'success'" :disabled="scope.row.username === 'admin'" @click="onToggleActive(scope.row)">
            {{ scope.row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User } from '@element-plus/icons-vue'

const API_BASE = 'http://localhost:8000/api'

const loading = ref(false)
const users = ref<any[]>([])
const keyword = ref('')

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/admin/users`, { params: { keyword: keyword.value || undefined, limit: 200 } })
    users.value = res.data
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const onToggleActive = async (row: any) => {
  const next = !row.is_active
  try {
    await ElMessageBox.confirm(`确定要${next ? '启用' : '禁用'}用户 "${row.username}" 吗？`, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  try {
    const res = await axios.patch(`${API_BASE}/admin/users/${row.id}/status`, { is_active: next })
    row.is_active = res.data.is_active
    ElMessage.success('操作成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

const onResetPassword = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要重置用户 "${row.username}" 的密码吗？系统将生成临时密码，用户下次登录必须修改。`, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  try {
    const res = await axios.post(`${API_BASE}/admin/users/${row.id}/reset-password`)
    row.must_change_password = true
    await ElMessageBox.alert(`临时密码：${res.data.temp_password}\n\n请复制保存，此密码仅显示一次。`, '重置成功', {
      confirmButtonText: '我已复制'
    })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '重置失败')
  }
}

onMounted(fetchUsers)
</script>
