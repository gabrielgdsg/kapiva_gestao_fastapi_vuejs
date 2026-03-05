<template>
  <div class="page-layout">
    <div class="page-header">
      <h1 class="page-title">Financeiro Caixa</h1>
      <div class="page-subtitle">Selecione a data ou visualize o período carregado</div>
    </div>
    <div class="page-main">
      <component :is="currentComponent" :data_caixa="data_caixa" :dados_caixa="dados_caixa"/>
    </div>
  </div>
</template>

<script>
import FinanceiroCaixaSelect from '../components/FinanceiroCaixaSelect'
import FinanceiroCaixaTable from '../components/FinanceiroCaixaTable'

export default {
  name: 'FinanceiroCaixa',
  components: {'selecionar': FinanceiroCaixaSelect, 'tabela': FinanceiroCaixaTable},
  props: {
    currentComponent: String,
    data_caixa: String,
    dados_caixa: {}
  },
  data () {
    return {
    }
  },
  methods: {
  }
}
</script>

<style scoped>

</style>
