<template>
  <div class="vendas-view">
    <h2>Vendas do Vendedor</h2>
    <ul>
      <li v-for="sale in salesData" :key="sale.id">
        {{ sale.base_calculo }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: "Vendas",
  data() {
    return {
      salesData: [] // Array to hold sales data
    };
  },
  created() {
    const codVendedor = this.$route.params.cod_vendedor;
    const selectedDate = this.$route.params.date;
    const path = `/api/vendas/${codVendedor}/${selectedDate}`;
    axios
        .get(path)
        .then((res) => {
          this.salesData = res.data; // Assuming res.data contains the sales data
        })
        .catch((error) => {
          console.error(error);
        });
  }
};
</script>

<style scoped>
.vendas-view {
  margin: 20px;
}
</style>