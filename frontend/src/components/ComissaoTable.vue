<template>
  <div class="comissao-table">
    <div class="comissao-table-inner">
        <b-row class="mb-3">
          <b-col>
            <b-form @submit.stop.prevent="recarregarComissao" inline>
              <b-button type="submit" variant="primary" class="mr-2">Recarregar</b-button>
            </b-form>
          </b-col>
          <b-col cols="auto" class="d-flex align-items-center">
            <b-form-checkbox v-model="showExtras" switch size="sm" class="mr-3">
              Obs / Ações
            </b-form-checkbox>
          </b-col>
          <b-col class="text-right">
            <b-button variant="info" size="sm" class="mr-2" @click="openEditLogByMonthModal">
              📋 Ver log de edições do mês
            </b-button>
            <b-button 
              :variant="editMode ? 'danger' : 'warning'" 
              @click="toggleEditMode"
              class="mr-2"
            >
              {{ editMode ? 'Cancelar Edição' : 'Editar Comissões' }}
            </b-button>
            <b-button 
              v-if="editMode" 
              variant="success" 
              @click="saveEdits"
              :disabled="!hasChanges"
            >
              Salvar Alterações
            </b-button>
          </b-col>
        </b-row>

      <b-table striped hover :items="items" :fields="visibleFields" class="text-right" :small=true>
        <template v-slot:cell(pos)="data">
          {{ data.index + 1}}
        </template>
        <template v-slot:cell(base_calc_comissao)="data">
          <span v-if="!editMode">{{ formatMoney(data.item.base_calc_comissao) }}</span>
          <b-form-input
            v-else
            v-model.number="data.item.base_calc_comissao_edit"
            type="number"
            step="0.01"
            size="sm"
            class="text-right"
            style="max-width: 140px;"
            @input="onBaseCalcInput(data.item)"
          ></b-form-input>
        </template>
        <template v-slot:cell(vlr_comissao)="data">
          {{ formatMoney(editMode ? data.item.vlr_comissao_edit : data.item.vlr_comissao) }}
        </template>
        <template v-slot:cell(observacao)="data">
          <span v-if="!editMode">{{ data.item.observacao }}</span>
          <b-form-input
            v-else
            v-model="data.item.observacao"
            type="text"
            size="sm"
            placeholder="Observação..."
            style="min-width: 140px;"
          ></b-form-input>
        </template>
        <template v-slot:cell(actions)="data">
          <b-button 
            v-if="data.item.alteracoes && data.item.alteracoes.length > 0"
            variant="info" 
            size="sm" 
            @click="showLog(data.item.cod_vendedor)"
          >
            Ver Histórico
          </b-button>
        </template>
      </b-table>
      
      <!-- Edit Mode Info -->
      <b-alert v-if="editMode" show variant="info" class="mt-2">
        <strong>Modo de Edição Ativo:</strong> Altere os valores de "Base Calc. Vendas" acima. 
        A comissão será calculada automaticamente como 1% da base. Adicione observações se necessário.
        As alterações serão salvas apenas no MongoDB (não afetam PostgreSQL).
        <div v-if="hasChanges" class="mt-2">
          <small>Você tem alterações não salvas.</small>
        </div>
      </b-alert>
      
      <b-alert show dismissible variant="secondary">
        <div class="text-center">Total de Vendas: <strong> {{ formatMoney(computed_sum_comissao) }}</strong></div>
      </b-alert>
      
      <!-- Edit log by month (edits made in selected month) -->
      <b-modal id="edit-log-by-month-modal" size="xl" title="Log de edições de comissão (por mês da alteração)" @show="onShowEditLogModal" @hidden="editLogByMonthPayload = null">
        <div class="pl-mb">
          <label class="pl-label">Mês</label>
          <b-row>
            <b-col cols="4">
              <b-form-select v-model="editLogMonth" :options="monthOptions" size="sm" class="pl-select" />
            </b-col>
            <b-col cols="4">
              <b-form-select v-model="editLogYear" :options="yearOptions" size="sm" class="pl-select" />
            </b-col>
            <b-col cols="4">
              <b-button size="sm" variant="primary" :disabled="editLogLoading" @click="fetchEditLogByMonth">
                <b-spinner v-if="editLogLoading" small class="mr-1" />
                {{ editLogLoading ? 'Carregando…' : 'Buscar' }}
              </b-button>
            </b-col>
          </b-row>
        </div>
        <template v-if="editLogByMonthPayload">
          <div class="pl-summary pl-mb">
            <strong>Totais da loja (vendas base):</strong>
            <span class="ml-2">Antes: {{ formatMoney(editLogByMonthPayload.total_before) }}</span>
            <span class="ml-2">→ Depois: {{ formatMoney(editLogByMonthPayload.total_after) }}</span>
          </div>
          <div v-if="editLogByMonthPayload.by_seller && editLogByMonthPayload.by_seller.length" class="pl-mb">
            <strong>Por vendedor (soma das alterações no mês)</strong>
            <b-table small striped :items="editLogByMonthPayload.by_seller" :fields="editLogBySellerFields" class="mt-2">
              <template v-slot:cell(sum_before)="data">{{ formatMoney(data.value) }}</template>
              <template v-slot:cell(sum_after)="data">{{ formatMoney(data.value) }}</template>
            </b-table>
          </div>
          <div v-if="editLogByMonthPayload.rows && editLogByMonthPayload.rows.length">
            <strong>Detalhe das alterações</strong>
            <b-table small striped hover :items="editLogByMonthPayload.rows" :fields="editLogMonthLogFields" class="mt-2" responsive>
              <template v-slot:cell(data_alteracao)="data">{{ formatDate(data.value) }}</template>
              <template v-slot:cell(base_calc_anterior)="data">{{ formatMoney(data.value) }}</template>
              <template v-slot:cell(base_calc_novo)="data">{{ formatMoney(data.value) }}</template>
              <template v-slot:cell(comissao_anterior)="data">{{ formatMoney(data.value) }}</template>
              <template v-slot:cell(comissao_novo)="data">{{ formatMoney(data.value) }}</template>
            </b-table>
          </div>
          <p v-else class="text-muted">Nenhuma edição neste mês.</p>
        </template>
        <template v-slot:modal-footer>
          <b-button variant="secondary" @click="$bvModal.hide('edit-log-by-month-modal')">Fechar</b-button>
        </template>
      </b-modal>

      <!-- Change Log Modal -->
      <b-modal 
        v-for="(item, idx) in itemsWithLogs" 
        :key="idx"
        :id="'log-modal-' + item.cod_vendedor"
        :title="'Histórico de Alterações - ' + item.nom_vendedor"
        size="lg"
      >
        <b-table 
          :items="item.alteracoes" 
          :fields="logFields" 
          small 
          striped
          :tbody-tr-class="rowClass"
        >
          <template v-slot:cell(data_alteracao)="data">
            {{ formatDate(data.value) }}
          </template>
          <template v-slot:cell(base_calc_anterior)="data">
            {{ formatMoney(data.value) }}
          </template>
          <template v-slot:cell(base_calc_novo)="data">
            {{ formatMoney(data.value) }}
          </template>
          <template v-slot:cell(comissao_anterior)="data">
            {{ formatMoney(data.value) }}
          </template>
          <template v-slot:cell(comissao_novo)="data">
            {{ formatMoney(data.value) }}
          </template>
          <template v-slot:cell(actions)="data">
            <b-button 
              variant="danger" 
              size="sm" 
              @click="excluirAlteracao(item.cod_vendedor, data.index)"
            >
              Excluir
            </b-button>
          </template>
        </b-table>
        <template v-slot:modal-footer="{ ok }">
          <b-button variant="secondary" @click="ok()">Fechar</b-button>
        </template>
      </b-modal>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import moment from "moment";

export default {
    name: 'ComissaoTable',
    props: ['data_ini', 'data_fim', 'dados_comissao'],
    data () {
    return {
      sortBy: 'base_calc_comissao',
      sortDesc: true,
      showExtras: false,
      fields: [
        {key: 'pos', label: 'Pos.'},
        {key: 'cod_vendedor', label: 'Cod. Vendedor'},
        {key: 'nom_vendedor', label: 'Nom. Vendedor'},
        {key: 'base_calc_comissao', label: 'Base Calc. Vendas'},
        {key: 'cred_dev', label: 'Cred. Dev.'},
        {key: 'vlr_comissao', label: 'Vlr. Com. (1%)'},
        {key: 'observacao', label: 'Observação', extra: true},
        {key: 'data_fim', label: 'Data'},
        {key: 'actions', label: 'Ações', thClass: 'text-center', tdClass: 'text-center', extra: true}
      ],
      items: [],
      sum_comissao: '',
      comissao_vendedores_array: [], // Initialize as empty array, will be set from prop
      editMode: false,
      logFields: [
        {key: 'data_alteracao', label: 'Data'},
        {key: 'base_calc_anterior', label: 'Base Calc. Anterior'},
        {key: 'base_calc_novo', label: 'Base Calc. Novo'},
        {key: 'comissao_anterior', label: 'Comissão Anterior'},
        {key: 'comissao_novo', label: 'Comissão Novo'},
        {key: 'observacao', label: 'Observação'},
        {key: 'actions', label: 'Ações', thClass: 'text-center', tdClass: 'text-center'}
      ],
      monthLogFields: [
        {key: 'cod_vendedor', label: 'Código'},
        {key: 'nom_vendedor', label: 'Vendedor'},
        {key: 'data_alteracao', label: 'Data'},
        {key: 'base_calc_anterior', label: 'Base Calc. Anterior'},
        {key: 'base_calc_novo', label: 'Base Calc. Novo'},
        {key: 'comissao_anterior', label: 'Comissão Anterior'},
        {key: 'comissao_novo', label: 'Comissão Novo'},
        {key: 'observacao', label: 'Observação'},
        {key: 'actions', label: 'Ações', thClass: 'text-center', tdClass: 'text-center'}
      ],
      monthLogData: [],
      editedCommissions: {}, // Store edited values from API
      editLogMonth: null,
      editLogYear: new Date().getFullYear(),
      editLogLoading: false,
      editLogByMonthPayload: null,
      editLogBySellerFields: [
        { key: 'cod_vendedor', label: 'Cód.' },
        { key: 'nom_vendedor', label: 'Vendedor' },
        { key: 'sum_before', label: 'Soma vendas antes' },
        { key: 'sum_after', label: 'Soma vendas depois' }
      ]
    }
  },
  created() {
    const d = new Date()
    this.editLogMonth = d.getMonth() + 1
    this.editLogYear = d.getFullYear()
  },
  watch: {
    dados_comissao: {
      handler(newVal) {
        if (newVal && newVal.comissao_vendedores) {
          this.comissao_vendedores_array = newVal.comissao_vendedores
          // Only load if we have dates
          if (this.data_ini && this.data_fim) {
            this.loadComissao()
          }
        }
      },
      immediate: false, // Changed to false to avoid duplicate calls
      deep: true
    },
    data_ini() {
      if (this.data_ini && this.data_fim && this.comissao_vendedores_array.length > 0) {
        this.loadComissao()
      }
    },
    data_fim() {
      if (this.data_ini && this.data_fim && this.comissao_vendedores_array.length > 0) {
        this.loadComissao()
      }
    }
  },
  beforeMount () {
    // Initialize from prop if available
    if (this.dados_comissao && this.dados_comissao.comissao_vendedores) {
      this.comissao_vendedores_array = this.dados_comissao.comissao_vendedores
    }
    // Only load if we have both dates and data
    if (this.data_ini && this.data_fim && this.comissao_vendedores_array.length > 0) {
      this.loadComissao()
    }
  },
  mounted () {
  },
  computed: {
    computed_sum_comissao() {
      let comissao_vendedores_sum = this.items.reduce(function (sum, item) {
        let itemValor = parseFloat(item.base_calc_comissao)
        if (!isNaN(itemValor)) {
          return sum + itemValor
        } else {
          return sum
        }
      }, 0)
      return comissao_vendedores_sum
    },
    computed_comissao_vendedores_array() {
      return this.comissao_vendedores_array
    },
    visibleFields() {
      if (this.showExtras) return this.fields
      return this.fields.filter(f => !f.extra)
    },
    hasChanges() {
      return this.items.some(item => {
        const baseChanged = parseFloat(item.base_calc_comissao_edit) !== parseFloat(item.base_calc_comissao_original)
        const obsChanged = (item.observacao || '') !== (item.observacao_original || '')
        return baseChanged || obsChanged
      })
    },
    itemsWithLogs() {
      return this.items.filter(item => item.alteracoes && item.alteracoes.length > 0)
    },
    monthOptions() {
      const names = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
      return names.map((n, i) => ({ value: i + 1, text: n }))
    },
    yearOptions() {
      const y = new Date().getFullYear()
      return Array.from({ length: 6 }, (_, i) => ({ value: y - i, text: String(y - i) }))
    },
    editLogMonthLogFields() {
      return this.monthLogFields.filter(f => f.key !== 'actions')
    }
  },
  methods: {
    async loadComissao () {
      // Clear items first to prevent duplicates
      this.items = []
      
      // Check if we have data to load
      if (!this.computed_comissao_vendedores_array) {
        return
      }
      
      // Handle both array and object formats
      let dataArray = []
      if (Array.isArray(this.computed_comissao_vendedores_array)) {
        dataArray = this.computed_comissao_vendedores_array
      } else if (typeof this.computed_comissao_vendedores_array === 'object') {
        // Convert object to array
        dataArray = Object.values(this.computed_comissao_vendedores_array)
      }
      
      if (dataArray.length === 0) {
        return
      }
      
      // Load edited commissions from API
      await this.loadEditedCommissions()
      
      // Use for...of for arrays - this prevents duplicate iteration
      for (const comissao_vendedor of dataArray) {
        if (!comissao_vendedor) continue // Skip null/undefined items
        
        const item = {...comissao_vendedor}
        const originalBaseCalc = parseFloat(item.base_calc_comissao) || 0
        item.base_calc_comissao_edit = originalBaseCalc
        item.base_calc_comissao_original = originalBaseCalc
        item.vlr_comissao = Math.round(originalBaseCalc * 0.01 * 100) / 100
        item.vlr_comissao_edit = item.vlr_comissao
        item.vlr_comissao_original = item.vlr_comissao
        item.observacao = ''
        item.observacao_original = ''
        item.alteracoes = []
        this.items.push(item)
      }
      
      this.items.forEach(item => {
        const cod_vendedor = item.cod_vendedor
        const edited = this.editedCommissions[cod_vendedor]
        if (edited) {
          const editedBase = edited.base_calc_comissao_editado != null
            ? edited.base_calc_comissao_editado
            : parseFloat(item.base_calc_comissao) || 0
          item.base_calc_comissao = editedBase
          item.base_calc_comissao_edit = editedBase
          item.base_calc_comissao_original = edited.base_calc_comissao_original || item.base_calc_comissao_original
          item.vlr_comissao = Math.round(editedBase * 0.01 * 100) / 100
          item.vlr_comissao_edit = item.vlr_comissao
          item.vlr_comissao_original = item.vlr_comissao
          item.observacao = edited.observacao || ''
          item.observacao_original = edited.observacao || ''
          item.alteracoes = edited.alteracoes || []
        }
      })
    },
    async loadEditedCommissions() {
      // Only load if data_ini and data_fim are defined
      if (!this.data_ini || !this.data_fim) {
        this.editedCommissions = {}
        return
      }
      try {
        const path = `/api/comissao/edit/${this.data_ini}/${this.data_fim}`
        const response = await axios.get(path)
        this.editedCommissions = response.data || {}
      } catch (error) {
        console.warn('Could not load edited commissions:', error)
        this.editedCommissions = {}
      }
    },
    toggleEditMode() {
      if (this.editMode && this.hasChanges) {
        if (!confirm('Você tem alterações não salvas. Deseja realmente cancelar?')) {
          return
        }
        // Reset to original values
        this.items.forEach(item => {
          item.base_calc_comissao_edit = item.base_calc_comissao_original || parseFloat(item.base_calc_comissao) || 0
          item.vlr_comissao_edit = item.vlr_comissao_original || parseFloat(item.vlr_comissao) || 0
          item.observacao = item.observacao_original || ''
        })
      }
      this.editMode = !this.editMode
    },
    onBaseCalcInput(item) {
      const baseCalc = parseFloat(item.base_calc_comissao_edit) || 0
      this.$set(item, 'vlr_comissao_edit', Math.round(baseCalc * 0.01 * 100) / 100)
    },
    async saveEdits() {
      // Check if data_ini and data_fim are defined
      if (!this.data_ini || !this.data_fim) {
        alert('Datas não definidas. Não é possível salvar alterações.')
        return
      }
      
      // Find items that actually changed by comparing to originals
      const edits = {}
      this.items.forEach(item => {
        const baseChanged = parseFloat(item.base_calc_comissao_edit) !== parseFloat(item.base_calc_comissao_original)
        const obsChanged = (item.observacao || '') !== (item.observacao_original || '')
        if (baseChanged || obsChanged) {
          const baseCalc = parseFloat(item.base_calc_comissao_edit) || 0
          edits[item.cod_vendedor] = {
            base_calc_comissao: baseCalc,
            vlr_comissao: Math.round(baseCalc * 0.01 * 100) / 100,
            observacao: item.observacao || ''
          }
        }
      })
      
      if (Object.keys(edits).length === 0) {
        alert('Nenhuma alteração para salvar')
        return
      }
      
      try {
        const path = `/api/comissao/edit/${this.data_ini}/${this.data_fim}`
        await axios.put(path, edits)
        
        // Update originals to match saved values
        this.items.forEach(item => {
          item.base_calc_comissao = item.base_calc_comissao_edit
          item.base_calc_comissao_original = item.base_calc_comissao_edit
          item.vlr_comissao = item.vlr_comissao_edit
          item.vlr_comissao_original = item.vlr_comissao_edit
          item.observacao_original = item.observacao || ''
        })
        await this.loadEditedCommissions()
        // Reload items with updated logs
        this.items.forEach(item => {
          const cod_vendedor = item.cod_vendedor
          const edited = this.editedCommissions[cod_vendedor]
          if (edited) {
            item.alteracoes = edited.alteracoes || []
          }
        })
        alert('Alterações salvas com sucesso!')
      } catch (error) {
        console.error('Error saving edits:', error)
        alert('Erro ao salvar alterações: ' + (error.response?.data?.detail || error.message))
      }
    },
    formatMoney(value) {
      if (!value && value !== 0) return 'R$ 0,00'
      const num = typeof value === 'string' ? parseFloat(value) : value
      return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num)
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      return moment(dateStr).format('DD/MM/YYYY HH:mm')
    },
    showLog(cod_vendedor) {
      this.$bvModal.show('log-modal-' + cod_vendedor)
    },
    onShowEditLogModal() {
      if (this.editLogMonth == null) this.editLogMonth = new Date().getMonth() + 1
      if (!this.editLogYear) this.editLogYear = new Date().getFullYear()
      this.fetchEditLogByMonth()
    },
    async fetchEditLogByMonth() {
      this.editLogLoading = true
      this.editLogByMonthPayload = null
      try {
        const res = await axios.get('/api/comissao/edit-log-by-month', { params: { year: this.editLogYear, month: this.editLogMonth } })
        this.editLogByMonthPayload = res.data
      } catch (e) {
        console.error(e)
        this.editLogByMonthPayload = { rows: [], by_seller: [], total_before: 0, total_after: 0 }
      }
      this.editLogLoading = false
    },
    openEditLogByMonthModal() {
      this.$bvModal.show('edit-log-by-month-modal')
    },
    async excluirAlteracao(cod_vendedor, alteracaoIndex) {
      if (!confirm('Deseja realmente excluir esta alteração do histórico?')) {
        return
      }
      
      if (!this.data_ini || !this.data_fim) {
        alert('Datas não definidas. Não é possível excluir alteração.')
        return
      }
      
      try {
        const response = await axios.delete(`/api/comissao/edit/alteracao/${this.data_ini}/${this.data_fim}/${cod_vendedor}/${alteracaoIndex}`)
        if (response.data.status === 'success') {
          // Reload the commission data
          await this.loadEditedCommissions()
          await this.loadComissao()
          // Reload month log if it's open
          if (this.monthLogData.length > 0) {
            await this.loadMonthLog()
          }
          alert('Alteração excluída com sucesso!')
        }
      } catch (error) {
        console.error('Error excluding alteration:', error)
        alert('Erro ao excluir alteração: ' + (error.response?.data?.detail || error.message))
      }
    },
    async showMonthLog() {
      if (!this.data_ini || !this.data_fim) {
        alert('Datas não definidas. Não é possível carregar o log.')
        return
      }
      
      await this.loadMonthLog()
      this.$bvModal.show('month-log-modal')
    },
    async loadMonthLog() {
      if (!this.data_ini || !this.data_fim) {
        this.monthLogData = []
        return
      }
      
      try {
        const response = await axios.get(`/api/comissao/edit/log/${this.data_ini}/${this.data_fim}`)
        // Flatten the log data - each alteration becomes a row with vendedor info
        this.monthLogData = []
        for (const [cod_vendedor_str, data] of Object.entries(response.data)) {
          const cod_vendedor = parseInt(cod_vendedor_str)
          const item = this.items.find(i => i.cod_vendedor === cod_vendedor)
          const nom_vendedor = item ? item.nom_vendedor : `Vendedor ${cod_vendedor}`
          
          if (data.alteracoes && Array.isArray(data.alteracoes)) {
            data.alteracoes.forEach((alt, idx) => {
              this.monthLogData.push({
                cod_vendedor: cod_vendedor,
                nom_vendedor: nom_vendedor,
                alteracao_index: idx,
                data_alteracao: alt.data_alteracao,
                base_calc_anterior: alt.base_calc_anterior,
                base_calc_novo: alt.base_calc_novo,
                comissao_anterior: alt.comissao_anterior,
                comissao_novo: alt.comissao_novo,
                observacao: alt.observacao || ''
              })
            })
          }
        }
        // Sort by date (most recent first)
        this.monthLogData.sort((a, b) => {
          const dateA = new Date(a.data_alteracao)
          const dateB = new Date(b.data_alteracao)
          return dateB - dateA
        })
      } catch (error) {
        console.error('Error loading month log:', error)
        this.monthLogData = []
      }
    },
    rowClass(item, type) {
      if (!item || type !== 'row') return
      return 'table-info'
    },
    recarregarComissao() {
      if (!this.data_ini || !this.data_fim) {
        alert('Datas não definidas. Não é possível recarregar.')
        return
      }
      const path = `/api/comissao/delete/${this.data_ini}`
      axios.delete(path)
        .then(() => {
            const path = `/api/comissao/${this.data_ini}/${this.data_fim}`
            axios.get(path)
                .then((res) => {
                if (res.data && res.data.comissao_vendedores) {
                  this.comissao_vendedores_array = res.data.comissao_vendedores
                  this.loadComissao()
                }
                })
                .catch((error) => {
                console.log(error)
        })})
        .catch((error) => {
          console.log(error)
        })
      }
  }
}

</script>

<style scoped>
.pl-mb { margin-bottom: 14px; }
.pl-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 6px; display: block; }
.pl-select { max-width: 100%; }
.pl-summary { padding: 10px 12px; background: #f1f5f9; border-radius: 8px; font-size: 14px; }
</style>
