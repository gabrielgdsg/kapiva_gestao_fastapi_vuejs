<template>
<b-toast id="my-toast" :append-toast="true" no-auto-hide>
<!--<b-toast id="my-toast" :append-toast="true" v-model="notif_item.available" @hidden="handleHidden('this toast was hidden',$event)" no-auto-hide>-->
              <template v-slot:toast-title>
                <div class="d-flex flex-grow-1 align-items-baseline">
                  <b-img blank blank-color="#002f59" class="mr-2" width="12" height="12"></b-img>
                  <strong class="mr-auto">Sangria</strong>
                  <small class="text-muted mr-2"> {{time_ago}} </small>
                </div>
              </template>
            Sangria disponível: R$
          </b-toast>
</template>

<script>
import moment from 'moment'

export default {
  name: 'MyToast',
  props: {
    visibility: {type: Boolean, default: true},
    // ago: {type: String, default: ""},
    notif_item: {type: Object}
  },
  data () {
    return {
      sangria_notification_available_list_json: [],
      ago: '',
      oldTime: ''
    }
  },
  computed: {
  },
  methods: {
    handleHidden: function () {
    // handleHidden: function (text, event) {
      this.postJsonData()
    },
    time_ago: function () {
      this.oldTime = this.notif_item.created_timestamp
      this.ago = moment(this.oldTime).fromNow()
      // this.oldTime = new Date();
      setInterval(() => {
        // this.ago = moment(this.oldTime).fromNow();
      }, 1000)
      return this.ago
    }
    // getJsonData: function () {
    //   $.getJSON('/notify', function (sangria_notification_available_list) {
    //     this.sangria_notification_available_list_json = sangria_notification_available_list
    //   }.bind(this))
    // }
  }
}
</script>

<style scoped>

</style>
