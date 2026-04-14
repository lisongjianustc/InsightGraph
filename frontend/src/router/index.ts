import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import FeedView from '../views/FeedView.vue'
import CapsuleView from '../views/CapsuleView.vue'
import GraphView from '../views/GraphView.vue'
import GlobalChatView from '../views/GlobalChatView.vue'
import SettingsView from '../views/SettingsView.vue'
import SearchView from '../views/SearchView.vue'
import DailyNoteView from '../views/DailyNoteView.vue'
import AuthView from '../views/AuthView.vue'
import AdminUsersView from '../views/AdminUsersView.vue'
import SpotlightView from '../views/SpotlightView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/auth',
      name: 'auth',
      component: AuthView
    },
    {
      path: '/spotlight',
      name: 'spotlight',
      component: SpotlightView,
      meta: { isSpotlight: true }
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
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
          path: 'search',
          name: 'search',
          component: SearchView
        },
        {
          path: 'daily',
          name: 'daily',
          component: DailyNoteView
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsView
        },
        {
          path: 'admin/users',
          name: 'admin-users',
          component: AdminUsersView,
          meta: { requiresAdmin: true }
        }
      ]
    }
  ]
})

// Global route guard
router.beforeEach((to, _from, next) => {
  // Allow spotlight to load without redirecting to login view, it handles its own logic
  if (to.meta.isSpotlight) {
    next()
    return
  }

  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  let user: any = null
  try {
    user = userStr ? JSON.parse(userStr) : null
  } catch {}
  const isAdmin = !!user && user.username === 'admin' && user.is_admin === true
  const mustChangePassword = !!user && user.must_change_password === true
  
  // If route requires auth and there's no token
  if (to.matched.some(record => record.meta.requiresAuth) && !token) {
    next({ name: 'auth' })
  } else if (to.name === 'auth' && token) {
    // If logged in and trying to go to auth, redirect to home
    next({ name: 'feed' })
  } else if (mustChangePassword && to.name !== 'settings') {
    next({ name: 'settings', query: { tab: 'account' } })
  } else if (to.matched.some(record => record.meta.requiresAdmin) && !isAdmin) {
    next({ name: 'feed' })
  } else {
    next()
  }
})

export default router
