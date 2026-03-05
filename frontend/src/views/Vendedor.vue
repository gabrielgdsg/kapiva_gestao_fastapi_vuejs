<template>
  <div class="page-layout vendedor-admin">
    <div class="page-header">
      <h1 class="page-title">Vendedores</h1>
      <div class="page-subtitle">Gerencie vendedores, links de acesso e metas</div>
    </div>
    <div class="page-main">
    <b-container fluid>
      <b-row class="mb-3 align-items-center">
        <b-col cols="auto" class="ml-auto">
          <b-button variant="primary" size="sm" @click="generateSlugs" :disabled="generating">
            {{ generating ? 'Gerando...' : 'Gerar Links Faltantes' }}
          </b-button>
        </b-col>
      </b-row>

      <!-- Filter Tabs -->
      <b-card no-body class="mb-3">
        <b-card-header class="d-flex align-items-center justify-content-between py-2">
          <div class="d-flex align-items-center" style="gap:12px;">
            <b-button
              :variant="filterMode === 'active' ? 'primary' : 'outline-secondary'"
              size="sm"
              @click="filterMode = 'active'"
            >
              Ativos no mês ({{ activeCount }})
            </b-button>
            <b-button
              :variant="filterMode === 'all' ? 'primary' : 'outline-secondary'"
              size="sm"
              @click="filterMode = 'all'; loadAllVendedores()"
            >
              Todos ({{ allCount }})
            </b-button>
          </div>
          <div class="d-flex align-items-center" style="gap:8px;">
            <label class="mb-0 small text-muted">Mês:</label>
            <b-form-select v-model="selectedMes" :options="mesOptions" size="sm" style="width:120px;" @change="loadActiveSellers"></b-form-select>
            <b-form-select v-model="selectedAno" :options="anoOptions" size="sm" style="width:90px;" @change="loadActiveSellers"></b-form-select>
          </div>
        </b-card-header>

        <b-table
          :items="filteredVendedores"
          :fields="tableFields"
          striped
          hover
          responsive
          :busy="loading"
          show-empty
          empty-text="Nenhum vendedor encontrado"
          :sort-by.sync="sortBy"
          :sort-desc.sync="sortDesc"
          small
        >
          <template #table-busy>
            <div class="text-center text-primary my-3">
              <b-spinner class="align-middle"></b-spinner>
              <strong class="ml-2">Carregando...</strong>
            </div>
          </template>

          <template #cell(nom_vendedor)="row">
            <div>
              <strong>{{ row.value }}</strong>
              <b-badge v-if="isActiveThisMonth(row.item.cod_vendedor)" variant="success" class="ml-1" pill>ativo</b-badge>
            </div>
          </template>

          <template #cell(total_vendas)="row">
            <span v-if="row.value > 0" class="font-weight-bold">R$ {{ formatCurrency(row.value) }}</span>
            <span v-else class="text-muted">—</span>
          </template>

          <template #cell(link)="row">
            <div v-if="row.item.slug" class="d-flex align-items-center" style="gap:6px;">
              <code class="small" style="background:#f0f2f5; padding:2px 8px; border-radius:4px; user-select:all;">
                /painel/{{ row.item.slug }}
              </code>
              <b-button
                variant="outline-primary"
                size="sm"
                style="padding:1px 6px; font-size:11px;"
                @click="copyLink(row.item.slug)"
                v-b-tooltip.hover
                title="Copiar link completo"
              >
                📋
              </b-button>
              <b-button
                variant="outline-secondary"
                size="sm"
                style="padding:1px 6px; font-size:11px;"
                @click="openPainel(row.item.slug)"
                v-b-tooltip.hover
                title="Abrir painel"
              >
                🔗
              </b-button>
              <b-button
                variant="outline-warning"
                size="sm"
                style="padding:1px 6px; font-size:11px;"
                @click="regenerateSlug(row.item.cod_vendedor)"
                v-b-tooltip.hover
                title="Gerar novo link"
              >
                🔄
              </b-button>
            </div>
            <div v-else>
              <b-button variant="outline-primary" size="sm" @click="regenerateSlug(row.item.cod_vendedor)">
                Gerar Link
              </b-button>
            </div>
          </template>

          <template #cell(actions)="row">
            <b-button
              variant="info"
              size="sm"
              @click="openMetasModal(row.item)"
            >
              Metas
            </b-button>
          </template>
        </b-table>
      </b-card>

      <!-- Metas Modal -->
      <b-modal v-model="showMetasModal" :title="metasModalTitle" size="lg" @ok="saveMetasFromModal" ok-title="Salvar" cancel-title="Cancelar">
        <div v-if="metasModalVendedor">
          <b-row class="mb-3">
            <b-col sm="4">
              <label class="small text-muted">Ano</label>
              <b-form-select v-model="metasModalAno" :options="anoOptions" size="sm" @change="loadMetasForModal"></b-form-select>
            </b-col>
          </b-row>
          <b-table
            :items="metasModalConfig"
            :fields="metasModalFields"
            small
            striped
          >
            <template #cell(mes_nome)="row">
              {{ row.value }}
            </template>
            <template #cell(vlr_liquido_total)="row">
              <span v-if="row.value > 0">R$ {{ formatCurrency(row.value) }}</span>
              <span v-else class="text-muted">—</span>
            </template>
            <template #cell(meta_1_2)="row">
              <b-form-input v-model.number="row.item.meta_1_2" type="number" step="0.01" placeholder="0.00" size="sm"></b-form-input>
            </template>
            <template #cell(meta_1_5)="row">
              <b-form-input v-model.number="row.item.meta_1_5" type="number" step="0.01" placeholder="0.00" size="sm"></b-form-input>
            </template>
          </b-table>
        </div>
      </b-modal>
    </b-container>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Vendedor',
  data() {
    const hoje = new Date()
    return {
      loading: false,
      generating: false,
      filterMode: 'active',
      selectedAno: hoje.getFullYear(),
      selectedMes: hoje.getMonth() + 1,
      sortBy: 'total_vendas',
      sortDesc: true,
      activeSellers: [],
      allVendedores: [],
      allVendedoresLoaded: false,
      slugMap: {},
      showMetasModal: false,
      metasModalVendedor: null,
      metasModalAno: hoje.getFullYear(),
      metasModalConfig: [],
      metasModalFields: [
        { key: 'mes_nome', label: 'Mês' },
        { key: 'vlr_liquido_total', label: 'Vendas', sortable: false },
        { key: 'meta_1_2', label: 'Meta 1.2x' },
        { key: 'meta_1_5', label: 'Meta 1.5x' },
      ],
    }
  },
  computed: {
    anoOptions() {
      const cur = new Date().getFullYear()
      const opts = []
      for (let y = 2020; y <= cur + 1; y++) opts.push({ value: y, text: y.toString() })
      return opts
    },
    mesOptions() {
      const meses = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
      return meses.map((m, i) => ({ value: i + 1, text: m }))
    },
    tableFields() {
      return [
        { key: 'cod_vendedor', label: 'Cód.', sortable: true, thStyle: 'width:70px' },
        { key: 'nom_vendedor', label: 'Vendedor', sortable: true },
        { key: 'total_vendas', label: 'Vendas Mês', sortable: true, thStyle: 'width:140px' },
        { key: 'link', label: 'Link do Painel', sortable: false },
        { key: 'actions', label: '', thStyle: 'width:80px' },
      ]
    },
    activeCount() {
      return this.activeSellers.length
    },
    allCount() {
      return this.allVendedoresLoaded ? this.allVendedores.length : '...'
    },
    activeCods() {
      return new Set(this.activeSellers.map(s => s.cod_vendedor))
    },
    filteredVendedores() {
      if (this.filterMode === 'active') {
        return this.activeSellers.map(s => ({ ...s, slug: this.slugMap[s.cod_vendedor] || null }))
      }
      return this.allVendedores.map(v => {
        const active = this.activeSellers.find(a => a.cod_vendedor === v.cod_vendedor)
        return {
          ...v,
          total_vendas: active ? active.total_vendas : 0,
          slug: this.slugMap[v.cod_vendedor] || null,
        }
      })
    },
    metasModalTitle() {
      if (!this.metasModalVendedor) return 'Metas'
      return `Metas — ${this.metasModalVendedor.nom_vendedor} (${this.metasModalVendedor.cod_vendedor})`
    },
  },
  methods: {
    isActiveThisMonth(cod) {
      return this.activeCods.has(cod)
    },
    formatCurrency(val) {
      if (!val && val !== 0) return '0,00'
      return parseFloat(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    async loadActiveSellers() {
      this.loading = true
      try {
        const resp = await axios.get('/api/vendedor/ativos-mes', {
          params: { ano: this.selectedAno, mes: this.selectedMes }
        })
        this.activeSellers = resp.data || []
      } catch (e) {
        console.error('Error loading active sellers:', e)
        this.activeSellers = []
      } finally {
        this.loading = false
      }
    },
    async loadAllVendedores() {
      if (this.allVendedoresLoaded) return
      this.loading = true
      try {
        const resp = await axios.get('/api/vendedor/ativos')
        this.allVendedores = (resp.data || []).map(v => ({
          cod_vendedor: v.cod_vendedor,
          nom_vendedor: v.nom_vendedor,
          total_vendas: 0,
        }))
        this.allVendedoresLoaded = true
      } catch (e) {
        console.error('Error loading all vendedores:', e)
      } finally {
        this.loading = false
      }
    },
    async loadSlugs() {
      try {
        const resp = await axios.get('/api/painel/slugs')
        const map = {}
        for (const s of (resp.data || [])) {
          map[s.cod_vendedor] = s.slug
        }
        this.slugMap = map
      } catch (e) {
        console.error('Error loading slugs:', e)
      }
    },
    async generateSlugs() {
      this.generating = true
      try {
        const resp = await axios.post('/api/painel/slugs/generate')
        this.$bvToast.toast(`${resp.data.created} links gerados`, { title: 'Sucesso', variant: 'success', solid: true })
        await this.loadSlugs()
      } catch (e) {
        console.error('Error generating slugs:', e)
        this.$bvToast.toast('Erro ao gerar links', { title: 'Erro', variant: 'danger', solid: true })
      } finally {
        this.generating = false
      }
    },
    async regenerateSlug(cod_vendedor) {
      try {
        const resp = await axios.post(`/api/painel/slugs/${cod_vendedor}`)
        this.$set(this.slugMap, cod_vendedor, resp.data.slug)
        this.$bvToast.toast(`Link gerado: /painel/${resp.data.slug}`, { title: 'Sucesso', variant: 'success', solid: true })
      } catch (e) {
        console.error('Error regenerating slug:', e)
        this.$bvToast.toast('Erro ao gerar link', { title: 'Erro', variant: 'danger', solid: true })
      }
    },
    copyLink(slug) {
      const url = `${window.location.origin}/painel/${slug}`
      navigator.clipboard.writeText(url).then(() => {
        this.$bvToast.toast(`Link copiado: ${url}`, { title: 'Copiado', variant: 'info', solid: true, autoHideDelay: 2000 })
      }).catch(() => {
        prompt('Copie o link:', url)
      })
    },
    openPainel(slug) {
      const route = this.$router.resolve({ path: `/painel/${slug}` })
      window.open(route.href, '_blank')
    },
    async openMetasModal(vendedor) {
      this.metasModalVendedor = vendedor
      this.metasModalAno = this.selectedAno
      this.showMetasModal = true
      await this.loadMetasForModal()
    },
    async loadMetasForModal() {
      if (!this.metasModalVendedor) return
      const cod = this.metasModalVendedor.cod_vendedor
      const ano = this.metasModalAno
      const meses = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

      let monthlySales = []
      try {
        const resp = await axios.get(`/api/vendedor/${cod}/vendas/monthly`, { params: { ano } })
        monthlySales = resp.data || []
      } catch (e) { /* ok */ }
      const salesMap = {}
      for (const s of monthlySales) {
        salesMap[parseInt(s.mes)] = parseFloat(s.vlr_liquido_total) || 0
      }

      let savedMetas = []
      try {
        const resp = await axios.get(`/api/vendedor/${cod}/metas`, { params: { ano } })
        savedMetas = (resp.data && resp.data.metas_mensais) || []
      } catch (e) { /* ok */ }
      const metaMap = {}
      for (const m of savedMetas) {
        metaMap[m.mes] = { meta_1_2: m.meta_1_2, meta_1_5: m.meta_1_5 }
      }

      this.metasModalConfig = []
      for (let mes = 1; mes <= 12; mes++) {
        const existing = metaMap[mes] || {}
        this.metasModalConfig.push({
          mes,
          mes_nome: meses[mes - 1],
          vlr_liquido_total: salesMap[mes] || 0,
          meta_1_2: existing.meta_1_2 ? parseFloat(existing.meta_1_2) : 0,
          meta_1_5: existing.meta_1_5 ? parseFloat(existing.meta_1_5) : 0,
        })
      }
    },
    async saveMetasFromModal() {
      if (!this.metasModalVendedor) return
      const cod = this.metasModalVendedor.cod_vendedor
      const metas = this.metasModalConfig.map(m => ({
        mes: m.mes,
        ano: this.metasModalAno,
        meta_1_2: m.meta_1_2 || 0,
        meta_1_5: m.meta_1_5 || 0,
      }))
      try {
        await axios.post(`/api/vendedor/${cod}/metas`, metas)
        this.$bvToast.toast('Metas salvas com sucesso', { title: 'Sucesso', variant: 'success', solid: true })
      } catch (e) {
        console.error('Error saving metas:', e)
        this.$bvToast.toast('Erro ao salvar metas', { title: 'Erro', variant: 'danger', solid: true })
      }
    },
  },
  async mounted() {
    await Promise.all([this.loadActiveSellers(), this.loadSlugs()])
  },
}
</script>

<style scoped>
.vendedor-admin {
  padding: 20px;
}
</style>
