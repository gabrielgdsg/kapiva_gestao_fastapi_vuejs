import Vue from 'vue'
import VueRouter from 'vue-router'
// import Vendedor from "../components/Vendedor.vue";
// import Vendas from "../components/Vendas.vue";
import VendedoresList from "../components/VendedoresList.vue";
import VendedorDetail from "../components/VendedorDetail.vue";


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
    path: '/metas/:currentComponent',
    name: 'Metas',
    component: () => import('../views/Metas.vue'),
    props: true
  },
   {
    path: "/vendedores",
    name: "VendedoresList",
    component: VendedoresList
  },
  {
    path: "/vendedor/:cod_vendedor",
    name: "VendedorDetail",
    component: VendedorDetail,
    props: true
  },
  {
    path: "/vendedor/:cod_vendedor/vendas",
    name: "Vendas",
    component: () => import("../components/Vendas.vue"),
    props: true
  },
  {
    path: "/vendedor/:cod_vendedor/metas",
    name: "Metas",
    component: () => import("../components/Metas.vue"),
    props: true
  }

]



const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
