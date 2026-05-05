import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Analysis from '../views/Analysis.vue'
import QAPage from '../views/QAPage.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/analysis/:id?', name: 'Analysis', component: Analysis },
  { path: '/qa/:id', name: 'QA', component: QAPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
