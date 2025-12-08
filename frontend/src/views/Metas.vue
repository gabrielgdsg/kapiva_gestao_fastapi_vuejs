<template>
  <div class="metas">
    <component :is="currentComponent" :data_ini="data_ini" :data_fim="data_fim" :dados_comissao="dados_comissao"/>
  </div>
</template>

<script>
import ComissaoSelect from '../components/ComissaoSelect'
import ComissaoTable from '../components/ComissaoTable'

export default {
  name: 'Metas',
  components: {'selecionar': ComissaoSelect, 'tabela': ComissaoTable},
  props: {
    currentComponent: String,
    data_ini: String,
    data_fim: String,
    dados_comissao: {}
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
