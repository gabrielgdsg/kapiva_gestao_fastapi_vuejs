<template>
    <div class="levantamentos">
        <div>
  <b-dropdown id="dropdown-1" text="Dropdown Button" class="m-md-2">
    <b-dropdown-item>First Action</b-dropdown-item>
    <b-dropdown-item>Second Action</b-dropdown-item>
    <b-dropdown-item>Third Action</b-dropdown-item>
    <b-dropdown-divider></b-dropdown-divider>
    <b-dropdown-item active>Active action</b-dropdown-item>
    <b-dropdown-item disabled>Disabled action</b-dropdown-item>
  </b-dropdown>
</div>

        <h1>Levantamentos</h1>
        <b-form @submit.stop.prevent="onSubmit">
            <b-row>
            <b-col>
                <div class="autosuggest-container">
                    <b>Marca: </b>
                    <vue-autosuggest
                            :get-suggestion-value="getSuggestionValue"
                            :input-props="{id:'autosuggest__input', placeholder:'Digite a marca', class:'form-control'}"
                            :suggestions="filteredOptions" @click="clickHandler" @focus="focusMe" @input="onInputChange"
                            @selected="onSelected"
                            v-model="query">
                        <div slot-scope="{suggestion}" style="display: flex; align-items: center;" class="autosuggest-container-results">
                            <div> {{suggestion.item.nom_marca}} ({{suggestion.item.cod_marca}})</div>
                        </div>
                    </vue-autosuggest>
                    <br>
                </div>
            </b-col>
            <b-col>
                <div id="form_checkbox">
                    <b-form-group>
                        <template #label>
                            <b>Fornecedores da Marca:</b>
                            <b-form-checkbox
                                    :indeterminate="form_indeterminate"
                                    @change="form_toggleAll"
                                    aria-controls="flavours"
                                    aria-describedby="flavours"
                                    v-model="form_allSelected"
                            >{{ form_allSelected ? 'Desmarcar todos' : 'Marcar todos' }}
                            </b-form-checkbox>
                        </template>

                        <template v-slot="{ ariaDescribedby }">
                            <b-form-checkbox-group
                                    :aria-describedby="ariaDescribedby"
                                    :options="availableFornecedores"
                                    aria-label="Individual flavours"
                                    class="ml-4"
                                    id="flavors"
                                    name="flavors"
                                    stacked
                                    v-model="form_selected"
                            ></b-form-checkbox-group>
                        </template>
                    </b-form-group>
                </div>
            </b-col>
        </b-row>

            <label for="datepicker-data-ini">Data Cadastro inicial: </label>
            <mydatepicker-ini id="datepicker-data-ini" :datepicker_default="datepicker_ini"
                              @childToParent="receiveDataCadastroIni"/>
            <br><br>
            <label for="datepicker-data-fim">Data Cadastro final: </label>
            <mydatepicker-fim id="datepicker-data-fim" :datepicker_default="datepicker_fim"
                              @childToParent="receiveDataCadastroFim"/>
            <br><br>
            <b-button type="submit" variant="primary">Enviar</b-button>
        </b-form>
        <b-table striped hover :items="items" :fields="fields" class="text-right" :small=true></b-table>
    </div>
</template>

<script>
    import Mydatepicker from '../components/Mydatepicker'
    import axios from "axios"
    import {VueAutosuggest} from 'vue-autosuggest'

    export default {
        name: "Levantamentos",
        components: {
            'mydatepicker-ini': Mydatepicker,
            'mydatepicker-fim': Mydatepicker,
            'vue-autosuggest': VueAutosuggest
        },
        data() {
            return {
                form_selected: [],
                form_allSelected: true,
                form_indeterminate: false,
                query: "",
                suggestion_selected: {
                    cod_marca: 0,
                    fornecedores: [{fan_fornecedor: ''}],
                    nom_marca: "carregando",
                },
                suggestions: [
                    {
                        data: [
                            {
                                cod_marca: 0,
                                fornecedores: [],
                                nom_marca: "carregando marcas",
                            }
                        ]
                    }
                ],
                datepicker_ini: new Date(2019, 0, 1),
                datepicker_fim: new Date(2019, 11, 16),
                data_cadastro_ini: '',
                data_cadastro_fim: '',
                cod_fornecedor: 70,
                items: [],
                fields: [
                    {key: 'nom_marca', label: 'Nom. Marca'},
                    {key: 'dat_cadastro', label: 'Data Cad.'},
                    {key: 'dat_alteracao', label: 'Data Alt.'},
                    {key: 'cod_referencia', label: 'Ref.'},
                    {key: 'des_produto', label: 'Descrição.'},
                    // {key: 'qtd', label: 'Qtd.'},
                    {key: 'saldo_estoque', label: 'Saldo Est.'},
                    {key: 'vlr_venda1', label: 'Vlr. Venda'},
                    {key: 'vlr_custo_bruto', label: 'Custo'},
                    {key: 'cod_grade', label: 'cod grade'},
                    {key: 'des_grade', label: 'des_grade'},
                    {key: 'cod_tamanho', label: 'cod_tamanho'},
                    {key: 'des_tamanho', label: 'des_tamanho'}
                ]
            }
        },
        computed: {
            filteredOptions() {
                return [
                    {
                        data: this.suggestions[0].data
                            .filter(option => {
                                return option.nom_marca.toLowerCase().indexOf(this.query.toLowerCase()) > -1;
                            })
                            .map(filtered_items => {
                                const mapped_items = filtered_items
                                return mapped_items;
                            })
                    }
                ];
            },
            availableFornecedores() {
                return this.suggestion_selected.fornecedores
                    .filter(item => item)
                    .map(item => item.fan_fornecedor)
            }
        },
        beforeMount() {
            this.loadMarcas()
        },
        methods: {
            onSubmit() {
                const path = `/api/levantamentos/${this.data_cadastro_ini}/${this.data_cadastro_fim}/${this.suggestion_selected.cod_marca}/`
                axios.get(path)
                    .then((res) => {
                        console.log(res)
                        this.items = res.data
                        // this.$router.push({name: 'FinanceiroCaixa', params: {currentComponent: 'tabela', data_caixa: this.data_caixa, dados_caixa: res.data}})
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            receiveDataCadastroIni(value) {
                this.data_cadastro_ini = value
            },
            receiveDataCadastroFim(value) {
                this.data_cadastro_fim = value
            },
            loadMarcas() {
                const path = `/api/read/marcas/`
                axios.get(path)
                    .then((res) => {
                        console.log('res')
                        console.log(res)
                        this.suggestions[0].data = res.data
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            clickHandler(item) {
                console.log(item)
                // event fired when clicking on the input
            },
            onSelected(item) {
                this.suggestion_selected = item.item;
                this.form_selected = this.availableFornecedores

            },
            onInputChange(text) {
                console.log(text)
            },
            /**
             * This is what the <input/> value is set to when you are selecting a suggestion.
             */
            getSuggestionValue(suggestion) {
                return suggestion.item.nom_marca;
            },
            focusMe(e) {
                console.log(e) // FocusEvent
            },
            form_toggleAll(checked) {
                this.form_selected = checked ? this.availableFornecedores.slice() : []
            }
            
        }
    }
</script>

<style>
/*<style scoped>*/
.autosuggest-container {
    position: absolute;
    display: flex;
    justify-content: center;
    width: 280px;

}

.autosuggest__results {
    z-index: 1000;
    position: absolute;
    display: flex;
    /*justify-content: center;*/
    /*width: 280px;*/
    background-color: #fff;
    background-clip: padding-box;
    border: 1px solid rgba(0, 0, 0, .15);
    border-radius: .25rem;

}


</style>