import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Lab from '../views/Lab.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/lab/:subject_type/:subject_name/:project_name/:poc_name',
      name: 'lab',
      component: Lab,
      props: true
    }
  ]
})

export default router
