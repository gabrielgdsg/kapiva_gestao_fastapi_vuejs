<template>
  <div class="page-layout comissao">
    <div class="page-header">
      <h1 class="page-title">Comissão</h1>
      <div class="page-subtitle">{{ subtitle }}</div>
    </div>
    <div class="page-main">
      <component :is="currentComponent" :data_ini="data_ini" :data_fim="data_fim" :dados_comissao="dados_comissao"/>
    </div>
  </div>
</template>

<script>
import ComissaoSelect from '../components/ComissaoSelect'
import ComissaoTable from '../components/ComissaoTable'

export default {
  name: 'Comissao',
  components: {'selecionar': ComissaoSelect, 'tabela': ComissaoTable},
  props: {
    currentComponent: String,
    data_ini: String,
    data_fim: String,
    dados_comissao: {}
  },
  data () {
    return {}
  },
  computed: {
    subtitle () {
      if (this.currentComponent === 'tabela' && this.data_ini && this.data_fim) {
        return `Período: ${this.data_ini} a ${this.data_fim}`
      }
      return 'Selecione o período para carregar a tabela de comissões'
    }
  },
  methods: {}
}
</script>

<style scoped>
</style>
