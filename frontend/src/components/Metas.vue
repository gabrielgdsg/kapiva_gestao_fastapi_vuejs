<script>
export default {
  name: "Metas"
}
</script>

<template>
  <div class="metas-view">
    <h2>Metas</h2>
    <label for="datepicker-data">Escolha a data:</label>
    <mydatepicker id="datepicker-data" @childToParent="receiveDate" />
    <b-button @click="fetchGoalsData" variant="primary">Buscar Metas</b-button>
    <div v-if="goalsData.length > 0">
      <h3>Metas do Vendedor</h3>
      <ul>
        <li v-for="goal in goalsData" :key="goal.cod_origem">
          Origem: {{ goal.cod_origem }}, Tipo: {{ goal.tipo_origem }}, Base Cálculo: {{ goal.base_calculo }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>

</style>