<template>
  <div class="vendedor-detail">
    <h2>Vendedor: {{ cod_vendedor }}</h2>
    <router-link :to="{ name: 'Vendas', params: { cod_vendedor: cod_vendedor } }">Vendas</router-link>
    <router-link :to="{ name: 'Metas', params: { cod_vendedor: cod_vendedor } }">Metas</router-link>
  </div>
</template>

<script>
export default {
  name: "VendedorDetail",
  props: {
    cod_vendedor: {
      type: Number,
      required: true
    }
  }
};
</script>

<style scoped>
.vendedor-detail {
  margin: 20px;
}
</style>