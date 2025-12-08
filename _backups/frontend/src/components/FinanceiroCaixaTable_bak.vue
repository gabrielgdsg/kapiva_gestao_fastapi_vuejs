<template>
  <b-container class="financeiro-caixa-table">
    {{data_caixa}}
    <b-row align-h="center">
      <b-col cols="4">
        <h4 class="text-center"> Caixa - Loja</h4>
<!--        <b-table responsive striped hover :items="loj_items" :fields="fields">-->
        <b-table responsive striped hover :items="computedItems.lojItems" :fields="fields">
          <template v-slot:cell(icons)="data">
            <div class="text-center">
              <font-awesome-icon icon="trash-alt" :style="{color: 'red'}" size="lg"
                                 @click="deleteRow(data.index, data.item)"/>
            </div>
          </template>

          <template v-slot:head(icons)="data"> <!-- eslint-disable-line-->
            <div class="text-center">
              <button type='button' class="btn btn-info" @click="addNewRow">
                <font-awesome-icon icon="plus-circle"/>
              </button>
            </div>
          </template>

          <template v-for="field in editableFields" v-slot:[`cell(${field.key})`]="{ item }">
            <template v-if="item.editable && field.key =='item'">
              <b-input class="lefted-input" v-model="item[field.key]"/> <!-- eslint-disable-line-->
            </template>
            <template v-else-if="item.editable && field.key =='valor'">
              <b-input class="righted-input" v-model="item[field.key]"/> <!-- eslint-disable-line-->
            </template>
            <template v-else>
              {{item[field.key]}}
            </template>
          </template>
        </b-table>
      </b-col>

      <b-col cols="4">
        <h4 class="text-center"> Caixa - Sistema</h4>
        <b-table responsive striped hover :items="sist_items" :fields="fields"></b-table>
        <h4 class="text-center"> Caixa - Fechamento</h4>
        <b-table responsive striped hover :items="computedItems.resItems" :fields="fields"></b-table>
        <b-form @submit.stop.prevent="saveCaixa">
          <b-button type="submit" variant="primary">Salvar</b-button>
        </b-form>

<!--          <b-form @submit.stop.prevent="getCartao">-->
<!--            <b-button type="submit" variant="primary">getCartao</b-button>-->
<!--          </b-form>-->
      </b-col>

    </b-row>
  </b-container>
</template>

<script>
import axios from 'axios'
import numeral from 'numeral'

export default {
  name: 'FinanceiroCaixaTable',
  // props: {data_caixa: {type: String}},
  props: ['data_caixa', 'dados_caixa'],
  data: function () {
    return {
      fields: [
        {
          key: 'item',
          label: 'Item',
          editable: true,
          thStyle: {width: '25rem', textAlign: 'left'},
          tdClass: 'text-left'
        },
        {
          key: 'valor',
          label: 'Valor',
          editable: true,
          thStyle: {width: '20rem', textAlign: 'center'},
          tdClass: this.valorTdClass
        },
        {
          key: 'icons',
          label: '',
          thStyle: {width: '5rem'}
        }],
      loj_items: [],
      sist_items: [],
      res_items: [],
      n_outros: 0,
      sist_troco: 0,
      sist_pos: 0,
      sist_dinheiro: 0,
      loj_suprimento: 0,
      loj_val_sangria_list: '',
      loj_cartao: 0,
      loj_troco: 0,
      loj_outras_entradas_list: [],
      loja_outras_entradas_list: []

    }
  },
  computed: {
    editableFields () {
      return this.fields.filter(field => field.editable)
    },
    computedItems () {
      let lojCartao = {
        item: 'Cartão',
        valor: this.$options.filters.numero(this.loj_cartao),
        ref: 'cartao',
        editable: true
      }
      // this.loj_items.push(lojCartao)
      let lojSubtotal = {
        item: 'SUBTOTAL',
        valor: this.$options.filters.numero(this.calculaTotals.lojSubtotal),
        ref: 'subtotal'
      }
      let lojSuprimento = {
        item: 'Suprimento',
        valor: this.$options.filters.numero(0 - this.loj_suprimento),
        ref: 'suprimento'
      }
      let lojTotal = {
        item: 'TOTAL Loja',
        valor: this.$options.filters.numero(this.calculaTotals.lojTotal),
        ref: 'total'
      }
      let resCaixa = {
        item: 'RESULTADO',
        valor: this.$options.filters.numero(this.calculaTotals.resCaixa),
        ref: 'res_caixa'
      }
      let lojItems = this.loj_items.concat(lojCartao, lojSubtotal, lojSuprimento, lojTotal)
      let resItems = this.res_items.concat(resCaixa)
      return {
        lojItems: lojItems, resItems: resItems
      }
    },
    calculaTotals () {
      var sangria = this.filterItemsByTerm('sangria')
      var cartao = this.filterItemsByTerm('cartao')
      var troco = this.filterItemsByTerm('troco')
      var outros = this.filterItemsByTerm('outr')
      var subItens = sangria.concat(cartao, troco, outros)
      var lojSubtotal = subItens.reduce(function (sum, item) {
        var itemValor = parseFloat(numeral(item.valor).value())
        if (!isNaN(itemValor)) {
          return sum + itemValor
        } else {
          return sum
        }
      }, 0)
      var lojTotal = lojSubtotal - this.loj_suprimento
      var sistTotal = this.sist_dinheiro + this.sist_pos + this.sist_troco
      let resCaixa = lojTotal - sistTotal
      let totals = {
        lojSubtotal: this.$options.filters.numero(lojSubtotal),
        lojTotal: this.$options.filters.numero(lojTotal),
        sistTotal: this.$options.filters.numero(sistTotal),
        resCaixa: this.$options.filters.numero(resCaixa)
      }
      return totals
    }
  },
  beforeMount () {
    this.loadCaixa()
  },
  mounted () {
    this.getCartao()
  },
  created: function(){
      this.loadOutrEntradas();
  },
  methods: {
    loadCaixa () {

      this.sist_dinheiro = this.dados_caixa.sist_dinheiro
      this.sist_pos = this.dados_caixa.sist_pos
      this.sist_troco = this.dados_caixa.sist_troco
      this.loj_suprimento = this.dados_caixa.loj_suprimento
      this.loj_val_sangria_list = this.dados_caixa.loj_val_sangria_list
      this.loj_cartao = this.dados_caixa.loj_cartao
      this.loj_troco = this.dados_caixa.loj_troco
      this.loj_outras_entradas_list = this.dados_caixa.loj_outras_entradas_list
      this.res_caixa = this.dados_caixa.res_caixa


      this.toTableItems()
    },
    saveCaixa () {
      this.loadOutrEntradas ()
      console.log(this.outrasEntrToList())
      const path = 'http://localhost:5000/api/financeiro/caixa/table'
      const payload = {
        data_caixa: this.data_caixa,
        loj_suprimento: this.loj_suprimento,
        sist_troco: this.sist_troco,
        sist_pos: this.sist_pos,
        sist_dinheiro: this.sist_dinheiro,
        loj_val_sangria: JSON.stringify(this.sangriasToList()),
        loj_cartao: parseFloat(numeral(this.computedItems.lojItems[this.loj_val_sangria.length + 1].valor).value()),
        // loj_cartao: parseFloat(numeral(this.filterItemsByTerm('cartao')[0].valor).value()),
        loj_troco: parseFloat(numeral(this.filterItemsByTerm('troco')[0].valor).value()),
        loj_outras_entradas: JSON.stringify(this.outrasEntrToList()),
        res_caixa: parseFloat(numeral(this.calculaTotals.resCaixa).value())
      }
      axios.post(path, payload)
        .then(() => {
        })
        .catch((error) => {
          console.log(error)
        })
    },
    getCartao () {
      const path = `/api/financeiro/caixacartao/${this.data_caixa}`
      // const path = 'http://localhost:5000/api/financeiro/caixa/cartao'
      axios.get(path, {params: {data_caixa: this.data_caixa}})
        .then((res) => {
          this.loj_cartao = JSON.parse(res.data.loj_cartao)
        })
        .catch((error) => {
          // eslint-disable-next-line
            console.error(error)
        })
    },
    toTableItems () {
      for (let i = 0; i < this.loj_val_sangria_list.length; i++) {
        let lojSangrias = {
          item: "Sangria "+i,
          valor: this.$options.filters.numero(this.loj_val_sangria_list[i]),
          ref: 'sangria',
          editable: true
        }
        this.loj_items.push(lojSangrias)
      }
      // let lojCartao = {
      //   item: 'Cartão',
      //   valor: this.$options.filters.numero(this.loj_cartao),
      //   ref: 'cartao',
      //   editable: true
      // }
      // this.loj_items.push(lojCartao)
      let lojTroco = {
        item: 'Troco',
        valor: this.$options.filters.numero(this.loj_troco),
        ref: 'troco',
        editable: true
      }
      this.loj_items.push(lojTroco)
      for (let i = 0; i < this.loj_outras_entradas_list.length; i++) {
        console.log(this.loj_outras_entradas_list)
        let lojOutrasEntradas = {
          item: this.loj_outras_entradas_list[i].name,
          valor: this.$options.filters.numero(this.loj_outras_entradas_list[i].valor),
          ref: 'outr',
          editable: true
        }
        console.log(lojOutrasEntradas)
        this.loj_items.push(lojOutrasEntradas)
      }
      let sistDinheiro = {
        item: 'Dinheiro',
        valor: this.$options.filters.numero(this.sist_dinheiro),
        ref: 'sist_dinheiro'
      }
      this.sist_items.push(sistDinheiro)
      let sistPos = {
        item: 'P.O.S.',
        valor: this.$options.filters.numero(this.sist_pos),
        ref: 'sist_pos'
      }
      this.sist_items.push(sistPos)
      let sistTroco = {
        item: 'Troco',
        valor: this.$options.filters.numero(this.sist_troco),
        ref: 'sist_troco'
      }
      this.sist_items.push(sistTroco)
      let sistTotal = {
        item: 'TOTAL Sistema',
        valor: this.$options.filters.numero(this.calculaTotals.sistTotal),
        ref: 'sist_total'
      }
      this.sist_items.push(sistTotal)
    },
    filterItemsByTerm (key) {
      return this.loj_items.filter(item => {
        return item.ref.toLowerCase().includes(key)
      })
    },
    loadOutrEntradas () {
      let outr_array = this.filterItemsByTerm('outr')
      console.log('loadOutr')
      // console.log(outr_array)
      let lista = []
      for (const outra_entr in outr_array) {
        console.log(outr_array[outra_entr])
        console.log(outra_entr)
        // console.log(outr_array[outra_entr].valor)
        // console.log(this.loj_outras_entradas_list)
        lista[outra_entr] = outr_array[outra_entr].valor
        // this.loj_outras_entradas_list.push(outr_array[outra_entr].valor)
      }
      this.loja_outras_entradas_list = lista
      console.log('loadOutr')
    },
    outrasEntrToList () {
      var outrasEntrList = []
      for (let i = 0; i < this.filterItemsByTerm('outr').length+1; i++) {
        let outros = {
          name: this.filterItemsByTerm('outr')[i].item,
          valor: parseFloat(numeral(this.filterItemsByTerm('outr')[i].valor).value())
        }
        outrasEntrList.push(outros)
      }
      return outrasEntrList
    },
    sangriasToList () {
      var sangriasList = []
      for (let i = 0; i < this.filterItemsByTerm('sangria').length; i++) {
        let sangrias = {
          name: this.filterItemsByTerm('sangria')[i].item,
          valor: parseFloat(numeral(this.filterItemsByTerm('sangria')[0].valor).value())
        }
        sangriasList.push(sangrias)
      }
      return sangriasList
    },
    deleteRow (index, item) {
      var idx = this.loj_items.indexOf(item)
      if (idx > -1) {
        this.loj_items.splice(index, 1)
      }
    },
    addNewRow () {
      this.loj_items.push({
        item: 'Outros ' + (this.n_outros + 1),
        valor: this.$options.filters.numero(0),
        ref: 'outr',
        editable: true
      })
      this.n_outros++
    },
    getDadosStone () {
      var data = null

      var xhr = new XMLHttpRequest()

      xhr.addEventListener('readystatechange', function () {
        if (this.readyState === this.DONE) {
          console.log(this.responseText)
        }
      })
      let affiliationCode = '232084871'
      let referenceDate = this.data_caixa.replace(/-/g, '')
      let url = 'https://conciliation.stone.com.br/conciliation-file/v2.2/' + referenceDate + '?affiliationCode=' + affiliationCode
      xhr.open('GET', url)
      xhr.setRequestHeader('authorization', 'Bearer 7b5fd261-3537-4a8a-bffc-0f2d5ec34501')
      xhr.setRequestHeader('x-authorization-raw-data', 'kapivacalcados2020emmovimento')
      xhr.setRequestHeader('x-authorization-encrypted-data', '084da7241e06fa5612edf44693991cb5b1af63e118cf5fdaa27a1faaa866f04162eee459d7536bcdf00ff80e512aa3ad1d9f408b64d3a06b94791d484de09c95')
      // xhr.setRequestHeader('accept-encoding', 'gzip')
      xhr.send(data)
    },
    getDadosStoneNode () {
      var request = require('request')
      var options = {
        method: 'GET',
        url: 'https://conciliation.stone.com.br/conciliation-file/v2.2/20200317?affiliationCode=232084871',
        headers: {
          authorization: 'Bearer 7b5fd261-3537-4a8a-bffc-0f2d5ec34501',
          'x-authorization-raw-data': 'kapivacalcados2020emmovimento',
          'x-authorization-encrypted-data': '084da7241e06fa5612edf44693991cb5b1af63e118cf5fdaa27a1faaa866f04162eee459d7536bcdf00ff80e512aa3ad1d9f408b64d3a06b94791d484de09c95',
          'accept-encoding': 'gzip'
        }
      }
      request(options, function (error, response, body) {
        if (error) throw new Error(error)
        console.log(body)
      })
    },
    valorTdClass (value, key, item) {
      var firstChar = value.charAt(0)
      if (firstChar !== '-' && item.ref === 'res_caixa') {
        return ['text-success', 'text-right']
      } else if (firstChar === '-' && item.ref === 'res_caixa') {
        return ['text-danger', 'text-right']
      } else {
        return 'text-right'
      }
    }
  }
}
</script>

<style scoped>
  body {
    padding: 1rem;
  }

  .righted-input {
    text-align: right
  }
  .lefted-input {
    text-align: left
  }
</style>
