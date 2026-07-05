import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/kb',
    children: [
      {
        path: '/kb',
        name: 'KnowledgeBase',
        component: () => import('../views/KnowledgeBase.vue'),
        meta: { title: '知识库', requiresAuth: true }
      },
      {
        path: '/chat',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { title: '对话', requiresAuth: true }
      },
      {
        path: '/kb/:kbId/documents',
        name: 'Documents',
        component: () => import('../views/Documents.vue'),
        meta: { title: '文档管理', requiresAuth: true }
      },
      {
        path: '/departments',
        name: 'Department',
        component: () => import('../views/Department.vue'),
        meta: { title: '部门管理', requiresAuth: true }
      },
      {
        path: '/users',
        name: 'User',
        component: () => import('../views/UserList.vue'),
        meta: { title: '用户管理', requiresAuth: true }
      },
      {
        path: '/tenants',
        name: 'Tenant',
        component: () => import('../views/TenantList.vue'),
        meta: { title: '租户管理', requiresAuth: true, requiresSuperAdmin: true }
      },
      {
        path: '/roles',
        name: 'Role',
        component: () => import('../views/RoleList.vue'),
        meta: { title: '角色权限', requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
