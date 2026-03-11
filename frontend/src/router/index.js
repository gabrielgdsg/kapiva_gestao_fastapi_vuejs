import Vue from 'vue'
import VueRouter from 'vue-router'
import PedidosChegando from '../views/PedidosChegando.vue'

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
    path: '/levantamentos',
    name: 'Levantamentos',
    component: () => import('../views/LevantamentosTest2.vue'),
    props: true
  },
  {
    path: '/levantamentos2',
    name: 'Levantamentos2',
    component: () => import('../views/Levantamentos2.vue'),
    props: true
  },
  {
    path: '/faturamento',
    name: 'Faturamento',
    component: () => import('../views/Faturamento.vue'),
    props: true
  },
  {
    path: '/vendedor',
    name: 'Vendedor',
    component: () => import('../views/Vendedor.vue'),
    props: true
  },
  {
    path: '/painel/:slug',
    name: 'VendedorPainel',
    component: () => import('../views/VendedorPainel.vue'),
    props: true,
    meta: { hideNavbar: true }
  },
  {
    path: '/financeiro/caixa/:currentComponent?',
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
    path: '/estoque',
    name: 'Estoque',
    component: () => import('../views/Estoque'),
    props: true
  },
  {
    path: '/estoque_test',
    name: 'Estoque_test',
    component: () => import('../views/Estoque_test'),
    props: true
  },
  {
    path: '/googleimagetestview',
    name: 'GoogleImageTestView',
    component: () => import('../views/GoogleImageTestView'),
    props: true
  },
  {
    path: '/metas',
    name: 'Metas',
    component: () => import('../views/Metas.vue')
  },
  {
    path: '/metas/:currentComponent',
    name: 'MetasWithComponent',
    component: () => import('../views/Metas.vue'),
    props: true
  },
  {
    path: '/pedidos-chegando',
    name: 'PedidosChegando',
    component: PedidosChegando,
    props: true
  },
]



const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
