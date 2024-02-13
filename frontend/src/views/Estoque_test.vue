<template>
    <div class="levantamento-row">
        <b-row>
            <b-col sm="2">

                <b-form @submit.stop.prevent="readProdutosFromMongoWithFilter">
                    <b-button type="submit" variant="primary">Mongo Estoque Produtos with Filter</b-button>
                </b-form>
                <b/>
                <b-form @submit.stop.prevent="readProdutosFromMongo">
                    <div class="autosuggest">
                            <b>Marca: </b>
                            <vue-autosuggest
                                    :get-suggestion-value="getSuggestionValue"
                                    :input-props="{id:'autosuggest__input', placeholder:'Digite a marca', class:'form-control'}"
                                    :suggestions="filteredOptions" @click="clickHandler" @focus="focusMe"
                                    @input="onInputChange"
                                    @selected="onSelected"
                                    v-model="marcas_suggestion_query">
                                <div class="autosuggest-container-results" slot-scope="{suggestion}"
                                     style=" align-items: center;">
                                    <div> {{suggestion.item.nom_marca}} ({{suggestion.item.cod_marca}})</div>
                                </div>
                            </vue-autosuggest>
                        </div>

                    <b-button type="submit" variant="primary">Read Produtos From Mongo</b-button>
                </b-form>
            </b-col>
            <b-col sm="2">
                    <b-row>
                        <label>Data Movto inicial: </label>
                        <mydatepicker-ini :datepicker_default="datepicker_ini" @childToParent="receiveDataMovtoIni"  placeholder="Selecione a data"/>
                        <br><br>
                    </b-row>
                    <b-row>
                        <label>Data Movto final: </label>
                        <mydatepicker-fim :datepicker_default="datepicker_fim" @childToParent="receiveDataMovtoFim"  placeholder="Selecione a data"/>
                        <br><br>

                    </b-row>
                </b-col>
            <b-col>
                <div id="grades_check_box">
                        <b-row>
                        <b-col :key="grade.name" sm="6" v-for="grade in grades_options">

                            <div class='form-check form-switch'>
                                <div>
                                    <input :value="grade" class='form-check-input' type="checkbox"
                                           v-model="grades_selected"/>
                                    <label class='form-check-label'>{{grade.name}}</label>
                                    <!--                        <br>-->
                                </div>
                            </div>

                        </b-col>
                    </b-row>
                </div>
            </b-col>
        </b-row>
        <b-row>
            <b-input v-model="filter" placeholder="Filtros OU separados por vírgulas"></b-input>
            <!--            <b-table :bordered="true" :fields="computedFields" :filter="filter" :items="items" :filter-function="filterFn"-->
<!--            <b-table :bordered="true" :fields="computedFields" :filter="filter" :items="filteredItemsComputed" :filter-function="filterFn"-->
            <b-table :bordered="true" :fields="computedFields" :filter="filter" :items="filteredData" :filter-function="filterFn"
                 :small=true
                  @row-clicked="expandAdditionalInfo" class="text-right" head-variant="light" hover sticky-header="700px" striped>
<!--                 :sort-compare="dateSorter" @row-clicked="expandAdditionalInfo" class="text-right" head-variant="light" hover sticky-header="700px" striped>-->

            <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item }">
                <div v-if="item.estoque_history[item.estoque_history.length-1]"><!-- eslint-disable-line-->
                    {{item.estoque_history[item.estoque_history.length-1].grade_estoque[field.key+"_E"]}}<br>
                <b>{{item.estoque_history[item.estoque_history.length-1].grade_estoque[field.key]}}</b>
                </div>


                    <div v-if="grade_estoque_totais[field.key+'_E']"><!-- eslint-disable-line-->
                        {{grade_estoque_totais[field.key+"_E"] = grade_estoque_totais[field.key+"_E"] + item.estoque_history[item.estoque_history.length-1].grade_estoque[field.key+"_E"]}}
                    </div>
                    <div v-else><!-- eslint-disable-line-->
                        {{grade_estoque_totais[field.key+"_E"] = item.estoque_history[item.estoque_history.length-1].grade_estoque[field.key+"_E"]}}
                    </div>
                    <div v-if="grade_estoque_totais[field.key]"><!-- eslint-disable-line-->
                        {{grade_estoque_totais[field.key] = item.estoque_history[item.estoque_history.length-1].grade_estoque[field.key]}}
                    </div>
                    <div v-else><!-- eslint-disable-line-->
                        {{grade_estoque_totais[field.key] = item.estoque_history[item.estoque_history.length-1].grade_estoque[field.key]}}
                    </div>

            </template>

<!--                <template v-slot:cell(estoque_history)="data">-->
<!--&lt;!&ndash;                    <div v-if="data.item.estoque_history">&ndash;&gt;-->
<!--                    {{data.item.estoque_history}}-->
<!--&lt;!&ndash;                    </div>&ndash;&gt;-->
<!--                </template>-->


                <template v-slot:cell(saidas)="data">
                    <div v-if="data.item.estoque_history[data.item.estoque_history.length-1]">
                    {{data.item.estoque_history[0].saidas - data.item.estoque_history[data.item.estoque_history.length-1].saidas}}
                    </div>
                </template>

                <template v-slot:cell(totais)="data">
                    <div v-if="data.item.estoque_history[data.item.estoque_history.length-1]">
                        {{data.item.estoque_history[data.item.estoque_history.length-1].saldo_estoque_e - data.item.estoque_history[0].saldo_estoque_e}}<br>
                     <b>{{data.item.estoque_history[data.item.estoque_history.length-1].saldo_estoque}}</b>
                    </div>


                </template>

                <template scope="data" slot="top-row" ><!-- eslint-disable-line-->
                <td :key="field.key" v-for="field in [...baseFields,...gradeFields,...valoresFields]">
                    <template v-if="field.key==='nom_marca'||field.key==='raz_fornecedor'||field.key==='dat_cadastro'||field.key==='dat_ultcompra'||field.key==='estoque_history'||field.key==='cod_referencia'||field.key==='des_cor'||field.key==='des_produto'||field.key==='vlr_custo_bruto'||field.key==='vlr_venda1'">
                        <b-form-input :placeholder="field.label" class="col-sm" v-model="multiSearch[field.key]"></b-form-input>
<!--                        <b-form-input :placeholder="field.label" class="col-sm" v-model="filters[field.key]"></b-form-input>-->
                    </template>
                    <template v-else>
<!--                        {{this.grade_estoque_totais}}-->
                        <div v-if="grade_estoque_totais[field.key+'_E'] && grade_estoque_totais[field.key]">
                            <b>{{grade_estoque_totais[field.key+"_E"]}}</b>
                            {{grade_estoque_totais[field.key]}}
                        </div>
                    </template>
                </td>
                </template>




            </b-table>
        </b-row>

    </div>
</template>

<script>
    import {VueAutosuggest} from 'vue-autosuggest'
    import axios from "axios";
    import moment from "moment";
    // import DatePicker from 'vue2-datepicker'
    import 'vue2-datepicker/index.css'
    import 'vue2-datepicker/locale/pt-br'
    import Mydatepicker from '../components/Mydatepicker'
    // import moment from "moment";

    export default {
        name: "Estoque_test",
        components: {
            'mydatepicker-ini': Mydatepicker,
            'mydatepicker-fim': Mydatepicker,
            'vue-autosuggest': VueAutosuggest
        },
        data() {
            return {
                a_just_for_testing:'',
                cod_marca: 0, //olympikus = 567
                // cod_marca: '567', //olympikus = 567
                // data_movto_ini: new Date('2019-01-01 03:00:00.000'),
                // data_movto_fim: new Date,
                default_date: new Date('1900-01-01 01:00:00.000'),
                datepicker_ini: new Date(1900, 0, 1),
                datepicker_fim: new Date(2019, 11, 16),
                data_movto_ini: '',
                data_movto_fim: '',
                // default_date: new Date('1900-01-01 01:00:00.000'),
                filter: null,
                filters: {nom_marca: '', dat_cadastro: '', des_cor: '', des_produto: ''},
                grades_selected: [],
                grade_estoque_totais: {},
                soma_deletar: {},
                grades_options: [
                    {
                        "name": 'Calçado Bebê',
                        "grade": [{key: '1', label: '1'},
                            {key: '2', label: '2'},
                            {key: '3', label: '3'},
                            {key: '4', label: '4'}]
                    },
                    {
                        "name": 'Roupa Infantil PI-MI-GI',
                        "grade": [
                            {key: 'PI', label: 'PI'},
                            {key: 'MI', label: 'MI'},
                            {key: 'GI', label: 'GI'}]
                    },
                    {
                        "name": 'Calçado Infantil',
                        "grade": [
                            {key: '15', label: '15'},
                            {key: '16', label: '16'},
                            {key: '17', label: '17'},
                            {key: '18', label: '18'},
                            {key: '19', label: '19'},
                            {key: '20', label: '20'},
                            {key: '21', label: '21'},
                            {key: '22', label: '22'},
                            {key: '23', label: '23'},
                            {key: '24', label: '24'},
                            {key: '25', label: '25'},
                            {key: '26', label: '26'},
                            {key: '27', label: '27'},
                            {key: '28', label: '28'},
                            {key: '29', label: '29'},
                            {key: '30', label: '30'},
                            {key: '31', label: '31'},
                            {key: '32', label: '32'},
                            {key: '33', label: '33'},
                            {key: '34', label: '34'},
                            {key: '35', label: '35'},
                            {key: '36', label: '36'}]
                    },
                    {
                        "name": 'Roupa Infantil 8-16',
                        "grade": [
                            {key: '8', label: '8'},
                            {key: '10', label: '10'},
                            {key: '12', label: '12'},
                            {key: '14', label: '14'},
                            {key: '16', label: '16'}]
                    },
                    {
                        "name": 'Calçado Infantil Duplo',
                        "grade": [{key: '17/18', label: '17/18'},
                            {key: '19/20', label: '19/20'},
                            {key: '21/22', label: '21/22'},
                            {key: '23/24', label: '23/24'},
                            {key: '25/26', label: '25/26'},
                            {key: '27/28', label: '27/28'},
                            {key: '29/30', label: '29/30'},
                            {key: '31/32', label: '31/32'},
                            {key: '33/34', label: '33/34'},
                            {key: '35/36', label: '35/36'}]
                    },
                    {
                        "name": 'Roupa Adulto PP',
                        "grade": [
                            {key: 'PP', label: 'PP'},
                            {key: 'EP', label: 'EP'},]
                    },
                    {
                        "name": 'Calçado Adulto',
                        "grade": [{key: '33', label: '33'},
                            {key: '34', label: '34'},
                            {key: '35', label: '35'},
                            {key: '36', label: '36'},
                            {key: '37', label: '37'},
                            {key: '38', label: '38'},
                            {key: '39', label: '39'},
                            {key: '40', label: '40'},
                            {key: '41', label: '41'},
                            {key: '42', label: '42'},
                            {key: '43', label: '43'},
                            {key: '44', label: '44'}]
                    },
                    {
                        "name": 'Roupa Adulto 34-56',
                        "grade": [
                            {key: '34', label: '34'},
                            {key: '36', label: '36'},
                            {key: '38', label: '38'},
                            {key: '40', label: '40'},
                            {key: '42', label: '42'},
                            {key: '44', label: '44'},
                            {key: '46', label: '46'},
                            {key: '48', label: '48'},
                            {key: '50', label: '50'},
                            {key: '52', label: '52'},
                            {key: '54', label: '54'},
                            {key: '56', label: '56'},
                            {key: '58', label: '58'}]
                    },
                    {
                        "name": 'Calçado Adulto Duplo',
                        "grade": [
                            {key: '33/34', label: '33/34'},
                            {key: '35/36', label: '35/36'},
                            {key: '37/38', label: '37/38'},
                            {key: '39/40', label: '39/40'},
                            {key: '41/42', label: '41/42'},
                            {key: '43/44', label: '43/44'},
                            {key: '45/46', label: '45/46'},
                            {key: '47/48', label: '47/48'}]
                    },
                    {
                        "name": 'Roupa Adulto P-M-G-GG',
                        "grade": [
                            {key: 'P', label: 'P'},
                            {key: 'M', label: 'M'},
                            {key: 'G', label: 'G'},
                            {key: 'GG', label: 'GG'}]
                    },
                    {
                        "name": 'Calçado Adulto Big',
                        "grade": [{key: '45', label: '45'},
                            {key: '46', label: '46'},
                            {key: '47', label: '47'},
                            {key: '48', label: '48'}]
                    },
                    {
                        "name": 'Roupa Adulto XGs',
                        "grade": [
                            {key: 'XG', label: 'XG'},
                            {key: 'X1', label: 'X1'},
                            {key: 'X2', label: 'X2'},
                            {key: 'X3', label: 'X3'},
                            {key: 'GGG', label: 'GGG'},
                            {key: 'EG', label: 'EG'},
                            {key: 'EGG', label: 'EGG'},
                            {key: 'EXGG', label: 'EXGG'},
                            {key: 'G1', label: 'G1'},
                            {key: 'G2', label: 'G2'},
                            {key: 'G3', label: 'G3'},
                            {key: 'G4', label: 'G4'},
                            {key: '1G', label: '1G'},
                            {key: '2G', label: '2G'},
                            {key: '3G', label: '3G'},
                            {key: '4G', label: '4G'}]
                    },
                    {
                        "name": 'Cinto',
                        "grade": [
                            {key: '90', label: '90'},
                            {key: '95', label: '95'},
                            {key: '100', label: '100'},
                            {key: '105', label: '105'},
                            {key: '110', label: '110'},
                            {key: '115', label: '115'},
                            {key: '120', label: '120'}]
                    },
                    {
                        "name": 'Img Link',
                        "grade": {key: 'img_link', label: 'Img Link'}
                    },
                ],
                items:[],
                mapped_items: [],
                marcas: {},
                multiSearch: {},
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
                marcas_suggestion_query: ""
            };
        },
        computed: {
            filteredData() {
                if (this.multiSearch) {
                    return this.items.filter((item) => {
                        return Object.entries(this.multiSearch).every(([key, value]) => {
                            if (value.includes("|") && !value.includes("!")) {
                                let el = value.split("|");
                                return el.some((elem) =>
                                    (item[key] || "").toString().toUpperCase().startsWith(elem.toString().toUpperCase())
                                );
                            }
                            if (value.substring(0, 1) === "!" && !value.includes("|")) {
                                let el = value.split("!");
                                return el.some((elem) =>
                                    !(item[key] || "").toString().toUpperCase().startsWith(elem.toString().toUpperCase())
                                );
                            }
                            if (value.includes("|") && value.substring(0, 1) === "!") {
                                let el = value.split("!")[1].split("|");
                                return !el.some((elem) =>
                                    (item[key] || "").toString().toUpperCase().startsWith(elem.toString().toUpperCase())
                                );
                            }
                            if ((key === "dat_cadastro" || key === "dat_ultcompra") && value.substring(0, 1) === "<") {
                                let el = value.split("<");
                                if (item[key] !== " ") {
                                    return moment(item[key], 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate();
                                }
                            }
                            if ((key === "dat_cadastro" || key === "dat_ultcompra") && value.substring(0, 1) === ">") {
                                let el = value.split(">");
                                if (item[key] !== " ") {
                                    return moment(item[key], 'YYYY-MM-DD').toDate() > moment(el[1], 'YYYY-MM-DD').toDate();
                                }
                            }
                            if (value.substring(0, 1) === ">") {
                                let el = value.split(">");
                                if (item[key] !== " ") {
                                    return Number(item[key] || "") > el[1];
                                }
                            }

                            if (value.substring(0, 1) === "<") {
                                let el = value.split("<");
                                if (item[key] !== " ") {
                                    return Number(item[key] || "") < el[1];
                                }
                            }
                            if (value.substring(0, 1) === "=") {
                                let el = value.split("=");
                                return (item[key] || "").toString().toUpperCase() === el[1].toString().toUpperCase();
                            }
                            // TODO - trying to implement estoque_history filter
                            if ((key === "estoque_history") && value.substring(0, 1) === "m") {
                                // let test = item[key].map(a => a.data_movto);
                                console.log('test')

                                let el = value.split("m");
                                if (item[key] !== " ") {
                                    console.log(el)
                                    console.log("item[key]")
                                    console.log(item[key])

                                    let result = item[key].filter( history_item => moment(history_item.data_movto, 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate());

                                    // let result = item[key].filter( history_item => history_item.saidas >= -50 && history_item.saidas <= el[1])
                                    console.log("result")
                                    console.log(result)

                                    // console.log(item[key].map(a => a.saidas))
                                    // let retorno = Number(item[key].saidas || "") < el[1]
                                    // console.log("item[key].saidas")
                                    // console.log(item[key].saidas)
                                    // console.log("retorno")
                                    // console.log(retorno)
                                    return item[key].filter( history_item => moment(history_item.data_movto, 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate());
                                    // return item[key].filter( history_item => moment(history_item.data_movto, 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate());

                                }
                            }
                            if ((key === "estoque_history") && value.substring(0, 1) === "M") {
                                // let test = item[key].map(a => a.data_movto);
                                console.log('test')

                                let el = value.split("M");
                                if (item[key] !== " ") {
                                    console.log(el)
                                    console.log("item[key]")
                                    console.log(item[key])

                                    let result = item[key].filter( history_item => moment(history_item.data_movto, 'YYYY-MM-DD').toDate() > moment(el[1], 'YYYY-MM-DD').toDate());

                                    // let result = item[key].filter( history_item => history_item.saidas >= -50 && history_item.saidas <= el[1])
                                    console.log("result")
                                    console.log(result)

                                    // console.log(item[key].map(a => a.saidas))
                                    // let retorno = Number(item[key].saidas || "") < el[1]
                                    // console.log("item[key].saidas")
                                    // console.log(item[key].saidas)
                                    // console.log("retorno")
                                    // console.log(retorno)
                                    return item[key].filter( history_item => moment(history_item.data_movto, 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate());
                                    // return item[key].filter( history_item => moment(history_item.data_movto, 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate());
                                }
                            }
                            // if (value.substring(0, 1) === "<" && (key === "dat_estoque_history_ini" || key === "dat_estoque_history_fim")) {
                            //     // this.just_for_testing = item
                            //     let el = value.split("<");
                            //     if (item[key] !== " ") {
                            //         return moment(item[key], 'YYYY-MM-DD').toDate() < moment(el[1], 'YYYY-MM-DD').toDate();
                            //     }
                            // }

                            return (item[key] || "").toString().toUpperCase().includes(value.toString().toUpperCase());
                        });
                    });
                } else {
                    return this.items;
                }
            },
            // saldoEstoque() {
            //
            // },
            //TODO maybe one can speed code up with reduce instead of map+filter
            mappedItemsComputed() {
                const mapped_items = this.items.map((item) => {
                    return {
                        ...item,
                        estoque_history: item.estoque_history.filter((movto) => {
                            let data_aux =  new Date(movto.data_movto)
                            if (data_aux > this.data_movto_ini && data_aux < this.data_movto_fim)
                                return true
                        })
                    }
                })
                return mapped_items
            },
            filteredItemsComputed() {
                // return  Object.freeze(this.filteredItemsByDescription(this.filteredItemsByCor(this.items)))
                return  this.filteredItemsByCor(this.filteredItemsByDescription(this.items))
                // return  this.filteredItemsByDescription(this.filteredItemsByCor(this.items))
                // return this.items.filter(item => item.des_produto.toLowerCase().includes(this.filters.des_produto.toLowerCase()))
            },


            filteredmappedItemsComputed() {
                const filtered = this.items.filter(item => {
                // const filtered = this.mappedItemsComputed.filter(item => {
                //     console.log(filtered)
                    return Object.keys(this.filters).every(key =>{
                        String(item[key].toString().toLowerCase()).includes(this.filters[key].toString().toLowerCase())
                    }
                    )
                });
                // console.log('filtered')
                // console.log(filtered)
                return filtered
                // return this.items
            },
            computedFields() {
                // return [].concat(this.baseFields, this.adultoFields, this.valoresFields)
                return [].concat(this.baseFields, this.gradeFields, this.valoresFields)
                // return [].concat(this.baseFields, this.gradeFields, this.totaisFields, this.valoresFields)
            },
            gradeFields() {
                var grades = this.grades_selected.map(selected => {
                    return selected.grade
                })
                // return [].concat(grades.flat(1)) //manter totaisFields aqui para que os totais fiquem corretos
                return [].concat(grades.flat(1), this.totaisFields) //manter totaisFields aqui para que os totais fiquem corretos
                // return [].concat(this.infantoFields, this.adultoFields, this.totaisFields)
            },
            baseFields() {
                return [
                    {key: 'selected', label: 'Sel.'},
                    {key: 'nom_marca', label: 'Nom. Marca', sortable: true},
                    {key: 'raz_fornecedor', label: 'Forn.', sortable: true},
                    {key: 'dat_cadastro', label: 'Data Cad.', sortable: true},
                    {key: 'dat_ultcompra', label: 'Data UltCompra', sortable: true},
                    {key: 'estoque_history', label: 'EstoqHist'},
                    {key: 'estoque_history.data_movto', label: 'DatEstoqFim'},
                    {key: 'cod_referencia', label: 'Ref.', sortable: true},
                    {key: 'des_cor', label: 'Cor', sortable: true},
                    {key: 'img', label: 'Img.'},
                    {key: 'img_link', label: 'Img Link'},
                    {key: 'des_produto', label: 'Descrição.', sortable: true},
                    {key: 'actions', label: '+'}
                ]
            },
            valoresFields() {
                return [
                    // {key: 'totais', label: 'Tot.', sortable: true},
                    {key: 'vlr_custo_bruto', label: 'Custo', sortable: true},
                    {key: 'vlr_venda1', label: 'Vlr. Venda', sortable: true}
                ]
            },
            totaisFields() {
                return [
                    {key: 'totais', label: 'Tot.', sortable: true},
                    {key: 'saidas', label: 'Saídas.', sortable: true}
                ]
            },
            filteredOptions() {
                return [
                    {
                        // data: this.marcas
                        data: this.suggestions[0].data
                            .filter(option => {
                                // return 'a'
                                return option.nom_marca.toLowerCase().indexOf(this.marcas_suggestion_query.toLowerCase()) > -1;
                            })
                            .map(filtered_items => {
                                const mapped_items = filtered_items;
                                return mapped_items;
                            })
                    }
                ];
            }

            // gradeTotals() {
            //     let sum = this.filteredItemsComputed.reduce(function (sum, item) {
            //     let itemValor = parseFloat(item.grade_estoque[0])
            //     if (!isNaN(itemValor)) {
            //         return sum + itemValor
            //     } else {
            //         return sum
            //     }
            // }, 0)
            // return sum
            // }
        },

        beforeMount() {
            this.loadMarcas()
            // this.grade_estoque_totais= {'33':0}
            // this.updateEstoqueProdutos()
        },
        methods: {
            filteredItemsByDescription:function(items){
                console.log(items)
                // return items.filter(item => !item.des_produto.toLowerCase().indexOf(this.filters.des_produto))
                return this.items.filter(item => (item.des_produto||'').toLowerCase().includes(this.filters.des_produto.toLowerCase()))},
                // return items.filter(item => !item.des_produto.toLowerCase().includes(this.filters.des_produto))
            //    TODO
            //    des_cor in FERRACINI = null sometimes, find a way to bypass
            //    chaining filters like below might work
            //    https://5balloons.info/combining-multiple-filters-on-list-using-computed-properties-in-vuejs/
            filteredItemsByCor:function(items){
                console.log(items)
                return this.items.filter(item => (item.des_cor||'').toLowerCase().includes(this.filters.des_cor.toLowerCase()))},

            // const filtered = this.items.filter(item => {
            //     // const filtered = this.mappedItemsComputed.filter(item => {
            //     //     console.log(filtered)
            //         return Object.keys(this.filters).every(key =>{
            //             String(item[key].toString().toLowerCase()).includes(this.filters[key].toString().toLowerCase())
            //         }
            //         )
            //     })




            receiveDataMovtoIni(value) {
                this.data_movto_ini = value
            },
            receiveDataMovtoFim(value) {
                this.data_movto_fim = value
            },
            loadMarcas() {
                const path = `/api/read/marcas/`;
                // const path = `http://localhost/api/read/marcas/`; //this way works
                axios.get(path)
                    .then((res) => {
                        // console.log('res_marcas');
                        // console.log(res);
                        // this.marcas = res.data
                        this.suggestions[0].data = res.data
                        Object.freeze(this.suggestions)
                    })
                    .catch((error) => {
                        console.log(error)
                        console.log(error.response.data); // => the response payload
                    })
            },
            clickHandler(item) {
                console.log(item)
                // event fired when clicking on the input
            },
            onSelected(item) {
                this.suggestion_selected = item.item;
                // this.form_selected = this.availableFornecedores
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
            estoqueHistoryBoundDates(object) {
                var date_array = Object.keys(object)
                var date_diff_min = 0;
                var date_diff_max = 0;
                var estoque_history_bound_dates = {
                    'data_ini': this.default_date,
                    'data_fim': this.default_date
                }

                if (this.data_movto_ini < this.data_movto_fim) {
                    for (let i = 0; i < date_array.length; i++) {
                        date_diff_min = new Date(date_array[i]) - this.data_movto_ini;
                        if (date_diff_min > 0) {
                            if (i > 0) {
                                estoque_history_bound_dates.data_ini = date_array[i - 1]
                            }
                            break
                        }
                    }

                    for (let i = date_array.length; i > 0; i--) {
                        date_diff_max = new Date(date_array[i]) - this.data_movto_fim;
                        if (date_diff_max < 0) {
                            estoque_history_bound_dates.data_fim = date_array[i];
                            break
                        }
                    }
                }

                return estoque_history_bound_dates
            },
            gradeTotals(object) {
                let totais_E = Object.keys(object).reduce(function (sum, key) {
                    return sum + (key.slice(-1) == 'E' && object[key]);
                }, 0);

                let totais = Object.keys(object).reduce(function (sum, key) {
                    return sum + (key.slice(-1) !== 'E' && object[key]);
                }, 0);
                return {'totais_E':totais_E, 'totais': totais}
            },
            gradeEstoque(object) {
                // console.log(object)
                var grade_estoque = Object.values(object)
                // console.log("grade_estoque")
                // console.log(grade_estoque)
                // console.log("grade_estoque[grade_estoque.lenght - 1]")
                // console.log(grade_estoque[grade_estoque.lenght - 1])
                return grade_estoque[grade_estoque.lenght - 1]

            },
    normalizeString(s) {
      return `${s}`.trim().toLowerCase();
    },
    filterFn(row) {
      return this.filter.split(',')
        .map(this.normalizeString)
        .some(
          term => Object.values(row)
            .map(this.normalizeString)
            .some(
              val => val.indexOf(term) > -1
            )
        );
    },
            expandAdditionalInfo(row) {
                row._showDetails = !row._showDetails;
            },
            readProdutosFromMongo() {
                const path = `/api/estoque/read_produtos_from_mongo_db_test/${this.suggestion_selected.cod_marca}`
                // const path = `/api/estoque/read_produtos_from_mongo_db/${this.cod_marca}`
                console.log(path)
                axios.get(path)
                    .then((produtos) => {
                        console.log("produtos")
                        console.log(produtos)
                        this.items = produtos.data
                        Object.freeze(this.items)
                        // console.log("this.items")
                        // console.log(this.items)
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            readProdutosFromMongoWithFilter() {
                // const path = `/api/estoque/read_produtos_from_mongo_db_filter/${this.suggestion_selected.cod_marca}/${this.filters.des_produto}`
                // this.data_movto_ini = '2000-01-01 01:01:01.000000'
                // this.data_movto_fim = '2020-01-01 01:01:01.000000'
                const path = `/api/estoque/read_produtos_from_mongo_db_beanie/${this.suggestion_selected.cod_marca}/${this.data_movto_ini}/${this.data_movto_fim}`
                // const path = `/api/estoque/read_produtos_from_mongo_db/${this.cod_marca}`
                console.log(path)
                axios.get(path)
                    .then((produtos) => {
                        console.log("produtos")
                        console.log(produtos)
                        this.items = produtos.data
                        Object.freeze(this.items)
                        // console.log("this.items")
                        // console.log(this.items)
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            updateEstoqueProdutos() {
                // this.data_movto_ini = '2000-01-01T11%3A18%3A26.989000'
                this.data_movto_ini = '2000-01-01 01:01:01.000000'
                // this.data_movto_ini = moment(new Date).format('YYYY-MM-DDTHH:mm:ss.SSSSSS')
                this.cod_marca = '567'

                const path = `/api/estoque/read_produtos_from_postgres_db/${this.cod_marca}/${this.data_movto_ini}`
                axios.get(path)
                    .then((produtos_da_marca) => {
                        console.log("produtos_da_marca")
                        console.log(produtos_da_marca)
                        // this.items = produtos_da_marca.data
                        // console.log("this.items")
                        // console.log(this.items)
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            dateSorter(a, b, key) {

                if (key === 'dat_ultcompra' || key === 'dat_cadastro'|| key === 'data_movto') {
                    if (moment(a[key], 'DD/MM/YYYY').toDate() > moment(b[key], 'DD/MM/YYYY').toDate()) return 1;
                    if (moment(a[key], 'DD/MM/YYYY').toDate() < moment(b[key], 'DD/MM/YYYY').toDate()) return -1;
                    return 0;
                } else {
                    return false       // If field is not `date` we let b-table handle the sorting
                }
            },
        },
        watch: {
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