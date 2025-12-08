<template>
  <div class="vendedores-list">
    <h2>Lista de Vendedores</h2>
    <ul>
      <li v-for="vendedor in vendedores" :key="vendedor.cod_vendedor">
        <router-link :to="{ name: 'VendedorDetail', params: { cod_vendedor: vendedor.cod_vendedor } }">
          {{ vendedor.name }} ({{ vendedor.cod_vendedor }})
        </router-link>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: "VendedoresList",
  data() {
    return {
      vendedores: [
        { cod_vendedor: 74, name: "Thassia" },
        { cod_vendedor: 7, name: "Vanessa" },
        { cod_vendedor: 3, name: "Vendedor 3" }
      ]
    };
  }
};
</script>

<style scoped>
.vendedores-list {
  margin: 20px;
}
</style>