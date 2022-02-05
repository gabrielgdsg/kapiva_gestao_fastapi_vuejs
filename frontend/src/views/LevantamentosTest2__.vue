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
        <b-table :bordered="true" :fields="computedFields" :filter="filter" :items="mappedItemsComputed" :small=true
                 :sort-compare="dateSorter" class="text-right" head-variant="light" hover sticky-header="700px" striped>

<!--            <b-table :bordered="true" :fields="computedFields" :filter="filter" :items="mapped_items" :small=true-->
<!--                 :sort-compare="dateSorter" class="text-right" head-variant="light" hover sticky-header="700px" striped>-->



            <template #cell(selected)="row">  <!-- eslint-disable-line-->
<!--                <input type="checkbox" v-model="this.subgrouped_items_bycolor_obj[0][0][0].selected" />-->
<!--                <input type="checkbox" v-model="row.item.selected" />-->
                <input type="checkbox" v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected" />
<!--                <input type="checkbox" v-model="this.subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected" />-->
<!--                {{this.subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected}}-->
<!--                <div v-if="this.subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected=true">-->
<!--                <div v-if="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected==true">-->
<!--                    {{subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected}}-->
<!--                </div>-->
<!--                <div v-else>-->
<!--                    {{subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected}}-->
<!--                    null or false-->
<!--                </div>-->
<!--                    {{row.item.selected}}-->
            </template>

            // eslint-disable-next-line vue/no-unused-vars
            <template #cell(img)="data">  <!-- eslint-disable-line-->
                <!--            <template slot="[img]" slot-scope="data">-->
                <!--                <img :src="this.produtos.img" v-bind="imageProps"/>-->
                <!--                <img :src=imagem_test v-bind="imageProps"/>-->
                <img :src="data.value" v-bind="imageProps"/>
            </template>


            <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item }">
                <!-- eslint-disable-line-->
                {{item[field.key+"_E"]}}
                <br><!-- eslint-disable-line-->
                <b> {{item[field.key]}} </b><!-- eslint-disable-line-->
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
                //     {key: 'des_cor', label: 'Cor'},
                //     {key: 'img', label: 'Img.'},
                //     {key: 'des_produto', label: 'Descrição.'},
                // ]
            }
        },
        computed: {
            mappedItemsComputed() {
                let mapped_items = [];
                // this.produtos = [];

                for (const ref_group in this.subgrouped_items_bycolor_obj) {
                    for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
                        let saldo_estoq_entrada = 0;
                        let saldo_estoq = 0;
                        let graded_prods_estoq = {};

                        for (const prod in this.subgrouped_items_bycolor_obj[ref_group][cor]) {
                            var estoq_entrada = 0;
                            // this.subgrouped_items_bycolor_obj[ref_group][cor][prod].img = 'https://martialartsplusinc.com/wp-content/uploads/2017/04/default-image.jpg';

                            // {
                            // if (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto == 'E' &&
                            //     (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 7)) {

                                if (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto === 'E' &&
                                (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 7) &&
                                (new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) >=
                                    new Date(moment(this.data_cadastro_ini).format('YYYY/MM/DD')) &&
                                    new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) <=
                                    new Date(moment(this.data_cadastro_fim).format('YYYY/MM/DD')))) {

                                // fazer um filtro por dat_movto???
                                //
                                // console.log("this.subgrouped_items_bycolor_obj[ref_group]")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group])
                                //
                                // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto)
                                //
                                // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto)
                                //
                                // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto)
                                //
                                // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto)


                                // {(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 7 ||
                                //         this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 3)) {


                                // this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 2) &&
                                // (new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) >=
                                //     new Date(moment(this.data_cadastro_ini).format('YYYY/MM/DD')) &&
                                //     new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) <=
                                //     new Date(moment(this.data_cadastro_fim).format('YYYY/MM/DD')))) {

                                // console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto')
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto)

                                estoq_entrada = estoq_entrada + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
                                let estoq_entrada_name = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString() + "_E"

                                if (isNaN(graded_prods_estoq[estoq_entrada_name])) {
                                    graded_prods_estoq[estoq_entrada_name] = estoq_entrada
                                } else {
                                    graded_prods_estoq[estoq_entrada_name] = graded_prods_estoq[estoq_entrada_name] + estoq_entrada
                                }
                                saldo_estoq_entrada = saldo_estoq_entrada + estoq_entrada

                                // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia)
                                // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor")
                                // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor)
                                // console.log("estoq_entrada_name")
                                // console.log(estoq_entrada_name)
                                // console.log("estoq_entrada")
                                // console.log(estoq_entrada)
                                // console.log("saldo_estoq_entrada")
                                // console.log(saldo_estoq_entrada)


                            }
                            //calculating saldo_estoq summing saldo.estoque only once per item
                            if (isNaN(graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho])) {
                                saldo_estoq = saldo_estoq + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque
                            }

                            graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho] = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque

                        }

                        graded_prods_estoq['nom_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca;
                        graded_prods_estoq['dat_cadastro'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_cadastro;
                        graded_prods_estoq['dat_alteracao'] = this.subgrouped_items_bycolor_obj[ref_group][cor][this.subgrouped_items_bycolor_obj[ref_group][cor].length - 1].dat_alteracao;
                        graded_prods_estoq['cod_referencia'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia;
                        graded_prods_estoq['des_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor
                        graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_tamanho, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca, '');
                        // graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.slice(0, -3);
                        // graded_prods_estoq['img'] = this.imagem_test;
                        // graded_prods_estoq['img'] = this.computedImage;
                        // graded_prods_estoq['img'] = this.fetchImage(this.refs_array[ref_group][0].nom_marca, this.refs_array[ref_group][0].cod_referencia, this.refs_array[ref_group][0].des_cor);
                        graded_prods_estoq['img'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].img;
                        // graded_prods_estoq['img'] = 'https://martialartsplusinc.com/wp-content/uploads/2017/04/default-image.jpg';
                        // graded_prods_estoq['img'] = 'No';
                        graded_prods_estoq['selected'] =this.subgrouped_items_bycolor_obj[ref_group][cor][0].selected;
                        graded_prods_estoq['totais_E'] = saldo_estoq_entrada;
                        graded_prods_estoq['totais'] = saldo_estoq;
                        graded_prods_estoq['vlr_custo_bruto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_bruto;
                        graded_prods_estoq['vlr_venda1'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_venda1;

                        // this.graded_prods_estoq = graded_prods_estoq

                        mapped_items.push(graded_prods_estoq);
                        // this.produtos.push({
                        //     // selectable: false,
                        //
                        //     nom_marca: this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca,
                        //     cod_referencia: this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia,
                        //     des_cor: this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor,
                        //     // img: this.subgrouped_items_bycolor_obj[ref_group][cor][0].img,
                        //     img: 'data:image/jpeg;base64,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'
                        // })
                    }
                }
                return mapped_items
            },
            todosProdutos() {
               var produtos =  this.mappedItemsComputed.map(produto => {
                    return {cod_referencia: produto.cod_referencia, des_cor: produto.des_cor, img: produto.img, nom_marca: produto.nom_marca, des_produto: produto.des_produto}
                })
                return produtos
            },
            produtosSelecionados() {
                var selected_rows = this.mappedItemsComputed.filter(row => row.selected==true)
                // return selected_rows
                return selected_rows.map(produto => {
                    return {cod_referencia: produto.cod_referencia, des_cor: produto.des_cor, img: produto.img, nom_marca: produto.nom_marca, des_produto: produto.des_produto}
                })
            },
            // produtosSelecionados() {
            //     var selected_rows = this.mappedItemsComputed.map(row => {return row.selected})
            //     return selected_rows
            //     // return selected_rows.map(produto => {
            //     //     return {cod_referencia: produto.cod_referencia, des_cor: produto.des_cor, img: produto.img, nom_marca: produto.nom_marca}
            //     // })
            // },
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
                    {key: 'dat_alteracao', label: 'Data Alt.', sortable: true},
                    {key: 'cod_referencia', label: 'Ref.', sortable: true},
                    {key: 'des_cor', label: 'Cor', sortable: true},
                    {key: 'img', label: 'Img.'},
                    {key: 'des_produto', label: 'Descrição.', sortable: true}
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
            },
            computedImage() {
                return this.imagem_test
                // return this.fetchImage('nike', '646433', 'preto')

            },
        },
        beforeMount() {
            this.loadMarcas()
        },
        methods: {
            clearGradesSelected() {
                console.log("this.grades_selected")
                console.log(this.grades_selected)
                // this.grades_selected = [];
            },
            dateSorter(a, b, key) {
                // console.log('a')
                // console.log(a)
                // console.log(a[key])
                // console.log('a[key]')
                // console.log(b.key)
                // console.log('b.key')
                // console.log(key)
                // if (key !== 'dat_cadastro') {
                // if (key !== 'dat_alteracao') {
                if (key === 'dat_alteracao' || key === 'dat_cadastro') {
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
                        des_tamanho: element[17],
                        cod_cor: element[18],
                        des_cor: element[19],
                        // dat_cadastro: element[20],
                        // dat_cadastro: moment(element[20]),
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
                        cod_origem_movto: element[34],
                        selected:false,
                        img: 'https://media.istockphoto.com/vectors/male-profile-flat-blue-simple-icon-with-long-shadow-vector-id522855255?k=20&m=522855255&s=612x612&w=0&h=fLLvwEbgOmSzk1_jQ0MgDATEVcVOh_kqEe0rqi7aM5A='
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
            // gradearProdutos() {
            //     // this.mapped_items = [];
            //     // this.produtos = [];
            //
            //     for (const ref_group in this.subgrouped_items_bycolor_obj) {
            //         for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
            //             let saldo_estoq_entrada = 0;
            //             let saldo_estoq = 0;
            //             let graded_prods_estoq = {};
            //
            //             for (const prod in this.subgrouped_items_bycolor_obj[ref_group][cor]) {
            //                 var estoq_entrada = 0;
            //
            //                 // {
            //                 // if (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto == 'E' &&
            //                 //     (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 7)) {
            //
            //                     if (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto === 'E' &&
            //                     (this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto === 7) &&
            //                     (new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) >=
            //                         new Date(moment(this.data_cadastro_ini).format('YYYY/MM/DD')) &&
            //                         new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) <=
            //                         new Date(moment(this.data_cadastro_fim).format('YYYY/MM/DD')))) {
            //
            //                     // fazer um filtro por dat_movto???
            //                     //
            //                     console.log("this.subgrouped_items_bycolor_obj[ref_group]")
            //                     console.log(this.subgrouped_items_bycolor_obj[ref_group])
            //
            //                     console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto")
            //                     console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].tipo_movto)
            //
            //                     console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto")
            //                     console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto)
            //
            //                     console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto")
            //                     console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto)
            //
            //                     console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto")
            //                     console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto)
            //
            //
            //                     // {(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 7 ||
            //                     //         this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 3)) {
            //
            //
            //                     // this.subgrouped_items_bycolor_obj[ref_group][cor][prod].cod_origem_movto == 2) &&
            //                     // (new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) >=
            //                     //     new Date(moment(this.data_cadastro_ini).format('YYYY/MM/DD')) &&
            //                     //     new Date(moment(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto).format('DD/MM/YYYY')) <=
            //                     //     new Date(moment(this.data_cadastro_fim).format('YYYY/MM/DD')))) {
            //
            //                     // console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto')
            //                     // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][prod].data_movto)
            //
            //                     estoq_entrada = estoq_entrada + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].qtd_movto;
            //                     let estoq_entrada_name = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho.toString() + "_E"
            //
            //                     if (isNaN(graded_prods_estoq[estoq_entrada_name])) {
            //                         graded_prods_estoq[estoq_entrada_name] = estoq_entrada
            //                     } else {
            //                         graded_prods_estoq[estoq_entrada_name] = graded_prods_estoq[estoq_entrada_name] + estoq_entrada
            //                     }
            //                     saldo_estoq_entrada = saldo_estoq_entrada + estoq_entrada
            //
            //                     // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia")
            //                     // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia)
            //                     // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor")
            //                     // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor)
            //                     // console.log("estoq_entrada_name")
            //                     // console.log(estoq_entrada_name)
            //                     // console.log("estoq_entrada")
            //                     // console.log(estoq_entrada)
            //                     // console.log("saldo_estoq_entrada")
            //                     // console.log(saldo_estoq_entrada)
            //
            //
            //                 }
            //                 //calculating saldo_estoq summing saldo.estoque only once per item
            //                 if (isNaN(graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho])) {
            //                     saldo_estoq = saldo_estoq + this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque
            //                 }
            //
            //                 graded_prods_estoq[this.subgrouped_items_bycolor_obj[ref_group][cor][prod].des_tamanho] = this.subgrouped_items_bycolor_obj[ref_group][cor][prod].saldo_estoque
            //
            //             }
            //
            //
            //             graded_prods_estoq['nom_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca;
            //             graded_prods_estoq['dat_cadastro'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_cadastro;
            //             graded_prods_estoq['dat_alteracao'] = this.subgrouped_items_bycolor_obj[ref_group][cor][this.subgrouped_items_bycolor_obj[ref_group][cor].length - 1].dat_alteracao;
            //             graded_prods_estoq['cod_referencia'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia;
            //             graded_prods_estoq['des_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor
            //             graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_tamanho, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca, '');
            //             // graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.slice(0, -3);
            //             // graded_prods_estoq['img'] = this.imagem_test;
            //             // graded_prods_estoq['img'] = this.computedImage;
            //             // graded_prods_estoq['img'] = this.fetchImage(this.refs_array[ref_group][0].nom_marca, this.refs_array[ref_group][0].cod_referencia, this.refs_array[ref_group][0].des_cor);
            //             graded_prods_estoq['img'] = 'https://martialartsplusinc.com/wp-content/uploads/2017/04/default-image.jpg';
            //             // graded_prods_estoq['img'] = 'No';
            //             graded_prods_estoq['totais_E'] = saldo_estoq_entrada;
            //             graded_prods_estoq['totais'] = saldo_estoq;
            //             graded_prods_estoq['vlr_custo_bruto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_bruto;
            //             graded_prods_estoq['vlr_venda1'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_venda1;
            //
            //             // this.graded_prods_estoq = graded_prods_estoq
            //
            //             this.mapped_items.push(graded_prods_estoq);
            //             // this.produtos.push({
            //             //     // selectable: false,
            //             //
            //             //     nom_marca: this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca,
            //             //     cod_referencia: this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia,
            //             //     des_cor: this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor,
            //             //     // img: this.subgrouped_items_bycolor_obj[ref_group][cor][0].img,
            //             //     img: 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQDw8PDQ8QDQ8PEA8NDg8PDxANDRAQFREWFhURFRUYHSggGBolHRUVITEiJSkrLy4uFx84ODMsNygtLisBCgoKDg0OGA8PFisdHR4rKystKy0tLS0rLSstLS0tKystLS0rKzctLSstLSs3LTcrLSsrKzctKystNy0rLSsrK//AABEIAOEA4QMBIgACEQEDEQH/xAAbAAEAAgMBAQAAAAAAAAAAAAAAAQUCBAYDB//EAEQQAAICAQEDBQ0GBAMJAAAAAAABAgMRBAUSIQYTMVFxIiMyM0FhcoGRobGywQcUJEJzgjRikqJSwtEVFiU1dIOz8PH/xAAXAQEBAQEAAAAAAAAAAAAAAAAAAQID/8QAHBEBAQEBAQEAAwAAAAAAAAAAAAERAjESAyFB/9oADAMBAAIRAxEAPwD7iAAAAAAAAAAAAAEEgAAAIJAAAAAAAAAAAAAAAAAAgAASAAAAAAEZAkHnKzzGDm//AIB6ykl0sjnY9aPDdG6XEbCmute0yyam4RujBuA08PrftJ3pdbGGtsGrzkuv3E89LqQxWyDWWoflj7zL7z5mQe4PFamPnXqJ5+PWB6g81bHrXtM00+jiBIAAAAAAAIAAEgAAAABq6t8V2G0aus6V6xB4qx9bMuel1+5HmDSPVXvqXsHP/wAq9rPIAe3PLqftJ52Pn9h4AYNhTj1+5k5XWvbg1gMG1js9o3PMapKb6wNhxI3TxVkut+0y56XWQZ7pDilxbSXW+CMJ3tQm+GUljh5ytsscnmTb7SyJW5bqoLwVvvrfCJ67NulJy3uhJYSWEuJVljsjpn+36ls/RKswAYaAAAAAEAACQAAAAA1tZ5PWbJravyessGsACsgAAAAAAAAAAAACLfF2di+ZFcWFvi59kfmRoFiVBZbH/P8At+pWllsj8/q+ovhPVkADDYAAAAAgAASCCQAAAGtq/J6zZNfWdC7SwaoIBWUggASCABIIAEggASCABF3i5/t+KNA3r/Fz/b8SvyWJUlnsjon2oq8lpsfwZdq+AvhPViADDYAAAAAgAASAAAAAGtrehdpsmtrvBXb9Cwclyv5TPQfd92j7w75zgoqe5JNYxjg85yOT3K2rVytqlVZpdRTFznRb4W6ulplD9qtu5LZs8OW5qJz3Y8ZSw63hefgeWwVfq9p6jaEtNZpKY6aylK2LhKUtxJLiuL6W+xHWSY57dXOg+0PZ1sowdk6XLCXO1tRy+uSykdPfqYVwdlk41wXFzlJRgl2s+HaTaVL2VPRc1KzVWahTpagnhdzwUunPkwus6nlNRZbbsXZt8moyqqlqEnxckt1+tKMl6xeYn0+iaLaFN6cqLa7orpdc4zx24NlP/wB6T5xt3QV7K2hs+/RJ013zdF9Sk3CSzFeXzSz2pHhrtlPWbd1VH3i7TqNKtjOmbjLeUYJLs7onyv0+nEZOI5KbZ1CW0NDqrOcv0MZuu58ZTjiWG89LXcv1npyY29qLNj3au2asvq+8OMpRSXcRTjlLpJeV+nZ5JOGq5UbRlodNrKtLTqFKN8tVxlUoKEsRcVvdSfX0G3yW5X3ayUec0U6KZQsl95U3OjMOlZcVjy+wfNPp12Qca/tI0POOGL3WpbvPqvNPb05x6jrqbYzjGcJKcJJSjKLzFxaymmSyxdTqH3qfbD5ityWGqfep9sPiysyWJWeS32L4MvS+hS5LrYfgS9L6IdeHPqyABzbAAAAAEAACQAAAAA1tf4K7TZNbX+B60WDiuWew7tXPQyo3Mae/nbFKW693MOjhxfcs6TUZcJJcW4ySXnwycjJvWMfK9Pyb1EdkSlKmdWr0upepqju5sccRT3cdPkeP5Sy5UX2SWy9sRqm1TurU17rU4ZfdZT6OO8vWj6FkPjlPinwafFYL9J8vmvKHa9W1dbs6jQuVka7HbbLdlFRWYt5z1KL9qNzT6uurlDq53WQqj93xvTkoRzivhl9jO302jqqbdVVdTl4ThCMG+3CK7aXJjRambsv08Z2SxvTzKMnjoy00XYZXJ8mp/edoba1VOXVKqdcJY4SbjhY9UG/WhyRkv93dXx6Fq0/N3C/1O72fs+nT1qrT1xqrWXuxXBt9LfWzkdb9n6crVptZdptPfLft067qDeeOOK96GxMenJX/AJA/0NV8ZmlsKxx5NXOPB83ql6nNp/E61bJjXopaPT9zFUTorc35XFrek+15Zocm9gSp2a9DqnBuSvhN1yco7tjlxTaXkfUTVxocltn1T2EoOKatpvsnw6Z708S7Vhew9fst1Mp7NgpPPN221R9HhJL+4oaf9qaLTW7Oho3qYvnIUamvjFQm3nK9b6cYydfyN2PLRaKuizHOZlZZh5SnJ8Un5lheovX9SLnVvvM/Sh9SryWWsfeZelD6lTkzFrPJfbC8XL038Ec9k6HYHin6b+CHXi8+rIAHNsAAAAAQAAJAAAAADW1/getGya20PAfaviIVW5GTHIydGGrte6+FE5aSuN16xzdcmoxl3SystryZOP0nLnWO2dE9mOdlTUbo02uTry8ZaUWved1k4nkm/wDjG1+2PzliVua/l7p6NRdp7Kb26ZbkpwipxfBcenKXEtdTym0lVFOout5qvURU6lKMnZJNZ8GKb4ZRw9G07dNtfaU6NLPWZajOFed6MeD3sYZuctE1ds3aN2nlPTQhGOoolHLqcu6xJPh+by44wRfmJtdfVyj0Uq42rVU83OW5GUp7i38Z3XnGHjyM3NPr6bMc3dXZno3LIyb9jKerZeztVpVKqmmyibnfFRW7FWOO63heDLhhryHK/ZnsSiyqWrnGXP06iyFclJqO7zUeDj0PwmTIuvpS83EZPlHIjY0dTCdj112mtrv3Y1wtSUopRlxjnLy8o+qixZdZZGTHIyQYa595l6cPgypyWm0H3h+nD4Mp8l5SvTJ0ewPE/vkcxk6fk/4helL4k68OfVmADm6AAAAACAABIAAAAAa20PFv1fE2TW2h4uXq+IgqRkwyMnRhnk53Ymw7aNfrtVNwdepadai25rus90sF/kZCODnTtDR7R1uqo0L1Vd7Si1ZGPcrDyknnydRa7W5TyphWtXoLZVajTqdm4t9QsllSpnleZcfOdPknJrUxxv2a6eyGk1EpwlXXZbKdEJZTUN1pvj5Oj2GP2VS/A3/9TZ/4qzs8mFVUIJqEIwTeWoxUU31tLsXsGmPmXITZOgvhKzVSjHUV6jNWbublupRa7nPFZyfU8nO28jdnyal92jFpqScJThxznPBl/klurGeRkwyMkVhtF94f6kflZT5LXab7x/3V8rKbJrlmvTJ1fJ/+Hj2y+JyGTr+T38PDtl8zM9+Lx6sgAc3QAAAAAQAAJAAAAADX2h4qXZ9TYNfX+Kn2AUeRkwyMnRzZ5GTDIyBnkZMMjIGeRkwyMgZ5GTDIyMGeRkwyMjB57UfeF+r/AJClyW+1X+Hj+r/kKXJvnxKzydlye/hq/wB3zM4rJ2ewX+Hr7H8zM9+Lx6tESYJmSZydEgAAAAIAAEgAAAABr6/xU/RZsHhrvFT9F/ADnMjJhkZOrmzyMmGRkIzyMmGRkDPIyYZGQM8jJhkZCs8jJhkZA89rv8PD9Z/IUmS42w/w9f6svkKTJvnxms8nZ7Ef4er0fqzicnY7Il3ir0UZ/J4vK2jI9FI1YyPWMjk6NhMk8kz0RFSAAIAAEgAAAABrbSk1VY1Fz7l8I4z7zZPPULMJrrjJe4DjXq4rwlKHpQkl7egzqvjPjCUZ+i1I9UmeN2lhPjOEZPrcVve3pOrk9cjJqvQRXgTtqf8ALY5L+meUYum9eDbXP9Svdfti/oUbeScmg9RfHw9Pv+em2M/dLdZg9r1R8bzlH61U61/U1j3gWWRk1qNXXYs12Qs9CcZfA9gM8jJhkZAzyMmGRkDx20+8Vfqz+VFJvFxtx94p/Ut+EShuujCLlNqMV0tmufGens5pLLeEul+Q63ZNuaKmuhwi15OB8v1e0JWvCzGHkj+aXnf+h9T2No7HTTw3VzdfGXD8q8hPyeRrj1vQme9WX0HpToorp7p+72GykcHSMK4Y6T0ACgAAgAASAAAAAGM1wfYzIhgc66zB1llKgwdBvWMVzrMXWb7pMHUUaO4Rus3HUYusJio1OytPY82UVSl/i3FGf9S4ms9iRXidRqaPNG3nYf02Jl66zF1l0xQvTa6Hi76NQuq6qVUn+6Dx7jze0NXDx2hlJeWWnuhcv6XiR0DrMXAamOeXKjSp4ulZppdV9VlX9zWPeWWl19NvGq2uz0Jxl8Gbs45WJLK6msoqtXyb0VrzZpq97/FBc1P2xwX9CeVOqjVp9O55zK22MIRWZzk1HEYrys5K3Z11086hqtLwaYPe3O19DkX89gVaaUbKucnOSlCErbJWuqKxlV73g5z0nrRpfMWXExX6TZsILuY8et8WfVdJHFda6oQX9qOKo0p3MFwS6kkc+7rpzGQAMNAAAAACAABIAAAAAAAPJ1mLqPcDRqukwdJuEOJdTGhKk85UFk4GLrGmKyVB5ypLR1GMqS6mKp1GLqLN0mDoLpisdZi6yxlR5jzlQNTFVtCjKq83OfFGNGlLW3T53PNvfE9qNL5hpjV0+l6C/Rr11JGwZtagACKAAAAAIAAAAAAAAAAAAAAAAAAAhgAYsxYBUYM82AVEP8vr+JsQ6CQSqziSARQAAAAAAAAAAf/Z'
            //             // })
            //         }
            //     }
            // },
            carregarImagens() {
                // const payload = this.produtos[0]
                // console.log('this.produtos')
                // console.log(this.produtos)
                console.log('this.todosProdutos')
                console.log(this.todosProdutos)
                const path = `/api/produtos/images/`;
                axios.put(path, this.todosProdutos)
                // axios.put(path, this.produtos)
                    .then((res) => {
                        console.log('res.data carregar imagens');
                        console.log(res.data);
                        for (const key in res.data) {
                            console.log('res.data')
                            console.log(res.data)
                            // this.mapped_items[key].img = res.data[key].img
                            // this.produtos[key].img = res.data[key].img
                            // console.log('this.todosProdutos')
                            // console.log(this.todosProdutos)
                            // this.todosProdutos[key].img = res.data[key].img
                            console.log('res.data[key].img')
                            console.log(res.data[key].img)
                            console.log('this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img')
                            console.log(this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img)
                            this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img = res.data[key].img
                            // this.subgrouped_items_bycolor_obj[ref_group][cor][0].img = image_url[0]
                            // console.log('res.data[key].img')
                            // console.log(res.data[key].img)
                            // console.log('this.mapped_items[key].img')
                            // console.log(this.mapped_items[key].img)
                        }

                    })
                    .catch((error) => {
                        console.log(error)
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

                    // // let image_url = this.imagem_test
                    console.log('this.produtos_from_carregarImagens')

                    console.log('marca')
                    console.log(marca)
                    console.log('cor')
                    console.log(cor)
                    console.log('ref_group')
                    console.log(ref_group)

                    // console.log("this.produtosSelecionados[key]['nom_marca']")
                    // console.log(this.produtosSelecionados[key]['nom_marca'])
                    // // console.log("this.produtosSelecionados[key]['cod_referencia']")
                    // console.log(this.produtosSelecionados[key]['cod_referencia'])
                    // console.log("this.produtosSelecionados[key]['des_cor']")
                    // console.log(this.produtosSelecionados[key]['des_cor'])
                    // console.log('image_url_pesquisarImagens')
                    // console.log(image_url)
                    // console.log('image_url[0]')
                    // console.log(image_url[0])


                    console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][0].img')
                    console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].img)
                    // this.subgrouped_items_bycolor_obj[ref_group][cor][0].img = 'data:image/jpeg;base64,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'
                    this.subgrouped_items_bycolor_obj[ref_group][cor][0].img = image_url[0]
                    console.log('this.subgrouped_items_bycolor_obj[ref_group][cor][0].img')
                    console.log(this.subgrouped_items_bycolor_obj[ref_group][cor][0].img)
                    // this.gradearProdutos()
                    // this.produtos[key].img = image_url[0]
                    // this.produtosSelecionados[key].img = image_url[0]
                    // this.mapped_items[key].img = image_url[0]

                    // this.produtos[key]['img'] = image_url
                    // this.mapped_items[key].img= image_url
                    // this.mapped_items[key]['img'] = image_url
                    // this.mapped_items[key * 2 + 1]['img'] = image_url
                    // this.mapped_items[key*2-1]['img'] = image_url
                    // this.mapped_items[key*2]['img'] = image_url
                    // console.log("this.mapped_items[key*2+1]['img']")
                    // console.log("this.mapped_items[key]['img']")
                    // console.log(this.mapped_items[key]['img'])
                    // console.log('this.produtos[key].img')
                    // console.log(this.produtos[key]['img'])
                }
            },
            //maybe remove asyncs..

            async saveProdutos() {
                // const api_path = `/api/produtos/images/`
                const api_path = `/api/produtos/save`
                // const produto = [{nom_marca: "marca", cod_referencia: 'ref', des_cor: 'cor', img: 'string'}]
                // console.log('this.produtos_from_saveProdutos')
                // console.log(this.produtos)
                // console.log(produto)
                // console.log(this.produtos[0])
                // axios.put(api_path, produto)
                axios.put(api_path, this.produtosSelecionados)
                // axios.put(api_path, this.produtos)
                    // axios.put(api_path, [this.produtos[0]])
                    .then((res) => {
                        console.log('axios.put')
                        console.log(res.data)
                    })
                    .catch((error) => {
                        console.log(error)
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