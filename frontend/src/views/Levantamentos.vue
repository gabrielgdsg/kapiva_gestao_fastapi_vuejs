<template>
  <div class="levantamentos-optimized">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet" />

    <!-- Header -->
    <div class="lev-header">
      <h1 class="lev-title">Levantamentos</h1>
      <p class="lev-subtitle">
        {{ filteredProducts.length }} produtos · {{ visibleCols.length }} colunas de tamanho
      </p>
    </div>

    <!-- Load / Filters bar -->
    <div class="lev-controls-card">
      <div class="lev-load-row">
        <div class="lev-field">
          <label class="lev-label">Marca</label>
          <b-form-select
            v-model="cod_marca"
            :options="marcaOptions"
            value-field="cod_marca"
            text-field="nom_marca"
            size="sm"
            class="lev-select"
          >
            <template #first>
              <option :value="null">— Selecione a marca —</option>
            </template>
          </b-form-select>
        </div>
        <div class="lev-field">
          <label class="lev-label">Data inicial</label>
          <b-form-input v-model="data_cadastro_ini" type="date" size="sm" class="lev-input" />
        </div>
        <div class="lev-field">
          <label class="lev-label">Data final</label>
          <b-form-input v-model="data_cadastro_fim" type="date" size="sm" class="lev-input" />
        </div>
        <div class="lev-field lev-actions">
          <b-button variant="primary" size="sm" :disabled="loading || !cod_marca" @click="onSubmit">
            <b-spinner v-if="loading" small class="mr-1" />
            {{ loading ? 'Carregando...' : 'Carregar' }}
          </b-button>
          <span v-if="loadTime" class="lev-load-time">{{ loadTime }}ms</span>
        </div>
      </div>

      <div class="lev-filters-row">
        <div class="lev-grade-wrap">
          <div class="lev-label">Grupos de Grade</div>
          <div class="lev-grade-buttons">
            <button
              v-for="g in gradeGroups"
              :key="g.id"
              type="button"
              class="lev-grade-btn"
              :class="{ 'lev-grade-btn-on': selectedGroups.includes(g.id) }"
              @click="toggleGroup(g.id)"
            >
              {{ g.label }}
              <span class="lev-grade-count">({{ g.sizes.length }})</span>
            </button>
          </div>
        </div>
        <div class="lev-filter-wrap">
          <div class="lev-label">Filtrar</div>
          <input
            v-model="filter"
            type="text"
            placeholder="Ref., descrição, cor..."
            class="lev-filter-input"
          />
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="lev-legend">
      <div v-for="([t, l]) in legendTypes" :key="t" class="lev-legend-item">
        <span class="lev-legend-dot" :style="{ background: typeColors[t], borderColor: typeDot[t] }" />
        {{ l }}
      </div>
      <div class="lev-legend-nums">
        <span class="lev-num-stock">12</span> = estoque
        <span class="lev-num-sold">7</span> = vendido
      </div>
    </div>

    <!-- Table -->
    <div class="lev-table-wrap">
      <div class="lev-table-scroll">
        <table class="lev-table">
          <thead>
            <tr>
              <th class="lev-th lev-th-fixed">Marca</th>
              <th class="lev-th lev-th-sort" @click="handleSort('ref')">
                Ref. <span class="lev-sort-icon">{{ sortIcon('ref') }}</span>
              </th>
              <th class="lev-th">Cor</th>
              <th class="lev-th lev-th-sort" @click="handleSort('desc')">
                Descrição <span class="lev-sort-icon">{{ sortIcon('desc') }}</span>
              </th>
              <th class="lev-th lev-th-plus">+</th>
              <th
                v-for="col in visibleCols"
                :key="col"
                class="lev-th lev-th-size"
                :class="{ 'lev-th-empty': !colTotals.stock[col] }"
                :style="sizeThStyle(col)"
              >
                <div class="lev-th-size-inner">
                  <span class="lev-th-dot" :style="dotStyle(col)" />
                  {{ col }}
                </div>
              </th>
              <th class="lev-th lev-th-sort" @click="handleSort('tot')">
                Tot. <span class="lev-sort-icon">{{ sortIcon('tot') }}</span>
              </th>
              <th class="lev-th lev-th-sort" @click="handleSort('price')">
                Preço <span class="lev-sort-icon">{{ sortIcon('price') }}</span>
              </th>
              <th class="lev-th lev-th-sort" @click="handleSort('perf')">
                Performance <span class="lev-sort-icon">{{ sortIcon('perf') }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Totals row -->
            <tr class="lev-totals-row">
              <td class="lev-td" colspan="4">TOTAIS ({{ filteredProducts.length }} itens)</td>
              <td class="lev-td" />
              <td
                v-for="col in visibleCols"
                :key="'tot-' + col"
                class="lev-td lev-td-center"
                :class="{ 'lev-td-has-stock': colTotals.stock[col] > 0 }"
              >
                <template v-if="colTotals.stock[col] > 0">
                  <div class="lev-tot-stock">{{ colTotals.stock[col] }}</div>
                  <div v-if="colTotals.sold[col] > 0" class="lev-tot-sold">{{ colTotals.sold[col] }}</div>
                </template>
              </td>
              <td class="lev-td lev-td-center lev-td-tot">
                <div class="lev-tot-stock">{{ totalStockAll }}</div>
                <div v-if="totalSoldAll > 0" class="lev-tot-sold">{{ totalSoldAll }}</div>
              </td>
              <td class="lev-td" />
              <td class="lev-td" />
            </tr>

            <tr
              v-for="(p, ri) in sortedProducts"
              :key="p.id"
              class="lev-data-row"
              :class="{ 'lev-row-odd': ri % 2 === 0 }"
            >
              <td class="lev-td lev-td-brand">{{ p.brand }}</td>
              <td class="lev-td lev-td-ref">{{ p.ref }}</td>
              <td class="lev-td">
                <span class="lev-badge-color">{{ p.color }}</span>
              </td>
              <td class="lev-td lev-td-desc" :title="p.desc">{{ p.desc }}</td>
              <td class="lev-td lev-td-center">
                <button type="button" class="lev-btn-plus">+</button>
              </td>
              <td
                v-for="col in visibleCols"
                :key="col"
                class="lev-td lev-td-size lev-td-center"
                :class="sizeCellClass(p.stock[col], p.sold[col])"
              >
                <div class="lev-size-stock">{{ (p.stock[col] ?? 0) || '—' }}</div>
                <div v-if="(p.sold[col] ?? 0) > 0" class="lev-size-sold">{{ p.sold[col] }}</div>
              </td>
              <td class="lev-td lev-td-center lev-td-tot">
                <div class="lev-size-stock">{{ productTotalStock(p) }}</div>
                <div v-if="productTotalSold(p) > 0" class="lev-size-sold">{{ productTotalSold(p) }}</div>
              </td>
              <td class="lev-td lev-td-price">R$ {{ formatMoney(p.price) }}</td>
              <td class="lev-td lev-td-perf">
                <div class="lev-perf-bar">
                  <div class="lev-perf-track">
                    <div
                      class="lev-perf-fill"
                      :style="{ width: perfPct(p) + '%', background: perfColor(p) }"
                    />
                  </div>
                  <span
                    class="lev-perf-label"
                    :style="{ color: perfColor(p), background: perfBg(p) }"
                  >
                    {{ perfPct(p) }}% {{ perfLabel(p) }}
                  </span>
                </div>
              </td>
            </tr>

            <tr v-if="sortedProducts.length === 0">
              <td class="lev-td lev-td-empty" colspan="999">
                Nenhum produto encontrado. Selecione marca, datas e clique em Carregar; depois ajuste grupos de grade ou filtro.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="lev-footer">
      Colunas sem estoque nos itens filtrados ficam apagadas. Selecione/remova grupos de grade para adaptar as colunas ao tipo de produto.
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const GRADE_GROUPS = [
  { id: 'calcado_ad', label: 'Calçado Ad.', sizes: [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44].map(String) },
  { id: 'meias', label: 'Meias', sizes: ['33-38', '39-42', '39-44', '43-45'] },
  { id: 'UN', label: 'UN', sizes: ['UN'] },
  { id: 'calcado_inf', label: 'Calçado Inf.', sizes: [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33].map(String) },
  { id: 'roupas', label: 'Roupas', sizes: ['PP', 'P', 'M', 'G', 'GG'] }
]

const TYPE_COLORS = { shoe: '#dbeafe', sock: '#dcfce7', other: '#fef3c7' }
const TYPE_DOT = { shoe: '#3b82f6', sock: '#22c55e', other: '#f59e0b' }

export default {
  name: 'Levantamentos',
  data() {
    const today = new Date()
    const y = today.getFullYear()
    const m = String(today.getMonth() + 1).padStart(2, '0')
    const d = String(today.getDate()).padStart(2, '0')
    return {
      gradeGroups: GRADE_GROUPS,
      selectedGroups: ['calcado_ad', 'meias', 'UN'],
      filter: '',
      sortKey: null,
      sortDir: 1,
      products: [],
      loading: false,
      loadTime: null,
      cod_marca: null,
      data_cadastro_ini: `${y}-01-01`,
      data_cadastro_fim: `${y}-${m}-${d}`,
      marcas: [],
      legendTypes: [['shoe', 'Calçado'], ['sock', 'Meias'], ['other', 'Outros']],
      typeColors: TYPE_COLORS,
      typeDot: TYPE_DOT
    }
  },
  computed: {
    marcaOptions() {
      return this.marcas || []
    },
    visibleCols() {
      const seen = new Set()
      const cols = []
      for (const g of this.gradeGroups) {
        if (!this.selectedGroups.includes(g.id)) continue
        for (const s of g.sizes) {
          const key = String(s)
          if (!seen.has(key)) {
            seen.add(key)
            cols.push(key)
          }
        }
      }
      return cols
    },
    filteredProducts() {
      return this.products.filter(p => {
        const hasRelevant = this.visibleCols.some(col => (p.stock[col] ?? 0) > 0)
        if (!hasRelevant) return false
        if (!this.filter.trim()) return true
        const f = this.filter.toLowerCase()
        return (
          (p.desc || '').toLowerCase().includes(f) ||
          (p.ref || '').toLowerCase().includes(f) ||
          (p.color || '').toLowerCase().includes(f)
        )
      })
    },
    sortedProducts() {
      if (!this.sortKey) return this.filteredProducts
      return [...this.filteredProducts].sort((a, b) => {
        let va, vb
        if (this.sortKey === 'perf') {
          va = this.perfPct(a)
          vb = this.perfPct(b)
        } else if (this.sortKey === 'tot') {
          va = this.productTotalStock(a)
          vb = this.productTotalStock(b)
        } else if (this.sortKey === 'ref') {
          va = (a.ref || '').toLowerCase()
          vb = (b.ref || '').toLowerCase()
        } else if (this.sortKey === 'desc') {
          va = (a.desc || '').toLowerCase()
          vb = (b.desc || '').toLowerCase()
        } else if (this.sortKey === 'price') {
          va = Number(a.price) || 0
          vb = Number(b.price) || 0
        } else {
          return 0
        }
        if (va < vb) return -1 * this.sortDir
        if (va > vb) return 1 * this.sortDir
        return 0
      })
    },
    colTotals() {
      const stock = {}
      const sold = {}
      for (const col of this.visibleCols) {
        stock[col] = 0
        sold[col] = 0
        for (const p of this.filteredProducts) {
          stock[col] += p.stock[col] ?? 0
          sold[col] += p.sold[col] ?? 0
        }
      }
      return { stock, sold }
    },
    totalStockAll() {
      return Object.values(this.colTotals.stock).reduce((a, b) => a + b, 0)
    },
    totalSoldAll() {
      return Object.values(this.colTotals.sold).reduce((a, b) => a + b, 0)
    }
  },
  mounted() {
    this.loadMarcas()
  },
  methods: {
    sizeType(size) {
      const s = String(size)
      if (/^\d+$/.test(s)) return 'shoe'
      if (s.includes('-')) return 'sock'
      return 'other'
    },
    sizeThStyle(col) {
      const t = this.sizeType(col)
      const hasData = this.colTotals.stock[col] > 0
      return {
        background: hasData ? this.typeColors[t] : '#f9fafb',
        borderBottomColor: hasData ? this.typeDot[t] : '#e5e7eb',
        color: hasData ? '#111' : '#bbb'
      }
    },
    dotStyle(col) {
      const hasData = this.colTotals.stock[col] > 0
      return { background: hasData ? this.typeDot[this.sizeType(col)] : '#e5e7eb' }
    },
    sizeCellClass(stock, sold) {
      if (stock == null && sold == null) return ''
      const hasSold = (sold || 0) > 0
      const hasStock = (stock || 0) > 0
      if (hasSold) return 'lev-cell-sold'
      if (hasStock) return 'lev-cell-stock'
      return 'lev-cell-empty'
    },
    productTotalStock(p) {
      return Object.values(p.stock || {}).reduce((a, b) => a + (Number(b) || 0), 0)
    },
    productTotalSold(p) {
      return Object.values(p.sold || {}).reduce((a, b) => a + (Number(b) || 0), 0)
    },
    perfPct(p) {
      const total = this.productTotalStock(p)
      if (!total) return 0
      const sold = this.productTotalSold(p)
      return Math.round((sold / total) * 100)
    },
    perfLabel(p) {
      const pct = this.perfPct(p)
      if (pct >= 60) return 'Rápido'
      if (pct >= 35) return 'Médio'
      return 'Lento'
    },
    perfColor(p) {
      const pct = this.perfPct(p)
      if (pct >= 60) return '#22c55e'
      if (pct >= 35) return '#f59e0b'
      return '#ef4444'
    },
    perfBg(p) {
      const pct = this.perfPct(p)
      if (pct >= 60) return '#f0fdf4'
      if (pct >= 35) return '#fffbeb'
      return '#fef2f2'
    },
    formatMoney(val) {
      const n = Number(val)
      if (isNaN(n)) return '0,00'
      return n.toFixed(2).replace('.', ',')
    },
    toggleGroup(id) {
      if (this.selectedGroups.includes(id)) {
        this.selectedGroups = this.selectedGroups.filter(x => x !== id)
      } else {
        this.selectedGroups = [...this.selectedGroups, id]
      }
    },
    handleSort(key) {
      if (this.sortKey === key) {
        this.sortDir = -this.sortDir
      } else {
        this.sortKey = key
        this.sortDir = 1
      }
    },
    sortIcon(key) {
      if (this.sortKey !== key) return '↕'
      return this.sortDir === 1 ? '↑' : '↓'
    },
    loadMarcas() {
      axios.get('/api/read/marcas/')
        .then(res => {
          this.marcas = res.data || []
        })
        .catch(err => {
          console.warn('Erro ao carregar marcas:', err)
        })
    },
    onSubmit() {
      if (!this.cod_marca) return
      const ini = this.data_cadastro_ini || ''
      const fim = this.data_cadastro_fim || ''
      if (!ini || !fim) {
        this.$bvToast?.toast('Informe data inicial e final.', { variant: 'warning' })
        return
      }
      this.loading = true
      this.loadTime = null
      const start = performance.now()
      const path = `/api/levantamentos/${ini}/${fim}/${this.cod_marca}/`
      axios.get(path)
        .then(res => {
          this.loadTime = Math.round(performance.now() - start)
          this.products = this.buildProductsFromRows(res.data || [])
        })
        .catch(err => {
          console.error(err)
          this.$bvToast?.toast('Erro ao carregar levantamentos: ' + (err.response?.data?.detail || err.message), { variant: 'danger' })
          this.products = []
        })
        .finally(() => {
          this.loading = false
        })
    },
    buildProductsFromRows(rows) {
      const byKey = {}
      for (let i = 0; i < rows.length; i++) {
        const row = rows[i]
        if (!Array.isArray(row)) continue
        const cod_referencia = row[7]
        const des_cor = row[19] || ''
        const des_tamanho = row[17] != null ? String(row[17]) : ''
        const saldo_estoque = Number(row[9]) || 0
        const vlr_venda1 = Number(row[12]) || 0
        const nom_marca = row[26] || ''
        const des_produto = row[5] || ''
        const key = `${cod_referencia}|${des_cor}`
        if (!byKey[key]) {
          byKey[key] = {
            id: key,
            brand: nom_marca,
            ref: cod_referencia,
            color: des_cor,
            desc: des_produto.replace(des_cor, '').replace(des_tamanho, '').replace(nom_marca, '').trim() || des_produto,
            price: vlr_venda1,
            stock: {},
            sold: {}
          }
        }
        if (des_tamanho) {
          byKey[key].stock[des_tamanho] = (byKey[key].stock[des_tamanho] || 0) + saldo_estoque
        }
      }
      return Object.values(byKey)
    }
  }
}
</script>

<style scoped>
.levantamentos-optimized {
  font-family: 'DM Sans', system-ui, sans-serif;
  background: #f8fafc;
  min-height: 100vh;
  padding: 20px;
}
.lev-header { margin-bottom: 16px; }
.lev-title { font-size: 22px; font-weight: 700; color: #111827; margin: 0; }
.lev-subtitle { color: #6b7280; font-size: 13px; margin: 4px 0 0; }

.lev-controls-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
}
.lev-load-row { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px; flex: 1; }
.lev-field { display: flex; flex-direction: column; gap: 4px; }
.lev-field .lev-label { font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
.lev-select, .lev-input { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 140px; }
.lev-actions { flex-direction: row; align-items: center; }
.lev-load-time { font-size: 12px; color: #6b7280; margin-left: 8px; }
.lev-filters-row { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-start; width: 100%; }
.lev-grade-wrap { flex: 1; min-width: 200px; }
.lev-grade-wrap .lev-label { margin-bottom: 6px; }
.lev-grade-buttons { display: flex; flex-wrap: wrap; gap: 6px; }
.lev-grade-btn {
  padding: 4px 10px; font-size: 12px; border-radius: 6px; cursor: pointer; border: 1.5px solid #d1d5db;
  background: #fff; color: #6b7280; font-weight: 400; transition: all 0.15s;
}
.lev-grade-btn-on { border-color: #2563eb; background: #eff6ff; color: #1d4ed8; font-weight: 700; }
.lev-grade-count { margin-left: 4px; font-size: 10px; color: #93c5fd; }
.lev-grade-btn:not(.lev-grade-btn-on) .lev-grade-count { color: #d1d5db; }
.lev-filter-wrap { min-width: 200px; }
.lev-filter-wrap .lev-label { margin-bottom: 6px; }
.lev-filter-input {
  padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; width: 100%;
  outline: none; box-sizing: border-box;
}

.lev-legend { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; font-size: 11px; align-items: center; }
.lev-legend-item { display: flex; align-items: center; gap: 4px; color: #6b7280; }
.lev-legend-dot { width: 10px; height: 10px; border-radius: 2px; border: 1.5px solid; }
.lev-legend-nums { color: #6b7280; margin-left: 8px; }
.lev-num-stock { color: #374151; font-weight: 600; }
.lev-num-sold { color: #16a34a; font-weight: 700; }

.lev-table-wrap {
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
}
.lev-table-scroll { max-height: 520px; overflow-y: auto; }
.lev-table { border-collapse: collapse; width: 100%; font-size: 12px; }
.lev-th {
  padding: 6px 4px; font-size: 11px; font-weight: 700; color: #374151;
  background: #f3f4f6; border-bottom: 2px solid #e5e7eb;
  white-space: nowrap; text-align: center; position: sticky; top: 0; z-index: 2;
}
.lev-th-fixed { left: 0; z-index: 3; background: #f3f4f6; min-width: 80px; }
.lev-th-sort { cursor: pointer; min-width: 60px; }
.lev-th-plus { min-width: 48px; }
.lev-th-size { min-width: 48px; }
.lev-th-empty { color: #bbb; }
.lev-th-size-inner { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.lev-th-dot { width: 6px; height: 6px; border-radius: 99px; }
.lev-td {
  padding: 5px 6px; font-size: 12px; border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}
.lev-totals-row { background: #f0f9ff; }
.lev-totals-row .lev-td:first-child { font-weight: 700; font-size: 11px; color: #2563eb; white-space: nowrap; }
.lev-td-center { text-align: center; }
.lev-td-has-stock { background: #dbeafe; }
.lev-tot-stock { font-size: 11px; font-weight: 700; color: #1d4ed8; }
.lev-tot-sold { font-size: 10px; font-weight: 700; color: #16a34a; }
.lev-td-tot { background: #f8fafc; font-weight: 700; }
.lev-td-brand { font-weight: 600; color: #374151; white-space: nowrap; }
.lev-td-ref { font-family: monospace; font-size: 11px; color: #4b5563; }
.lev-badge-color { font-size: 11px; background: #f3f4f6; padding: 2px 6px; border-radius: 4px; color: #374151; white-space: nowrap; }
.lev-td-desc { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #111; }
.lev-btn-plus { padding: 2px 7px; font-size: 11px; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer; background: #f9fafb; color: #374151; }
.lev-td-size { padding: 4px 2px; }
.lev-cell-sold { background: #f0fdf4; }
.lev-cell-stock { background: #fff; }
.lev-cell-empty { background: #fafafa; }
.lev-size-stock { font-size: 12px; color: #111; line-height: 1.2; }
.lev-size-stock:only-child { color: #bbb; }
.lev-size-sold { font-size: 11px; font-weight: 700; color: #16a34a; }
.lev-td-price { text-align: right; font-weight: 600; color: #374151; white-space: nowrap; }
.lev-td-perf { min-width: 130px; }
.lev-perf-bar { display: flex; align-items: center; gap: 6px; min-width: 110px; }
.lev-perf-track { flex: 1; height: 6px; background: #e5e7eb; border-radius: 99px; overflow: hidden; }
.lev-perf-fill { height: 100%; border-radius: 99px; transition: width 0.4s; min-width: 2%; }
.lev-perf-label { font-size: 11px; font-weight: 700; padding: 1px 5px; border-radius: 4px; white-space: nowrap; }
.lev-data-row:hover { background: #f0f9ff !important; }
.lev-row-odd { background: #fff; }
.lev-data-row:not(.lev-row-odd) { background: #fafafa; }
.lev-td-empty { text-align: center; color: #9ca3af; padding: 40px; }
.lev-footer { margin-top: 10px; font-size: 11px; color: #9ca3af; }
</style>
