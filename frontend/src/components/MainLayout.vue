<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Connection, Document, ChatDotRound, Setting, MagicStick, Share, Search, Calendar, SwitchButton, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const username = ref('Admin')
const isAdmin = ref(false)
const mustChangePassword = ref(false)

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      if (user.display_name) username.value = user.display_name
      else if (user.username) username.value = user.username
      isAdmin.value = user.username === 'admin' && user.is_admin === true
      mustChangePassword.value = user.must_change_password === true
    } catch (e) {}
  }
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push({ name: 'auth' })
}
</script>

<template>
  <div class="flex h-screen bg-app text-primary" style="-webkit-app-region: drag">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-sidebar border-r border-border flex flex-col backdrop-blur-[var(--glass-blur)]" style="-webkit-app-region: no-drag">
      <div class="p-6">
        <h1 class="text-2xl font-bold text-primary flex items-center gap-2">
          <el-icon class="text-accent"><Connection /></el-icon>
          InsightGraph
        </h1>
        <p class="text-xs text-secondary mt-1">Personal Knowledge Base</p>
      </div>

      <nav class="flex-1 px-4 space-y-1 mt-4 text-sm font-medium">
        <template v-if="mustChangePassword">
          <div class="px-4 py-3 text-red-600 font-medium bg-red-50 border border-red-100 rounded-lg mb-4 text-xs leading-relaxed shadow-sm">
            您的密码已被管理员重置。<br/>
            为了保障账号安全，请先修改密码。
          </div>
          <router-link to="/settings?tab=account" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><Setting /></el-icon>
            账号设置 (Account)
          </router-link>
        </template>
        <template v-else>
          <router-link to="/" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" exact-active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><Document /></el-icon>
            今日资讯 (Feed)
          </router-link>
          
          <router-link to="/capsule" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><MagicStick /></el-icon>
            闪念胶囊 (Capsule)
          </router-link>
  
          <router-link to="/daily" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><Calendar /></el-icon>
            每日笔记 (Daily)
          </router-link>
  
          <router-link to="/graph" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><Share /></el-icon>
            知识图谱 (Graph)
          </router-link>
  
          <router-link to="/search" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><Search /></el-icon>
            文献检索 (Search)
          </router-link>
          
          <!-- 预留其他菜单 -->
          <router-link to="/chat" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><ChatDotRound /></el-icon>
            全局问答 (Chat)
          </router-link>
          <router-link to="/settings" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><Setting /></el-icon>
            系统设置 (Settings)
          </router-link>
  
          <router-link v-if="isAdmin" to="/admin/users" class="flex items-center gap-3 px-4 py-3 rounded-lg text-secondary hover:bg-card hover:text-primary transition-colors" active-class="bg-indigo-50 text-indigo-700 font-semibold shadow-sm">
            <el-icon :size="18"><User /></el-icon>
            用户管理
          </router-link>
        </template>
      </nav>
      
      <div class="p-4 border-t border-border flex items-center justify-between">
        <div class="flex items-center gap-3 px-2 py-2">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-400 to-indigo-500 text-white flex items-center justify-center font-bold text-xs uppercase">
            {{ username.substring(0, 2) }}
          </div>
          <span class="text-sm font-medium text-primary truncate max-w-[80px]" :title="username">{{ username }}</span>
        </div>
        <el-tooltip content="退出登录" placement="top">
          <el-button text circle size="small" @click="handleLogout" class="!text-secondary hover:!text-red-500">
            <el-icon :size="16"><SwitchButton /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-auto flex flex-col" style="-webkit-app-region: no-drag">
      <header class="h-16 bg-card border-b border-border flex items-center px-8 shrink-0">
        <h2 class="text-lg font-medium text-primary">
          <template v-if="route.name === 'feed'">知识发现</template>
          <template v-else-if="route.name === 'capsule'">闪念胶囊</template>
          <template v-else-if="route.name === 'graph'">知识图谱</template>
          <template v-else-if="route.name === 'search'">文献检索</template>
          <template v-else-if="route.name === 'chat'">全局问答</template>
          <template v-else>InsightGraph</template>
        </h2>
      </header>
      
      <div class="p-8 flex-1 flex flex-col" :class="{'!p-0': route.name === 'capsule' || route.name === 'graph' || route.name === 'chat'}">
        <router-view v-slot="{ Component }">
          <keep-alive include="GlobalChatView">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </main>
  </div>
</template>
