<template>
  <div class="page-layout clientes-page">
    <div class="page-header">
      <h1 class="page-title">Clientes</h1>
      <div class="page-subtitle">Gestão de clientes, inadimplência e crediário · {{ lastUpdate || 'Carregando...' }}</div>
    </div>
    <div class="page-main">
      <b-nav pills class="mb-3 clientes-nav-pills">
        <b-nav-item
          v-for="item in navItems"
          :key="item.id"
          :active="section === item.id"
          @click="section = item.id"
        >
          {{ item.icon }} {{ item.label }}
          <b-badge v-if="item.badge" :variant="item.id === 'perdidos' ? 'danger' : 'secondary'" class="ml-1">{{ item.badge }}</b-badge>
        </b-nav-item>
      </b-nav>

      <div v-if="loading" class="clientes-loading">
        <b-spinner /> Carregando...
      </div>

      <!-- OVERVIEW -->
      <div v-else-if="section === 'overview'" class="clientes-section">
        <div class="clientes-s-title">📊 Visão Geral</div>
        <div class="clientes-kpi-grid">
          <div class="clientes-kpi-card">
            <div class="clientes-kpi-icon">👥</div>
            <div class="clientes-kpi-label">Total Clientes</div>
            <div class="clientes-kpi-value">{{ kpis.total_clientes_ativos || 0 }}</div>
            <div class="clientes-kpi-sub">{{ (kpis.clientes_com_divida || 0) - (kpis.clientes_inadimplentes || 0) }} adimplentes</div>
          </div>
          <div class="clientes-kpi-card">
            <div class="clientes-kpi-icon">📉</div>
            <div class="clientes-kpi-label">Taxa Inadimplência</div>
            <div class="clientes-kpi-value">{{ taxaMedia }}%</div>
            <div class="clientes-kpi-sub">{{ taxaMediaSub }}</div>
          </div>
          <div class="clientes-kpi-card">
            <div class="clientes-kpi-icon">⛔</div>
            <div class="clientes-kpi-label">Baixa de Crédito</div>
            <div class="clientes-kpi-value">{{ fmt(writeoffsSummary.total_perdido || 0) }}</div>
            <div class="clientes-kpi-sub">{{ writeoffsClientes.length }} clientes</div>
          </div>
          <div class="clientes-kpi-card">
            <div class="clientes-kpi-icon">💹</div>
            <div class="clientes-kpi-label">Juros Recebidos</div>
            <div class="clientes-kpi-value">{{ fmt(kpis.total_juros_recebidos || 0) }}</div>
            <div class="clientes-kpi-sub">total acumulado</div>
          </div>
        </div>

        <div class="clientes-panel" v-if="inadimplenciaHistory.length">
          <div class="clientes-panel-title">
            📉 Taxa de Inadimplência
            <b-form-select v-model="inadimplenciaMeses" size="sm" :options="inadimplenciaMesesOptions" class="clientes-inad-select" @change="loadInadimplencia" />
            <b-form-select v-model="inadimplenciaSortMode" size="sm" :options="inadimplenciaSortOptions" class="clientes-inad-select" />
          </div>
          <div class="clientes-chart-wrap">
            <div v-for="(m, i) in inadimplenciaSorted" :key="i" class="clientes-bar-row clientes-bar-click" @click="openInadimplenciaMonth(m)">
              <span class="clientes-bar-label">{{ m.period }}</span>
              <div class="clientes-bar-track">
                <div class="clientes-bar-fill" :style="{ width: Math.min(100, (m.taxa_inadimplencia || 0) * 8) + '%', background: '#DC2626' }" />
              </div>
              <span class="clientes-bar-val">{{ (m.taxa_inadimplencia || 0).toFixed(1) }}%</span>
              <span class="clientes-bar-raw">{{ fmt(m.vlr_vencido || 0) }}</span>
            </div>
          </div>
          <div v-if="selectedMonthDevedores !== null" class="clientes-month-devedores mt-3">
            <h6 class="mb-2">👥 Clientes em atraso — {{ selectedMonthLabel }}</h6>
            <div v-for="c in selectedMonthDevedores" :key="c.cod_cliente" class="clientes-card clientes-card-atraso" @click="openCliente(c.cod_cliente)">
              <div class="clientes-card-row">
                <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
                <span class="clientes-card-val danger">{{ fmt(c.vlr_vencido || 0) }}</span>
              </div>
              <div class="clientes-card-sub">{{ c.telefone }} · {{ c.dias_em_atraso || 0 }} dias</div>
            </div>
            <b-button size="sm" variant="outline-secondary" @click="selectedMonthDevedores = null; selectedMonthPeriod = null">✕ Fechar</b-button>
          </div>
        </div>

        <div class="clientes-panel">
          <div class="clientes-panel-title">⚠️ Maiores devedores ativos</div>
          <div v-for="c in topDevedores.slice(0, 5)" :key="c.cod_cliente" class="clientes-card clientes-card-click" @click="openCliente(c.cod_cliente)">
            <div class="clientes-card-row">
              <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
              <span class="clientes-card-val danger">{{ fmt(c.vlr_vencido || 0) }}</span>
            </div>
            <div class="clientes-card-sub">{{ c.telefone }} · {{ c.dias_em_atraso || 0 }} dias</div>
          </div>
        </div>
      </div>

      <!-- INADIMPLÊNCIA -->
      <div v-else-if="section === 'inadimplencia'" class="clientes-section">
        <div class="clientes-s-title">📉 Radar de Inadimplência</div>
        <div v-for="c in topDevedores" :key="c.cod_cliente" class="clientes-card clientes-card-atraso" @click="openCliente(c.cod_cliente)">
          <div class="clientes-card-row">
            <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
            <span class="clientes-card-val danger">{{ fmt(c.vlr_vencido || 0) }}</span>
          </div>
          <div class="clientes-card-sub">{{ c.telefone }} · {{ c.dias_em_atraso || 0 }} dias em atraso</div>
          <div class="clientes-card-actions">
            <b-button size="sm" variant="success">📲 WhatsApp</b-button>
            <b-button size="sm" variant="outline-primary">📋 Acordo</b-button>
          </div>
        </div>
      </div>

      <!-- BAIXA DE CRÉDITO -->
      <div v-else-if="section === 'perdidos'" class="clientes-section">
        <div class="clientes-s-title">⛔ Baixa de Crédito — Clientes Perdidos</div>
        <div class="clientes-alert danger">
          <div><strong>TOTAL PERDIDO</strong> {{ fmt(writeoffsSummary.total_perdido || 0) }}</div>
          <div><strong>CLIENTES</strong> {{ writeoffsClientes.length }}</div>
          <div><strong>VS JUROS</strong> {{ fmt(writeoffsSummary.total_juros_recebidos_geral || 0) }}</div>
        </div>
        <div v-for="c in writeoffsClientes" :key="c.cod_cliente" class="clientes-card clientes-card-perdido" @click="openCliente(c.cod_cliente)">
          <div class="clientes-card-row">
            <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
            <span class="clientes-card-val danger">{{ fmt(c.vlr_perdido || 0) }}</span>
          </div>
          <div class="clientes-card-sub">{{ c.telefone }} · {{ c.parcelas_perdidas }} parcelas</div>
          <div class="clientes-card-actions">
            <b-button size="sm" variant="outline-danger" @click.stop="registrarWriteoff(c.cod_cliente)">📋 Registrar Baixa</b-button>
          </div>
        </div>
      </div>

      <!-- VIP -->
      <div v-else-if="section === 'vip'" class="clientes-section">
        <div class="clientes-s-title">⭐ Clientes VIP</div>
        <div class="clientes-filters mb-3">
          <label class="clientes-filter-label">Período:</label>
          <b-form-select v-model="vipRange" size="sm" :options="vipRangeOptions" class="clientes-range-select" @change="loadVip" />
        </div>
        <div v-for="(c, i) in clientesVip" :key="c.cod_cliente" class="clientes-card clientes-card-vip" @click="openCliente(c.cod_cliente)">
          <div class="clientes-card-row">
            <span class="clientes-card-rank">#{{ i + 1 }}</span>
            <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
            <span class="clientes-card-val success">{{ fmt(c.ltv || 0) }}</span>
          </div>
          <div class="clientes-card-sub">{{ c.total_compras }} compras · Ticket {{ fmt(Math.round((c.ticket_medio || 0))) }}</div>
        </div>
      </div>

      <!-- ANIVERSARIANTES -->
      <div v-else-if="section === 'aniversariantes'" class="clientes-section">
        <div class="clientes-s-title">🎂 Aniversariantes — {{ mesAtualNome }}</div>
        <div v-if="aniversariantes.length === 0" class="clientes-empty">Nenhum aniversariante este mês</div>
        <div v-for="c in aniversariantes" :key="c.cod_cliente" class="clientes-card clientes-card-aniv" @click="openCliente(c.cod_cliente)">
          <div class="clientes-card-row">
            <span class="clientes-card-icon">🎂</span>
            <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
            <span class="clientes-card-val">Dia {{ c.dia_nascto || '-' }}</span>
          </div>
          <div class="clientes-card-sub">{{ c.telefone }} · {{ c.cidade }}</div>
        </div>
      </div>

      <!-- TODOS -->
      <div v-else-if="section === 'todos'" class="clientes-section">
        <div class="clientes-s-title">👥 Todos os Clientes</div>
        <div class="clientes-filters">
          <b-form-input v-model="search" placeholder="🔍 Buscar nome ou telefone..." size="sm" class="clientes-search" />
        </div>
        <div v-for="c in clientesLista" :key="c.cod_cliente" class="clientes-card" @click="openCliente(c.cod_cliente)">
          <div class="clientes-card-row">
            <span class="clientes-card-name">{{ clienteDisplayName(c) }}</span>
            <span class="clientes-card-val success">{{ fmt(c.total_gasto || 0) }}</span>
          </div>
          <div class="clientes-card-sub">{{ c.telefone }} · {{ c.cidade }} · Ticket {{ fmt(Math.round(c.ticket_medio || 0)) }}</div>
        </div>
        <div v-if="clientesLista.length === 0 && !loadingLista" class="clientes-empty">Nenhum cliente encontrado</div>
      </div>
    </div>

    <!-- Modal detalhe do cliente -->
    <b-modal v-model="modalShow" size="xl" title="Detalhe do Cliente" hide-footer @hidden="selectedCliente = null" scrollable>
      <div v-if="clienteDetail" class="clientes-modal">
        <div class="clientes-modal-header">
          <div class="clientes-modal-avatar">{{ initials }}</div>
          <div class="flex-grow-1">
            <div class="clientes-modal-name">{{ clienteDisplayName(clienteDetail.cliente) }}</div>
            <div class="clientes-modal-sub">{{ clienteDetail.cliente?.telefone }} · {{ clienteDetail.cliente?.cidade }}</div>
            <div class="clientes-modal-tags">
              <span v-for="t in (clienteDetail.score?.tags || [])" :key="t" class="clientes-tag">{{ t }}</span>
            </div>
          </div>
          <div class="clientes-modal-score" :class="scoreClass">{{ clienteDetail.score?.grade || '-' }}</div>
        </div>
        <div class="clientes-modal-stats">
          <div class="clientes-modal-stat"><span class="label">Total Gasto</span><span class="val">{{ fmt(clienteDetail.stats?.total_gasto || 0) }}</span></div>
          <div class="clientes-modal-stat"><span class="label">Compras</span><span class="val">{{ clienteDetail.stats?.total_compras || 0 }}</span></div>
          <div class="clientes-modal-stat"><span class="label">Ticket Médio</span><span class="val">{{ fmt(clienteDetail.stats?.ticket_medio || 0) }}</span></div>
          <div class="clientes-modal-stat"><span class="label">Em Aberto</span><span class="val">{{ fmt(clienteDetail.stats?.vlr_aberto || 0) }}</span></div>
          <div class="clientes-modal-stat"><span class="label">Vencido</span><span class="val danger">{{ fmt(clienteDetail.stats?.vlr_vencido || 0) }}</span></div>
        </div>
        <div class="clientes-modal-actions mb-3">
          <b-button variant="dark" @click="whatsappLink">📲 WhatsApp</b-button>
        </div>

        <h6 class="mb-2">🛍️ Histórico de Compras</h6>
        <div v-for="(compra, ci) in clienteDetail.compras || []" :key="ci" class="clientes-compra-card">
          <div class="clientes-compra-row" @click="toggleCompraItems(compra)">
            <div class="clientes-compra-info">
              <span class="clientes-compra-nf">NF {{ compra.num_nf }}</span>
              <span class="clientes-compra-meta">{{ formatDate(compra.dat_emissao) }} · {{ compra.nom_vendedor }} · {{ fmt(compra.vlr_total) }}</span>
            </div>
            <span class="clientes-compra-chevron" :class="{ open: compra._open }">▸</span>
          </div>
          <div v-if="compra._open" class="clientes-compra-items">
            <div v-if="compra._loadingItems" class="clientes-items-loading">Carregando itens...</div>
            <div v-else-if="compra._items && compra._items.length" class="clientes-items-list">
              <div v-for="(it, ii) in compra._items" :key="ii" class="clientes-item-row">
                <span class="clientes-item-name">{{ it.des_produto }}</span>
                <span class="clientes-item-detail">{{ it.cod_referencia }} · {{ it.nom_marca }} · Qtd: {{ it.qtd_produto }}</span>
                <span class="clientes-item-val">{{ fmt(it.vlr_total || (it.vlr_unitario * it.qtd_produto)) }}</span>
              </div>
            </div>
            <div v-else class="clientes-items-empty">Sem itens</div>
          </div>
        </div>
        <div v-if="!clienteDetail.compras || !clienteDetail.compras.length" class="clientes-empty-small">Nenhuma compra</div>

        <h6 class="mb-2">💳 Crediário (Parcelas)</h6>
        <div class="clientes-crediario-filters mb-2">
          <b-form-select v-model="crediarioFilter" size="sm" :options="crediarioFilterOptions" class="clientes-filter-select" />
        </div>
        <b-table
          :items="parcelasFiltered"
          :fields="parcelasFields"
          small
          striped
          hover
          show-empty
          empty-text="Nenhuma parcela"
          class="clientes-table"
        >
          <template #cell(dat_vencto)="row">
            {{ formatDate(row.value) }}
          </template>
          <template #cell(dat_ultpagto)="row">
            {{ row.value ? formatDate(row.value) : '-' }}
          </template>
          <template #cell(vlr_doc)="row">
            {{ fmt(row.value) }}
          </template>
          <template #cell(vlr_pago)="row">
            {{ fmt(row.value) }}
          </template>
          <template #cell(vlr_saldo)="row">
            {{ fmt(row.value) }}
          </template>
          <template #cell(vlr_juros)="row">
            {{ fmt(row.value) }}
          </template>
          <template #cell(flg_aberto)="row">
            <b-badge :variant="row.value === 'S' ? 'warning' : 'success'">{{ row.value === 'S' ? 'Aberto' : 'Quitado' }}</b-badge>
          </template>
          <template #cell(dias_atraso)="row">
            <span :class="{ 'text-danger': (row.value || 0) > 0 }">{{ row.value || 0 }}d</span>
          </template>
        </b-table>
      </div>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Clientes',
  data() {
    return {
      section: 'overview',
      loading: true,
      loadingLista: false,
      lastUpdate: null,
      search: '',
      modalShow: false,
      selectedCliente: null,
      clienteDetail: null,
      kpis: {},
      inadimplenciaHistory: [],
      inadimplenciaMeses: 24,
      inadimplenciaSortMode: 'taxa_desc',
      selectedMonthDevedores: null,
      selectedMonthPeriod: null,
      crediarioFilter: 'all',
      topDevedores: [],
      writeoffsData: { summary: {}, clientes: [] },
      clientesVip: [],
      vipRange: 'all',
      aniversariantes: [],
      clientesLista: [],
      campanhas: []
    }
  },
  computed: {
    navItems() {
      const atrasados = this.topDevedores.length
      const perdidos = this.writeoffsClientes.length
      return [
        { id: 'overview', label: 'Visão Geral', icon: '📊' },
        { id: 'inadimplencia', label: 'Inadimplência', icon: '📉', badge: atrasados },
        { id: 'perdidos', label: 'Baixa de Crédito', icon: '⛔', badge: perdidos },
        { id: 'vip', label: 'VIP', icon: '⭐' },
        { id: 'aniversariantes', label: 'Aniversários', icon: '🎂', badge: this.aniversariantes.length },
        { id: 'todos', label: 'Clientes', icon: '👥' }
      ]
    },
    writeoffsSummary() {
      return this.writeoffsData.summary || {}
    },
    writeoffsClientes() {
      return this.writeoffsData.clientes || []
    },
    inadimplenciaMesesOptions() {
      return [
        { value: 3, text: '3 meses' },
        { value: 6, text: '6 meses' },
        { value: 12, text: '12 meses' },
        { value: 24, text: '24 meses' },
        { value: 36, text: '36 meses' },
        { value: 54, text: '54 meses' },
        { value: 60, text: '5 anos' }
      ]
    },
    inadimplenciaSortOptions() {
      return [
        { value: 'taxa_desc', text: '↓ Maior taxa' },
        { value: 'taxa_asc', text: '↑ Menor taxa' },
        { value: 'recent', text: 'Mais recente' },
        { value: 'oldest', text: 'Mais antigo' }
      ]
    },
    inadimplenciaSorted() {
      const list = [...(this.inadimplenciaHistory || [])]
      const mode = this.inadimplenciaSortMode || 'taxa_desc'
      return list.sort((a, b) => {
        if (mode === 'taxa_desc') return (Number(b.taxa_inadimplencia) || 0) - (Number(a.taxa_inadimplencia) || 0)
        if (mode === 'taxa_asc') return (Number(a.taxa_inadimplencia) || 0) - (Number(b.taxa_inadimplencia) || 0)
        const da = new Date(a.period_date || 0).getTime()
        const db = new Date(b.period_date || 0).getTime()
        if (mode === 'recent') return db - da
        return da - db
      })
    },
    selectedMonthLabel() {
      if (!this.selectedMonthPeriod) return ''
      const m = this.inadimplenciaHistory.find(h => (h.period_ym || '').startsWith(this.selectedMonthPeriod))
      return m ? m.period : this.selectedMonthPeriod
    },
    taxaMedia() {
      const h = this.inadimplenciaHistory
      if (!h.length) return '0'
      const sum = h.reduce((s, x) => s + (Number(x.taxa_inadimplencia) || 0), 0)
      return (sum / h.length).toFixed(1)
    },
    taxaMediaSub() {
      const meses = Number(this.inadimplenciaMeses) || 24
      return `média ${meses} meses`
    },
    parcelasFiltered() {
      const list = this.clienteDetail?.parcelas || []
      const f = this.crediarioFilter
      if (f === 'aberto') return list.filter(p => p.flg_aberto === 'S')
      if (f === 'quitado') return list.filter(p => p.flg_aberto !== 'S')
      return list
    },
    crediarioFilterOptions() {
      return [
        { value: 'all', text: 'Todos' },
        { value: 'aberto', text: 'Em aberto' },
        { value: 'quitado', text: 'Quitados' }
      ]
    },
    vipRangeOptions() {
      return [
        { value: 'all', text: 'Todo o período' },
        { value: 'this_year', text: 'Este ano' },
        { value: 'last_year', text: 'Ano passado' },
        { value: 'last_2_years', text: 'Últimos 2 anos' }
      ]
    },
    mesAtualNome() {
      const m = new Date().getMonth()
      const nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
      return nomes[m] + ' ' + new Date().getFullYear()
    },
    initials() {
      const c = this.clienteDetail?.cliente
      const n = (c?.nom_cliente || '').trim()
      if (n) {
        const inits = n.split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase()
        if (inits) return inits
      }
      const t = (c?.telefone || '').replace(/\D/g, '').slice(-2)
      if (t) return t
      const cod = c?.cod_cliente
      if (cod != null) return String(cod).slice(-2) || '?'
      return '?'
    },
    scoreClass() {
      const g = (this.clienteDetail?.score?.grade || '').toUpperCase()
      if (g === 'A') return 'score-a'
      if (g === 'B') return 'score-b'
      if (g === 'C') return 'score-c'
      return 'score-d'
    },
    comprasFields() {
      return [
        { key: 'num_nf', label: 'NF', sortable: true },
        { key: 'dat_emissao', label: 'Data', sortable: true },
        { key: 'vlr_total', label: 'Valor', sortable: true },
        { key: 'prazo_medio_dias', label: 'Prazo (d)', sortable: true },
        { key: 'nom_vendedor', label: 'Vendedor' }
      ]
    },
    parcelasFields() {
      return [
        { key: 'num_doc', label: 'Doc', sortable: true },
        { key: 'parcela_label', label: 'Parcela', sortable: true },
        { key: 'dat_vencto', label: 'Vencimento', sortable: true },
        { key: 'dat_ultpagto', label: 'Últ. Pagto', sortable: true },
        { key: 'vlr_doc', label: 'Valor', sortable: true },
        { key: 'vlr_pago', label: 'Pago', sortable: true },
        { key: 'vlr_saldo', label: 'Saldo', sortable: true },
        { key: 'vlr_juros', label: 'Juros', sortable: true },
        { key: 'flg_aberto', label: 'Status', sortable: true },
        { key: 'dias_atraso', label: 'Atraso', sortable: true }
      ]
    }
  },
  watch: {
    section(val) {
      if (val === 'todos') this.loadLista()
    },
    search() {
      clearTimeout(this._searchTimer)
      this._searchTimer = setTimeout(() => this.loadLista(), 300)
    }
  },
  mounted() {
    this.loadAll()
  },
  methods: {
    fmt(n) {
      return 'R$ ' + Number(n).toLocaleString('pt-BR', { minimumFractionDigits: 0 })
    },
    formatDate(val) {
      if (!val) return '-'
      const d = typeof val === 'string' ? new Date(val) : val
      return d.toLocaleDateString ? d.toLocaleDateString('pt-BR') : String(val)
    },
    async loadAll() {
      this.loading = true
      try {
        await Promise.all([
          this.loadKpis(),
          this.loadInadimplencia(),
          this.loadTopDevedores(),
          this.loadWriteoffs(),
          this.loadVip(),
          this.loadAniversariantes()
        ])
        this.lastUpdate = new Date().toLocaleTimeString('pt-BR')
      } catch (e) {
        console.error('Clientes loadAll:', e)
        this.$bvToast?.toast('Erro ao carregar dados: ' + (e.response?.data?.detail || e.message), { variant: 'danger' })
      } finally {
        this.loading = false
      }
    },
    async loadKpis() {
      const r = await axios.get('/api/clientes/kpis')
      this.kpis = r.data || {}
    },
    async loadInadimplencia() {
      const r = await axios.get('/api/clientes/inadimplencia-historico', { params: { meses: this.inadimplenciaMeses } })
      this.inadimplenciaHistory = r.data || []
    },
    async loadTopDevedores() {
      const r = await axios.get('/api/clientes/top-devedores?limit=20')
      this.topDevedores = r.data || []
    },
    async loadWriteoffs() {
      const r = await axios.get('/api/clientes/writeoffs')
      this.writeoffsData = { summary: r.data?.summary || {}, clientes: r.data?.clientes || [] }
    },
    async loadVip() {
      const r = await axios.get('/api/clientes/vip', { params: { limit: 20, range_type: this.vipRange } })
      this.clientesVip = r.data || []
    },
    async loadAniversariantes() {
      const r = await axios.get('/api/clientes/aniversariantes')
      this.aniversariantes = r.data || []
    },
    async loadLista() {
      this.loadingLista = true
      try {
        const r = await axios.get('/api/clientes/lista', {
          params: { search: this.search || undefined, limit: 200, offset: 0 }
        })
        this.clientesLista = r.data || []
      } catch (e) {
        this.clientesLista = []
      } finally {
        this.loadingLista = false
      }
    },
    async openCliente(cod) {
      this.selectedCliente = cod
      this.modalShow = true
      try {
        const r = await axios.get(`/api/clientes/${cod}`)
        this.clienteDetail = r.data
      } catch (e) {
        this.$bvToast?.toast('Erro ao carregar cliente', { variant: 'danger' })
        this.clienteDetail = null
      }
    },
    whatsappLink() {
      const tel = (this.clienteDetail?.cliente?.telefone || '').replace(/\D/g, '')
      if (tel) window.open('https://wa.me/55' + tel, '_blank')
    },
    clienteDisplayName(c) {
      if (!c) return '-'
      const n = (c.nom_cliente || c.fan_cliente || c.raz_cliente || '').trim()
      if (n) return n
      const t = (c.telefone || '').trim()
      if (t) return `Tel. ${t}`
      const city = (c.cidade || '').trim()
      if (city) return city
      return `Cliente #${c.cod_cliente || '-'}`
    },
    async openInadimplenciaMonth(m) {
      if (!m || !m.period_ym) {
        this.section = 'inadimplencia'
        return
      }
      this.selectedMonthPeriod = m.period_ym
      try {
        const r = await axios.get('/api/clientes/devedores-por-mes', { params: { period: m.period_ym, limit: 50 } })
        this.selectedMonthDevedores = r.data || []
      } catch (e) {
        this.selectedMonthDevedores = []
      }
    },
    async toggleCompraItems(compra) {
      if (compra._open) {
        this.$set(compra, '_open', false)
        return
      }
      this.$set(compra, '_open', true)
      if (!compra._items) {
        this.$set(compra, '_loadingItems', true)
        try {
          const r = await axios.get(`/api/clientes/nf/${compra.nf_interno}/items`)
          this.$set(compra, '_items', r.data || [])
        } catch (e) {
          this.$set(compra, '_items', [])
        }
        this.$set(compra, '_loadingItems', false)
      }
    },
    async registrarWriteoff(cod) {
      try {
        await axios.post(`/api/clientes/${cod}/writeoff`)
        this.$bvToast?.toast('Baixa registrada', { variant: 'success' })
        this.loadWriteoffs()
      } catch (e) {
        this.$bvToast?.toast('Erro: ' + (e.response?.data?.detail || e.message), { variant: 'danger' })
      }
    }
  }
}
</script>

<style scoped>
.clientes-nav-pills { flex-wrap: wrap; }
.clientes-nav-pills .nav-link { cursor: pointer; }
.clientes-loading { text-align: center; padding: 48px; color: #6B7280; }
.clientes-s-title { font-size: 17px; font-weight: 800; color: #111827; margin-bottom: 16px; }
.clientes-kpi-grid { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
.clientes-kpi-card { background: #fff; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 20px; flex: 1 1 160px; min-width: 150px; }
.clientes-kpi-icon { font-size: 22px; }
.clientes-kpi-label { font-size: 11px; color: #9CA3AF; font-weight: 600; text-transform: uppercase; margin-top: 8px; }
.clientes-kpi-value { font-size: 22px; font-weight: 800; color: #111827; margin-top: 2px; }
.clientes-kpi-sub { font-size: 11px; color: #9CA3AF; margin-top: 3px; }
.clientes-panel { background: #fff; border: 1px solid #E5E7EB; border-radius: 16px; padding: 20px 22px; margin-bottom: 16px; }
.clientes-panel-title { font-weight: 700; font-size: 14px; margin-bottom: 14px; }
.clientes-chart-wrap { display: flex; flex-direction: column; gap: 8px; }
.clientes-bar-row { display: flex; align-items: center; gap: 10px; }
.clientes-bar-click { cursor: pointer; padding: 4px 0; border-radius: 6px; }
.clientes-bar-click:hover { background: #F3F4F6; }
.clientes-panel-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.clientes-inad-select { width: 120px; display: inline-block; }
.clientes-sort-hint { font-size: 11px; color: #6B7280; cursor: pointer; margin-left: 8px; }
.clientes-filter-label { font-size: 12px; margin-right: 8px; }
.clientes-range-select { width: 160px; display: inline-block; }
.clientes-bar-label { font-size: 11px; color: #6B7280; min-width: 50px; }
.clientes-bar-track { flex: 1; height: 8px; background: #F3F4F6; border-radius: 99px; overflow: hidden; }
.clientes-bar-fill { height: 100%; border-radius: 99px; }
.clientes-bar-val { font-size: 11px; font-weight: 700; min-width: 40px; text-align: right; }
.clientes-bar-raw { font-size: 10px; color: #6B7280; min-width: 70px; text-align: right; }
.clientes-month-devedores { background: #F9FAFB; border-radius: 12px; padding: 14px; border: 1px solid #E5E7EB; }
.clientes-compra-card { border: 1px solid #E5E7EB; border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; }
.clientes-compra-row { display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
.clientes-compra-nf { font-weight: 700; margin-right: 8px; }
.clientes-compra-meta { font-size: 11px; color: #6B7280; }
.clientes-compra-chevron { font-size: 12px; transition: transform 0.2s; }
.clientes-compra-chevron.open { transform: rotate(90deg); }
.clientes-compra-items { margin-top: 10px; padding-top: 10px; border-top: 1px solid #E5E7EB; }
.clientes-items-loading, .clientes-items-empty { font-size: 12px; color: #9CA3AF; padding: 6px 0; }
.clientes-items-list { display: flex; flex-direction: column; gap: 6px; }
.clientes-item-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 12px; }
.clientes-item-name { font-weight: 600; flex: 1; }
.clientes-item-detail { font-size: 11px; color: #6B7280; }
.clientes-item-val { font-weight: 700; }
.clientes-empty-small { font-size: 12px; color: #9CA3AF; padding: 12px 0; }
.clientes-crediario-filters { display: flex; gap: 8px; align-items: center; }
.clientes-filter-select { width: 140px; }
.clientes-card { background: #fff; border: 1px solid #E5E7EB; border-radius: 14px; padding: 16px 20px; margin-bottom: 8px; }
.clientes-card-click { cursor: pointer; transition: box-shadow 0.15s; }
.clientes-card-click:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
.clientes-card-atraso { border-left: 3px solid #D97706; cursor: pointer; }
.clientes-card-perdido { border-left: 3px solid #DC2626; background: #FFFAFA; cursor: pointer; }
.clientes-card-vip { border-left: 3px solid #F59E0B; cursor: pointer; }
.clientes-card-aniv { border-left: 3px solid #EC4899; cursor: pointer; }
.clientes-card-row { display: flex; align-items: center; gap: 12px; }
.clientes-card-name { font-weight: 700; font-size: 14px; color: #111827; flex: 1; }
.clientes-card-val { font-weight: 800; font-size: 14px; }
.clientes-card-val.success { color: #059669; }
.clientes-card-val.danger { color: #DC2626; }
.clientes-card-rank { width: 36px; height: 36px; border-radius: 50%; background: #F3F4F6; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; }
.clientes-card-icon { font-size: 22px; }
.clientes-card-sub { font-size: 11px; color: #9CA3AF; margin-top: 4px; margin-bottom: 8px; }
.clientes-card-actions { display: flex; gap: 8px; margin-top: 8px; }
.clientes-alert { border-radius: 14px; padding: 16px 20px; margin-bottom: 20px; display: flex; gap: 20px; flex-wrap: wrap; }
.clientes-alert.danger { background: #FEF2F2; border: 1px solid #FECACA; }
.clientes-empty { text-align: center; color: #9CA3AF; padding: 48px; }
.clientes-filters { margin-bottom: 14px; }
.clientes-search { max-width: 300px; }
.clientes-modal-header { display: flex; gap: 16px; align-items: center; margin-bottom: 20px; }
.clientes-modal-avatar { width: 56px; height: 56px; border-radius: 50%; background: #E5E7EB; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px; flex-shrink: 0; }
.clientes-modal-name { font-weight: 800; font-size: 18px; }
.clientes-modal-sub { color: #6B7280; font-size: 12px; margin-top: 2px; }
.clientes-modal-tags { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.clientes-tag { background: #E5E7EB; color: #374151; border-radius: 99px; padding: 2px 9px; font-size: 10px; font-weight: 700; }
.clientes-modal-score { width: 52px; height: 52px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 22px; }
.clientes-modal-score.score-a { background: #D1FAE5; border: 2.5px solid #059669; color: #059669; }
.clientes-modal-score.score-b { background: #DBEAFE; border: 2.5px solid #2563EB; color: #2563EB; }
.clientes-modal-score.score-c { background: #FEF3C7; border: 2.5px solid #D97706; color: #D97706; }
.clientes-modal-score.score-d { background: #FEE2E2; border: 2.5px solid #DC2626; color: #DC2626; }
.clientes-modal-stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-bottom: 20px; }
.clientes-modal-stat { background: #F9FAFB; border-radius: 12px; padding: 12px; text-align: center; }
.clientes-modal-stat .label { font-size: 10px; color: #9CA3AF; display: block; }
.clientes-modal-stat .val { font-weight: 800; font-size: 15px; }
.clientes-modal-stat .val.danger { color: #DC2626; }
.clientes-modal-actions { display: flex; gap: 8px; }
.clientes-table { font-size: 12px; }
.clientes-table >>> .table { margin-bottom: 0; }
</style>
