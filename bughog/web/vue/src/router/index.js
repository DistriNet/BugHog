import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Playground from '../views/Playground.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/play/:subject_type/:subject_name/:project_name/:poc_name',
      name: 'playground',
      component: Playground,
      props: true
    }
  ]
})

export default router
