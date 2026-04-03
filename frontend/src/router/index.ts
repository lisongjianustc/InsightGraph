import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import FeedView from '../views/FeedView.vue'
import CapsuleView from '../views/CapsuleView.vue'
import GraphView from '../views/GraphView.vue'
import GlobalChatView from '../views/GlobalChatView.vue'
import SettingsView from '../views/SettingsView.vue'

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
        },
        {
          path: 'graph',
          name: 'graph',
          component: GraphView
        },
        {
          path: 'chat',
          name: 'chat',
          component: GlobalChatView
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsView
        }
      ]
    }
  ]
})

export default router
