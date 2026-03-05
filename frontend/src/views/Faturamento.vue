<template>
  <div class="page-layout faturamento">
    <div class="page-header">
      <h1 class="page-title">Faturamento</h1>
      <div class="page-subtitle">Comparação de vendas por marca, produto, margem e coleção</div>
    </div>
    <div class="page-main">
    <b-container fluid>
      <!-- Date Range Selector -->
      <b-row class="mb-4">
        <b-col md="3">
          <label>Data Inicial:</label>
          <b-form-datepicker v-model="data_ini" class="mb-2"></b-form-datepicker>
        </b-col>
        <b-col md="3">
          <label>Data Final:</label>
          <b-form-datepicker v-model="data_fim" class="mb-2"></b-form-datepicker>
        </b-col>
        <b-col md="3" class="d-flex align-items-end">
          <b-button variant="primary" @click="loadData" :disabled="loading">
            <b-spinner small v-if="loading"></b-spinner>
            Carregar Dados
          </b-button>
        </b-col>
        <b-col md="3" class="d-flex align-items-end">
          <b-form-checkbox v-model="includeDevolucoesEstornos" @change="onFilterChange">
            Incluir Devoluções/Estornos
          </b-form-checkbox>
          <b-form-text class="ml-2" style="font-size: 0.75rem;">
            (Fiscal - itens que entraram/saíram sem venda)
          </b-form-text>
        </b-col>
      </b-row>

      <!-- Tabs for different views -->
      <b-tabs v-model="tabIndex" class="mt-3">
        <!-- Brand Comparison -->
        <b-tab title="Marcas" @click="loadBrands">
          <b-row class="mt-3">
            <b-col md="12" class="mb-3">
              <b-form-group label="Mkt. Share Base:" label-cols-sm="3" label-cols-lg="2">
                <b-form-radio-group
                  v-model="mktShareMode"
                  :options="[
                    { text: 'Valor Bruto', value: 'bruto' },
                    { text: 'Lucro', value: 'lucro' }
                  ]"
                  buttons
                  button-variant="outline-primary"
                  size="sm"
                ></b-form-radio-group>
              </b-form-group>
            </b-col>
          </b-row>
          <b-row class="mt-3">
            <b-col>
              <b-table 
                :items="brands" 
                :fields="brandFields" 
                striped 
                hover
                :busy="loading"
                show-empty
                empty-text="Nenhum dado encontrado"
                :sort-compare="sortCompareNumeric"
                :sort-by="'vlr_bruto_total'"
                :sort-desc="true"
                @row-clicked="toggleBrandExpand"
              >
                <template #bottom-row>
                  <td :key="field.key" v-for="field in brandFields">
                    <template v-if="field.key === 'mkt_share'">
                      <strong>TOTAL</strong>
                    </template>
                    <template v-else-if="field.key === 'nom_marca'">
                      <strong>-</strong>
                    </template>
                    <template v-else-if="field.key === 'total_itens'">
                      <strong>{{ brandTotals.total_itens }}</strong>
                    </template>
                    <template v-else-if="field.key === 'custo_total'">
                      <strong>R$ {{ formatCurrency(brandTotals.custo_total) }}</strong>
                    </template>
                    <template v-else-if="field.key === 'vlr_bruto_total'">
                      <strong>R$ {{ formatCurrency(brandTotals.vlr_bruto_total) }}</strong>
                    </template>
                    <template v-else-if="field.key === 'total_descontos'">
                      <strong>R$ {{ formatCurrency(brandTotals.total_descontos) }}</strong>
                    </template>
                    <template v-else-if="field.key === 'vlr_liquido_total'">
                      <strong>R$ {{ formatCurrency(brandTotals.vlr_liquido_total) }}</strong>
                    </template>
                    <template v-else-if="field.key === 'lucro_total'">
                      <strong>R$ {{ formatCurrency(brandTotals.lucro_total) }}</strong>
                    </template>
                    <template v-else-if="field.key === 'margem_percentual'">
                      <strong>{{ brandTotals.margem_percentual ? parseFloat(brandTotals.margem_percentual || 0).toFixed(2) : '0.00' }}%</strong>
                    </template>
                    <template v-else-if="field.key === 'actions'">
                      <strong>-</strong>
                    </template>
                    <template v-else>
                      <strong>-</strong>
                    </template>
                  </td>
                </template>
                <template #table-busy>
                  <div class="text-center text-danger my-2">
                    <b-spinner class="align-middle"></b-spinner>
                    <strong> Carregando...</strong>
                  </div>
                </template>
                <template #cell(actions)="row">
                  <b-button 
                    size="sm" 
                    variant="link" 
                    @click.stop="toggleBrandExpand(row.item)"
                  >
                    {{ expandedBrands.has(row.item.cod_marca) ? '−' : '+' }}
                  </b-button>
                </template>
                <template #cell(vlr_liquido_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(vlr_bruto_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(total_descontos)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(custo_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(lucro_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(mkt_share)="row">
                  {{ mktShareMode === 'bruto' 
                    ? (row.item.mkt_share_bruto ? parseFloat(row.item.mkt_share_bruto || 0).toFixed(2) : '0.00')
                    : (row.item.mkt_share_lucro ? parseFloat(row.item.mkt_share_lucro || 0).toFixed(2) : '0.00')
                  }}%
                </template>
                <template #cell(margem_percentual)="row">
                  <span :class="getMarginClass(row.value)">
                    {{ row.value !== null && row.value !== undefined ? parseFloat(row.value || 0).toFixed(2) : '0.00' }}%
                  </span>
                </template>
                <template #row-details="row">
                  <b-card>
                    <b-table 
                      :items="getBrandProducts(row.item.cod_marca)" 
                      :fields="productFields"
                      small
                      :busy="loadingBrandProducts === row.item.cod_marca"
                    >
                      <template #table-busy>
                        <div class="text-center text-muted my-2">
                          <b-spinner small></b-spinner> Carregando produtos...
                        </div>
                      </template>
                      <template #cell(show_details)="productRow">
                        <b-button 
                          variant="link" 
                          size="sm" 
                          @click="toggleProductDetails(productRow.item)"
                        >
                          {{ isProductExpanded(productRow.item) ? '−' : '+' }}
                        </b-button>
                      </template>
                      <template #cell(custo_medio)="productRow">
                        <span :class="getCostClass(productRow.item)">
                          R$ {{ formatCurrency(productRow.value) }}
                        </span>
                      </template>
                      <template #cell(vlr_liquido_total)="productRow">
                        R$ {{ formatCurrency(productRow.value) }}
                      </template>
                      <template #cell(margem_percentual)="productRow">
                        <span :class="getMarginClass(productRow.value)">
                          {{ productRow.value ? parseFloat(productRow.value || 0).toFixed(2) : '0.00' }}%
                        </span>
                      </template>
                      <template #cell(des_produto)="productRow">
                        {{ removeSizeFromDescription(productRow.value) }}
                      </template>
                      <template #row-details="productRow">
                        <b-card>
                          <b-alert v-if="formatMovimentosByDate(productRow.item).length === 0 && !loadingMovimentos" show variant="info" class="mb-2">
                            <small>
                              <strong>Nenhum movimento encontrado.</strong>
                              <span v-if="!includeDevolucoesEstornos">
                                <br>Movimentos cancelados (mesmo cod_movto com E e S) são automaticamente excluídos.
                                <br>Para ver devoluções/estornos, marque a opção "Incluir Devoluções/Estornos" acima.
                              </span>
                              <span v-else>
                                <br>Nenhum movimento encontrado mesmo com devoluções/estornos incluídos.
                              </span>
                            </small>
                          </b-alert>
                          <b-table 
                            :items="formatMovimentosByDate(productRow.item)" 
                            :fields="getMovimentoFieldsForProduct(productRow.item)"
                            small
                            :busy="loadingMovimentos === getProductKey(productRow.item)"
                            bordered
                            striped
                            hover
                          >
                            <template #table-busy>
                              <div class="text-center text-muted my-2">
                                <b-spinner small></b-spinner> Carregando movimentos...
                              </div>
                            </template>
                            <template #cell(dat_emissao)="movRow">
                              {{ formatDate(movRow.value) }}
                            </template>
                            <template #cell(origem_nome)="movRow">
                              <span :class="getOrigemClass(movRow.item.cod_origem_movto)">
                                <span v-if="movRow.item.tipo_movto === 'E'" class="badge badge-success mr-1">E</span>
                                <span v-else-if="movRow.item.tipo_movto === 'S'" class="badge badge-danger mr-1">S</span>
                                {{ movRow.value || 'N/A' }}
                              </span>
                            </template>
                            <template #cell(vlr_liquido)="movRow">
                              <span v-if="movRow.value && movRow.value > 0">
                                R$ {{ formatCurrency(movRow.value) }}
                              </span>
                              <span v-else class="text-muted">-</span>
                            </template>
                            <template v-for="field in getSizeFieldsForProduct(productRow.item)" v-slot:[`cell(${field.key})`]="movRow">
                              <span :key="field.key" :class="getMovimentoClass(movRow.value)">
                                {{ movRow.value && movRow.value !== 0 ? movRow.value : '' }}
                              </span>
                            </template>
                          </b-table>
                        </b-card>
                      </template>
                    </b-table>
                  </b-card>
                </template>
              </b-table>
            </b-col>
          </b-row>
        </b-tab>

        <!-- Product Comparison -->
        <b-tab title="Produtos" @click="loadProducts">
          <b-row class="mt-3">
            <b-col md="3">
              <b-form-select v-model="selectedMarca" :options="marcaOptions" @change="loadProducts">
                <template #first>
                  <b-form-select-option :value="null">Todas as Marcas</b-form-select-option>
                </template>
              </b-form-select>
            </b-col>
          </b-row>
          <b-row class="mt-3">
            <b-col>
              <b-table 
                :items="products" 
                :fields="productFields" 
                striped 
                hover
                :busy="loading"
                show-empty
                empty-text="Nenhum dado encontrado"
                :sort-compare="sortCompareNumeric"
                :sort-by="'vlr_liquido_total'"
                :sort-desc="true"
              >
                <template #table-busy>
                  <div class="text-center text-danger my-2">
                    <b-spinner class="align-middle"></b-spinner>
                    <strong> Carregando...</strong>
                  </div>
                </template>
                <template #cell(custo_medio)="row">
                  <span :class="getCostClass(row.item)">
                    R$ {{ formatCurrency(row.value) }}
                  </span>
                </template>
                <template #cell(vlr_liquido_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(lucro_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(mkt_share)="row">
                  {{ mktShareMode === 'bruto' 
                    ? (row.item.mkt_share_bruto ? parseFloat(row.item.mkt_share_bruto || 0).toFixed(2) : '0.00')
                    : (row.item.mkt_share_lucro ? parseFloat(row.item.mkt_share_lucro || 0).toFixed(2) : '0.00')
                  }}%
                </template>
                <template #cell(margem_percentual)="row">
                  <span :class="getMarginClass(row.value)">
                    {{ row.value !== null && row.value !== undefined ? parseFloat(row.value || 0).toFixed(2) : '0.00' }}%
                  </span>
                </template>
              </b-table>
            </b-col>
          </b-row>
        </b-tab>

        <!-- Size Comparison -->
        <b-tab title="Tamanhos" @click="loadSizes">
          <b-row class="mt-3">
            <b-col>
              <b-table 
                :items="sizes" 
                :fields="sizeFields" 
                striped 
                hover
                :busy="loading"
                show-empty
                empty-text="Nenhum dado encontrado"
              >
                <template #table-busy>
                  <div class="text-center text-danger my-2">
                    <b-spinner class="align-middle"></b-spinner>
                    <strong> Carregando...</strong>
                  </div>
                </template>
                <template #cell(vlr_liquido_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
              </b-table>
            </b-col>
          </b-row>
        </b-tab>

        <!-- Collection Comparison -->
        <b-tab title="Coleções" @click="loadCollections">
          <b-row class="mt-3">
            <b-col>
              <b-table 
                :items="collections" 
                :fields="collectionFields" 
                striped 
                hover
                :busy="loading"
                show-empty
                empty-text="Nenhum dado encontrado"
              >
                <template #table-busy>
                  <div class="text-center text-danger my-2">
                    <b-spinner class="align-middle"></b-spinner>
                    <strong> Carregando...</strong>
                  </div>
                </template>
                <template #cell(vlr_liquido_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
              </b-table>
            </b-col>
          </b-row>
        </b-tab>

        <!-- Promotion Only Products (Alerts) -->
        <b-tab title="Promoção Apenas" @click="loadPromotionOnly">
          <b-alert variant="warning" show class="mt-3">
            <strong>Atenção:</strong> Estes produtos só vendem em promoção. Considere promover imediatamente.
          </b-alert>
          <b-row class="mt-3">
            <b-col>
              <b-table 
                :items="promotionOnly" 
                :fields="promotionFields" 
                striped 
                hover
                :busy="loading"
                show-empty
                empty-text="Nenhum produto encontrado"
              >
                <template #table-busy>
                  <div class="text-center text-danger my-2">
                    <b-spinner class="align-middle"></b-spinner>
                    <strong> Carregando...</strong>
                  </div>
                </template>
                <template #cell(vlr_liquido_total)="row">
                  R$ {{ formatCurrency(row.value) }}
                </template>
                <template #cell(percentual_desconto)="row">
                  <span class="text-danger font-weight-bold">
                    {{ row.value ? parseFloat(row.value || 0).toFixed(2) : '0.00' }}%
                  </span>
                </template>
              </b-table>
            </b-col>
          </b-row>
        </b-tab>
      </b-tabs>
    </b-container>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  name: 'Faturamento',
  data() {
    return {
      data_ini: moment().format('YYYY-MM-DD'),
      data_fim: moment().format('YYYY-MM-DD'),
      loading: false,
      tabIndex: 0,
      mktShareMode: 'bruto', // 'bruto' or 'lucro'
      includeDevolucoesEstornos: false, // Default: exclude devoluções/estornos
      brands: [],
      products: [],
      sizes: [],
      collections: [],
      promotionOnly: [],
      selectedMarca: null,
      marcaOptions: [],
      expandedBrands: new Set(), // Track which brands are expanded
      brandProducts: {}, // Cache products by brand
      loadingBrandProducts: null, // Track which brand is loading products
      expandedProducts: new Set(), // Track which products (referencia+cor) are expanded
      productMovimentos: {}, // Cache movimentos by referencia+cor
      loadingMovimentos: null, // Track which product is loading movimentos
      brandFields: [
        { key: 'mkt_share', label: 'Mkt. Share', sortable: true },
        { key: 'nom_marca', label: 'Marca', sortable: true },
        { key: 'total_itens', label: 'Total Itens', sortable: true },
        { key: 'custo_total', label: 'Custo Total', sortable: true },
        { key: 'vlr_bruto_total', label: 'Vlr. Fat. Bruto', sortable: true },
        { key: 'total_descontos', label: 'Descontos', sortable: true },
        { key: 'vlr_liquido_total', label: 'Vlr. Fat. Líq', sortable: true },
        { key: 'lucro_total', label: 'Lucro', sortable: true },
        { key: 'margem_total', label: 'Margem Tot.', sortable: true },
        { key: 'margem_percentual', label: 'Margem %', sortable: true },
        { key: 'actions', label: '' }
      ],
      productFields: [
        { key: 'show_details', label: '', tdClass: 'text-center' },
        { key: 'cod_referencia', label: 'Ref', sortable: true },
        { key: 'des_cor', label: 'Cor', sortable: true },
        { key: 'des_produto', label: 'Produto', sortable: true },
        { key: 'qtd_total', label: 'Qnt.', sortable: true },
        { key: 'custo_medio', label: 'Custo Médio', sortable: true },
        { key: 'vlr_liquido_total', label: 'Vlr. Fat. Líq', sortable: true },
        { key: 'margem_percentual', label: 'Margem', sortable: true },
        { key: 'nom_vendedor', label: 'Vendedor', sortable: true }
      ],
      movimentoFields: [], // Will be computed dynamically based on sizes found
      movimentoFieldsBase: [
        { key: 'dat_emissao', label: 'Data', sortable: true },
        { key: 'origem_nome', label: 'Origem', sortable: true },
        { key: 'nom_vendedor', label: 'Vendedor', sortable: true },
        { key: 'nf_interno', label: 'NF', sortable: true },
        { key: 'vlr_liquido', label: 'Vlr. Fat.', sortable: true }
      ],
      sizeFields: [
        { key: 'des_grade', label: 'Grade', sortable: true },
        { key: 'des_tamanho', label: 'Tamanho', sortable: true },
        { key: 'qtd_total', label: 'Quantidade', sortable: true },
        { key: 'vlr_liquido_total', label: 'Valor Líquido', sortable: true }
      ],
      collectionFields: [
        { key: 'colecao', label: 'Coleção', sortable: true },
        { key: 'total_notas', label: 'Total Notas', sortable: true },
        { key: 'total_itens', label: 'Total Itens', sortable: true },
        { key: 'vlr_liquido_total', label: 'Valor Líquido', sortable: true }
      ],
      promotionFields: [
        { key: 'cod_referencia', label: 'Referência', sortable: true },
        { key: 'des_produto', label: 'Produto', sortable: true },
        { key: 'nom_marca', label: 'Marca', sortable: true },
        { key: 'qtd_total', label: 'Quantidade', sortable: true },
        { key: 'vlr_liquido_total', label: 'Valor Líquido', sortable: true },
        { key: 'percentual_desconto', label: '% Desconto', sortable: true }
      ]
    }
  },
  computed: {
    brandTotals() {
      if (!this.brands || this.brands.length === 0) {
        return {
          total_itens: 0,
          custo_total: 0,
          vlr_bruto_total: 0,
          total_descontos: 0,
          vlr_liquido_total: 0,
          lucro_total: 0,
          margem_percentual: 0
        }
      }
      
      const totals = {
        total_itens: 0,
        custo_total: 0,
        vlr_bruto_total: 0,
        total_descontos: 0,
        vlr_liquido_total: 0,
        lucro_total: 0,
        margem_percentual: 0
      }
      
      this.brands.forEach(brand => {
        totals.total_itens += parseFloat(brand.total_itens || 0)
        totals.custo_total += parseFloat(brand.custo_total || 0)
        totals.vlr_bruto_total += parseFloat(brand.vlr_bruto_total || 0)
        totals.total_descontos += parseFloat(brand.total_descontos || 0)
        totals.vlr_liquido_total += parseFloat(brand.vlr_liquido_total || 0)
        totals.lucro_total += parseFloat(brand.lucro_total || 0)
      })
      
      // Calculate average margin percentage
      if (totals.vlr_liquido_total > 0) {
        totals.margem_percentual = (totals.lucro_total / totals.vlr_liquido_total) * 100
      }
      
      return totals
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        await Promise.all([
          this.loadBrands(),
          this.loadMarcaOptions()
        ])
      } catch (error) {
        console.error('Error loading data:', error)
        this.$bvToast.toast('Erro ao carregar dados', {
          title: 'Erro',
          variant: 'danger',
          solid: true
        })
      } finally {
        this.loading = false
      }
    },
    async loadBrands() {
      try {
        // Ensure dates are in YYYY-MM-DD format
        const data_ini_formatted = moment(this.data_ini).format('YYYY-MM-DD')
        const data_fim_formatted = moment(this.data_fim).format('YYYY-MM-DD')
        
        // Use template string to avoid double encoding issues
        const url = `/api/faturamento/brand?data_ini=${encodeURIComponent(data_ini_formatted)}&data_fim=${encodeURIComponent(data_fim_formatted)}`
        const response = await axios.get(url)
        console.log(`API Response for ${data_ini_formatted} to ${data_fim_formatted}:`, response.data)
        // Initialize _showDetails for each brand
        this.brands = response.data.map(brand => ({
          ...brand,
          _showDetails: this.expandedBrands.has(brand.cod_marca)
        }))
        console.log(`Loaded ${this.brands.length} brands for period ${data_ini_formatted} to ${data_fim_formatted}`)
        if (this.brands.length === 0) {
          console.warn('No brands found. Check backend logs for details.')
          console.warn('This could mean:')
          console.warn('  1. No invoices exist for this period')
          console.warn('  2. All invoices are canceled (flg_cancelado=S)')
          console.warn('  3. All invoices are devoluções (grupo_operacoes=6)')
          console.warn('  4. There is a query issue')
        }
      } catch (error) {
        console.error('Error loading brands:', error)
        throw error
      }
    },
    async loadProducts() {
      this.loading = true
      try {
        const params = {
          data_ini: moment(this.data_ini).format('YYYY-MM-DD'),
          data_fim: moment(this.data_fim).format('YYYY-MM-DD')
        }
        if (this.selectedMarca) {
          params.cod_marca = this.selectedMarca
        }
        const response = await axios.get('/api/faturamento/product', { params })
        // Mark products with default cost if needed
        // Products already have custo_is_default flag from backend
        this.products = response.data
      } catch (error) {
        console.error('Error loading products:', error)
        this.$bvToast.toast('Erro ao carregar produtos', {
          title: 'Erro',
          variant: 'danger',
          solid: true
        })
      } finally {
        this.loading = false
      }
    },
    async loadSizes() {
      this.loading = true
      try {
        const params = {
          data_ini: moment(this.data_ini).format('YYYY-MM-DD'),
          data_fim: moment(this.data_fim).format('YYYY-MM-DD')
        }
        const response = await axios.get('/api/faturamento/size', { params })
        this.sizes = response.data
      } catch (error) {
        console.error('Error loading sizes:', error)
        this.$bvToast.toast('Erro ao carregar tamanhos', {
          title: 'Erro',
          variant: 'danger',
          solid: true
        })
      } finally {
        this.loading = false
      }
    },
    async loadCollections() {
      this.loading = true
      try {
        const response = await axios.get('/api/faturamento/collection', {
          params: {
            data_ini: this.data_ini,
            data_fim: this.data_fim
          }
        })
        this.collections = response.data
      } catch (error) {
        console.error('Error loading collections:', error)
        this.$bvToast.toast('Erro ao carregar coleções', {
          title: 'Erro',
          variant: 'danger',
          solid: true
        })
      } finally {
        this.loading = false
      }
    },
    async loadPromotionOnly() {
      this.loading = true
      try {
        const response = await axios.get('/api/faturamento/promotion-only', {
          params: {
            data_ini: this.data_ini,
            data_fim: this.data_fim
          }
        })
        this.promotionOnly = response.data
      } catch (error) {
        console.error('Error loading promotion-only products:', error)
        this.$bvToast.toast('Erro ao carregar produtos em promoção', {
          title: 'Erro',
          variant: 'danger',
          solid: true
        })
      } finally {
        this.loading = false
      }
    },
    async loadMarcaOptions() {
      try {
        // Ensure dates are in YYYY-MM-DD format
        const data_ini_formatted = moment(this.data_ini).format('YYYY-MM-DD')
        const data_fim_formatted = moment(this.data_fim).format('YYYY-MM-DD')
        
        // Use template string to avoid double encoding issues
        const url = `/api/faturamento/brand?data_ini=${encodeURIComponent(data_ini_formatted)}&data_fim=${encodeURIComponent(data_fim_formatted)}`
        const response = await axios.get(url)
        this.marcaOptions = response.data.map(b => ({
          value: b.cod_marca,
          text: b.nom_marca
        }))
      } catch (error) {
        console.error('Error loading marca options:', error)
      }
    },
    formatCurrency(value) {
      if (!value) return '0.00'
      return parseFloat(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    getMarginClass(margin) {
      if (!margin && margin !== 0) return ''
      if (margin < 0) return 'text-danger font-weight-bold' // Negative margins in red
      if (margin >= 50) return 'text-success font-weight-bold'
      if (margin >= 30) return 'text-info'
      if (margin >= 10) return 'text-warning'
      return 'text-danger'
    },
    getCostClass(item) {
      // Check if cost is default (using vlr_venda1/2)
      // This happens when all cost fields (vlr_custo_bruto_medio, vlr_custo_medio, vlr_custo_aquis) are <= 1.00
      if (item.custo_is_default) {
        return 'text-warning font-weight-bold bg-warning'
      }
      return ''
    },
    toggleBrandExpand(brand) {
      const codMarca = brand.cod_marca
      if (this.expandedBrands.has(codMarca)) {
        this.expandedBrands.delete(codMarca)
        this.$set(brand, '_showDetails', false)
      } else {
        this.expandedBrands.add(codMarca)
        this.$set(brand, '_showDetails', true)
        // Load products for this brand if not already loaded
        if (!this.brandProducts[codMarca]) {
          this.loadBrandProducts(codMarca)
        }
      }
    },
    async loadBrandProducts(codMarca) {
      this.loadingBrandProducts = codMarca
      try {
        const response = await axios.get('/api/faturamento/product', {
          params: {
            data_ini: this.data_ini,
            data_fim: this.data_fim,
            cod_marca: codMarca,
            include_devolucoes_estornos: this.includeDevolucoesEstornos
          }
        })
        // Products already have custo_is_default flag from backend
        // Add _showDetails property for expandable rows
        this.brandProducts[codMarca] = response.data.map(product => ({
          ...product,
          _showDetails: this.isProductExpanded(product)
        }))
      } catch (error) {
        console.error('Error loading brand products:', error)
        this.brandProducts[codMarca] = []
      } finally {
        this.loadingBrandProducts = null
      }
    },
    getBrandProducts(codMarca) {
      return this.brandProducts[codMarca] || []
    },
    getProductKey(product) {
      return `${product.cod_referencia}_${product.cod_cor}`
    },
    isProductExpanded(product) {
      return this.expandedProducts.has(this.getProductKey(product))
    },
    toggleProductDetails(product) {
      const key = this.getProductKey(product)
      if (this.expandedProducts.has(key)) {
        this.expandedProducts.delete(key)
        this.$set(product, '_showDetails', false)
      } else {
        this.expandedProducts.add(key)
        this.$set(product, '_showDetails', true)
        // Always reload movimentos when expanding (to get latest filter state)
        this.loadProductMovimentos(product, true)
      }
    },
    async loadProductMovimentos(product, forceReload = false) {
      const key = this.getProductKey(product)
      if (!forceReload && this.productMovimentos[key] && this.loadingMovimentos !== key) {
        // Already loaded, skip
        return
      }
      this.loadingMovimentos = key
      try {
        // Ensure cod_cor is an integer
        const cod_cor = product.cod_cor ? parseInt(product.cod_cor) : null
        if (!cod_cor) {
          console.error('cod_cor is missing or invalid:', product)
          this.productMovimentos[key] = []
          return
        }
        
        const response = await axios.get('/api/faturamento/movimentos', {
          params: {
            cod_referencia: product.cod_referencia,
            cod_cor: cod_cor,
            data_ini: this.data_ini,
            data_fim: this.data_fim,
            include_devolucoes_estornos: this.includeDevolucoesEstornos
          }
        })
        this.$set(this.productMovimentos, key, response.data || [])
        console.log(`Loaded ${response.data?.length || 0} movimentos for ${product.cod_referencia} with filter=${this.includeDevolucoesEstornos}`)
      } catch (error) {
        console.error('Error loading movimentos:', error)
        this.$set(this.productMovimentos, key, [])
      } finally {
        this.loadingMovimentos = null
      }
    },
    async onFilterChange() {
      // Reload all expanded brands and their products when filter changes
      const expandedBrands = Array.from(this.expandedBrands)
      
      // Clear product cache
      this.brandProducts = {}
      this.productMovimentos = {}
      
      // Reload products for each expanded brand
      for (const codMarca of expandedBrands) {
        await this.loadBrandProducts(codMarca)
      }
      
      // Reload movimentos for expanded products
      const expandedKeys = Array.from(this.expandedProducts)
      for (const key of expandedKeys) {
        // Find the product from brandProducts
        for (const brandCod in this.brandProducts) {
          const products = this.brandProducts[brandCod] || []
          const product = products.find(p => this.getProductKey(p) === key)
          if (product) {
            await this.loadProductMovimentos(product, true)
            break
          }
        }
      }
    },
    getProductMovimentos(product) {
      const key = this.getProductKey(product)
      return this.productMovimentos[key] || []
    },
    formatMovimentosByDate(product) {
      const movimentos = this.getProductMovimentos(product)
      if (!movimentos || movimentos.length === 0) {
        return []
      }
      
      // Group by date + origem + vendedor + NF (to show separate rows for different movements)
      // But ensure same NF shows same vlr_liquido for all rows
      const nfValues = {} // Cache vlr_liquido by NF
      const groupedByDate = {}
      const allSizes = new Set()
      
      // First pass: collect NF values
      movimentos.forEach(mov => {
        const nf = mov.nf_interno
        if (nf && mov.vlr_liquido && mov.vlr_liquido > 0) {
          if (!nfValues[nf] || nfValues[nf] < mov.vlr_liquido) {
            nfValues[nf] = mov.vlr_liquido
          }
        }
      })
      
      movimentos.forEach(mov => {
        const dateKey = mov.dat_emissao ? moment(mov.dat_emissao).format('YYYY-MM-DD') : 'unknown'
        const origem = mov.origem_nome || mov.cod_origem_movto || 'N/A'
        const vendedor = mov.nom_vendedor || 'N/A'
        const nf = mov.nf_interno || mov.cod_movto || 'N/A'
        const rowKey = `${dateKey}_${origem}_${vendedor}_${nf}`
        
        if (!groupedByDate[rowKey]) {
          // Use cached NF value if available, otherwise use movimento value
          const vlr = (nf && nfValues[nf]) ? nfValues[nf] : (mov.vlr_liquido || 0)
          groupedByDate[rowKey] = {
            dat_emissao: mov.dat_emissao,
            origem_nome: origem,
            cod_origem_movto: mov.cod_origem_movto,
            tipo_movto: mov.tipo_movto,
            nom_vendedor: vendedor,
            nf_interno: nf,
            vlr_liquido: vlr,
            sizes: {}
          }
        }
        
        const size = mov.des_tamanho || 'N/A'
        allSizes.add(size)
        
        if (!groupedByDate[rowKey].sizes[size]) {
          groupedByDate[rowKey].sizes[size] = 0
        }
        // For devoluções (cod_origem_movto=4), show as positive (entrada)
        if (mov.cod_origem_movto === 4) {
          groupedByDate[rowKey].sizes[size] += Math.abs(mov.qtd_produto || 0)
        } else {
          groupedByDate[rowKey].sizes[size] += mov.qtd_produto || 0
        }
      })
      
      // Convert to array format with size columns
      const result = Object.values(groupedByDate).map(row => {
        const formattedRow = {
          dat_emissao: row.dat_emissao,
          origem_nome: row.origem_nome,
          cod_origem_movto: row.cod_origem_movto,
          tipo_movto: row.tipo_movto,
          nom_vendedor: row.nom_vendedor,
          nf_interno: row.nf_interno,
          vlr_liquido: row.vlr_liquido
        }
        
        // Add each size as a column
        allSizes.forEach(size => {
          formattedRow[size] = row.sizes[size] || 0
        })
        
        return formattedRow
      })
      
      // Sort by date descending, then by NF
      result.sort((a, b) => {
        const dateA = moment(a.dat_emissao)
        const dateB = moment(b.dat_emissao)
        if (dateB.isSame(dateA)) {
          return (b.nf_interno || 0) - (a.nf_interno || 0)
        }
        return dateB - dateA
      })
      
      return result
    },
    getSizeFieldsForProduct(product) {
      const movimentos = this.getProductMovimentos(product)
      if (!movimentos || movimentos.length === 0) {
        return []
      }
      
      const sizes = new Set()
      movimentos.forEach(mov => {
        if (mov.des_tamanho) {
          sizes.add(mov.des_tamanho)
        }
      })
      
      // Return fields for each size, sorted
      return Array.from(sizes).sort().map(size => ({
        key: size,
        label: size,
        sortable: true
      }))
    },
    getMovimentoFieldsForProduct(product) {
      const baseFields = [...this.movimentoFieldsBase]
      const sizeFields = this.getSizeFieldsForProduct(product)
      return [...baseFields, ...sizeFields]
    },
    getMovimentoClass(value) {
      if (!value || value === 0) return 'text-muted'
      return 'text-right font-weight-bold'
    },
    getOrigemClass(cod_origem_movto) {
      const classes = {
        2: 'text-primary',   // Emissão Nota Fiscal
        3: 'text-info',       // Requisição
        4: 'text-warning',    // Devolução
        7: 'text-success',   // Ent. Proc. Notas
        9: 'text-primary',   // Frente de Caixa
        12: 'text-danger',   // Estorno Proc. Notas
        15: 'text-secondary' // Condicional
      }
      return classes[cod_origem_movto] || 'text-muted'
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('pt-BR')
    },
    removeSizeFromDescription(description) {
      if (!description) return ''
      // Remove size patterns at the end:
      // 1. Numbers: " 42", " - 42", " 39-42", etc.
      // 2. Letter sizes: " M", " P", " G", " GG", " XG", " PP", etc. (single or double letters)
      // Matches patterns like " 42", " 39-42", " M", " GG", " XG", etc.
      let cleaned = description
      // First remove number sizes
      cleaned = cleaned.replace(/\s*[-–—]?\s*\d+(\s*[-–—]\s*\d+)?\s*$/, '').trim()
      // Then remove letter sizes (P, M, G, GG, XG, PP, etc. - 1-2 letters, case insensitive)
      cleaned = cleaned.replace(/\s+[A-Z]{1,2}\s*$/i, '').trim()
      return cleaned
    },
    sortCompareNumeric(a, b, key) {
      // Custom sort function for numeric fields
      const numericFields = ['vlr_bruto_total', 'vlr_liquido_total', 'custo_total', 'margem_total', 'margem_percentual', 'total_descontos', 'custo_medio', 'qtd_total', 'total_notas', 'total_itens', 'lucro_total', 'mkt_share_bruto', 'mkt_share_lucro', 'mkt_share']
      if (numericFields.includes(key)) {
        // Handle mkt_share specially - it's a computed field based on mktShareMode
        if (key === 'mkt_share') {
          const aVal = this.mktShareMode === 'bruto' 
            ? (a.mkt_share_bruto || 0) 
            : (a.mkt_share_lucro || 0)
          const bVal = this.mktShareMode === 'bruto' 
            ? (b.mkt_share_bruto || 0) 
            : (b.mkt_share_lucro || 0)
          return parseFloat(aVal) - parseFloat(bVal)
        }
        
        // Handle null, undefined, empty string, or non-numeric values
        let aVal = a[key]
        let bVal = b[key]
        
        // Convert to number, handling various formats
        if (typeof aVal === 'string') {
          // Remove currency formatting if present
          aVal = aVal.replace(/[^\d.,-]/g, '').replace(',', '.')
        }
        if (typeof bVal === 'string') {
          bVal = bVal.replace(/[^\d.,-]/g, '').replace(',', '.')
        }
        
        aVal = parseFloat(aVal) || 0
        bVal = parseFloat(bVal) || 0
        
        if (isNaN(aVal)) aVal = 0
        if (isNaN(bVal)) bVal = 0
        
        return aVal - bVal
      }
      // Default string comparison for non-numeric fields
      const aVal = a[key] || ''
      const bVal = b[key] || ''
      if (aVal < bVal) return -1
      if (aVal > bVal) return 1
      return 0
    }
  },
  mounted() {
    this.loadData()
  }
}
</script>

<style scoped>
.faturamento {
  padding: 20px;
}

.bg-warning {
  background-color: #ffc107 !important;
  color: #000 !important;
  padding: 2px 4px;
  border-radius: 3px;
}
</style>
