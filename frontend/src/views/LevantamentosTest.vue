<template>
    <div class="levantamentos">
        <h1>Levantamentos</h1>
        <b-form @submit.stop.prevent="onSubmit">
            <b-row>
                <b-col sm="2">
                    <b-row>
                        <div class="autosuggest">
                            <b>Marca: </b>
                            <vue-autosuggest
                                    :get-suggestion-value="getSuggestionValue"
                                    :input-props="{id:'autosuggest__input', placeholder:'Digite a marca', class:'form-control'}"
                                    :suggestions="filteredOptions" @click="clickHandler" @focus="focusMe"
                                    @input="onInputChange"
                                    @selected="onSelected"
                                    v-model="query">
                                <div class="autosuggest-container-results" slot-scope="{suggestion}"
                                     style=" align-items: center;">
                                    <div> {{suggestion.item.nom_marca}} ({{suggestion.item.cod_marca}})</div>
                                </div>
                            </vue-autosuggest>
                        </div>
                    </b-row>
                    <b-row>
                        <div>
                            <b-form @submit.stop.prevent="pesquisarImagens">
                                <b-button type="submit" variant="primary">Pesquisar Imagens</b-button>
                            </b-form>
                            <b-form @submit.stop.prevent="carregarImagens">
                                <b-button type="submit" variant="primary">Carregar Imagens</b-button>
                            </b-form>
                            <b-form @submit.stop.prevent="saveProdutos">
                                <b-button type="submit" variant="primary">Salvar Produtos</b-button>
                            </b-form>
                        </div>

                        <b-form-checkbox name="check-button" switch v-model="showHideImgLink">
                            Link Imagens <b></b>
                        </b-form-checkbox>

                    </b-row>
                </b-col>
                <b-col sm="2">
                    <b-row>
                        <label for="datepicker-data-ini">Data Cadastr inicial: </label>
                        <mydatepicker-ini :datepicker_default="datepicker_ini" @childToParent="receiveDataCadastroIni"
                                          id="datepicker-data-ini"/>
                        <br><br>
                    </b-row>
                    <b-row>
                        <label for="datepicker-data-fim">Data Cadastro final: </label>
                        <mydatepicker-fim :datepicker_default="datepicker_fim" @childToParent="receiveDataCadastroFim"
                                          id="datepicker-data-fim"/>
                        <br><br>

                    </b-row>
                </b-col>

                <b-col sm="2">
                    <b-row>
                        <b-button type="submit" variant="primary">Enviar</b-button>
                    </b-row>
                    <b-row>
                        <br>
                        <!--np-->
                    </b-row>

                    <b-row>
                        <b-form-group>
                            <b-input-group size="sm">
                                <b-form-input
                                        id="filter-input"
                                        placeholder="Filtrar por.."
                                        type="search"
                                        v-model="filter"
                                ></b-form-input>

                                <b-input-group-append>
                                    <b-button :disabled="!filter" @click="filter = ''">Limpar</b-button>
                                </b-input-group-append>
                            </b-input-group>
                        </b-form-group>
                    </b-row>

                </b-col>

                <b-col sm="4">
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
                </b-col>

            </b-row>

            <b-row>
            </b-row>

        </b-form>


        <b-table :bordered="true" :fields="computedFields" :filter="filter" :items="filteredmappedItemsComputed" :small=true
                 :sort-compare="dateSorter" class="text-right" head-variant="light" hover sticky-header="700px" striped
                 @row-clicked="expandAdditionalInfo" >

<template v-slot:cell(actions)="{ detailsShowing, item }" >
        <!-- Use the built in method from the scoped data to toggle the row details -->
        <b-btn @click="toggleDetails(item)">{{ detailsShowing ? '-' : '+'}}</b-btn>

      </template>
      <template v-slot:row-details="{ item }">
<!--          {{item.movtos}}-->
          <b-table :sort-compare="dateSorter" :sort-by="'data_movto'" :sort-asc=true :fields="[{key:'data_movto', sortable: true},'tipo_movto','qtd_movto',...gradeFields]" :items="item.movtos">
          </b-table>

      </template>

            <template scope="data" slot="top-row"><!-- eslint-disable-line-->
                <td :key="field.key" v-for="field in [...baseFields,...gradeFields,...valoresFields]">
                    <template
                            v-if="field.key==='nom_marca'||field.key==='dat_cadastro'||field.key==='dat_ultcompra'||field.key==='cod_referencia'||field.key==='des_cor'||field.key==='des_produto'||field.key==='vlr_custo_bruto'||field.key==='vlr_venda1'">
                        <b-form-input :placeholder="field.label" class="col-sm"
                                      v-model="filters[field.key]"></b-form-input>
                    </template>
                    <template v-else>

                        {{gradeTotals[field.key+"_E"]}}
                        <br><!-- eslint-disable-line-->
                        <b>{{gradeTotals[field.key]}}</b>

                    </template>
                </td>
            </template>




      <template #head(selected)="row"><!-- eslint-disable-line-->
        <b-form-checkbox
                                    :indeterminate="form_indeterminate"
                                    @change="form_toggleAll"
                                    v-model="form_allSelected">
                            </b-form-checkbox>
      </template>


            <template #cell(selected)="row">  <!-- eslint-disable-line-->

                <input type="checkbox" @change="formAnySelected"
                       v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected"/>
            </template>

            <template #cell(img)="data">  <!-- eslint-disable-line-->
                <img @click="increaseImageIndex(data.item.cod_referencia, data.item.des_cor)" :src="data.value" v-bind="imageProps"/>
            </template>

            <template v-slot:head(img_link)="row">
                <div v-show="showHideImgLink">{{ row.label }}</div>
            </template>

            <template #cell(img_link)="row">
                <div v-show="showHideImgLink">
                    <b-form-input v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].img[0]"/>
                    <b-form-file placeholder="Nenhum arquivo" accept="image/*" @change="previewImage($event, row.item.cod_referencia, row.item.des_cor)" ref="file-input"></b-form-file>
<!--                    <input type="file" @change="previewImage($event, row.item.cod_referencia, row.item.des_cor)" accept="image/*">-->
<!--                    <img class="preview" :src="imageData">-->
                </div>
            </template>



            <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item }">
                <!-- eslint-disable-line-->
                {{item[field.key+"_E"]}}
                <br><!-- eslint-disable-line-->
                <b> {{item[field.key]}} </b><!-- eslint-disable-line-->
            </template>

        </b-table>

    </div>
</template>

<script>
    import Mydatepicker from '../components/Mydatepicker'
    import axios from "axios"
    import {VueAutosuggest} from 'vue-autosuggest'
    import moment from "moment";

    export default {
        name: "LevantamentosTest",
        components: {
            'mydatepicker-ini': Mydatepicker,
            'mydatepicker-fim': Mydatepicker,
            'vue-autosuggest': VueAutosuggest
        },
        data() {
            return {
                // imageData: null,
                // file: null,
                showHideImgLink: false,
                form_selected_: [],
                image_index: 0,
                produtos_selected: [],
                fields_selected: [],
                grades_selected: [],
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
                        "grade": [{key: '17', label: '17'},
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
                        "name": 'Meias',
                        "grade":[ {key: '33/38', label: '33/38'},
                         {key: '39/44', label: '39/44'}]
                    },
                    {
                        "name": 'Outros',
                        "grade": {key: 'un', label: 'un'}
                    },
                ],
                graded_prods_entrada: '',
                graded_prods_estoq: '',
                array: [],
                filter: null,
                google_search_array: [],
                produtos: [],
                ref_cor_marca: [],
                refs_array: '',
                mapped_items: [],
                form_selected: [],
                form_allSelected: false,
                form_indeterminate: false,
                grouped_items_byref_map: [],
                subgrouped_items_bycolor_obj: {},
                query: "",
                imageProps: {blank: true, width: 75, height: 75, class: 'm1'},
                imagem_test: 'https://www.katy.com.br/cdn/imagens/produtos/original/indoor-nike-beco-2-a451f3b4e2327ab6c8dc817bbc0250a3.jpg',
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
                filters: {nom_marca: '', dat_cadastro: '', des_cor: '', des_produto: ''},
                currentItems: []
            }
        },
        computed: {
            filteredmappedItemsComputed() {
                const filtered = this.mappedItemsComputed.filter(item => {
                    return Object.keys(this.filters).every(key =>
                        String(item[key].toString().toLowerCase()).includes(this.filters[key].toString().toLowerCase()))
                });

                return filtered
            },
            gradeTotals() {
                const grade_totals = {}
                if (this.filteredmappedItemsComputed.length > 0) {
                    for (const item in this.filteredmappedItemsComputed) {
                        for (const numero_da_grade in this.filteredmappedItemsComputed[item]) {
                            if (numero_da_grade === 'nom_marca') {
                                break; //break loop when finds anything different from "numeros de grade"
                            }
                            if (isNaN(grade_totals[numero_da_grade])) {
                                    grade_totals[numero_da_grade]= this.filteredmappedItemsComputed[item][numero_da_grade]
                                }
                            else {
                                grade_totals[numero_da_grade]= grade_totals[numero_da_grade] + this.filteredmappedItemsComputed[item][numero_da_grade]
                            }
                        }
                    }
                }
                let grade_totals_split = {}
                let grade_totals_split_E = {}
                let grade_totals_keys_E = Object.keys(grade_totals).filter((key) => key.includes('E'))
                let grade_totals_keys = Object.keys(grade_totals).filter((key) => !key.includes('E'))

                for (const key in grade_totals_keys) {
                    grade_totals_split_E[grade_totals_keys_E[key]]=grade_totals[grade_totals_keys_E[key]]
                    grade_totals_split[grade_totals_keys[key]]=grade_totals[grade_totals_keys[key]]
                }

                grade_totals["totais"] = Object.values(grade_totals_split).reduce((a, b) => a + b, 0)
                grade_totals["totais_E"]  = Object.values(grade_totals_split_E).reduce((a, b) => a + b, 0)

                return grade_totals
            },
            mappedItemsComputed() {
                let mapped_items = [];

                for (const ref_group in this.subgrouped_items_bycolor_obj) {
                    for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
                        let saldo_estoq_entrada = 0;
                        let saldo_estoq = 0;
                        let graded_prods_estoq = {};
                        let movtos = [];

                        for (const prod in this.subgrouped_items_bycolor_obj[ref_group][cor]) {
                            let estoq_entrada = 0;
                            let estoq_entrada_name = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString() + "_E";

                            if (isNaN(graded_prods_estoq[estoq_entrada_name])) {
                                    graded_prods_estoq[estoq_entrada_name] = 0
                                }

                            if (
                                // (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 7) || (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 3)) {
                                (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 7) || (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 3)|| (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 9)) {

                                    if  (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto === 'E') {
                                        estoq_entrada = estoq_entrada + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
                                        let entrada = {};
                                        entrada[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString()] ={};
                                        entrada['data_movto']= this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto;
                                        entrada[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString()]= this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
                                        movtos.push(entrada)

                                    } else if (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto === 'S') {
                                        // estoq_entrada = estoq_entrada - this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
                                        let saida = {};
                                        saida[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString()] ={};
                                        saida['data_movto']= this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto;
                                        saida[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString()]=0-this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
                                        movtos.push(saida)
                                    }

                                graded_prods_estoq[estoq_entrada_name] = graded_prods_estoq[estoq_entrada_name] + estoq_entrada;
                                saldo_estoq_entrada = saldo_estoq_entrada + estoq_entrada;

                            }
                            //calculating saldo_estoq summing saldo.estoque only once per item
                            if (isNaN(graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho])) {
                                saldo_estoq = saldo_estoq + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque
                            }
                            graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho] = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque
                        }

                           let reduced_movtos = Object.values(movtos.reduce((r, {data_movto, ...rest}) => {
                                r[data_movto] = r[data_movto] || {data_movto};
                                r[data_movto] = {...r[data_movto], ...rest};
                                return r;
                            }, {}));
                        console.log("reduced_movtos");
                        console.log(reduced_movtos);
                        console.log("movtos")
                        console.log(movtos)

                        graded_prods_estoq['nom_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca;
                        graded_prods_estoq['dat_cadastro'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_cadastro;
                        graded_prods_estoq['dat_ultcompra'] = this.subgrouped_items_bycolor_obj[ref_group][cor][this.subgrouped_items_bycolor_obj[ref_group][cor].length - 1].dat_ultcompra;
                        // graded_prods_estoq['dat_alteracao'] = this.subgrouped_items_bycolor_obj[ref_group][cor][this.subgrouped_items_bycolor_obj[ref_group][cor].length - 1].dat_alteracao;
                        graded_prods_estoq['cod_referencia'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia;
                        graded_prods_estoq['des_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor
                        graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_tamanho, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca, '');
                        graded_prods_estoq['img'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].img[this.subgrouped_items_bycolor_obj[ref_group][cor][0].image_index];
                        graded_prods_estoq['selected'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].selected;
                        graded_prods_estoq['totais_E'] = saldo_estoq_entrada;
                        graded_prods_estoq['totais'] = saldo_estoq;
                        graded_prods_estoq['vlr_custo_bruto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_bruto;
                        graded_prods_estoq['vlr_venda1'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_venda1;

                        graded_prods_estoq['des_grupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_grupo;
                        graded_prods_estoq['cod_grupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_grupo;
                        graded_prods_estoq['cod_subgrupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_subgrupo;
                        graded_prods_estoq['des_subgrupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_subgrupo;
                        graded_prods_estoq['cod_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_produto;
                        graded_prods_estoq['vlr_custo_aquis'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_aquis;
                        graded_prods_estoq['cod_grade'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_grade;
                        graded_prods_estoq['des_grade'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_grade;
                        graded_prods_estoq['cod_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_cor;
                        // graded_prods_estoq['dat_emissao'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_emissao;
                        // graded_prods_estoq['dat_lancamento'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_lancamento;
                        graded_prods_estoq['cod_fornecedor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_fornecedor;
                        graded_prods_estoq['raz_fornecedor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].raz_fornecedor;
                        graded_prods_estoq['fan_fornecedor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].fan_fornecedor;
                        graded_prods_estoq['cod_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_marca;
                        graded_prods_estoq['image_index'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].image_index;
                        graded_prods_estoq['image_index'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].image_index;
                        graded_prods_estoq['image_index'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].image_index;
                        // graded_prods_estoq['ult_entrada'] = ult_entrada;
                        graded_prods_estoq['movtos'] =reduced_movtos;

                        mapped_items.push(graded_prods_estoq);
                    }
                }
                return mapped_items
            },
            todosProdutos() {
                var produtos = this.mappedItemsComputed.map(produto => {
                    if (!produto.cod_referencia) {produto.cod_referencia = 'default'}
                    if (!produto.des_cor) {produto.des_cor = ''}
                    if (!produto.cod_cor) {produto.cod_cor = 0}
                    if (!produto.nom_marca) {produto.nom_marca = ''}
                    if (!produto.des_produto) {produto.des_produto = ''}
                    if (!produto.cod_grupo) {produto.cod_grupo = 0}
                    if (!produto.des_grupo) {produto.des_grupo = ''}
                    if (!produto.cod_subgrupo) {produto.cod_subgrupo = 0}
                    if (!produto.des_subgrupo) {produto.des_subgrupo = ''}
                    if (!produto.cod_produto) {produto.cod_produto = 0}
                    if (!produto.vlr_custo_bruto) {produto.vlr_custo_bruto = 0.0}
                    if (!produto.vlr_custo_aquis) {produto.vlr_custo_aquis = 0.0}
                    if (!produto.vlr_venda1) {produto.vlr_venda1 = 0.0}
                    if (!produto.cod_grade) {produto.cod_grade = 0}
                    if (!produto.des_grade) {produto.des_grade = ''}
                    // if (!produto.dat_cadastro) {produto.dat_cadastro = ''}
                    // if (isNaN(produto.dat_ultcompra)) {produto.dat_ultcompra = '01/01/1900'}
                    if (!moment(produto.dat_cadastro, "DD/MM/YYYY", false).isValid())
                        {produto.dat_cadastro = '01/01/1900'}
                    if (!moment(produto.dat_ultcompra, "DD/MM/YYYY", false).isValid())
                        {produto.dat_ultcompra = '01/01/1900'}
                    if (!produto.cod_fornecedor) {produto.cod_fornecedor = 0}
                    if (!produto.raz_fornecedor) {produto.raz_fornecedor = ''}
                    if (!produto.fan_fornecedor) {produto.fan_fornecedor = ''}
                    return {
                        cod_grupo: produto.cod_grupo,
                        des_grupo: produto.des_grupo,
                        cod_subgrupo: produto.cod_subgrupo,
                        des_subgrupo: produto.des_subgrupo,
                        cod_produto: produto.cod_grupo,
                        des_produto: produto.des_produto,
                        vlr_custo_bruto: produto.vlr_custo_bruto,
                        vlr_custo_aquis: produto.vlr_custo_aquis,
                        vlr_venda1: produto.vlr_venda1,
                        cod_grade: produto.cod_grade,
                        des_grade: produto.des_grade,
                        cod_cor: produto.cod_cor,
                        dat_cadastro: moment(produto.dat_cadastro, 'DD/MM/YYYY', true).format('YYYY-MM-DDTHH:mm:ss.SSSSSS'),
                        dat_ultcompra: moment(produto.dat_ultcompra, 'DD/MM/YYYY', true).format('YYYY-MM-DDTHH:mm:ss.SSSSSS'),
                        // dat_lancamento: moment(produto.dat_lancamento, 'DD/MM/YYYY', true).format('YYYY-MM-DDTHH:mm:ss.SSSSSS'),
                        cod_fornecedor: produto.cod_fornecedor,
                        raz_fornecedor: produto.raz_fornecedor,
                        fan_fornecedor: produto.fan_fornecedor,
                        cod_marca: produto.cod_marca,
                        cod_referencia: produto.cod_referencia,
                        nom_marca: produto.nom_marca,
                        des_cor: produto.des_cor,
                        img: produto.img,
                        selected: produto.selected,
                        image_index: produto.image_index
                    }
                })
                return produtos
            },
            produtosSelecionados() {
                var selected_rows = this.todosProdutos.filter(row => row.selected == true)
                return selected_rows
            },
            computedFields() {
                // return [].concat(this.baseFields, this.adultoFields, this.valoresFields)
                return [].concat(this.baseFields, this.gradeFields, this.valoresFields)
            },
            gradeFields() {
                var grades = this.grades_selected.map(selected => {
                    return selected.grade
                })

                return [].concat(grades.flat(1), this.totaisFields) //manter totaisFields aqui para que os totais fiquem corretos
                // return [].concat(this.infantoFields, this.adultoFields, this.totaisFields)
            },
            baseFields() {
                return [
                    {key: 'selected', label: 'Sel.'},
                    {key: 'nom_marca', label: 'Nom. Marca', sortable: true},
                    {key: 'dat_cadastro', label: 'Data Cad.', sortable: true},
                    {key: 'dat_ultcompra', label: 'Data Alt.', sortable: true},
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
                    {key: 'totais', label: 'Tot.', sortable: true}
                ]
            },
            filteredOptions() {
                return [
                    {
                        data: this.suggestions[0].data
                            .filter(option => {
                                return option.nom_marca.toLowerCase().indexOf(this.query.toLowerCase()) > -1;
                            })
                            .map(filtered_items => {
                                const mapped_items = filtered_items;
                                return mapped_items;
                            })
                    }
                ];
            },
            availableFornecedores() {
                return this.suggestion_selected.fornecedores
                    .filter(item => item)
                    .map(item => item.fan_fornecedor)
            },
            computedItems() {
                return this.items
                    .filter(item => item)
                    .map(item => item)
            }
        },
        beforeMount() {
            this.loadMarcas()
        },
        // watch: {
        //     selected(newValue) {
        //         // Handle changes in individual flavour checkboxes
        //         if (newValue.length === 0) {
        //             this.indeterminate = false
        //             this.allSelected = false
        //         } else if (newValue.length === this.flavours.length) {
        //             this.indeterminate = false
        //             this.allSelected = true
        //         } else {
        //             this.indeterminate = true
        //             this.allSelected = false
        //         }
        //     }
        // },
        methods: {
            expandAdditionalInfo(row) {
                console.log("expand row")
      row._showDetails = !row._showDetails;
    },
            toggleDetails(row) {
        if(row._showDetails){
          this.$set(row, '_showDetails', false)
        }else{
          this.currentItems.forEach(item => {
            this.$set(item, '_showDetails', false)
          })

          this.$nextTick(() => {
            this.$set(row, '_showDetails', true)
          })
        }
      },
            toggleAll(checked) {
        this.selected = checked ? this.flavours.slice() : []
      },
            increaseImageIndex(cod_referencia, des_cor) {
                // console.log('this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index')
                // console.log(this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index)
                this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index = (this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index + 1) % this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].img.length;
                // console.log('this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index')
                // console.log(this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index)
                // this.index = (this.index + 1) % this.images.length;
            },
            clearGradesSelected() {
                console.log("this.grades_selected")
                console.log(this.grades_selected)
                // this.grades_selected = [];
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
            objectify(element) {
                var result =
                    {
                        cod_grupo: element[0],
                        des_grupo: element[1],
                        cod_subgrupo: element[2],
                        des_subgrupo: element[3],
                        cod_produto: element[4],
                        des_produto: element[5],
                        cod_barra: element[6],
                        cod_referencia: element[7],
                        qtd: element[8],
                        saldo_estoque: element[9],
                        vlr_custo_bruto: element[10],
                        vlr_custo_aquis: element[11],
                        vlr_venda1: element[12],
                        total: element[13],
                        cod_grade: element[14],
                        des_grade: element[15],
                        cod_tamanho: element[16],
                        //todo
                        des_tamanho: element[17] || 'un',
                        cod_cor: element[18],
                        des_cor: element[19],
                        // dat_cadastro: element[20],
                        // dat_cadastro: moment(element[20]),
                        dat_cadastro: moment(element[20]).format('DD/MM/YYYY'),
                        dat_ultcompra: moment(element[21]).format('DD/MM/YYYY'),
                        // dat_emissao: moment(element[22]).format('DD/MM/YYYY'),
                        // dat_lancamento: moment(element[23]).format('DD/MM/YYYY'),
                        // dat_saida: moment(element[22]).format('DD/MM/YYYY'),
                        cod_fornecedor: element[22],
                        raz_fornecedor: element[23],
                        fan_fornecedor: element[24],
                        cod_marca: element[25],
                        nom_marca: element[26],
                        tipo_movto: element[27],
                        qtd_movto: element[28],
                        data_movto: moment(element[29]).format('DD/MM/YYYY'),
                        cod_movto: element[30],
                        cod_origem_movto: element[31],
                        selected: false,
                        image_index: 0,
                        // img: ['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=']
                        img: ['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=', 'https://lojaferracini.vteximg.com.br/arquivos/ids/265063-800-800/Pro_0000022240415-0001.jpg?v=637406341029930000']
                    };
                return result
            },
            onSubmit() {
                // const path = `http://localhost/api/levantamentos/${this.data_cadastro_ini}/${this.data_cadastro_fim}/${this.suggestion_selected.cod_marca}/`;
                const path = `/api/levantamentos/${this.data_cadastro_ini}/${this.data_cadastro_fim}/${this.suggestion_selected.cod_marca}/`;
                axios.get(path)
                    .then((res) => {
                        console.log(res);
                        this.items = [];
                        res.data.forEach(item => this.items.push(this.objectify(item)));
                        this.groupItemsByRef()
                        this.subgroupItemsByColor()
                        // this.gradearProdutosOld()
                        // faz grade dos produtos (de acordo com entradas e saídas no estoque) por numeração
                        this.mapped_items = []
                        // this.gradearProdutos()
                        // this.carregarImagens()
                        // this.saveProdutos()

                        // const produtos_com_imagens = this.carregarImagens()
                        // this.saveProdutos(produtos_com_imagens)

                        // 2021-09-07 trying to merger 2 rows in one
                        // maybe this is the way https://stackoverflow.com/questions/67868703/how-to-use-rowspan-in-bootstrap-vue-b-table
                        // i think I should put the initial estoque and actual estoque in the same item  row
                    })
                    .catch((error) => {
                        console.log(error)
                        console.log(error.response.data); // => the response payload
                    })
            },
            groupItemsByRef() {
                this.grouped_items_byref_map = this.items.reduce(
                    (entryMap, e) => entryMap.set(e.cod_referencia, [...entryMap.get(e.cod_referencia) || [], e]),
                    new Map()
                );
                this.refs_array = Object.fromEntries(this.grouped_items_byref_map);
            },
            subgroupItemsByColor() {
                this.subgrouped_items_bycolor_obj = {};
                // this.produtos = [];
                for (const ref_group in this.refs_array) {

                    //MELHORAR ESSE LOOP
                    for (const item in this.refs_array[ref_group]) {
                        // console.log('item')
                        // console.log(item)
                        if (!this.refs_array[ref_group][item].des_cor)
                            this.refs_array[ref_group][item].des_cor = 'padrao'
                    }

                    let subgrouped_by_color_map = this.refs_array[ref_group].reduce(
                        (entryMap, e) =>
                            entryMap.set(e.des_cor, [...entryMap.get(e.des_cor) || [], e]),
                        new Map()
                    );
                    this.subgrouped_items_bycolor_obj[ref_group] = Object.fromEntries(subgrouped_by_color_map)

                    // this.produtos.push({nom_marca:this.refs_array[ref_group][0]['nom_marca'], cod_referencia:ref_group, des_cor:Object.keys(this.subgrouped_items_bycolor_obj[ref_group])})
                }

            },
            carregarImagens() {

                console.log('this.todosProdutos')
                console.log(this.todosProdutos)
                const path = `/api/produtos/images/`;
                // axios.put(path, this.produtosSelecionados)
                axios.put(path, this.todosProdutos)
                    // axios.put(path, this.produtos)
                    .then((res) => {
                        console.log('res.data carregar imagens');
                        console.log(res.data);
                        for (const key in res.data) {
                            console.log('res.data')
                            console.log(res.data)

                            console.log('res.data[key].img')
                            console.log(res.data[key].img)
                            console.log('this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img')
                            console.log(this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img)

                            this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img[this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].image_index] = res.data[key].img
                            //these next 3 lines make the images auto refresh
                            // const aux = this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].image_index
                            // this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].image_index = 1
                            // this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].image_index = aux
                        }

                    })
                    .catch((error) => {
                        console.log(error)
                        console.log(error.response.data); // => the response payload
                    })
            },
            async pesquisarImagens() {
                // const produtos = []
                // for (const key in this.mapped_items) {
                for (const key in this.produtosSelecionados) {
                    const marca = this.produtosSelecionados[key]['nom_marca']
                    const cor = this.produtosSelecionados[key]['des_cor']
                    const ref_group = this.produtosSelecionados[key]['cod_referencia']
                    const descricao = this.produtosSelecionados[key]['des_produto']
                    console.log('key')
                    console.log(key)
                    // for (const key in this.produtos) {
                    let image_url = await this.fetchImage(marca, ref_group, cor, descricao)
                    // let image_url = await this.fetchImage(this.produtosSelecionados[key]['nom_marca'], this.produtosSelecionados[key]['cod_referencia'], this.produtosSelecionados[key]['des_cor'])
                    if (typeof image_url == 'undefined')
                        image_url = 'data:image/png;base64,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'

                    console.log('this.produtos_from_carregarImagens')

                    console.log('marca')
                    console.log(marca)
                    console.log('cor')
                    console.log(cor)
                    console.log('ref_group')
                    console.log(ref_group)

                    console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][0].img')
                    console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].img)
                    // this.subgrouped_items_bycolor_obj[ref_group][cor][0].img = image_url[0]
                    for (var i=0; i< 10; i++) {
                        this.subgrouped_items_bycolor_obj[ref_group][cor][0].img[i] = image_url[i]
                    }


                    console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][0].img')
                    console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].img)
                    this.image_index = 1 //these both lines are needed to auto refresh images
                    this.image_index = 0 //these both lines are needed to auto refresh images

                }
            },
            //maybe remove asyncs..

            async saveProdutos() {
                // const api_path = `/api/produtos/images/`
                console.log('this.produtosSelecionados')
                console.log(this.produtosSelecionados)
                const api_path = `/api/produtos/save`
                axios.put(api_path, this.produtosSelecionados)
                    .then((res) => {
                        console.log('axios.put')
                        console.log(res.data)
                    })
                    .catch((error) => {
                        console.log(error)
                        console.log(error.response.data); // => the response payload
                    })

            },
            async fetchImage(nom_marca, cod_referencia, des_cor, des_produto) {
                const base_path = `https://www.googleapis.com/customsearch/v1?key=AIzaSyAxkljtWwOvBkyVgaCgQQYR2bgFMUdzrQs&cx=f5c6bf2ce19682bb8&&searchType=image&&num=10&lr=lang_pt&q=`

                const query = des_produto + '+' + nom_marca + '+' + cod_referencia + '+' + des_cor

                const path = base_path + query
                var path_without_spaces = path.replace(/\s/g, '+');
                console.log('path_without_spaces')
                console.log(path_without_spaces)

                let image_url = axios.get(path_without_spaces)
                    .then((response) => {
                        console.log("response from fetchImage")
                        console.log(response)
                        return response.data.items.map((item) => {
                            // console.log('item.link')
                            // console.log(item.link)
                            // this.imagem_test = item.link
                            return item.link
                        });
                    })
                    .catch((error) => {
                        console.log(error)
                        console.log(error.response.data); // => the response payload
                    })
                console.log('image_url_from fetchimage')
                console.log(image_url)
                console.log('typeof image_url')
                console.log(typeof image_url)
                if (typeof image_url == 'undefined')
                    image_url = 'data:image/png;base64,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'
                //TESTING TO RETURN A DEFAULT IMAGE IF UNINDETIFIED
                return image_url

            },
            receiveDataCadastroIni(value) {
                this.data_cadastro_ini = value
            },
            receiveDataCadastroFim(value) {
                this.data_cadastro_fim = value
            },
            loadMarcas() {
                const path = `/api/read/marcas/`;
                // const path = `http://localhost/api/read/marcas/`; //this way works
                axios.get(path)
                    .then((res) => {
                        console.log('res');
                        console.log(res);
                        this.suggestions[0].data = res.data
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
            form_toggleAll() {

                    for (const ref_group in this.subgrouped_items_bycolor_obj) {
                        console.log("this.subgrouped_items_bycolor_obj[ref_group]")
                        console.log(this.subgrouped_items_bycolor_obj[ref_group])
                        for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
                            console.log("this.subgrouped_items_bycolor_obj[ref_group][cor]")
                            console.log(this.subgrouped_items_bycolor_obj[ref_group][cor])
                            this.subgrouped_items_bycolor_obj[ref_group][cor][0].selected = this.form_allSelected
                        }
                    }
            },
            formAnySelected(checked) {
                // this.form_selected = checked ? this.form_options.slice() : []
                // this.produtosSelecionados = checked ? this.form_options.slice() : []
                var selected_rows = this.todosProdutos.filter(row => row.selected == true)
                this.form_selected_ = selected_rows
                console.log("checked")
                console.log(checked)
                console.log("this.produtosSelecionados")
                console.log(this.produtosSelecionados)
            },
            previewImage(event, cod_referencia, des_cor) {
            // Reference to the DOM input element
            var input = event.target;
            // Ensure that you have a file before attempting to read it
            if (input.files && input.files[0]) {
                // create a new FileReader to read this image and convert to base64 format
                var reader = new FileReader();
                // Define a callback function to run, when FileReader finishes its job
                reader.onload = (e) => {
                    // Note: arrow function used here, so that "this.imageData" refers to the imageData of Vue component
                    // Read image as base64 and set to imageData
                    // this.imageData = e.target.result;

                    this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].img[0] = e.target.result;
                    //these next three lines make the image auto reload
                    let image_index_backup = this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index
                    this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index = image_index_backup + 1
                    this.subgrouped_items_bycolor_obj[cod_referencia][des_cor][0].image_index = image_index_backup
                }
                // Start the reader job - read file as a data url (base64 format)
                this.imageData = reader.readAsDataURL(input.files[0]);
            }
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