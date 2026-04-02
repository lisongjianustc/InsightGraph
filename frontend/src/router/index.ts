import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import FeedView from '../views/FeedView.vue'
import CapsuleView from '../views/CapsuleView.vue'

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
        {
          path: 'capsule',
          name: 'capsule',
          component: CapsuleView
        }
      ]
    }
  ]
})

export default router
