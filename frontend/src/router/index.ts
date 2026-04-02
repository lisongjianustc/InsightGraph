import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import FeedView from '../views/FeedView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'feed',
          component: FeedView
        },
        // 后续可以在这里加 /chat, /settings 等页面
      ]
    }
  ]
})

export default router
