<template>
    <div class="levantamentos">
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

        <h1>Levantamentos</h1>
        <b-form @submit.stop.prevent="onSubmit">
            <b-row>
                <b-col>
                    <div class="autosuggest-container">
                        <b>Marca: </b>
                        <vue-autosuggest
                                :get-suggestion-value="getSuggestionValue"
                                :input-props="{id:'autosuggest__input', placeholder:'Digite a marca', class:'form-control'}"
                                :suggestions="filteredOptions" @click="clickHandler" @focus="focusMe"
                                @input="onInputChange"
                                @selected="onSelected"
                                v-model="query">
                            <div class="autosuggest-container-results" slot-scope="{suggestion}"
                                 style="display: flex; align-items: center;">
                                <div> {{suggestion.item.nom_marca}} ({{suggestion.item.cod_marca}})</div>
                            </div>
                        </vue-autosuggest>
                        <br>
                    </div>
                </b-col>

                <div checkbox fornecedors>
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
                                                        :options="
                                                        availableFornecedores"
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
                </div>

                <b-col>
                    <label for="datepicker-data-ini">Data Cadastroo inicial: </label>
                    <mydatepicker-ini :datepicker_default="datepicker_ini" @childToParent="receiveDataCadastroIni"
                                      id="datepicker-data-ini"/>
                    <br><br>
                    <label for="datepicker-data-fim">Data Cadastro final: </label>
                    <mydatepicker-fim :datepicker_default="datepicker_fim" @childToParent="receiveDataCadastroFim"
                                      id="datepicker-data-fim"/>
                    <br><br>
                    <b-button type="submit" variant="primary">Enviar</b-button>
                </b-col>
            </b-row>


        </b-form>
        <b-table :fields="computedFields" :items="mapped_items" :small=true class="text-right" hover striped>
            // eslint-disable-next-line vue/no-unused-vars
            <template #cell(img)="data">  <!-- eslint-disable-line-->
                <!--            <template slot="[img]" slot-scope="data">-->
                <!--                <img :src="this.produtos.img" v-bind="imageProps"/>-->
                <!--                <img :src=imagem_test v-bind="imageProps"/>-->
                <img :src="data.value" v-bind="imageProps"/>
            </template>

<!--            <template v-for="field in infantoFields" v-slot:[`cell(${field.key})`]="{ item }">&lt;!&ndash; eslint-disable-line&ndash;&gt;-->
<!--                {{item[field.key+"_E"]}}-->
<!--                {{item[field.key]}}-->
<!--            </template>-->

            <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item }"><!-- eslint-disable-line-->
                {{item[field.key+"_E"]}}
                <br><!-- eslint-disable-line-->
                {{item[field.key]}}
            </template>




        </b-table>

        <!--            <b-table :fields="fields" :items="filtered">-->
        <!--                <template v-for="field in editableFields" v-slot:[`cell(${field.key})`]="{ item }">-->
        <!--                    <b-input :key="field.key" v-model="item[field.key]"/>-->
        <!--                </template>-->
        <!--            </b-table>-->
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
                graded_prods_entrada: '',
                graded_prods_estoq: '',
                array: [],
                // test_new_items: [],
                google_search_array: [],
                produtos: [],
                ref_cor_marca: [],
                refs_array: '',
                mapped_items: [],
                form_selected: [],
                form_allSelected: true,
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
                // fields: [
                //     {key: 'nom_marca', label: 'Nom. Marca'},
                //     {key: 'dat_cadastro', label: 'Data Cad.'},
                //     {key: 'dat_alteracao', label: 'Data Alt.'},
                //     {key: 'cod_referencia', label: 'Ref.'},
                //     {key: 'des_produto', label: 'Descrição.'},
                //     // {key: 'qtd', label: 'Qtd.'},
                //     {key: 'saldo_estoque', label: 'Saldo Est.'},
                //     {key: 'vlr_venda1', label: 'Vlr. Venda'},
                //     {key: 'vlr_custo_bruto', label: 'Custo'},
                //     {key: 'cod_grade', label: 'cod grade'},
                //     {key: 'des_grade', label: 'des_grade'},
                //     {key: 'cod_tamanho', label: 'cod_tamanho'},
                //     {key: 'des_tamanho', label: 'des_tamanho'}
                // ]
                fields: [
                    {key: 'nom_marca', label: 'Nom. Marca'},
                    {key: 'dat_cadastro', label: 'Data Cad.'},
                    {key: 'dat_alteracao', label: 'Data Alt.'},
                    {key: 'cod_referencia', label: 'Ref.'},
                    {key: 'des_cor', label: 'Cor'},
                    {key: 'img', label: 'Img.'},
                    {key: 'des_produto', label: 'Descrição.'},
                    // {key: 'qtd', label: 'Qtd.'},
                    // {key: 'PP', label: 'PP'},
                    {key: 'EP', label: 'EP'},
                    {key: 'P', label: 'P'},
                    {key: 'M', label: 'M'},
                    {key: 'G', label: 'G'},
                    {key: 'GG', label: 'GG'},
                    // {key: 'EG', label: 'EG'},
                    // {key: 'EGG', label: 'EGG'},
                    // {key: 'G1', label: 'G1'},
                    // {key: 'G2', label: 'G2'},
                    // {key: 'G3', label: 'G3'},
                    // {key: 'G4', label: 'G4'},
                    // {key: '16', label: '16'},
                    // {key: '17', label: '17'},
                    // {key: '18', label: '18'},
                    // {key: '19', label: '19'},
                    // {key: '20', label: '20'},
                    // {key: '21', label: '21'},
                    // {key: '22', label: '22'},
                    // {key: '23', label: '23'},
                    // {key: '24', label: '24'},
                    // {key: '25', label: '25'},
                    // {key: '26', label: '26'},
                    // {key: '27', label: '27'},
                    {key: '28', label: '28'},
                    {key: '29', label: '29'},
                    {key: '30', label: '30'},
                    {key: '31', label: '31'},
                    {key: '32', label: '32'},
                    {key: '33', label: '33'},
                    {key: '34', label: '34'},
                    {key: '35', label: '35'},
                    {key: '36', label: '36'},
                    {key: '37', label: '37'},
                    {key: '38', label: '38'},
                    {key: '39', label: '39'},
                    {key: '40', label: '40'},
                    {key: '41', label: '41'},
                    {key: '41', label: '41'},
                    {key: '42', label: '42'},
                    {key: '43', label: '43'},
                    {key: '44', label: '44'},
                    {key: '45', label: '45'},
                    {key: '46', label: '46'},
                    {key: '47', label: '47'},
                    {key: '48', label: '48'},
                    {key: 'vlr_custo_bruto', label: 'Custo'},
                    {key: 'vlr_venda1', label: 'Vlr. Venda'}
                ]
            }
        },
        computed: {
            computedFields() {
                // return [].concat(this.baseFields, this.adultoFields, this.valoresFields)
                return [].concat(this.baseFields, this.gradeFields, this.valoresFields)
            },
            gradeFields(){
                // return [].concat(this.infantoFields_duplos, this.adultoFields_duplos)
                return [].concat(this.adultoFields)
                // return [].concat(this.infantoFields, this.adultoFields)
            },
            baseFields() {
                return [
                    {key: 'nom_marca', label: 'Nom. Marca'},
                    {key: 'dat_cadastro', label: 'Data Cad.'},
                    {key: 'dat_alteracao', label: 'Data Alt.'},
                    {key: 'cod_referencia', label: 'Ref.'},
                    {key: 'des_cor', label: 'Cor'},
                    {key: 'img', label: 'Img.'},
                    {key: 'des_produto', label: 'Descrição.'}
                ]
            },
            valoresFields() {
                return [
                    {key: 'vlr_custo_bruto', label: 'Custo'},
                    {key: 'vlr_venda1', label: 'Vlr. Venda'}
                ]
            },
            infantoFields() {
                return [
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
                    {key: '36', label: '36'}
                ]
            },
            adultoFields() {
                return [
                    {key: '33', label: '33'},
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
                    {key: '44', label: '44'},
                    {key: '45', label: '45'},
                    {key: '46', label: '46'},
                    {key: '47', label: '47'},
                    {key: '48', label: '48'},
                ]
            },
            infantoFields_duplos() {
                return [
                    {key: '17/18', label: '17/18'},
                    {key: '19/20', label: '19/20'},
                    {key: '21/22', label: '21/22'},
                    {key: '23/24', label: '23/24'},
                    {key: '25/26', label: '25/26'},
                    {key: '27/28', label: '27/28'},
                    {key: '29/30', label: '29/30'},
                    {key: '31/32', label: '31/32'},
                    {key: '33/34', label: '33/34'},
                    {key: '35/36', label: '35/36'}
                ]
            },
            adultoFields_duplos() {
                return [
                    {key: '33/34', label: '33/34'},
                    {key: '35/36', label: '35/36'},
                    {key: '37/38', label: '37/38'},
                    {key: '39/40', label: '39/40'},
                    {key: '41/42', label: '41/42'},
                    {key: '43/44', label: '43/44'},
                    {key: '45/46', label: '45/46'},
                    {key: '47/48', label: '47/48'}
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
            },
            computedImage() {
                return this.imagem_test
                // return this.fetchImage('nike', '646433', 'preto')

            }
        },
        beforeMount() {
            this.loadMarcas()
        },
        methods: {
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
                        des_tamanho: element[17],
                        cod_cor: element[18],
                        des_cor: element[19],
                        // dat_cadastro: element[20],
                        dat_cadastro: moment(element[20]).format('DD/MM/YYYY'),
                        dat_alteracao: moment(element[21]).format('DD/MM/YYYY'),
                        dat_emissao: moment(element[22]).format('DD/MM/YYYY'),
                        dat_lancamento: moment(element[23]).format('DD/MM/YYYY'),
                        dat_saida: moment(element[24]).format('DD/MM/YYYY'),
                        cod_fornecedor: element[25],
                        raz_fornecedor: element[26],
                        fan_fornecedor: element[27],
                        cod_marca: element[28],
                        nom_marca: element[29],
                        tipo_movto: element[30],
                        qtd_movto: element[31],
                        data_movto: moment(element[32]).format('DD/MM/YYYY'),
                        cod_movto: element[33],
                        cod_origem_movto: element[34]
                    };
                return result
            },
            onSubmit() {
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
                        this.gradearProdutos()
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
                    let subgrouped_by_color_map = this.refs_array[ref_group].reduce(
                        (entryMap, e) => entryMap.set(e.des_cor, [...entryMap.get(e.des_cor) || [], e]),
                        new Map()
                    );
                    this.subgrouped_items_bycolor_obj[ref_group] = Object.fromEntries(subgrouped_by_color_map)

                    // this.produtos.push({nom_marca:this.refs_array[ref_group][0]['nom_marca'], cod_referencia:ref_group, des_cor:Object.keys(this.subgrouped_items_bycolor_obj[ref_group])})
                }

            },
            // gradearProdutosOld() {
            //     this.mapped_items = [];
            //     for (const ref_group in this.refs_array) {
            //         let graded_prods_entrada = {};
            //         let graded_prods_estoq = {};
            //         for (const prod in this.refs_array[ref_group]) {
            //             var estoq_entrada = 0;
            //             if (this.refs_array[ref_group][prod].tipo_movto == 'E') {
            //                 estoq_entrada = estoq_entrada + this.refs_array[ref_group][prod].qtd_movto;
            //                 graded_prods_entrada[this.refs_array[ref_group][prod].des_tamanho] = estoq_entrada
            //             }
            //             graded_prods_estoq[this.refs_array[ref_group][prod].des_tamanho] = this.refs_array[ref_group][prod].saldo_estoque
            //         }
            //         graded_prods_estoq['nom_marca'] = this.refs_array[ref_group][0].nom_marca;
            //         graded_prods_estoq['dat_cadastro'] = this.refs_array[ref_group][0].dat_cadastro;
            //         graded_prods_estoq['dat_alteracao'] = this.refs_array[ref_group][0].dat_alteracao;
            //         graded_prods_estoq['cod_referencia'] = this.refs_array[ref_group][0].cod_referencia;
            //         // graded_prods_estoq['des_produto'] = this.refs_array[ref_group][0].des_produto
            //         graded_prods_estoq['des_cor'] = this.refs_array[ref_group][0].des_cor
            //         graded_prods_estoq['des_produto'] = this.refs_array[ref_group][0].des_produto.replace(this.refs_array[ref_group][0].des_cor, '').replace(this.refs_array[ref_group][0].des_tamanho, '').replace(this.refs_array[ref_group][0].nom_marca, '');
            //         // graded_prods_estoq['des_produto'] = this.refs_array[ref_group][0].des_produto.slice(0, -3);
            //         graded_prods_estoq['img'] = this.imagem_test;
            //         // graded_prods_estoq['img'] = this.computedImage;
            //         // graded_prods_estoq['img'] = this.fetchImage(this.refs_array[ref_group][0].nom_marca, this.refs_array[ref_group][0].cod_referencia, this.refs_array[ref_group][0].des_cor);
            //         // graded_prods_estoq['img'] = 'No';
            //         graded_prods_estoq['vlr_custo_bruto'] = this.refs_array[ref_group][0].vlr_custo_bruto;
            //         graded_prods_estoq['vlr_venda1'] = this.refs_array[ref_group][0].vlr_venda1;
            //         this.mapped_items.push(graded_prods_entrada);
            //         this.mapped_items.push(graded_prods_estoq)
            //     }
            //
            // },
            gradearProdutos() {
                this.mapped_items = [];
                this.produtos = [];
                for (const ref_group in this.subgrouped_items_bycolor_obj) {
                    for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
                        let graded_prods_estoq = {};
                        for (const prod in this.subgrouped_items_bycolor_obj[ref_group][cor]) {
                            var estoq_entrada = 0;
                            if (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto == 'E') {
                                estoq_entrada = estoq_entrada + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
                                let estoq_entrada_name = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString() + "_E"
                                graded_prods_estoq[estoq_entrada_name] = estoq_entrada
                            }
                            graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho] = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque
                        }

                        graded_prods_estoq['nom_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca;
                        graded_prods_estoq['dat_cadastro'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_cadastro;
                        graded_prods_estoq['dat_alteracao'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_alteracao;
                        graded_prods_estoq['cod_referencia'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia;
                        // graded_prods_estoq['des_produto'] = this.refs_array[ref_group][0].des_produto
                        graded_prods_estoq['des_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor

                        // console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor')
                        // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor)
                        //     console.log('this.subgrouped_items_bycolor_obj[ref_group]')
                        //     console.log(this.subgrouped_items_bycolor_obj[ref_group])
                        graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_tamanho, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca, '');
                        // graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.slice(0, -3);
                        // graded_prods_estoq['img'] = this.imagem_test;
                        // graded_prods_estoq['img'] = this.computedImage;
                        // graded_prods_estoq['img'] = this.fetchImage(this.refs_array[ref_group][0].nom_marca, this.refs_array[ref_group][0].cod_referencia, this.refs_array[ref_group][0].des_cor);
                        graded_prods_estoq['img'] = 'https://martialartsplusinc.com/wp-content/uploads/2017/04/default-image.jpg';
                        // graded_prods_estoq['img'] = 'No';
                        graded_prods_estoq['vlr_custo_bruto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_bruto;
                        graded_prods_estoq['vlr_venda1'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_venda1;

                        this.graded_prods_estoq = graded_prods_estoq

                        this.mapped_items.push(graded_prods_estoq);
                        this.produtos.push({
                            nom_marca: this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca,
                            cod_referencia: this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia,
                            des_cor: this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor,
                            // img: this.subgrouped_items_bycolor_obj[ref_group][cor][0].img,
                            img: 'data:image/jpeg;base64,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'
                        })
                    }
                }
            },
            carregarImagens() {
                // const payload = this.produtos[0]
                console.log('this.produtos')
                console.log(this.produtos)
                const path = `/api/produtos/images/`;
                axios.put(path, this.produtos)
                    .then((res) => {
                        console.log('res.data carregar imagens');
                        console.log(res.data);
                        for (const key in res.data) {
                            this.mapped_items[key].img = res.data[key].img
                            this.produtos[key].img = res.data[key].img
                            console.log('res.data[key].img')
                            console.log(res.data[key].img)
                            console.log('this.mapped_items[key].img')
                            console.log(this.mapped_items[key].img)
                        }

                    })
                    .catch((error) => {
                        console.log(error)
                    })
            },
            async pesquisarImagens() {
                // const produtos = []
                // for (const key in this.mapped_items) {
                for (const key in this.produtos) {
                    let image_url = await this.fetchImage(this.produtos[key]['nom_marca'], this.produtos[key]['cod_referencia'], this.produtos[key]['des_cor'])
                    if (typeof image_url == 'undefined')
                        image_url = 'data:image/png;base64,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'

                    // let image_url = this.imagem_test
                    console.log('this.produtos_from_carregarImagens')
                    // console.log('key in this.produtos')
                    console.log("this.produtos[key]['nom_marca']")
                    console.log(this.produtos[key]['nom_marca'])
                    // console.log("this.produtos[key]['cod_referencia']")
                    console.log(this.produtos[key]['cod_referencia'])
                    // console.log("this.produtos[key]['des_cor']")
                    console.log(this.produtos[key]['des_cor'])
                    console.log('image_url_pesquisarImagens')
                    console.log(image_url)
                    this.produtos[key].img = image_url[0]
                    this.mapped_items[key].img = image_url[0]

                    // this.produtos[key]['img'] = image_url
                    // this.mapped_items[key].img= image_url
                    // this.mapped_items[key]['img'] = image_url
                    // this.mapped_items[key * 2 + 1]['img'] = image_url
                    // this.mapped_items[key*2-1]['img'] = image_url
                    // this.mapped_items[key*2]['img'] = image_url
                    // console.log("this.mapped_items[key*2+1]['img']")
                    console.log("this.mapped_items[key]['img']")
                    console.log(this.mapped_items[key]['img'])
                    // console.log('this.produtos[key].img')
                    // console.log(this.produtos[key]['img'])
                }
            },
            //maybe remove asyncs..

            async saveProdutos() {
                // const api_path = `/api/produtos/images/`
                const api_path = `/api/produtos/save`
                // const produto = [{nom_marca: "marca", cod_referencia: 'ref', des_cor: 'cor', img: 'string'}]
                console.log('this.produtos_from_saveProdutos')
                console.log(this.produtos)
                // console.log(produto)
                console.log(this.produtos[0])
                // axios.put(api_path, produto)
                axios.put(api_path, this.produtos)
                    // axios.put(api_path, [this.produtos[0]])
                    .then((res) => {
                        console.log('axios.put')
                        console.log(res.data)
                    })
                    .catch((error) => {
                        console.log(error)
                    })

            },
            async fetchImage (nom_marca, cod_referencia, des_cor) {
                const base_path = `https://www.googleapis.com/customsearch/v1?key=AIzaSyAxkljtWwOvBkyVgaCgQQYR2bgFMUdzrQs&cx=f5c6bf2ce19682bb8&&searchType=image&&num=1&q=`

                const query = nom_marca + '+' + cod_referencia + '+' + des_cor

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
                    })
                console.log('image_url_from fetchimage')
                console.log(image_url)
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
                axios.get(path)
                    .then((res) => {
                        console.log('res');
                        console.log(res);
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