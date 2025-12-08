<template>
  <div>
     <component :is="currentComponent" :data_caixa="data_caixa" :dados_caixa="dados_caixa"/>
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
