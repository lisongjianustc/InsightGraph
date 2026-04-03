<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Connection, Document, ChatDotRound, Setting, MagicStick, Share, Search } from '@element-plus/icons-vue'

const route = useRoute()
</script>

<template>
  <div class="flex h-screen bg-gray-50">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div class="p-6">
        <h1 class="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <el-icon class="text-blue-500"><Connection /></el-icon>
          InsightGraph
        </h1>
        <p class="text-xs text-gray-500 mt-1">Personal Knowledge Base</p>
      </div>

      <nav class="flex-1 px-4 space-y-2 mt-4">
        <router-link to="/" 
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="route.path === '/' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-50'">
          <el-icon><Document /></el-icon>
          今日资讯 (Feed)
        </router-link>
        
        <router-link to="/capsule" 
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="route.path === '/capsule' ? 'bg-purple-50 text-purple-600 font-medium' : 'text-gray-600 hover:bg-gray-50'">
          <el-icon><MagicStick /></el-icon>
          闪念胶囊 (Capsule)
        </router-link>

        <router-link to="/graph" 
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="route.path === '/graph' ? 'bg-green-50 text-green-600 font-medium' : 'text-gray-600 hover:bg-gray-50'">
          <el-icon><Share /></el-icon>
          知识图谱 (Graph)
        </router-link>

        <router-link to="/search" 
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="route.path === '/search' ? 'bg-orange-50 text-orange-600 font-medium' : 'text-gray-600 hover:bg-gray-50'">
          <el-icon><Search /></el-icon>
          文献检索 (Search)
        </router-link>
        
        <!-- 预留其他菜单 -->
        <router-link to="/chat" 
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="route.path === '/chat' ? 'bg-indigo-50 text-indigo-600 font-medium' : 'text-gray-600 hover:bg-gray-50'">
          <el-icon><ChatDotRound /></el-icon>
          全局问答 (Chat)
        </router-link>
        <router-link to="/settings" 
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="route.path === '/settings' ? 'bg-gray-100 text-gray-800 font-medium' : 'text-gray-600 hover:bg-gray-50'">
          <el-icon><Setting /></el-icon>
          系统设置 (Settings)
        </router-link>
      </nav>
      
      <div class="p-4 border-t border-gray-100">
        <div class="flex items-center gap-3 px-4 py-2">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-400 to-indigo-500 text-white flex items-center justify-center font-bold">
            ME
          </div>
          <span class="text-sm font-medium text-gray-700">Admin</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-auto flex flex-col">
      <header class="h-16 bg-white border-b border-gray-200 flex items-center px-8 shrink-0">
        <h2 class="text-lg font-medium text-gray-800">
          <template v-if="route.name === 'feed'">知识发现</template>
          <template v-else-if="route.name === 'capsule'">闪念胶囊</template>
          <template v-else-if="route.name === 'graph'">知识图谱</template>
          <template v-else-if="route.name === 'search'">文献检索</template>
          <template v-else-if="route.name === 'chat'">全局问答</template>
          <template v-else>InsightGraph</template>
        </h2>
      </header>
      
      <div class="p-8 flex-1 flex flex-col" :class="{'!p-0': route.name === 'capsule' || route.name === 'graph' || route.name === 'chat'}">
        <router-view />
      </div>
    </main>
  </div>
</template>
