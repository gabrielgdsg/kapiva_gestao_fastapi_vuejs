<template>
  <div class="comissao-select">
    <h1>Comissão</h1>
    <b-form @submit.stop.prevent="onSubmit">
      <label for="datepicker-data-ini">Data inicial: </label>
      <mydatepicker-ini id="datepicker-data-ini" datepicker_default="2019/12/01" @childToParent="receiveDataIni"/>
      <br><br>
      <label for="datepicker-data-fim">Data final: </label>
      <mydatepicker-fim id="datepicker-data-fim" datepicker_default="2019/12/31" @childToParent="receiveDataFim"/>
      <br><br>
      <b-button type="submit" variant="primary">Enviar</b-button>
      </b-form>
  </div>
</template>

<script>
import Mydatepicker from './Mydatepicker'
import axios from 'axios'

export default {
  name: 'ComissaoSelect',
  components: {
    'mydatepicker-ini': Mydatepicker,
    'mydatepicker-fim': Mydatepicker
  },
  data () {
    return {
      data_ini: '',
      data_fim: ''
    }
  },
  methods: {
    onSubmit () {
      const path = `/api/comissao/${this.data_ini}/${this.data_fim}`
      axios.get(path)
        .then((res) => {
          this.$router.push({name: 'Comissao', params: {currentComponent: 'tabela', data_ini: this.data_ini, data_fim: this.data_fim, dados_comissao: res.data}})
        })
        .catch((error) => {
          console.log(error)
        })
    },
    receiveDataIni (value) {
      this.data_ini = value
    },
    receiveDataFim (value) {
      this.data_fim = value
    }
  }
}
</script>

<style scoped>

</style>
