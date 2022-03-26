<template>
    <div id="app">

<b-table striped show-empty :items="filtered">
  <template slot="top-row" slot-scope="{ fields }">
    <td v-for="field in fields" :key="field.key">
      <input v-model="filters[field.key]" :placeholder="field.label">
    </td>
  </template>
</b-table>
</div>
</template>

<script>
    export default {
        data() {return {
            filters: {
                id: '',
                issuedBy: '',
                issuedTo: ''
            },
            items: [{id: 1234, issuedBy: 'Operator', issuedTo: 'abcd-efgh'}, {
                id: 5678,
                issuedBy: 'User',
                issuedTo: 'ijkl-mnop'
            }]
        }},
        computed: {
            filtered() {
                const filtered = this.items.filter(item => {
                    return Object.keys(this.filters).every(key =>
                        String(item[key]).includes(this.filters[key]))
                })
                return filtered
                    .length > 0 ? filtered : [{
                    id: '',
                    issuedBy: '',
                    issuedTo: ''
                }]
            }
        }
    }
</script>



