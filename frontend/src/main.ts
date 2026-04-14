import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import axios from 'axios'

// Setup global Axios interceptors for JWT Auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

axios.interceptors.response.use((response) => {
  return response
}, (error) => {
  if (error.response && error.response.status === 401) {
    // Clear token and redirect to auth page on 401
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    if (router.currentRoute.value.name !== 'auth') {
      router.push({ name: 'auth' })
    }
  } else if (error.response && error.response.status === 403) {
    const detail = error.response.data?.detail
    if (detail === 'Password change required') {
      if (router.currentRoute.value.name !== 'settings') {
        router.push({ name: 'settings', query: { tab: 'account' } })
      }
    } else if (detail === 'Could not validate credentials') {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (router.currentRoute.value.name !== 'auth') {
        router.push({ name: 'auth' })
      }
    }
  }
  return Promise.reject(error)
})

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
