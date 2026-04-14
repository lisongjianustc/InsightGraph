<template>
  <div class="min-h-screen flex w-full bg-[#0a0a0a] text-white selection:bg-indigo-500 selection:text-white font-sans overflow-hidden">
    <!-- Left side: Abstract Visuals & Brand -->
    <div class="hidden lg:flex w-1/2 relative flex-col justify-between p-12 overflow-hidden bg-gradient-to-br from-indigo-900/20 to-black border-r border-white/10">
      <!-- Decorative background glow -->
      <div class="absolute top-[-10%] left-[-10%] w-3/4 h-3/4 bg-indigo-600/30 rounded-full blur-[120px] mix-blend-screen pointer-events-none"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-2/3 h-2/3 bg-emerald-600/20 rounded-full blur-[100px] mix-blend-screen pointer-events-none"></div>
      
      <!-- Content -->
      <div class="relative z-10">
        <div class="flex items-center gap-3">
          <svg class="w-8 h-8 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <defs>
              <linearGradient id="igGradientLg" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                <stop stop-color="#6366F1"/>
                <stop offset="1" stop-color="#34D399"/>
              </linearGradient>
            </defs>
            <rect x="3" y="3" width="26" height="26" rx="7" fill="url(#igGradientLg)" opacity="0.9"/>
            <path d="M10 19.5L15.8 12.5L22 18" stroke="white" stroke-opacity="0.9" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="10" cy="19.5" r="2.1" fill="white" fill-opacity="0.95"/>
            <circle cx="15.8" cy="12.5" r="2.1" fill="white" fill-opacity="0.95"/>
            <circle cx="22" cy="18" r="2.1" fill="white" fill-opacity="0.95"/>
          </svg>
          <span class="text-2xl font-bold tracking-tight">InsightGraph</span>
        </div>
      </div>
      
      <div class="relative z-10 max-w-md">
        <h1 class="text-5xl font-extrabold tracking-tight leading-[1.1] mb-6">
          构建你的知识图谱。<br/>
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-emerald-300">
            连接你的思考。
          </span>
        </h1>
        <p class="text-lg text-secondary font-medium leading-relaxed">
          基于多租户 AI 架构的新一代知识管理系统。
        </p>
      </div>
      
      <div class="relative z-10 text-sm text-secondary font-mono">
        © {{ new Date().getFullYear() }} InsightGraph Inc.
      </div>
    </div>

    <!-- Right side: Form -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-6 relative">
      <!-- Mobile brand header -->
      <div class="absolute top-8 left-8 flex lg:hidden items-center gap-3">
        <svg class="w-6 h-6" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <defs>
            <linearGradient id="igGradientSm" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
              <stop stop-color="#6366F1"/>
              <stop offset="1" stop-color="#34D399"/>
            </linearGradient>
          </defs>
          <rect x="3" y="3" width="26" height="26" rx="7" fill="url(#igGradientSm)" opacity="0.9"/>
          <path d="M10 19.5L15.8 12.5L22 18" stroke="white" stroke-opacity="0.9" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="10" cy="19.5" r="2.1" fill="white" fill-opacity="0.95"/>
          <circle cx="15.8" cy="12.5" r="2.1" fill="white" fill-opacity="0.95"/>
          <circle cx="22" cy="18" r="2.1" fill="white" fill-opacity="0.95"/>
        </svg>
        <span class="text-xl font-bold tracking-tight">InsightGraph</span>
      </div>

      <div class="w-full max-w-[400px]">
        <div class="mb-10 text-center lg:text-left">
          <h2 class="text-3xl font-bold mb-2">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
          <p class="text-secondary">
            {{ isLogin ? '输入账号密码以进入你的知识图谱。' : '开始构建你的个人知识库。' }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-300" for="username">用户名</label>
            <input 
              id="username" 
              v-model="form.username" 
              type="text" 
              required
              class="w-full px-4 py-3 bg-card/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all text-white placeholder-gray-500"
              placeholder="例如：admin"
            />
          </div>

          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-300" for="password">密码</label>
            <input 
              id="password" 
              v-model="form.password" 
              type="password" 
              required
              class="w-full px-4 py-3 bg-card/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all text-white placeholder-gray-500"
              placeholder="••••••••"
            />
          </div>

          <div v-if="error" class="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
            {{ error }}
          </div>

          <button 
            type="submit" 
            :disabled="loading"
            class="w-full py-3.5 px-4 bg-card text-black font-semibold rounded-xl hover:bg-gray-200 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_25px_rgba(255,255,255,0.2)]"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isLogin ? '登录' : '注册' }}
          </button>
        </form>

        <div class="mt-8 text-center text-sm text-secondary">
          {{ isLogin ? '还没有账号？' : '已有账号？' }}
          <button 
            @click="toggleMode" 
            type="button"
            class="text-indigo-400 hover:text-indigo-300 font-medium ml-1 transition-colors underline underline-offset-4 decoration-indigo-400/30 hover:decoration-indigo-300"
          >
            {{ isLogin ? '去注册' : '去登录' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// Assume API_BASE is globally accessible or we define it here
const API_BASE = 'http://localhost:8000/api'

const router = useRouter()
const isLogin = ref(true)
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: ''
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  error.value = ''
  form.password = ''
}

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  
  try {
    if (isLogin.value) {
      // Use FormData for login since OAuth2PasswordRequestForm expects form data
      const formData = new FormData()
      formData.append('username', form.username)
      formData.append('password', form.password)
      
      const res = await axios.post(`${API_BASE}/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      const token = res.data.access_token
      localStorage.setItem('token', token)
      
      // Fetch user info
      const userRes = await axios.get(`${API_BASE}/auth/me`)
      localStorage.setItem('user', JSON.stringify(userRes.data))
      
      ElMessage.success('登录成功')
      if (userRes.data.must_change_password) {
        ElMessage.warning('检测到临时密码，请先修改密码')
        router.push({ name: 'settings', query: { tab: 'account' } })
      } else {
        router.push({ name: 'feed' })
      }
    } else {
      // Registration
      await axios.post(`${API_BASE}/auth/register`, {
        username: form.username,
        password: form.password
      })
      
      ElMessage.success('注册成功，正在自动登录…')
      
      // Auto login after registration
      const formData = new FormData()
      formData.append('username', form.username)
      formData.append('password', form.password)
      
      const res = await axios.post(`${API_BASE}/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      const token = res.data.access_token
      localStorage.setItem('token', token)
      
      const userRes = await axios.get(`${API_BASE}/auth/me`)
      localStorage.setItem('user', JSON.stringify(userRes.data))

      if (userRes.data.must_change_password) {
        ElMessage.warning('检测到临时密码，请先修改密码')
        router.push({ name: 'settings', query: { tab: 'account' } })
      } else {
        router.push({ name: 'feed' })
      }
    }
  } catch (err: any) {
    console.error('Auth error:', err)
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = '发生未知错误，请稍后再试。'
    }
  } finally {
    loading.value = false
  }
}
</script>
