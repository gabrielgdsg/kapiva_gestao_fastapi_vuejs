<template>
  <div class="comissao-table">
    <div>
        <b-form @submit.stop.prevent="recarregarComissao">
                <b-button type="submit" variant="primary">Recarregar </b-button>
<!--                <b-button type="submit" variant="primary">Recarregar <img src="../assets/refresh-icon.png" /></b-button>-->
            </b-form>

      <b-table striped hover :items="items" :fields="fields" class="text-right" :small=true>
        <template v-slot:cell(pos)="data">
          {{ data.index + 1}}
        </template>
      </b-table>
      <b-alert show dismissible variant="secondary">
<!--        <div class="text-center">Total de Vendas: <strong> :{{this.dados_comissao.comissao_total}} </strong></div>-->
        <div class="text-center">Total de Vendas: <strong> {{ this.computed_sum_comissao | dinheiro }}</strong></div>
<!--        <div class="text-center">Total de Vendas: <strong> {{ sum_comissao }}</strong></div>-->
      </b-alert>
    </div>
  </div>
</template>

<script>
// import axios from 'axios'
// import moment from 'moment'

import axios from "axios";

export default {
    name: 'ComissaoTable',
    props: ['data_ini', 'data_fim', 'dados_comissao'],
    data () {
    return {
      sortBy: 'base_calc_comissao',
      sortDesc: true,
      fields: [
        {key: 'pos', label: 'Pos.'},
        {key: 'cod_vendedor', label: 'Cod. Vendedor'},
        {key: 'nom_vendedor', label: 'Nom. Vendedor'},
        {key: 'base_calc_comissao', label: 'Base Calc.'},
        {key: 'cred_dev', label: 'Cred. Dev.'},
        {key: 'vlr_comissao', label: 'Vlr. Com.'},
        // {key: 'data_ini', label: 'Data_ini'}],
        {key: 'data_fim', label: 'Data'}],
      items: [],
      sum_comissao: '',
      comissao_vendedores_array: this.dados_comissao.comissao_vendedores

    }
  },
  beforeMount () {
    this.loadComissao()
  },
  mounted () {
  },
    computed: {
        computed_sum_comissao() {
            let comissao_vendedores_sum = this.items.reduce(function (sum, item) {
                let itemValor = parseFloat(item.base_calc_comissao)
                if (!isNaN(itemValor)) {
                    return sum + itemValor
                } else {
                    return sum
                }
            }, 0)
            return comissao_vendedores_sum
        },
        computed_comissao_vendedores_array() {
           return this.comissao_vendedores_array
        }
    },
  methods: {
    loadComissao () {
        this.items = []
      console.log("this.dados_comissao")
      console.log(this.dados_comissao)
      // let comissao_vendedores_array = this.dados_comissao.comissao_vendedores
      for (const comissao_vendedor in this.computed_comissao_vendedores_array) {
          this.items.push(this.comissao_vendedores_array[comissao_vendedor])
      }
    },
      recarregarComissao() {
        const path = `/api/comissao/delete/${this.data_ini}`
      axios.delete(path)
        .then(() => {
            const path = `/api/comissao/${this.data_ini}/${this.data_fim}`
            axios.get(path)
                .then((res) => {
                // this.$router.push({name: 'Comissao', params: {currentComponent: 'tabela', data_ini: this.data_ini, data_fim: this.data_fim, dados_comissao: res.data}}).catch(()=>{});
                this.comissao_vendedores_array = res.data.comissao_vendedores
                this.loadComissao()
                })
                .catch((error) => {
                console.log(error)
        })})
        .catch((error) => {
          console.log(error)
        })

      }
  }

}

</script>

<style scoped>

</style>
