<template>
  <b-container class="financeiro-caixa-table">
    {{data_caixa}}

    <b-row align-h="center">
      <b-col cols="4">
        <h4 class="text-center"> Caixa - Loja</h4>
        <b-table responsive striped hover :items="computed_items.loj" :fields="fields">
          <template v-slot:cell(icons)="data">
            <div class="text-center">
              <font-awesome-icon icon="trash-alt" :style="{color: 'red'}" size="lg"
                                 @click="deleteRow(data.index, data.item)"/>
            </div>
          </template>
            <template #cell(item)="data">
                    <editable-field :editable=true :numero=false v-model="data.item.item"></editable-field>
            </template>
            <template #cell(valor)="data">
                <editable-field :editable=true :numero=true v-model="data.item.valor"></editable-field>
            </template>
          <template v-slot:head(icons)="data"> <!-- eslint-disable-line-->
            <div class="text-center">
              <button type='button' class="btn btn-info" @click="addNewRow">
                <font-awesome-icon icon="plus-circle"/>
              </button>
            </div>
          </template>
        </b-table>
          <b-table responsive striped hover :items="computed_items.loj_fixed" :fields="fields" thead-class="d-none">
          <template v-slot:cell(icons)="data">
            <div class="text-center">
              <font-awesome-icon icon="trash-alt" :style="{color: 'red'}" size="lg"
                                 @click="deleteRow(data.index, data.item)"/>
            </div>
          </template>
            <template #cell(item)="data">
                    <editable-field :editable=false :numero=false v-model="data.item.item"></editable-field>
            </template>
            <template #cell(valor)="data">
                <editable-field :editable=false :numero=true v-model="data.item.valor"></editable-field>
            </template>
        </b-table>
      </b-col>

      <b-col cols="4">
        <h4 class="text-center"> Caixa - Sistema</h4>
        <b-table responsive striped hover :items="computed_items.sist" :fields="fields">
            <template #cell(item)="data">
                    <editable-field :editable=false :numero=false v-model="data.item.item"></editable-field>
<!--                    <editable-field :editable=false :numero=false v-model="data.item.item"></editable-field>-->
            </template>
            <template #cell(valor)="data">
                <editable-field :editable=false :numero=true v-model="data.item.valor"></editable-field>
            </template>
        </b-table>
        <h4 class="text-center"> Caixa - Fechamento</h4>
        <b-table responsive striped hover :items="computed_items.res" :fields="fields">
            <template #cell(item)="data">
                <strong>  <editable-field :editable=false :numero=false v-model="data.item.item"></editable-field> </strong>
            </template>
            <template #cell(valor)="data">
               <strong> <editable-field :editable=false :numero=true v-model="data.item.valor"></editable-field> </strong>
            </template>
        </b-table>
        <b-form @submit.stop.prevent="saveCaixaToDb">
          <b-button type="submit" variant="primary">Salvar</b-button>
        </b-form>

          <b-form @submit.stop.prevent="saveCaixaToExcel">
          <b-button type="submit" variant="primary">Salvar para o Excel</b-button>
        </b-form>
      </b-col>



    </b-row>
  </b-container>
</template>

<script>
import axios from 'axios'
import moment from 'moment'
// import numeral from 'numeral'
import EditableField from '../components/EditableField'

export default {
  name: 'FinanceiroCaixaTable',
  props: ['data_caixa', 'dados_caixa'],
  components: {'editable-field' : EditableField},
  data: function () {
    return {
      fields: [
        {
          key: 'item', label: 'Item', thStyle: {width: '25rem', textAlign: 'left'}, tdClass: 'text-left'
        },
        {
          key: 'valor', label: 'Valor', thStyle: {width: '20rem', textAlign: 'center'}, tdClass: this.valorTdClass
        },
        {
          key: 'icons', label: '', thStyle: {width: '5rem'}
        }],
      caixa: {
            data_caixa: moment(this.data_caixa).format('YYYY-MM-DDTHH:mm:ss.SSS'),
            loj_sangria_list: this.dados_caixa.loj_sangria_list,
            loj_outras_entradas_list: this.dados_caixa.loj_outras_entradas_list,
            loj_cartao: this.dados_caixa.loj_cartao,
            loj_suprimento: this.dados_caixa.loj_suprimento,
            loj_troco: this.dados_caixa.loj_troco,
            loj_total: this.dados_caixa.loj_total,
            sist_troco: this.dados_caixa.sist_troco,
            sist_pos: this.dados_caixa.sist_pos,
            sist_dinheiro: this.dados_caixa.sist_dinheiro,
            sist_total: this.dados_caixa.sist_total,
            res_caixa: this.dados_caixa.res_caixa
        },
        n_outras_entradas:this.dados_caixa.loj_outras_entradas_list.length,
        loj_items:[],

    }
  },
  computed: {
    computed_items () {
        let loj_computed_items = this.loj_items
        let lojSubtotal_valor = loj_computed_items.reduce(function (sum, item) {
            let itemValor = parseFloat(item.valor)
            if (!isNaN(itemValor)) {
                return sum + itemValor
            } else {
                return sum
            }
        }, 0)

        let lojTotal_valor = lojSubtotal_valor - this.caixa.loj_suprimento.valor
        let sistTotal_valor = this.caixa.sist_dinheiro.valor + this.caixa.sist_pos.valor + this.caixa.sist_troco.valor
        let resCaixa_valor = lojTotal_valor - sistTotal_valor

        let loj_suprimento = {item:"Suprimento", valor: -this.caixa.loj_suprimento.valor}
        let loj_subtotal = {item:"SUBTOTAL", valor: lojSubtotal_valor}
        let loj_total = {item:"TOTAL Loja", valor:   lojTotal_valor}
        let sist_total = {item:"TOTAL Sistema", valor:  sistTotal_valor}
        let res_caixa = {item:"RESULTADO", valor:  resCaixa_valor}

        let loj_computed_nonedit_items = [].concat(loj_subtotal, loj_suprimento, loj_total)
        let sist_computed_items = [].concat(this.caixa.sist_dinheiro, this.caixa.sist_pos, this.caixa.sist_troco, sist_total)
        let res_computed_items = [res_caixa]

        let computed_items = {loj:loj_computed_items, loj_fixed: loj_computed_nonedit_items, sist: sist_computed_items, res:res_computed_items}
        return computed_items
    }

  },
  beforeMount () {
      this.getCartao()
      this.loadCaixa()
      console.log(this.dados_caixa)
  },
  methods: {
      loadCaixa() {
          this.loj_items = [].concat(this.caixa.loj_sangria_list, this.caixa.loj_cartao, this.caixa.loj_troco, this.caixa.loj_outras_entradas_list)
      },
      saveCaixaToDb() {
          const path = `/api/financeiro/caixa/save_to_db`
          this.caixa.loj_total= this.computed_items.loj_fixed[2]
          this.caixa.sist_total = this.computed_items.sist[3]
          this.caixa.res_caixa = this.computed_items.res[0]
          const payload = {
                  data_caixa:this.caixa.data_caixa,
                  loj_sangria_list: this.caixa.loj_sangria_list,
                  loj_outras_entradas_list: this.caixa.loj_outras_entradas_list,
                  loj_cartao: this.caixa.loj_cartao,
                  loj_suprimento: this.caixa.loj_suprimento,
                  loj_troco: this.caixa.loj_troco,
                  loj_total: this.caixa.loj_total,
                  sist_troco: this.caixa.sist_troco,
                  sist_pos: this.caixa.sist_pos,
                  sist_dinheiro: this.caixa.sist_dinheiro,
                  sist_total: this.caixa.sist_total,
                  res_caixa: this.caixa.res_caixa
          }
          axios.put(path, payload)
              .then(() => {
              })
              .catch((error) => {
                  console.log(error)
              })
      },
      saveCaixaToExcel() {
          const path = `/api/financeiro/caixa/save_to_excel`
          const payload = {
              // maybe send all items as a Caixa
                  data_caixa:this.caixa.data_caixa,
                  loj_sangria_list: this.caixa.loj_sangria_list,
                  loj_outras_entradas_list: this.caixa.loj_outras_entradas_list,
                  loj_cartao: this.caixa.loj_cartao,
                  loj_suprimento: this.caixa.loj_suprimento,
                  loj_troco: this.caixa.loj_troco,
                  loj_total: this.caixa.loj_total,
                  sist_troco: this.caixa.sist_troco,
                  sist_pos: this.caixa.sist_pos,
                  sist_dinheiro: this.caixa.sist_dinheiro,
                  sist_total: this.caixa.sist_total,
                  res_caixa: this.caixa.res_caixa
          }
          axios.put(path, payload)
              .then(() => {
              })
              .catch((error) => {
                  console.log(error)
              })
      },
      getCartao() {
          const path = `/api/financeiro/caixacartao/${this.data_caixa}`
          axios.get(path, {params: {data_caixa: this.data_caixa}})
              .then((res) => {
                  this.caixa.loj_cartao.valor = JSON.parse(res.data.loj_cartao)
              })
              .catch((error) => {
                  // eslint-disable-next-line
                  console.error(error)
              })
      },
      deleteRow(index, item) {
          var idx = this.loj_items.indexOf(item)
          if (idx > -1) {
              this.loj_items[index].valor=0
              this.loj_items.splice(index, 1)
          }
      },
      addNewRow() {
          this.caixa.loj_outras_entradas_list.push({
              item: 'Outros ' + (this.n_outras_entradas + 1),
              valor: 0
          })
          this.loj_items.push(this.caixa.loj_outras_entradas_list[this.n_outras_entradas])
          this.n_outras_entradas++
      },
      getDadosStone() {
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
      // commented to compile in 2024-02-20
      // getDadosStoneNode() {
      //     var request = require('request')
      //     var options = {
      //         method: 'GET',
      //         url: 'https://conciliation.stone.com.br/conciliation-file/v2.2/20200317?affiliationCode=232084871',
      //         headers: {
      //             authorization: 'Bearer 7b5fd261-3537-4a8a-bffc-0f2d5ec34501',
      //             'x-authorization-raw-data': 'kapivacalcados2020emmovimento',
      //             'x-authorization-encrypted-data': '084da7241e06fa5612edf44693991cb5b1af63e118cf5fdaa27a1faaa866f04162eee459d7536bcdf00ff80e512aa3ad1d9f408b64d3a06b94791d484de09c95',
      //             'accept-encoding': 'gzip'
      //         }
      //     }
      //     request(options, function (error, response, body) {
      //         if (error) throw new Error(error)
      //         console.log(body)
      //     })
      // },
      valorTdClass(value, key, item) {
          var firstChar = String(value).charAt(0)
          if (firstChar !== '-' && item.item === 'RESULTADO') {
              return ['text-success', 'text-right']
          } else if (firstChar === '-' && item.item === 'RESULTADO') {
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

  /*.righted-input {*/
  /*  text-align: right*/
  /*}*/
  /*.lefted-input {*/
  /*  text-align: left*/
  /*}*/
</style>
