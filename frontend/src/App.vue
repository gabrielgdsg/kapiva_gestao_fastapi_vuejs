<template>
  <div id="app">
    <template v-if="$route.meta.hideNavbar">
      <router-view/>
    </template>
    <template v-else>
      <navbar/>
      <div class="jumbotron">
        <router-view/>
      </div>
    </template>
  </div>
</template>

<script>
import Navbar from './components/Navbar'

export default {
  name: 'App',
  components: {
    'navbar': Navbar
  }
}
</script>

<style>
#app {
    font-family: 'DM Sans', 'Avenir', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    color: #0f172a;
  }
  .jumbotron {
    padding-top: 1rem;
    padding-bottom: 1.5rem;
  }
  /* Shared page layout (PedidosChegando / Levantamentos2 style) */
  .page-layout {
    background: #f1f5f9;
    min-height: calc(100vh - 120px);
    padding: 14px;
    font-size: 14px;
    color: #0f172a;
    border-radius: 10px;
  }
  .page-layout .page-header {
    margin-bottom: 14px;
  }
  .page-layout .page-title {
    font-size: 19px;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }
  .page-layout .page-subtitle {
    font-size: 11px;
    color: #64748b;
    margin-top: 2px;
  }
  .page-layout .page-main {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
</style>
