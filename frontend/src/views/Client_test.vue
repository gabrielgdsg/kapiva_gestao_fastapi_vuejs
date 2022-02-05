<template>
    <b-container class="levantamento-row">
        <b-row>
            <b-col>
                <div class="autosuggest-container">
                    <b>Marca_: </b>
                    <vue-autosuggest
                            :get-suggestion-value="getSuggestionValue"
                            :input-props="{id:'autosuggest__input', placeholder:'Digite a marca', class:'form-control'}"
                            :suggestions="filteredOptions" @click="clickHandler" @focus="focusMe" @input="onInputChange"
                            @selected="onSelected"
                            v-model="query">
                        <div slot-scope="{suggestion}" style="display: flex; align-items: center;">
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
                                    v-model="form_allSelected"
                            >{{ form_allSelected ? 'Desmarcar todos' : 'Marcar todos' }}
                            </b-form-checkbox>
                        </template>

                        <template >
                            <b-form-checkbox-group
                                    :options="form_options"
                                    v-model="form_selected"
                                    class="ml-4" stacked
                            ></b-form-checkbox-group>
                        </template>
                    </b-form-group>
                </div>
            </b-col>
        </b-row>
    </b-container>
</template>

<script>
    import {VueAutosuggest} from "vue-autosuggest";
    import axios from "axios";

    export default {
        name: "Client_test",
        components: {
            VueAutosuggest
        },
        data() {
            return {
                form_selected: [],
                form_allSelected: true,
                form_indeterminate: false,
                form_options: ["a","b"],

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
            };
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
                                // const mapped_items = filtered_items.fornecedores.cod_fornecedor + ': ' + filtered_items.fornecedores.fan_fornecedor
                                console.log('mapped_items')
                                console.log(mapped_items)
                                return mapped_items;
                            })
                    }
                ];
            },
            availableFornecedores() {
                console.log('this.suggestion_selected.fornecedores')
                console.log(this.suggestion_selected.fornecedores)
                return this.suggestion_selected.fornecedores
                    .filter(item => item)
                    .map(item => item.fan_fornecedor)
            }
        },
        beforeMount() {
            this.loadMarcas()
        },
        methods: {
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
                this.form_selected = checked ? this.form_options : []
                // this.form_selected = checked ? this.form_options.slice() : []
            },
        },
        watch: {
            selected(newValue, oldValue) {
                console.log(oldValue)
                // Handle changes in individual flavour checkboxes
                if (newValue.length === 0) {
                    this.form_indeterminate = false
                    this.form_allSelected = false
                } else if (newValue.length === this.availableFornecedores.length) {
                    // } else if (newValue.length === this.flavours.length) {
                    this.form_indeterminate = false
                    this.form_allSelected = true
                } else {
                    this.form_indeterminate = true
                    this.form_allSelected = false
                }
            }
        }
    }
</script>


<style scoped>
    .demo {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    input {
        width: 260px;
        padding: 0.5rem;
    }

    ul {
        width: 100%;
        color: rgba(30, 39, 46, 1.0);
        list-style: none;
        margin: 0;
        padding: 0.5rem 0 .5rem 0;
    }

    li {
        margin: 0 0 0 0;
        border-radius: 5px;
        padding: 0.75rem 0 0.75rem 0.75rem;
        display: flex;
        align-items: center;
    }

    li:hover {
        cursor: pointer;
    }

    .autosuggest-container {
        position: absolute;
        display: flex;
        justify-content: center;
        width: 280px;
    }

    #autosuggest {
        width: 100%;
        display: block;
    }

    .autosuggest__results-item--highlighted {
        background-color: rgba(51, 217, 178, 0.2);
    }
</style>