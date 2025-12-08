//import '@babel/polyfill'
import 'mutationobserver-shim'
import Vue from 'vue'
Vue.config.devtools = true
import './plugins/bootstrap-vue'
import './plugins/axios'
import App from './App.vue'
import router from './router'
import vueNumeralFilterInstaller from 'vue-numeral-filter'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faPlusCircle, faTrashAlt } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import VueCurrencyInput from 'vue-currency-input'


// font awesome configs
library.add(faPlusCircle, faTrashAlt)
Vue.component('font-awesome-icon', FontAwesomeIcon)

Vue.use(vueNumeralFilterInstaller, { locale: 'pt-BR' })

Vue.config.productionTip = false

// My custom filters
Vue.filter('dinheiro', function (value) {
  var numeral = require('numeral')
  return numeral(value).format('$ 0.0,')
})

Vue.filter('numero', function (value) {
  var numeral = require('numeral')
  return numeral(value).format('0.0,')
})

// VueCurrencyInput Configs
const pluginOptions = {
  globalOptions: { currency: {prefix:'', sufix:''}, locale:'pt'}
  // globalOptions: { currency: 'BRL', locale:'pt'}
}
Vue.use(VueCurrencyInput, pluginOptions)

// //Autosuggest component
// import VueAutosuggest from "vue-autosuggest";
// Vue.use(VueAutosuggest);

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
