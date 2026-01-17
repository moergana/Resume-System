import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import MainView from '../views/MainView.vue'
import AnalysisHistoryView from '../views/AnalysisHistoryView.vue'
import AnalysisDetailView from '../views/AnalysisDetailView.vue'
import JdRepositoryView from '../views/JdRepositoryView.vue'
import JdDetailView from '../views/JdDetailView.vue'
import ResumeRepositoryView from '../views/ResumeRepositoryView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: '登录 '}
    },
    {
      path: '/',
      name: 'home',
      component: MainView,
      meta: { title: '首页 - 简历职位分析系统' }
    },
    {
      path: '/analysis-history',
      name: 'analysis-history',
      component: AnalysisHistoryView,
      meta: { title: '分析任务历史记录' }
    },
    {
      path: '/analysis/:id',
      name: 'analysis-detail',
      component: AnalysisDetailView,
      meta: { title: '分析任务详情' }
    },
    {
      path: '/jd-repository',
      name: 'jd-repository',
      component: JdRepositoryView,
      meta: { title: 'JD仓库' }
    },
    {
      path: '/jd/:id',
      name: 'jd-detail',
      component: JdDetailView,
      meta: { title: '职位详情' }
    },
    {
      path: '/resume-repository',
      name: 'resume-repository',
      component: ResumeRepositoryView,
      meta: { title: '简历仓库' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  console.log(to)
  if (to.name === 'analysis-detail') {
    document.title = to.params && to.params.id ? to.meta.title + ' - ID: ' + to.params.id : to.meta.title
  }
  else if (to.name === 'jd-detail') {
    document.title = to.query && to.query.jdName ? to.meta.title + ' - ' + to.query.jdName : to.meta.title
  }
  else {
    document.title = to.meta.title || '简历职位分析系统'
  }
  next()
})

export default router
