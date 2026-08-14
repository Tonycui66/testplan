import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/common/AppLayout.vue'
import LoginView from '../views/auth/LoginView.vue'
import DashboardView from '../views/dashboard/DashboardView.vue'
import ProjectListView from '../views/project/ProjectListView.vue'
import PipelineEditView from '../views/pipeline/PipelineEditView.vue'
import PipelineListView from '../views/pipeline/PipelineListView.vue'
import PipelineRunView from '../views/pipeline/PipelineRunView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: LoginView },
    {
      path: '/dashboard',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [{ path: '', name: 'dashboard', component: DashboardView }]
    },
    {
      path: '/projects',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [{ path: '', name: 'projects', component: ProjectListView }]
    },
    {
      path: '/projects/:id/pipelines',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [{ path: '', name: 'pipelines', component: PipelineListView }]
    },
    {
      path: '/projects/:id/pipelines/:pid',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [{ path: '', name: 'pipeline-edit', component: PipelineEditView }]
    },
    {
      path: '/projects/:id/pipelines/:pid/runs/:rid',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [{ path: '', name: 'pipeline-run', component: PipelineRunView }]
    }
  ]
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
