import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/common/AppLayout.vue'
import LoginView from '../views/auth/LoginView.vue'
import DashboardView from '../views/dashboard/DashboardView.vue'
import ProjectListView from '../views/project/ProjectListView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: LoginView },
    {
      path: '/dashboard',
      component: AppLayout,
      children: [{ path: '', name: 'dashboard', component: DashboardView }]
    },
    {
      path: '/projects',
      component: AppLayout,
      children: [{ path: '', name: 'projects', component: ProjectListView }]
    }
  ]
})

export default router
