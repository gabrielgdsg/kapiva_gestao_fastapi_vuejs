<template>
  <div class="page-layout">
    <div class="page-header">
      <h1 class="page-title">Financeiro Caixa</h1>
      <div class="page-subtitle">Selecione a data ou visualize o período carregado</div>
    </div>
    <div class="page-main">
      <template v-if="effectiveComponent === 'tabela' && caixas.length > 0">
        <div class="caixa-grid" :class="{ 'caixa-grid-multi': caixas.length > 1 }">
          <div
            v-for="(caixa, idx) in caixas"
            :key="caixa.cod_caixa || idx"
            class="caixa-col"
          >
            <div class="caixa-col-header">
              {{ caixa.nom_operador || ('Caixa ' + (caixa.cod_caixa || (idx + 1))) }}
            </div>
            <FinanceiroCaixaTable :data_caixa="data_caixa" :dados_caixa="caixa" :compact="caixas.length > 1"/>
          </div>
        </div>
      </template>
      <component v-else :is="effectiveComponent" :data_caixa="data_caixa" :dados_caixa="effectiveDadosCaixa"/>
    </div>
  </div>
</template>

<script>
import FinanceiroCaixaSelect from '../components/FinanceiroCaixaSelect'
import FinanceiroCaixaTable from '../components/FinanceiroCaixaTable'

export default {
  name: 'FinanceiroCaixa',
  components: {'selecionar': FinanceiroCaixaSelect, 'tabela': FinanceiroCaixaTable, FinanceiroCaixaTable},
  props: {
    currentComponent: String,
    data_caixa: String,
    dados_caixa: {}
  },
  data () {
    return {
      selectedCaixaIndex: 0
    }
  },
  computed: {
    effectiveComponent() {
      return (this.currentComponent === 'tabela' ? 'tabela' : 'selecionar')
    },
    caixas() {
      const d = this.dados_caixa || {}
      if (Array.isArray(d.caixas) && d.caixas.length > 0) return d.caixas
      if (d.loj_sangria_list != null || d.loj_cartao != null) return [d]
      return []
    },
    effectiveDadosCaixa() {
      const d = this.dados_caixa || {}
      if (Array.isArray(d.caixas) && d.caixas.length > 0) {
        return d.caixas[this.selectedCaixaIndex] || d.caixas[0]
      }
      return d
    }
  },
  methods: {
  }
}
</script>

<style scoped>
.caixa-grid { display: flex; flex-direction: column; gap: 1rem; }
.caixa-grid-multi { flex-direction: row; flex-wrap: wrap; gap: 0.75rem; }
.caixa-grid-multi .caixa-col { flex: 1; min-width: 280px; max-width: 400px; }
.caixa-col { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.caixa-col-header {
  padding: 6px 10px; font-weight: 700; font-size: 13px; background: #f1f5f9; border-bottom: 1px solid #e5e7eb;
}
</style>
