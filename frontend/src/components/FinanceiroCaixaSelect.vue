<template>
  <div class="financeiro-caixa-select">
    <h1>Caixa</h1>
    <b-form @submit.stop.prevent="onSubmit">
      <label for="datepicker-date">Data: </label>
      <mydatepicker id="datepicker-date" datepicker_default="" @childToParent="receiveDataCaixa"/>
      <br><br>
      <br><br>
      <b-button type="submit" variant="primary">Enviar</b-button>
      </b-form>
  </div>
</template>

<script>
import Mydatepicker from './Mydatepicker'
import axios from "axios";
// import axios from 'axios'
// import moment from 'moment'
// import MyToast from './MyToast'

export default {
  name: 'FinanceiroCaixaSelect',
  components: {
    // MyToast,
    'mydatepicker': Mydatepicker
  },
  data () {
    return {
      data_caixa: ''
    }
  },
  methods: {
    onSubmit () {
      const path = `/api/financeiro/caixa/${this.data_caixa}`
      axios.get(path)
        .then((res) => {
          this.$router.push({name: 'FinanceiroCaixa', params: {currentComponent: 'tabela', data_caixa: this.data_caixa, dados_caixa: res.data}})
        })
        .catch((error) => {
          console.log(error)
        })
    },
    receiveDataCaixa (value) {
      this.data_caixa = value
    }
  }
}
</script>

<style scoped>

</style>
