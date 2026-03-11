<template>
    <div id="nav">
        <b-navbar type="dark">
            <b-collapse id="nav-collapse" is-nav>
                <b-navbar-nav>
                    <router-link class="nav-link" to="/" exact>
                        <img class="logo" src="../assets/kapiva_blue.jpg" alt=""/>
                    </router-link>
                    <router-link class="nav-link" :to="{name: 'Comissao', params: {currentComponent: 'selecionar'}}">
                        Comissão
                    </router-link>
                    <router-link class="nav-link" to="/levantamentos">Levantamentos</router-link>
                    <router-link class="nav-link" to="/levantamentos2">Levantamentos 2</router-link>
                    <router-link class="nav-link" to="/faturamento">Faturamento</router-link>
                    <router-link class="nav-link" to="/vendedor">Vendedores</router-link>
                    <router-link class="nav-link" to="/pedidos-chegando">Pedidos Chegando</router-link>
                    <router-link class="nav-link" to="/metas">Metas</router-link>
                    <b-nav-item-dropdown text="Financeiro" right>
                        <b-dropdown-item class="nav-link" to="/financeiro/caixa">
                            Caixa
                        </b-dropdown-item>
                    </b-nav-item-dropdown>
                </b-navbar-nav>

            </b-collapse>
            <b-navbar-nav align="start">
                <b-overlay :show="busy" @hidden="onHidden" rounded opacity="0.6" spinner-small spinner-variant="primary" class="d-inline-block" >
                    <b-button type="submit" variant="primary" @click="atualizarDB" ref="button" :disabled="busy">AtualizarDB</b-button>
                </b-overlay>
            </b-navbar-nav>
        </b-navbar>
        <mytoast></mytoast>
    </div>
</template>

<script>
    import axios from 'axios'
    import moment from 'moment'
    import MyToast from '../components/MyToast'

    export default {
        name: 'TheNavBar',
        data() {
            return {
                toastCount: 0,
                busy: false
            }
        },
        components: {
            'mytoast': MyToast
        },
        mounted() {
        },
        methods: {
            createToasts() {
                const today = '2020-03-16'
                // const today = new Date()
                const path = 'http://localhost:5000/api/toasts/create'
                const payload = {
                    data_caixa: moment(today).format('YYYY-MM-DD')
                }
                axios.post(path, payload)
                    .then((res) => {
                        console.log(res)
                        this.makeToast()
                    })
                    .catch((error) => {
                        console.log(error)
                        // this.getBooks()
                    })
            },
            testApi() {
                // const path = `http://192.168.1.126:80/api/comissao/2019-12-15/2019-12-15`
                const path = `/api/comissao/2019-12-15/2019-12-15`
                // const path = 'http://localhost:80/'
                axios.get(path)
                    .then((res) => {
                        console.log(res)
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            atualizarDB() {
                this.busy = true
                axios.get(`/api/reloadfrompostgresdb/marcafornecedor/`)
                    .then((res) => {
                        this.busy = false
                        const count = Array.isArray(res?.data) ? res.data.length : 0
                        this.$bvToast.toast(count > 0 ? `Marcas atualizadas: ${count} carregadas do PostgreSQL` : 'Marcas atualizadas', {
                            title: 'AtualizarDB',
                            variant: 'success',
                            autoHideDelay: 4000
                        })
                        window.dispatchEvent(new CustomEvent('marcas-updated'))
                    })
                    .catch((error) => {
                        this.busy = false
                        const d = error.response?.data?.detail
                        const msg = (typeof d === 'string' ? d : (d ? JSON.stringify(d) : error.message)) || 'Erro ao atualizar'
                        console.error('AtualizarDB failed:', error.response?.data || error)
                        if (this.$bvToast) {
                            this.$bvToast.toast(msg, { title: 'AtualizarDB falhou', variant: 'danger', noAutoHide: true })
                        }
                        alert('AtualizarDB falhou: ' + msg)
                    })
            },
            onHidden() {
                // Return focus to the button once hidden
                this.$refs.button.focus()
            },
            makeToast() {
                this.toastCount++
                this.$bvToast.toast(`This is toast number ${this.toastCount}`, {
                    // this.$bvToast.toast(`This is toast number ${this.toastCount}`, {
                    title: 'BootstrapVue Toast',
                    appendToast: true,
                    noAutoHide: true,
                    solid: true
                })
            }
        }
    }
</script>

<style scoped>

    #nav {
        /*font-weight: bold;*/
        background-color: #002f59;
    }

    #nav a.router-link-exact-active {
        font-weight: bold;
        /*color: #42b983;*/
    }

    .logo {
        height: 30px;
        margin-right: 10px;
    }

</style>
