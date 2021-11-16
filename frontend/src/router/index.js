import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
    {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/comissao/:currentComponent',
    name: 'Comissao',
    component: () => import('../views/Comissao.vue'),
    props: true
  },
    {
    path: '/levantamentos/',
    name: 'Levantamentos',
    component: () => import('../views/Levantamentos.vue'),
    props: true
  },
    {
    path: '/levantamentos_test/',
    name: 'LevantamentosTest',
    component: () => import('../views/LevantamentosTest.vue'),
    props: true
  },
    {
    path: '/levantamentos_test2/',
    name: 'LevantamentosTest2',
    component: () => import('../views/LevantamentosTest2.vue'),
    props: true
  },
    {
    path: '/financeiro/caixa',
    name: 'FinanceiroCaixa',
    component: () => import('../views/FinanceiroCaixa.vue'),
    props: true
  },
    {
    path: '/cliente',
    name: 'Cliente',
    component: () => import('../views/Client_test'),
    props: true
  },
    {
    path: '/googleimagetestview',
    name: 'GoogleImageTestView',
    component: () => import('../views/GoogleImageTestView'),
    props: true
  }

]



const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
