<template>
  <div class="levantamentos">
    <h1>Levantamentos</h1>

    <!-- FORM SECTION -->
    <b-form @submit.stop.prevent="onSubmit">
      <b-row>
        <!-- MARCA SELECTION -->
        <b-col sm="2">
          <b-row>
            <div class="autosuggest">
              <b>Marca:</b>
              <vue-autosuggest
                v-model="query"
                :suggestions="filteredOptions"
                :get-suggestion-value="getSuggestionValue"
                @selected="onSelected"
                @input="onInputChange"
                @focus="focusMe"
                @click="clickHandler"
                :input-props="{
                  id: 'autosuggest__input',
                  placeholder: 'Digite a marca',
                  class: 'form-control'
                }"
              >
                <template #suggestion="{ suggestion }">
                  <div class="autosuggest-container-results">
                    {{ suggestion.item.nom_marca }} ({{ suggestion.item.cod_marca }})
                  </div>
                </template>
              </vue-autosuggest>
            </div>
          </b-row>

          <b-row>
            <b-button variant="primary" @click.prevent="pesquisarImagens">
              Pesquisar Imagens
            </b-button>
            <b-button variant="primary" @click.prevent="carregarImagens">
              Carregar Imagens
            </b-button>
            <b-button variant="primary" @click.prevent="saveProdutos">
              Salvar Produtos
            </b-button>
          </b-row>

          <b-form-checkbox v-model="showHideImgLink" switch>
            Link Imagens
          </b-form-checkbox>
        </b-col>

        <!-- DATE PICKERS -->
        <b-col sm="2">
          <b-row>
            <label for="datepicker-data-ini">Data Cadastro Inicial:</label>
            <mydatepicker-ini
              id="datepicker-data-ini"
              :datepicker_default="datepicker_ini"
              @childToParent="receiveDataCadastroIni"
            />
          </b-row>
          <b-row>
            <label for="datepicker-data-fim">Data Cadastro Final:</label>
            <mydatepicker-fim
              id="datepicker-data-fim"
              :datepicker_default="datepicker_fim"
              @childToParent="receiveDataCadastroFim"
            />
          </b-row>
        </b-col>

        <!-- FILTER & SUBMIT -->
        <b-col sm="2">
          <b-button type="submit" variant="primary">Enviar</b-button>

          <b-form-group>
            <b-input-group size="sm">
              <b-form-input
                id="filter-input"
                placeholder="Filtrar por..."
                type="search"
                v-model="filter"
              />
              <b-input-group-append>
                <b-button :disabled="!filter" @click="filter = ''">Limpar</b-button>
              </b-input-group-append>
            </b-input-group>
          </b-form-group>
        </b-col>

        <!-- GRADE SELECTION -->
        <b-col sm="4">
          <b-row>
            <b-col sm="6" v-for="grade in grades_options" :key="grade.name">
              <div class="form-check form-switch">
                <input
                  class="form-check-input"
                  type="checkbox"
                  v-model="grades_selected"
                  :value="grade"
                />
                <label class="form-check-label">{{ grade.name }}</label>
              </div>
            </b-col>
          </b-row>
        </b-col>
      </b-row>
    </b-form>

    <!-- TABLE SECTION -->
    <b-table
      :bordered="true"
      :fields="computedFields"
      :items="filteredmappedItemsComputed"
      small
      striped
      hover
      head-variant="light"
      sticky-header="700px"
      :sort-compare="dateSorter"
      @row-clicked="expandAdditionalInfo"
    >

      <!-- ACTIONS COLUMN (SHOW/HIDE DETAILS) -->
      <template #cell(actions)="{ detailsShowing, item }">
        <b-btn @click="toggleDetails(item)">
          {{ detailsShowing ? '-' : '+' }}
        </b-btn>
      </template>

      <!-- ROW DETAILS -->
      <template #row-details="{ item }">
        <b-table
          :fields="[{ key: 'data_movto', sortable: true }, 'tipo_movto', 'qtd_movto', ...gradeFields]"
          :items="item.movtos"
          sort-asc
          sort-by="data_movto"
          :sort-compare="dateSorter"
          sticky-header
        />
      </template>

      <!-- FILTER INPUT ROW -->
      <template #top-row>
        <td v-for="field in [...baseFields, ...gradeFields, ...valoresFields]" :key="field.key">
          <b-form-input
            v-if="[
            'nom_marca',
            'dat_cadastro',
            'dat_ultcompra',
            'cod_referencia',
            'des_cor',
            'des_produto',
            'vlr_custo_bruto',
            'vlr_venda1'
          ].includes(field.key)"
            class="col-sm"
            :placeholder="field.label"
            v-model="filters[field.key]"
          />
          <template v-else>
            {{ gradeTotals[field.key + '_E'] }}
            <br />
            <b>{{ gradeTotals[field.key] }}</b>
          </template>
        </td>
      </template>

      <!-- CHECKBOX COLUMN FOR SELECTION -->
      <template #head(selected)>
        <b-form-checkbox
          :indeterminate="form_indeterminate"
          v-model="form_allSelected"
          @change="form_toggleAll"
        />
      </template>

      <template #cell(selected)="row">
        <input
          type="checkbox"
          v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected"
          @change="formAnySelected"
        />
      </template>

      <!-- IMAGE COLUMN -->
      <template #cell(img)="data">
        <img
          :src="data.value"
          @click="increaseImageIndex(data.item.cod_referencia, data.item.des_cor)"
          v-bind="imageProps"
        />
      </template>

      <template #head(img_link)>
        <div v-show="showHideImgLink">Link</div>
      </template>

      <template #cell(img_link)="row">
        <div v-show="showHideImgLink">
          <b-form-input
            v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].img[0]"
          />
          <b-form-file
            ref="file-input"
            accept="image/*"
            placeholder="Nenhum arquivo"
            @change="previewImage($event, row.item.cod_referencia, row.item.des_cor)"
          />
        </div>
      </template>

      <!-- DYNAMIC GRADE FIELDS -->
      <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item }">
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
// import { isValid, format } from 'date-fns';
import moment from "moment";

const MOVEMENT_TYPES = new Set([7, 3, 9, 12]); // Define the movement types

export default {
  name: "LevantamentosTest",
  components: {
    'mydatepicker-ini': Mydatepicker,
    'mydatepicker-fim': Mydatepicker,
    'vue-autosuggest': VueAutosuggest
  },

  // DATA PROPERTIES
  data() {
    return {
      // Data flags
      showHideImgLink: false,

      // Form flags
      form_allSelected: false,
      form_indeterminate: false,

      // Image data
      imageProps: {blank: true, width: 75, height: 75, class: 'm1'},

      // Suggestion data
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
      query: "",
      suggestion_selected: {
        cod_marca: 0,
        fornecedores: [{fan_fornecedor: ''}],
        nom_marca: "carregando",
      },

      // Datepicker data
      datepicker_ini: new Date(1900, 0, 1),
      datepicker_fim: new Date(2019, 11, 16),
      data_cadastro_ini: '',
      data_cadastro_fim: '',

      // Items data
      items: [],

      // Filter data
      filter: null,
      filters: {nom_marca: '', dat_cadastro: '', des_cor: '', des_produto: ''},
      currentItems: [],

      // Grade data
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
      graded_prods_entrada: '',
      graded_prods_estoq: '',
      array: [],
      google_search_array: [],
      produtos: [],
      ref_cor_marca: [],
      refs_array: '',
      mapped_items: [],
      form_selected: [],
      subgrouped_items_bycolor_obj: {},
      cod_fornecedor: 70,
      form_selected_: [],
    }
  },

  // COMPUTED PROPERTIES
  computed: {
    //FILTERED MAPPED ITEMS
    filteredmappedItemsComputed() {
      const filterKeys = Object.keys(this.filters);
      return this.mappedItemsComputed.filter(item => {
        return filterKeys.every(key => {
          const itemValue = String(item[key] || "").toLowerCase();
          const filterValue = String(this.filters[key] || "").toLowerCase();
          return itemValue.includes(filterValue);
        });
      });
    },

    //GRADE TOTALS
    gradeTotals() {
      const grade_totals = {};
      let total = 0; // Total for regular grades
      let totalE = 0; // Total for _E grades

      const filteredItems = this.filteredmappedItemsComputed;

      if (!Array.isArray(filteredItems) || filteredItems.length === 0) {
        return grade_totals; // Return empty if no items
      }

      for (const item of filteredItems) {
        for (const key in item) {
          const value = item[key];

          if (typeof value !== 'number' || isNaN(value)) {
            continue; // Skip non-numeric or NaN values
          }

          if (key.endsWith('_E')) {
            grade_totals[key] = (grade_totals[key] || 0) + value; // Sum _E grades
            totalE += value; // Accumulate total E
          } else if (/^\d+$|^G$|^P$|^M$/.test(key)) {
            grade_totals[key] = (grade_totals[key] || 0) + value;
            total += value; // ✅ Correctly sum all size-based values into totais
          }
        }
      }

      // ✅ Assign the aggregated totals
      grade_totals["totais"] = total;
      grade_totals["totais_E"] = totalE;

      return grade_totals;
    },

    //MAPPED ITEMS
    mappedItemsComputed() {
      let mapped_items = [];

      for (const ref_group in this.subgrouped_items_bycolor_obj) {
          for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
              const products = this.subgrouped_items_bycolor_obj[ref_group][cor];
              const { graded_prods_estoq, movtos, saldo_estoq_entrada, total_saldo_estoque } = this.processProducts(products);

              // Transform movtos to remove tipo_movto
              let reduced_movtos = Object.entries(movtos).map(([date, sizes]) => {
                  return { data_movto: date, ...sizes };
              });

              const firstProduct = products[0];

              let finalProduct = {
                  ...graded_prods_estoq,
                  nom_marca: firstProduct.nom_marca,
                  dat_cadastro: firstProduct.dat_cadastro,
                  dat_ultcompra: firstProduct.dat_ultcompra,
                  cod_referencia: firstProduct.cod_referencia,
                  des_cor: firstProduct.des_cor,
                  des_produto: firstProduct.des_produto,
                  img: firstProduct.img,
                  selected: false,
                  totais_E: saldo_estoq_entrada,
                  totais: total_saldo_estoque,
                  vlr_custo_bruto: firstProduct.vlr_custo_bruto,
                  vlr_venda1: firstProduct.vlr_venda1,
                  des_grupo: firstProduct.des_grupo,
                  cod_grupo: firstProduct.cod_grupo,
                  cod_subgrupo: firstProduct.cod_subgrupo,
                  des_subgrupo: firstProduct.des_subgrupo,
                  cod_produto: firstProduct.cod_produto,
                  vlr_custo_aquis: firstProduct.vlr_custo_aquis,
                  cod_grade: firstProduct.cod_grade,
                  des_grade: firstProduct.des_grade,
                  cod_cor: firstProduct.cod_cor,
                  cod_fornecedor: firstProduct.cod_fornecedor,
                  raz_fornecedor: firstProduct.raz_fornecedor,
                  fan_fornecedor: firstProduct.fan_fornecedor,
                  cod_marca: firstProduct.cod_marca,
                  image_index: 0,
                  movtos: reduced_movtos
              };

              mapped_items.push(finalProduct);
          }
      }

      return mapped_items;
  },

    //TODOS PRODUTOS
    todosProdutos() {
      return this.mappedItemsComputed.map(produto => {
        const dat_cadastro = produto.dat_cadastro;
        const dat_ultcompra = produto.dat_ultcompra;

        const formatDateTime = (dateString) => {
    if (dateString && moment(dateString).isValid()) {
        return moment(dateString).format('YYYY-MM-DDTHH:mm:ss.SSSSSS');
    }
    return null;
};

const formatted_dat_cadastro = formatDateTime(dat_cadastro);
const formatted_dat_ultcompra = formatDateTime(dat_ultcompra);

        return {
          cod_grupo: produto.cod_grupo != null ? produto.cod_grupo : 0, // Explicit null check
          des_grupo: produto.des_grupo || '',
          cod_subgrupo: produto.cod_subgrupo != null ? produto.cod_subgrupo : 0,
          des_subgrupo: produto.des_subgrupo || '',
          cod_produto: produto.cod_produto != null ?  produto.cod_produto : 0,
          des_produto: produto.des_produto || '',
          vlr_custo_bruto: produto.vlr_custo_bruto != null ?  produto.vlr_custo_bruto : 0.0,
          vlr_custo_aquis: produto.vlr_custo_aquis != null ? produto.vlr_custo_aquis : 0.0,
          vlr_venda1: produto.vlr_venda1 != null ? produto.vlr_venda1 : 0.0,
          cod_grade: produto.cod_grade != null ?  produto.cod_grade : 0,
          des_grade: produto.des_grade || '',
          cod_cor: produto.cod_cor != null ? produto.cod_cor : 0,
          dat_cadastro: formatted_dat_cadastro,
          dat_ultcompra: formatted_dat_ultcompra,
          cod_fornecedor: produto.cod_fornecedor != null ?  produto.cod_fornecedor : 0,
          raz_fornecedor: produto.raz_fornecedor || '',
          fan_fornecedor: produto.fan_fornecedor || '',
          cod_marca: produto.cod_marca != null ?  produto.cod_marca : 0,
          cod_referencia: produto.cod_referencia || 'default',
          nom_marca: produto.nom_marca || '',
          des_cor: produto.des_cor || '',
          img: produto.img,
          selected: produto.selected,
          image_index: produto.image_index
        };
      });
    },

    //PRODUTOS SELECIONADOS
    produtosSelecionados() {
      return this.todosProdutos.filter(row => row.selected == true)
    },

    //COMPUTED FIELDS
    computedFields() {
      return [].concat(this.baseFields, this.gradeFields, this.valoresFields)
    },

    //GRADE FIELDS
    gradeFields() {
      var grades = this.grades_selected.map(selected => {
        return selected.grade
      })
      return [].concat(grades.flat(1), this.totaisFields) //manter totaisFields aqui para que os totais fiquem corretos
    },

    //BASE FIELDS
    baseFields() {
      return [
        {key: 'selected', label: 'Sel.'},
        {key: 'nom_marca', label: 'Nom. Marca', sortable: true},
        {key: 'dat_cadastro', label: 'Data Cad.', sortable: true},
        {key: 'dat_ultcompra', label: 'Data UltCompra', sortable: true},
        {key: 'cod_referencia', label: 'Ref.', sortable: true},
        {key: 'des_cor', label: 'Cor', sortable: true},
        {key: 'img', label: 'Img.'},
        {key: 'img_link', label: 'Img Link'},
        {key: 'des_produto', label: 'Descrição.', sortable: true},
        {key: 'actions', label: '+'}
      ]
    },

    //VALORES FIELDS
    valoresFields() {
      return [
        {key: 'vlr_custo_bruto', label: 'Custo', sortable: true},
        {key: 'vlr_venda1', label: 'Vlr. Venda', sortable: true}
      ]
    },

    //TOTAIS FIELDS
    totaisFields() {
      return [
        {key: 'totais', label: 'Tot.', sortable: true}
      ]
    },

    //FILTERED OPTIONS
    filteredOptions() {
      console.log('this.suggestions')
      console.log(this.suggestions)
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

    //AVAILABLE FORNECEDORES
    availableFornecedores() {
      return this.suggestion_selected.fornecedores
        .filter(item => item)
        .map(item => item.fan_fornecedor)
    },

    //COMPUTED ITEMS
    computedItems() {
      return this.items
        .filter(item => item)
        .map(item => item)
    }
  },

  // LIFECYCLE HOOKS
  beforeMount() {
    this.loadMarcas()
  },

  // METHODS
  methods: {
     processProducts(products) {
        let graded_prods_estoq = {};
        let movtos = {};
        let saldo_estoq_entrada = 0;
        let total_saldo_estoque = 0;

        for (const product of products) {
            let sizeKey = String(product.des_tamanho);
            let estoq_entrada_key = `${sizeKey}_E`;

            if (!graded_prods_estoq[estoq_entrada_key]) graded_prods_estoq[estoq_entrada_key] = 0;
            if (!graded_prods_estoq[sizeKey]) graded_prods_estoq[sizeKey] = 0;

            let movimento = 0;
            if (MOVEMENT_TYPES.has(product.cod_origem_movto)) {
                movimento = product.tipo_movto === "S" && product.cod_origem_movto === 12
                    ? -product.qtd_movto
                    : product.tipo_movto === "E"
                        ? product.qtd_movto
                        : product.tipo_movto === "S"
                            ? -product.qtd_movto
                            : 0;

                movtos[product.data_movto] = movtos[product.data_movto] || { data_movto: product.data_movto };
                movtos[product.data_movto][sizeKey] = (movtos[product.data_movto][sizeKey] || 0) + movimento;

                if (product.tipo_movto === "E") {
                    graded_prods_estoq[estoq_entrada_key] += product.qtd_movto;
                    saldo_estoq_entrada += product.qtd_movto;
                }
            }
            graded_prods_estoq[sizeKey] = product.saldo_estoque;
            total_saldo_estoque += product.saldo_estoque;
        }

        return { graded_prods_estoq, movtos, saldo_estoq_entrada, total_saldo_estoque };
    },
    //TOGGLE DETAILS
    expandAdditionalInfo(row) {
      row._showDetails = !row._showDetails;
    },

    //TOGGLE DETAILS
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

    //DATE SORTER
    dateSorter(a, b, key) {

      if (key === 'dat_ultcompra' || key === 'dat_cadastro'|| key === 'data_movto') {
        if (new Date(a[key]) > new Date(b[key])) return 1;
        if (new Date(a[key]) < new Date(b[key])) return -1;
        return 0;
      } else {
        return false       // If field is not `date` we let b-table handle the sorting
      }
    },

    //OBJECTIFY
    objectify(element) {
      return {
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
        dat_cadastro: element[20],
        dat_ultcompra: element[21],
        cod_fornecedor: element[22],
        raz_fornecedor: element[23],
        fan_fornecedor: element[24],
        cod_marca: element[25],
        nom_marca: element[26],
        tipo_movto: element[27],
        qtd_movto: element[28],
        data_movto: element[29],
        cod_movto: element[30],
        cod_origem_movto: element[31],
        selected: false,
        image_index: 0,
                        // img: ['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=']
                        img: ['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=', 'https://lojaferracini.vteximg.com.br/arquivos/ids/265063-800-800/Pro_0000022240415-0001.jpg?v=637406341029930000']
                    };
            },
            onSubmit() {
                // const path = `http://localhost/api/levantamentos/${this.data_cadastro_ini}/${this.data_cadastro_fim}/${this.suggestion_selected.cod_marca}/`;
                const path = `/api/levantamentos/${this.data_cadastro_ini}/${this.data_cadastro_fim}/${this.suggestion_selected.cod_marca}/`;
                axios.get(path)
                    .then((res) => {
                        // console.log("res");
                        // console.log(res);
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

                // console.log('this.todosProdutos')
                // console.log(this.todosProdutos)
                const path = `/api/produtos/images/`;
                // axios.put(path, this.produtosSelecionados)
                axios.put(path, this.todosProdutos)
                    // axios.put(path, this.produtos)
                    .then((res) => {
                        // console.log('res.data carregar imagens');
                        // console.log(res.data);
                        for (const key in res.data) {
                            // console.log('res.data')
                            // console.log(res.data)
                            //
                            // console.log('res.data[key].img')
                            // console.log(res.data[key].img)
                            // console.log('this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img')
                            // console.log(this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0].img)

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
                    // console.log('key')
                    // console.log(key)
                    // for (const key in this.produtos) {
                    let image_url = await this.fetchImage(marca, ref_group, cor, descricao)
                    // let image_url = await this.fetchImage(this.produtosSelecionados[key]['nom_marca'], this.produtosSelecionados[key]['cod_referencia'], this.produtosSelecionados[key]['des_cor'])
                    if (typeof image_url == 'undefined')
                        image_url = 'data:image/png;base64,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'

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
                // console.log('this.produtosSelecionados')
                // console.log(this.produtosSelecionados)
                const api_path = `/api/produtos/save`
                axios.put(api_path, this.produtosSelecionados)
                    .then((res) => {
                        // console.log('axios.put')
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


                let image_url = axios.get(path_without_spaces)
                    .then((response) => {

                        return response.data.items.map((item) => {
                            // this.imagem_test = item.link
                            return item.link
                        });
                    })
                    .catch((error) => {
                        console.log(error)
                        console.log(error.response.data); // => the response payload
                    })
                // console.log('image_url_from fetchimage')
                // console.log(image_url)
                // console.log('typeof image_url')
                // console.log(typeof image_url)
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
                        // console.log('res');
                        // console.log(res);
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
                        // console.log("this.subgrouped_items_bycolor_obj[ref_group]")
                        // console.log(this.subgrouped_items_bycolor_obj[ref_group])
                        for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
                            // console.log("this.subgrouped_items_bycolor_obj[ref_group][cor]")
                            // console.log(this.subgrouped_items_bycolor_obj[ref_group][cor])
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
                // console.log("this.produtosSelecionados")
                // console.log(this.produtosSelecionados)
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