<template>
  <datepicker v-model="date_value" @change="emitToParent" :formatter="momentFormat" :shortcuts="shortcuts"
              placeholder="Selecione a data"/>
</template>

<script>
import DatePicker from 'vue2-datepicker'
import 'vue2-datepicker/index.css'
import 'vue2-datepicker/locale/pt-br'
import moment from 'moment'

export default {
  name: 'Mydatepicker',
  components: {
    'datepicker': DatePicker
  },
  props: ['datepicker_default'],
  data () {
    return {
      // date_value: this.initial_date,
      date_value: new Date(this.datepicker_default),
      // date_value: new Date('2020-03-18'),
      // date_value: '',
      // date_value: new Date(2019, 11, 15), // initial date_value
      childMessage: '',
      shortcuts: [
        { text: 'Hoje', onClick: () => this.today },
        { text: 'Ontem', onClick: () => this.yesterday },
        // {
        //   text: 'Ontem',
        //   onClick () {
        //     const yesterday = new Date()
        //     yesterday.setTime(yesterday.getTime() - 3600 * 1000 * 24)
        //     // this.yesterday  = yesterday
        //     return yesterday
        //   }
        // }
      ],
      momentFormat: {
        // Date to String
        stringify: (date) => {
          return date ? moment(date).format('DD/MM/YYYY') : ''
        },
        // String to Date
        parse: (value) => {
          return value ? moment(value, 'DD/MM/YYYY').toDate() : null
        }
      }
    }
  },
  computed: {
    today() {
      return new Date()
    },
    yesterday() {
      const yesterday = new Date()
      yesterday.setTime(yesterday.getTime() - 3600 * 1000 * 24)
      return yesterday
    },

    // computed_date_value() {
    //   var date_value =  new Date
    //   console.log(Date(this.datepicker_default))
    //   if (Date(this.datepicker_default) !== "Invalid Date") {
    //     date_value = new Date(this.datepicker_default)
    //   }
    //   return date_value
    // }
  },
  beforeMount () {
    // this.date_value = this.datepicker_default
    // this.date_value = new Date(this.datepicker_default)
    this.emitToParent()
  },
  methods: {
    emitToParent () {
      this.$emit('childToParent', moment(this.date_value).format('YYYY-MM-DD'))
    },
  }
}
</script>

<style scoped>

</style>
