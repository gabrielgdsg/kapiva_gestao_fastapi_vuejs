<template>
  <div class="vendedor-view">
    <h1>Vendedor</h1>
    <router-link :to="{ name: 'Vendas', params: { cod_vendedor: vendedorId }}">Vendas</router-link>
    <router-link :to="{ name: 'Metas', params: { cod_vendedor: vendedorId }}">Metas</router-link>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: "Vendedor",
  props: {
    vendedorId: {
      type: Number,
      required: true
    }
  }
};
</script>

<style scoped>
.vendedor-view {
  margin: 20px;
}
</style>