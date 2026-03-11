<template>
  <div class="lev2">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet" />

    <!-- Page header -->
    <div class="lev2-header">
      <div>
        <h1 class="lev2-title">Levantamentos 2</h1>
        <div class="lev2-subtitle">
          {{ visibleProducts.length }} produto(s) visíveis · {{ safeActiveCols.length }} tamanho(s)
        </div>
      </div>
      <div class="lev2-header-actions">
        <b-button size="sm" :variant="showImg ? 'primary' : 'outline-secondary'" @click="showImg = !showImg">
          {{ showImg ? 'ON' : 'OFF' }} Imagens
        </b-button>
        <b-button size="sm" :variant="showCost ? 'primary' : 'outline-secondary'" @click="showCost = !showCost">
          {{ showCost ? 'ON' : 'OFF' }} Custo
        </b-button>
        <b-button size="sm" :variant="showImgLink ? 'primary' : 'outline-secondary'" @click="showImgLink = !showImgLink">
          {{ showImgLink ? 'ON' : 'OFF' }} Link Img
        </b-button>
        <b-button size="sm" :variant="showPerf ? 'primary' : 'outline-secondary'" @click="showPerf = !showPerf">
          {{ showPerf ? 'ON' : 'OFF' }} Performance
        </b-button>
        <b-button size="sm" :variant="showDataCad ? 'primary' : 'outline-secondary'" @click="showDataCad = !showDataCad">
          {{ showDataCad ? 'ON' : 'OFF' }} Data Cad.
        </b-button>
        <b-button size="sm" :variant="showDataUltCompra ? 'primary' : 'outline-secondary'" @click="showDataUltCompra = !showDataUltCompra">
          {{ showDataUltCompra ? 'ON' : 'OFF' }} Data UltCompra
        </b-button>
        <b-button size="sm" variant="outline-secondary" @click="selectorOpen = !selectorOpen">
          {{ selectorOpen ? '▲ Ocultar' : '▼ Grades' }}
        </b-button>
      </div>
    </div>

    <!-- Load bar: Marca, dates, Enviar -->
    <div class="lev2-load-bar">
      <div class="lev2-load-field">
        <Levantamentos2MarcaSelect :marcas="marcas" :value="cod_marca" @input="cod_marca = $event"/>
      </div>
      <div class="lev2-load-field">
        <label class="lev2-label">Data inicial</label>
        <b-form-input v-model="data_cadastro_ini" type="date" size="sm" class="lev2-input" />
      </div>
      <div class="lev2-load-field">
        <label class="lev2-label">Data final</label>
        <b-form-input v-model="data_cadastro_fim" type="date" size="sm" class="lev2-input" />
      </div>
      <div class="lev2-load-field lev2-actions">
        <b-form-checkbox v-model="useMongo" size="sm" class="lev2-mongo-toggle" title="Usar cache MongoDB (mais rápido para marcas grandes)">
          MongoDB
        </b-form-checkbox>
        <b-button size="sm" variant="primary" :disabled="loading || !cod_marca" @click="onSubmit">
          <b-spinner v-if="loading" small class="mr-1" />
          {{ loading ? 'Carregando...' : 'Carregar' }}
        </b-button>
        <b-button size="sm" variant="outline-secondary" :disabled="syncing || loading || !cod_marca" @click="forceSync" title="Sincronizar Postgres → MongoDB para carregamento mais rápido">
          <b-spinner v-if="syncing" small class="mr-1" />
          {{ syncing ? 'Sincronizando...' : 'Force Sync' }}
        </b-button>
        <b-button size="sm" variant="outline-secondary" :disabled="loading || !products.length" @click="carregarImagens" title="Recarregar imagens da base">
          Recarregar Imagens
        </b-button>
        <span v-if="loadTime" class="lev2-load-ms">{{ loadTime }}ms</span>
      </div>
    </div>

    <!-- Hidden products alert -->
    <div v-if="hiddenProducts.length > 0" class="lev2-hidden-alert">
      <span class="lev2-hidden-icon">⚠️</span>
      <div>
        <strong>{{ hiddenProducts.length }} produto(s) oculto(s)</strong>
        — tamanhos não estão nos grupos de grade selecionados.
      </div>
      <b-button size="sm" variant="warning" class="ml-auto" @click="handleAutoDetect">✨ Revelar todos</b-button>
    </div>

    <!-- Controls: Grade selector + Global filter + Pagination -->
    <div v-if="selectorOpen" class="lev2-controls">
      <div class="lev2-grade-panel">
        <div class="lev2-grade-header">
          <span class="lev2-grade-title">Grupos de Grade</span>
          <span class="lev2-grade-badge">{{ selectedGroupIds.length }} selecionados</span>
          <b-button size="sm" variant="outline-primary" class="lev2-grade-btn-auto" @click="handleAutoDetect">✨ Auto</b-button>
          <b-button size="sm" variant="outline-danger" @click="clearGrades">✕ Limpar</b-button>
          <input v-model="gradeSearch" type="text" placeholder="Buscar..." class="lev2-grade-search" />
        </div>
        <div v-if="autoDetected.length" class="lev2-auto-msg">
          🔍 Auto: {{ (autoDetected || []).filter(Boolean).map(id => (groupById[id] && groupById[id].label) || id).join(', ') }}
        </div>
        <div class="lev2-cats">
          <div v-for="cat in categories" :key="cat.id" class="lev2-cat">
            <div
              class="lev2-cat-head"
              :class="{ 'lev2-cat-selected': selectedInCat(cat).length > 0 }"
              :style="selectedInCat(cat).length > 0 ? { background: cat.bg, '--cat-color': cat.color } : {}"
              @click="toggleCatOpen(cat.id)"
            >
              <span class="lev2-cat-arrow">{{ openCats.has(cat.id) || gradeSearch ? '▾' : '▸' }}</span>
              <span class="lev2-cat-label">{{ cat.label }}</span>
              <span v-if="selectedInCat(cat).length" class="lev2-cat-count" :style="{ background: cat.color }">{{ selectedInCat(cat).length }}/{{ cat.groups.length }}</span>
              <b-button size="sm" variant="outline" class="lev2-cat-all" :class="{ active: selectedInCat(cat).length === cat.groups.length }" :style="selectedInCat(cat).length === cat.groups.length ? { background: cat.color, color: '#fff', borderColor: cat.color } : {}" @click.stop="toggleAllInCat(cat)">
                {{ selectedInCat(cat).length === cat.groups.length ? '✓ Todos' : 'Todos' }}
              </b-button>
            </div>
            <div v-if="openCats.has(cat.id) || gradeSearch" class="lev2-cat-groups">
              <button
                v-for="g in filteredGroupsInCat(cat)"
                :key="g.id"
                type="button"
                class="lev2-group-btn"
                :class="{ on: selectedGroupIds.includes(g.id) }"
                :style="groupBtnStyle(g, cat)"
                @click="toggleGroup(g.id)"
              >
                {{ g.label }} <span class="lev2-group-n">({{ g.sizes.length }})</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="lev2-right-panel">
        <div class="lev2-filter-card">
          <div class="lev2-label">Filtro Global</div>
          <input
            v-model="globalFilter"
            type="text"
            placeholder="marca  cor:preto  >200  data:2024..."
            class="lev2-filter-input"
            @input="currentPage = 1"
          />
          <div class="lev2-filter-hint">brand: / cor: / ref: / desc: / data: / &gt;N / &lt;N / -cat</div>
          <b-button v-if="globalFilter" size="sm" variant="link" class="lev2-clear-filter" @click="globalFilter = ''; currentPage = 1">✕ Limpar</b-button>
        </div>
        <div class="lev2-pagination-card">
          <div class="lev2-label">Paginação</div>
          <b-form-checkbox v-model="pagination" switch size="sm">ON/OFF</b-form-checkbox>
          <template v-if="pagination">
            <span class="lev2-per-page-label">Por página:</span>
            <b-form-select v-model="perPage" size="sm" :options="[25,50,100,200,500]" class="lev2-per-page" @change="currentPage = 1" />
          </template>
        </div>
      </div>
    </div>

    <!-- Pagination bar (top) -->
    <div v-if="pagination && totalPages > 1" class="lev2-pagination-bar">
      <b-button size="sm" variant="outline-primary" @click="currentPage = 1">«</b-button>
      <b-button size="sm" variant="outline-primary" @click="currentPage = Math.max(1, currentPage - 1)">‹</b-button>
      <b-button
        v-for="p in pageNumbers"
        :key="p"
        size="sm"
        :variant="p === currentPage ? 'primary' : 'outline-primary'"
        @click="currentPage = p"
      >{{ p }}</b-button>
      <b-button size="sm" variant="outline-primary" @click="currentPage = Math.min(totalPages, currentPage + 1)">›</b-button>
      <b-button size="sm" variant="outline-primary" @click="currentPage = totalPages">»</b-button>
    </div>

    <!-- Table -->
    <div class="lev2-table-wrap">
      <div class="lev2-table-scroll">
        <table class="lev2-table">
          <thead>
            <tr>
              <th class="lev2-th lev2-th-fixed" @click="handleSort('brand')">Marca {{ sortIcon('brand') }}</th>
              <th class="lev2-th" @click="handleSort('ref')">Ref. {{ sortIcon('ref') }}</th>
              <th class="lev2-th" @click="handleSort('color')">Cor {{ sortIcon('color') }}</th>
              <th class="lev2-th" @click="handleSort('desc')">Descrição {{ sortIcon('desc') }}</th>
              <th v-if="showDataCad" class="lev2-th" @click="handleSort('dat_cadastro')">Data Cad. {{ sortIcon('dat_cadastro') }}</th>
              <th v-if="showDataUltCompra" class="lev2-th" @click="handleSort('dat_ultcompra')">Data UltCompra {{ sortIcon('dat_ultcompra') }}</th>
              <th v-if="showImg" class="lev2-th lev2-th-img">Img.</th>
              <th v-if="showImgLink" class="lev2-th">Link Img</th>
              <th class="lev2-th lev2-th-plus">+</th>
              <th
                v-for="(col, i) in safeColsIter"
                :key="col.key"
                class="lev2-th lev2-th-size"
                :style="thSizeStyle(col, i)"
              >{{ col.key }}</th>
              <th class="lev2-th lev2-th-tot" @click="handleSort('total')">Tot. {{ sortIcon('total') }}</th>
              <th v-if="showCost" class="lev2-th" @click="handleSort('cost')">Custo {{ sortIcon('cost') }}</th>
              <th class="lev2-th" @click="handleSort('price')">Preço {{ sortIcon('price') }}</th>
              <th v-if="showPerf" class="lev2-th" @click="handleSort('perf')">Performance {{ sortIcon('perf') }}</th>
            </tr>
            <!-- Filter row (persisted in localStorage) -->
            <tr class="lev2-filter-row">
              <td class="lev2-td lev2-td-fixed"><b-form-input v-model="filters.nom_marca" size="sm" placeholder="Marca" class="lev2-filter-inp" /></td>
              <td class="lev2-td"><b-form-input v-model="filters.cod_referencia" size="sm" placeholder="Ref." class="lev2-filter-inp" /></td>
              <td class="lev2-td"><b-form-input v-model="filters.des_cor" size="sm" placeholder="Cor" class="lev2-filter-inp" /></td>
              <td class="lev2-td"><b-form-input v-model="filters.des_produto" size="sm" placeholder="Descrição" class="lev2-filter-inp" /></td>
              <td v-if="showDataCad" class="lev2-td"><b-form-input v-model="filters.dat_cadastro" size="sm" placeholder="Data Cad." class="lev2-filter-inp" /></td>
              <td v-if="showDataUltCompra" class="lev2-td"><b-form-input v-model="filters.dat_ultcompra" size="sm" placeholder="Data UltCompra" class="lev2-filter-inp" /></td>
              <td v-if="showImg" class="lev2-td" />
              <td v-if="showImgLink" class="lev2-td" />
              <td class="lev2-td" />
              <td v-for="col in safeColsIter" :key="'f-'+col.key" class="lev2-td lev2-td-size-filter">
                <b-form-input v-model="sizeFilters[col.key]" size="sm" :placeholder="'E;S'" class="lev2-size-filter-inp" :title="'entrada;stock ex: 1;0 ou >1;&lt;1'" />
              </td>
              <td class="lev2-td" />
              <td v-if="showCost" class="lev2-td" />
              <td class="lev2-td"><b-form-input v-model="filters.vlr_venda1" size="sm" placeholder="Preço" class="lev2-filter-inp" /></td>
              <td v-if="showPerf" class="lev2-td" />
            </tr>
            <!-- Totals row (entries / stock) -->
            <tr class="lev2-totals-row">
              <td class="lev2-td lev2-td-fixed" :colspan="4 + (showDataCad?1:0) + (showDataUltCompra?1:0)">TOTAIS · {{ visibleProducts.length }} itens</td>
              <td v-if="showImg" class="lev2-td" />
              <td v-if="showImgLink" class="lev2-td" />
              <td class="lev2-td" />
              <td
                v-for="col in safeColsIter"
                :key="'tot-'+col.key"
                class="lev2-td lev2-td-center"
                :class="{ 'lev2-td-has': colTotals.stock[col.key] > 0 || colTotals.stockE[col.key] > 0 }"
                :style="tdTotStyle(col)"
              >
                <template v-if="colTotals.stockE[col.key] > 0 || colTotals.stock[col.key] > 0">
                  <div class="lev2-tot-entrada">{{ colTotals.stockE[col.key] }}</div>
                  <div class="lev2-tot-num">{{ colTotals.stock[col.key] }}</div>
                </template>
              </td>
              <td class="lev2-td lev2-td-center lev2-td-tot">
                <div class="lev2-tot-entrada">{{ totalEntriesAll }}</div>
                <div class="lev2-tot-num">{{ totalStockAll }}</div>
              </td>
              <td v-if="showCost" class="lev2-td" />
              <td class="lev2-td" />
              <td v-if="showPerf" class="lev2-td" />
            </tr>
          </thead>
          <tbody>
            <template v-for="(p, ri) in pageData">
              <tr
                :key="p._virtualId"
                class="lev2-data-row"
                :class="{ odd: ri % 2 === 0 }"
              >
                <td class="lev2-td lev2-td-fixed lev2-td-brand">{{ p.nom_marca }}</td>
                <td class="lev2-td lev2-td-ref">{{ p.cod_referencia }}</td>
                <td class="lev2-td"><span class="lev2-badge">{{ p.des_cor }}</span></td>
                <td class="lev2-td lev2-td-desc" :title="p.des_produto">{{ p.des_produto }}</td>
                <td v-if="showDataCad" class="lev2-td lev2-td-date">{{ p.dat_cadastro }}</td>
                <td v-if="showDataUltCompra" class="lev2-td lev2-td-date">{{ p.dat_ultcompra }}</td>
                <td v-if="showImg" class="lev2-td lev2-td-center lev2-td-img">
                  <template v-if="imgSrc(imgForProduct(p))">
                    <img :src="imgSrc(imgForProduct(p))" alt="" class="lev2-img" @error="$event.target.style.display='none'; $event.target.nextElementSibling && ($event.target.nextElementSibling.style.display='inline-block')" />
                    <span class="lev2-img-placeholder" style="display:none">—</span>
                  </template>
                  <span v-else class="lev2-img-placeholder">—</span>
                </td>
                <td v-if="showImgLink" class="lev2-td">
                  <input
                    type="text"
                    :value="getImgLinkDisplayValue(p)"
                    :placeholder="imgForProduct(p) ? 'Imagem definida (Ctrl+V para colar)' : 'URL ou Ctrl+V para colar imagem'"
                    class="lev2-img-input"
                    @focus="onImgLinkFocus(p)"
                    @paste="onImgLinkPaste(p, $event)"
                    @input="onImgLinkInput(p, $event)"
                    @blur="onImgLinkBlur(p)"
                  />
                </td>
                <td class="lev2-td lev2-td-center">
                  <button type="button" class="lev2-btn-plus" @click="toggleDetails(p)">{{ expandedRowId === p._virtualId ? '-' : '+' }}</button>
                </td>
                <td
                  v-for="(col, i) in safeColsIter"
                  :key="col.key"
                  class="lev2-td lev2-td-center lev2-td-size"
                  :class="sizeCellClass(p[col.key], p[col.key+'_E'])"
                  :style="tdSizeBorder(col, i)"
                >
                  <template v-if="(p[col.key+'_E'] || 0) > 0 || (p[col.key] || 0) !== 0">
                    <div class="lev2-size-entrada">{{ p[col.key+'_E'] || '' }}</div>
                    <div class="lev2-size-num" :class="{ 'text-danger': (p[col.key] || 0) < 0 }">{{ formatStock(p[col.key]) }}</div>
                  </template>
                </td>
                <td class="lev2-td lev2-td-center lev2-td-tot">
                  <div class="lev2-size-entrada">{{ productTotalEntries(p) }}</div>
                  <div class="lev2-size-num">{{ productTotalStock(p) }}</div>
                </td>
                <td v-if="showCost" class="lev2-td lev2-td-right">R$ {{ formatMoney(p.vlr_custo_bruto) }}</td>
                <td class="lev2-td lev2-td-right">R$ {{ formatMoney(p.vlr_venda1) }}</td>
                <td v-if="showPerf" class="lev2-td lev2-td-perf">
                  <div class="lev2-perf">
                    <div class="lev2-perf-track">
                      <div class="lev2-perf-fill" :style="perfFillStyle(p)" />
                    </div>
                    <span class="lev2-perf-label" :style="perfLabelStyle(p)">{{ perfPct(p) }}% {{ perfLabel(p) }}</span>
                  </div>
                </td>
              </tr>
              <tr v-if="expandedRowId === p._virtualId" :key="p._virtualId + '-det'">
                <td class="lev2-td lev2-td-details" :colspan="detailColspan">
                  <div class="lev2-movimentos-wrap">
                    <h6 class="mb-2"><strong>Histórico de Movimentos</strong></h6>
                    <b-table small striped hover :items="formatMovimentos(p.movtos)" :fields="movimentosFields" class="lev2-movimentos-table">
                      <template #cell(data_movto)="{ value }">{{ formatDate(value) }}</template>
                      <template #cell(origem)="{ item: movto }">
                        <span :class="getOrigemClass(movto.cod_origem)">
                          <span v-if="movto.tipo_movto === 'E'" class="badge badge-success mr-1">E</span>
                          <span v-else class="badge badge-danger mr-1">S</span>
                          {{ movto.origem_nome }}
                        </span>
                      </template>
                      <template v-for="col in safeColsIter" #[`cell(${col.key})`]="{ item: movto }">
                        <span :key="col.key" :class="getMovimentoClass(movto[col.key])">{{ movto[col.key] != null && movto[col.key] !== 0 ? movto[col.key] : '' }}</span>
                      </template>
                      <template #cell(tot_movto)="{ item: movto }">
                        <span :class="getMovimentoClass(movto.tot_movto)">{{ movto.tot_movto != null ? movto.tot_movto : 0 }}</span>
                      </template>
                    </b-table>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="pageData.length === 0">
              <td class="lev2-td lev2-td-empty" colspan="999">Nenhum produto encontrado. Carregue os dados e ajuste grupos ou filtro.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Bottom pagination -->
    <div v-if="pagination && totalPages > 1" class="lev2-pagination-bar">
      <b-button size="sm" variant="outline-primary" @click="currentPage = 1">«</b-button>
      <b-button size="sm" variant="outline-primary" @click="currentPage = Math.max(1, currentPage - 1)">‹</b-button>
      <b-button v-for="p in pageNumbersBottom" :key="'b'+p" size="sm" :variant="p === currentPage ? 'primary' : 'outline-primary'" @click="currentPage = p">{{ p }}</b-button>
      <b-button size="sm" variant="outline-primary" @click="currentPage = Math.min(totalPages, currentPage + 1)">›</b-button>
      <b-button size="sm" variant="outline-primary" @click="currentPage = totalPages">»</b-button>
      <span class="lev2-page-info">Página {{ currentPage }}/{{ totalPages }} · {{ sortedProducts.length }} itens</span>
    </div>

    <div class="lev2-footer">Filtro global: cor:preto, data:2024, &gt;200, -cintos para excluir categoria. Sem filtros por coluna de tamanho.</div>
  </div>
</template>

<script>
import axios from 'axios'
import moment from 'moment'
import Levantamentos2MarcaSelect from '../components/Levantamentos2MarcaSelect'

const CATEGORIES = [
  { id: 'calcado', label: '👟 Calçado', color: '#3b82f6', bg: '#dbeafe', groups: [
    { id: 'calcado_ad', label: 'Calçado Ad.', sizes: ['33','34','35','36','37','38','39','40','41','42','43','44'] },
    { id: 'calcado_inf', label: 'Calçado Inf.', sizes: ['17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32'] },
    { id: 'calcado_big', label: 'Calçado Big', sizes: ['45','46','47','48'] }
  ]},
  { id: 'havaianas', label: '🩴 Havaianas/Grendene', color: '#06b6d4', bg: '#cffafe', groups: [
    { id: 'hav_ad', label: 'Havaianas Ad.', sizes: ['33/34','35/36','37/38','39/40','41/42','43/44','45/46','47/48'] },
    { id: 'hav_inf', label: 'Havaianas Inf.', sizes: ['17/18','19/20','21/22','23/24','25/26','27/28','29/30','31/32'] },
    { id: 'grendene', label: 'Grendene', sizes: ['17/18','19','20/21','22','23/24','25','26/27','28','29','30','31','32/33'] }
  ]},
  { id: 'meias', label: '🧦 Meias', color: '#22c55e', bg: '#dcfce7', groups: [
    { id: 'meias', label: 'Meias', sizes: ['33-38','39-44','39-42','43-45','33 A 38'] }
  ]},
  { id: 'roupas', label: '👕 Roupas', color: '#8b5cf6', bg: '#ede9fe', groups: [
    { id: 'roupas', label: 'Roupas', sizes: ['PP','P','M','G','GG'] },
    { id: 'roupas_ex', label: 'Roupas Extra', sizes: ['EG','EGG','G1','G2','G3'] }
  ]},
  { id: 'cintos', label: '👔 Cintos', color: '#f59e0b', bg: '#fef3c7', groups: [
    { id: 'cintos', label: 'Cintos', sizes: ['85','90','95','100','105','110','115','120','125','130','135','140'] }
  ]},
  { id: 'especiais', label: '🔧 UN / Especiais', color: '#64748b', bg: '#f1f5f9', groups: [
    { id: 'UN', label: 'UN', sizes: ['UN'] }
  ]}
]

const ALL_GROUPS = []
const GROUP_BY_ID = {}
CATEGORIES.forEach(cat => {
  cat.groups.forEach(g => {
    const entry = { ...g, catId: cat.id, catColor: cat.color, catBg: cat.bg, catLabel: cat.label }
    ALL_GROUPS.push(entry)
    GROUP_BY_ID[g.id] = entry
  })
})

/** Sort key for size columns: ranges (X/Y) by first number ascending, then single numbers, then others. */
function sizeSortKey(key) {
  const s = String(key)
  const rangeMatch = s.match(/^(\d+)\/(\d+)$/)
  if (rangeMatch) return [0, parseInt(rangeMatch[1], 10)]
  const singleMatch = s.match(/^\d+$/)
  if (singleMatch) return [1, parseInt(s, 10)]
  return [2, s]
}
function compareSizeKeys(a, b) {
  const [ta, va] = sizeSortKey(a)
  const [tb, vb] = sizeSortKey(b)
  if (ta !== tb) return ta - tb
  if (typeof va === 'number' && typeof vb === 'number') return va - vb
  return String(va).localeCompare(String(vb))
}

export default {
  name: 'Levantamentos2',
  components: { Levantamentos2MarcaSelect },
  data() {
    const today = new Date()
    const y = today.getFullYear()
    const m = String(today.getMonth() + 1).padStart(2, '0')
    const d = String(today.getDate()).padStart(2, '0')
    return {
      categories: CATEGORIES,
      selectedGroupIds: ['calcado_ad'],
      autoDetected: [],
      openCats: new Set(['calcado']),
      gradeSearch: '',
      globalFilter: '',
      sortKey: 'dat_ultcompra',
      sortDir: -1,
      loading: false,
      loadTime: null,
      cod_marca: null,
      data_cadastro_ini: '2019-07-01',
      data_cadastro_fim: `${y}-${m}-${d}`,
      marcas: [],
      showImg: true,
      showCost: false,
      showImgLink: false,
      showPerf: true,
      showDataCad: true,
      showDataUltCompra: true,
      selectorOpen: true,
      pagination: true,
      currentPage: 1,
      perPage: 50,
      items: [],
      subgrouped_items_bycolor_obj: {},
      refs_array: {},
      filterDebounceTimer: null,
      filters: (() => {
        try {
          const s = localStorage.getItem('lev2_col_filters')
          if (s) {
            const o = JSON.parse(s)
          return {
            nom_marca: o.nom_marca || '',
            cod_referencia: o.cod_referencia || '',
            des_cor: o.des_cor || '',
            des_produto: o.des_produto || '',
            dat_cadastro: o.dat_cadastro || '',
            dat_ultcompra: o.dat_ultcompra || '',
            vlr_venda1: o.vlr_venda1 || ''
          }
        }
        } catch (e) { /* ignore parse */ }
        return { nom_marca: '', cod_referencia: '', des_cor: '', des_produto: '', dat_cadastro: '', dat_ultcompra: '', vlr_venda1: '' }
      })(),
      debouncedFilters: { nom_marca: '', cod_referencia: '', des_cor: '', des_produto: '', dat_cadastro: '', dat_ultcompra: '', vlr_venda1: '' },
      origemMapping: {
        2: 'Emissão Nota Fiscal',
        3: 'Requisição',
        4: 'Devolução',
        7: 'Ent. Proc. Notas',
        9: 'Frente de Caixa',
        12: 'Estorno Proc. Notas',
        15: 'Condicional'
      },
      expandedRowId: null,
      sizeFilters: {},
      imagesByKey: {},
      imgLinkEditBuffer: {}, // key: 'ref|cor' -> raw string while editing URL
      useMongo: false, // Use MongoDB cache for faster loads (sync first)
      syncing: false
    }
  },
  watch: {
    filters: {
      handler(newVal) {
        clearTimeout(this.filterDebounceTimer)
        this.filterDebounceTimer = setTimeout(() => {
          this.debouncedFilters = { ...newVal }
          try { localStorage.setItem('lev2_col_filters', JSON.stringify(newVal)) } catch (e) { /* ignore */ }
        }, 300)
      },
      deep: true
    },
    activeCols: {
      handler(cols) {
        try {
          (cols || []).filter(c => c && typeof c.key === 'string').forEach(col => {
            if (this.sizeFilters[col.key] === undefined) this.$set(this.sizeFilters, col.key, '')
          })
        } catch (e) {
          console.warn('Levantamentos2 activeCols watch:', e)
        }
      },
      immediate: true
    }
  },
  computed: {
    groupById: () => GROUP_BY_ID,
    mappedItemsComputed() {
      const mapped = []
      const obj = this.subgrouped_items_bycolor_obj
      const dataFim = this.data_cadastro_fim || ''
      let endDate = null
      if (dataFim) {
        try {
          const d = moment(dataFim, 'YYYY-MM-DD')
          if (d.isValid()) endDate = d
        } catch (e) { /* ignore */ }
      }
      for (const ref_group in obj) {
        for (const cor in obj[ref_group]) {
          const items = obj[ref_group][cor]
          let saldo_entrada = 0
          let saldo_estoq = 0
          const graded = {}
          const movtosMap = new Map()
          const entradaProcNotasDates = []
          for (let idx = 0; idx < items.length; idx++) {
            const item = items[idx]
            if (item.cod_origem_movto === 7 && item.tipo_movto === 'E' && item.data_movto) {
              try {
                const md = moment(item.data_movto, 'DD/MM/YYYY')
                if (md.isValid()) entradaProcNotasDates.push(md)
              } catch (e) { /* ignore */ }
            }
          }
          const processedMovements = new Set()
          let prodIndex = 0
          for (let idx = 0; idx < items.length; idx++) {
            const item = items[idx]
            const tamanho = (item.des_tamanho != null) ? String(item.des_tamanho) : ''
            if (!tamanho) continue
            const estoqE = tamanho + '_E'
            if (graded[estoqE] === undefined) graded[estoqE] = 0
            if (graded[tamanho] === undefined) graded[tamanho] = 0
            let movimento = 0
            if ([2, 3, 4, 7, 9, 12, 15].indexOf(item.cod_origem_movto) === -1) continue
            if (item.tipo_movto === 'S' && item.cod_origem_movto === 12) {
              movimento = -item.qtd_movto
              graded[estoqE] -= item.qtd_movto
              saldo_entrada -= item.qtd_movto
            } else if (item.tipo_movto === 'E') {
              movimento = item.qtd_movto
              if (item.cod_origem_movto === 3) {
                let exclude = false
                if (item.data_movto && entradaProcNotasDates.length) {
                  try {
                    const rq = moment(item.data_movto, 'DD/MM/YYYY')
                    if (rq.isValid()) {
                      for (const pd of entradaProcNotasDates) {
                        const six = rq.clone().subtract(6, 'months')
                        if (pd.isAfter(six) && (pd.isBefore(rq) || pd.isSame(rq, 'day'))) { exclude = true; break }
                      }
                    }
                  } catch (e) { /* ignore */ }
                }
                if (!exclude) { graded[estoqE] += item.qtd_movto; saldo_entrada += item.qtd_movto }
              } else if (item.cod_origem_movto !== 4 && item.cod_origem_movto !== 15) {
                graded[estoqE] += item.qtd_movto
                saldo_entrada += item.qtd_movto
              }
            } else if (item.tipo_movto === 'S') {
              movimento = -item.qtd_movto
            }
            const rowKey = `${ref_group}_${cor}_${prodIndex}`
            if (processedMovements.has(rowKey)) { prodIndex++; continue }
            processedMovements.add(rowKey)
            prodIndex++
            let includeInStock = true
            if (endDate && item.data_movto) {
              try {
                const mdate = moment(item.data_movto, 'DD/MM/YYYY')
                if (mdate.isValid()) includeInStock = mdate.isSameOrBefore(endDate, 'day')
              } catch (e) { /* ignore */ }
            }
            const movtoKey = `${item.data_movto}_${item.cod_origem_movto}`
            if (!movtosMap.has(movtoKey)) {
              movtosMap.set(movtoKey, { data_movto: item.data_movto, tipo_movto: item.tipo_movto, cod_origem_movto: item.cod_origem_movto })
            }
            const movto = movtosMap.get(movtoKey)
            movto[tamanho] = (movto[tamanho] || 0) + movimento
            if (includeInStock) graded[tamanho] += movimento
          }
          for (const t in graded) {
            if (!t.endsWith('_E') && t !== 'totais') saldo_estoq += Math.max(0, graded[t] || 0)
          }
          const reduced_movtos = Array.from(movtosMap.values()).sort((a, b) =>
            moment(b.data_movto, 'DD/MM/YYYY').toDate() - moment(a.data_movto, 'DD/MM/YYYY').toDate()
          )
          const first = items[0]
          const last = items[items.length - 1]
          const des_produto_clean = (first.des_produto || '').replace((first.des_cor || ''), '').replace((first.des_tamanho || ''), '').replace((first.nom_marca || ''), '').trim() || first.des_produto || ''
          mapped.push({
            _virtualId: `${ref_group}-${cor}`,
            nom_marca: first.nom_marca,
            dat_cadastro: first.dat_cadastro,
            dat_ultcompra: last.dat_ultcompra,
            cod_referencia: first.cod_referencia,
            des_cor: first.des_cor,
            des_produto: des_produto_clean,
            img: first.img,
            vlr_custo_bruto: first.vlr_custo_bruto,
            vlr_venda1: first.vlr_venda1,
            totais_E: saldo_entrada,
            totais: saldo_estoq,
            movtos: reduced_movtos,
            ...graded
          })
        }
      }
      return mapped
    },
    products() {
      return this.mappedItemsComputed
    },
    hasColumnFilters() {
      return Object.values(this.debouncedFilters).some(v => (v || '').trim() !== '')
    },
    metaKeys() {
      return new Set([
        'nom_marca', 'dat_cadastro', 'dat_ultcompra', 'cod_referencia', 'des_cor', 'des_produto', 'img',
        'vlr_custo_bruto', 'vlr_venda1', 'totais_E', 'totais', '_virtualId', 'movtos'
      ])
    },
    allPredefinedSizes() {
      const set = new Set()
      for (const g of ALL_GROUPS) {
        for (const s of g.sizes) set.add(String(s))
      }
      return set
    },
    visibleCols() {
      const seen = new Set()
      const cols = []
      for (const g of ALL_GROUPS) {
        if (!g || !this.selectedGroupIds.includes(g.id)) continue
        for (const s of (g.sizes || [])) {
          if (s == null) continue
          const key = String(s)
          if (!seen.has(key)) {
            seen.add(key)
            cols.push({ key, catId: g.catId, catColor: g.catColor, catBg: g.catBg })
          }
        }
      }
      const predefined = this.allPredefinedSizes
      const meta = this.metaKeys
      for (const p of this.products) {
        if (!p) continue
        for (const k of Object.keys(p)) {
          if (k.endsWith('_E') || meta.has(k)) continue
          if (typeof p[k] !== 'number' && typeof p[k + '_E'] !== 'number') continue
          const key = String(k)
          if (seen.has(key) || predefined.has(key)) continue
          seen.add(key)
          cols.push({ key, catId: 'especiais', catColor: '#64748b', catBg: '#f1f5f9' })
        }
      }
      cols.sort((a, b) => (a && b && a.key && b.key) ? compareSizeKeys(a.key, b.key) : 0)
      return cols.filter(c => c && c.key)
    },
    visibleCatIds() {
      return [...new Set((this.visibleCols || []).filter(c => c && c.catId).map(c => c.catId))]
    },
    colSet() {
      return new Set((this.visibleCols || []).filter(c => c && c.key).map(c => c.key))
    },
    hasSizeFilters() {
      return Object.keys(this.sizeFilters || {}).some(k => (this.sizeFilters[k] || '').trim() !== '')
    },
    allMatchingProducts() {
      let list = this.products
      if (this.hasColumnFilters) {
        list = list.filter(item => {
          return Object.keys(this.debouncedFilters).every(key => {
            const fv = (this.debouncedFilters[key] || '').trim()
            if (!fv) return true
            const iv = item[key]
            if (iv == null) return false
            return this.advancedFilterMatch(String(iv), fv, key)
          })
        })
      }
      if (this.hasSizeFilters) {
        list = list.filter(p => this.matchesSizeFilters(p))
      }
      return list.filter(p => this.matchesFilter(p))
    },
    visibleProducts() {
      return this.allMatchingProducts.filter(p =>
        Object.keys(p).some(k => !k.endsWith('_E') && k !== 'totais' && k !== 'totais_E' && typeof p[k] === 'number' && this.colSet.has(String(k)))
      )
    },
    hiddenProducts() {
      return this.allMatchingProducts.filter(p =>
        !Object.keys(p).some(k => !k.endsWith('_E') && k !== 'totais' && k !== 'totais_E' && typeof p[k] === 'number' && this.colSet.has(String(k)))
      )
    },
    activeCols() {
      return (this.visibleCols || []).filter(col =>
        col && col.key && this.visibleProducts.some(p => (Number(p[col.key]) || 0) > 0 || (Number(p[col.key + '_E']) || 0) > 0)
      )
    },
    safeActiveCols() {
      try {
        return (this.activeCols || []).filter(c => c && c.key && typeof c.key === 'string')
      } catch (_) {
        return []
      }
    },
    /** Guaranteed-safe array for v-for; never contains undefined or items without key */
    safeColsIter() {
      const arr = this.safeActiveCols || []
      return Array.isArray(arr) ? arr.filter(c => c != null && c && typeof c.key === 'string') : []
    },
    movimentosFields() {
      const gradeKeys = (this.safeColsIter || []).map(c => c.key).filter(k => k != null && k !== '')
      const sizeFields = gradeKeys.map(k => ({ key: k, label: k, sortable: true })).filter(f => f && f.key)
      return [
        { key: 'data_movto', label: 'Data', sortable: true },
        { key: 'origem', label: 'Origem', sortable: true },
        ...sizeFields,
        { key: 'tot_movto', label: 'Tot.', sortable: true }
      ].filter(f => f && f.key)
    },
    sortedProducts() {
      const list = [...this.visibleProducts]
      const key = this.sortKey
      if (!key) return list
      const dir = this.sortDir
      return list.sort((a, b) => {
        let va, vb
        if (key === 'perf') {
          va = this.perfPct(a)
          vb = this.perfPct(b)
        } else if (key === 'total') {
          va = this.productTotalStock(a)
          vb = this.productTotalStock(b)
        } else if (key === 'cost') {
          va = Number(a.vlr_custo_bruto) || 0
          vb = Number(b.vlr_custo_bruto) || 0
        } else if (key === 'brand') {
          va = (a.nom_marca || '').toString().toLowerCase()
          vb = (b.nom_marca || '').toString().toLowerCase()
        } else if (key === 'ref') {
          va = (a.cod_referencia || '').toString().toLowerCase()
          vb = (b.cod_referencia || '').toString().toLowerCase()
        } else if (key === 'color') {
          va = (a.des_cor || '').toString().toLowerCase()
          vb = (b.des_cor || '').toString().toLowerCase()
        } else if (key === 'desc') {
          va = (a.des_produto || '').toString().toLowerCase()
          vb = (b.des_produto || '').toString().toLowerCase()
        } else if (key === 'price') {
          va = Number(a.vlr_venda1) || 0
          vb = Number(b.vlr_venda1) || 0
        } else if (key === 'dat_cadastro' || key === 'dat_ultcompra') {
          const dA = (a[key] || '').toString()
          const dB = (b[key] || '').toString()
          va = dA ? moment(dA, 'DD/MM/YYYY').valueOf() : 0
          vb = dB ? moment(dB, 'DD/MM/YYYY').valueOf() : 0
        } else {
          va = (a[key] || '').toString().toLowerCase()
          vb = (b[key] || '').toString().toLowerCase()
        }
        if (va < vb) return -1 * dir
        if (va > vb) return 1 * dir
        return 0
      })
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.sortedProducts.length / this.perPage))
    },
    pageNumbers() {
      const total = Math.min(10, this.totalPages)
      const start = Math.max(1, this.currentPage - Math.floor(total / 2))
      return Array.from({ length: total }, (_, i) => Math.min(start + i, this.totalPages))
    },
    pageNumbersBottom() {
      return this.pageNumbers
    },
    pageData() {
      if (!this.pagination) return this.sortedProducts
      const start = (this.currentPage - 1) * this.perPage
      return this.sortedProducts.slice(start, start + this.perPage)
    },
    colTotals() {
      const stock = {}
      const stockE = {}
      for (const col of this.safeColsIter) {
        if (col && col.key) {
          stock[col.key] = 0
          stockE[col.key] = 0
        }
      }
      for (const p of this.visibleProducts) {
        for (const col of this.safeColsIter) {
          if (col && col.key) {
            stock[col.key] = (stock[col.key] || 0) + Math.max(0, Number(p[col.key]) || 0)
            stockE[col.key] = (stockE[col.key] || 0) + Number(p[col.key + '_E']) || 0
          }
        }
      }
      return { stock, stockE }
    },
    totalStockAll() {
      return Object.values(this.colTotals.stock).reduce((a, b) => a + b, 0)
    },
    totalEntriesAll() {
      return Object.values(this.colTotals.stockE).reduce((a, b) => a + b, 0)
    },
    detailColspan() {
      return 4 + (this.showDataCad ? 1 : 0) + (this.showDataUltCompra ? 1 : 0) + (this.showImg ? 1 : 0) + (this.showImgLink ? 1 : 0) + 1 + this.safeActiveCols.length + 1 + (this.showCost ? 1 : 0) + 1 + (this.showPerf ? 1 : 0)
    }
  },
  mounted() {
    this.loadMarcas()
    this.debouncedFilters = { ...this.filters }
  },
  methods: {
    selectedInCat(cat) {
      return (cat && cat.groups || []).filter(g => g && g.id && this.selectedGroupIds.includes(g.id))
    },
    filteredGroupsInCat(cat) {
      const groups = (cat && cat.groups) ? cat.groups.filter(g => g && g.id) : []
      if (!this.gradeSearch) return groups
      const q = this.gradeSearch.toLowerCase()
      return groups.filter(g =>
        (g.label || '').toLowerCase().includes(q) || (g.sizes || []).some(s => String(s).toLowerCase().includes(q))
      )
    },
    toggleCatOpen(id) {
      const s = new Set(this.openCats)
      if (s.has(id)) s.delete(id)
      else s.add(id)
      this.openCats = s
    },
    toggleGroup(id) {
      if (this.selectedGroupIds.includes(id)) {
        this.selectedGroupIds = this.selectedGroupIds.filter(x => x !== id)
      } else {
        this.selectedGroupIds = [...this.selectedGroupIds, id]
      }
    },
    toggleAllInCat(cat) {
      const allOn = this.selectedInCat(cat).length === cat.groups.length
      const ids = cat.groups.map(g => g.id)
      if (allOn) {
        this.selectedGroupIds = this.selectedGroupIds.filter(x => !ids.includes(x))
      } else {
        const set = new Set(this.selectedGroupIds)
        ids.forEach(id => set.add(id))
        this.selectedGroupIds = [...set]
      }
    },
    groupBtnStyle(g, cat) {
      const on = this.selectedGroupIds.includes(g.id)
      return {
        borderColor: on ? cat.color : '#e5e7eb',
        background: on ? cat.bg : '#fff',
        color: on ? cat.color : '#6b7280',
        fontWeight: on ? 700 : 400
      }
    },
    handleAutoDetect() {
      const allKeys = new Set()
      this.products.forEach(p => {
        Object.keys(p).forEach(k => {
          if (typeof p[k] === 'number' && !k.endsWith('_E') && k !== 'totais' && k !== 'totais_E') allKeys.add(k)
        })
      })
      const det = ALL_GROUPS.filter(g => g.sizes.some(s => allKeys.has(String(s)))).map(g => g.id)
      this.selectedGroupIds = det
      this.autoDetected = det
    },
    clearGrades() {
      this.selectedGroupIds = []
      this.autoDetected = []
    },
    matchesFilter(p) {
      const f = (this.globalFilter || '').trim().toLowerCase()
      if (!f) return true
      const tokens = f.split(/\s+/)
      const visibleCatIds = this.visibleCatIds
      return tokens.every(tok => {
        if (tok.startsWith('-')) {
          const term = tok.slice(1)
          const inCat = visibleCatIds.some(cid => {
            const cat = this.categories.find(c => c.id === cid)
            return cat && (cat.label.toLowerCase().includes(term) || cid.includes(term))
          })
          return !inCat
        }
        if (tok.startsWith('brand:') || tok.startsWith('marca:')) return (p.nom_marca || '').toLowerCase().includes(tok.slice(tok.indexOf(':') + 1))
        if (tok.startsWith('color:') || tok.startsWith('cor:')) return (p.des_cor || '').toLowerCase().includes(tok.slice(tok.indexOf(':') + 1))
        if (tok.startsWith('ref:')) return (p.cod_referencia || '').toLowerCase().includes(tok.slice(4))
        if (tok.startsWith('desc:')) return (p.des_produto || '').toLowerCase().includes(tok.slice(5))
        if (tok.startsWith('date:') || tok.startsWith('data:')) return (p.dat_cadastro || '').includes(tok.slice(tok.indexOf(':') + 1))
        if (tok.startsWith('>')) { const n = Number(tok.slice(1)); return !isNaN(n) && (Number(p.vlr_venda1) || 0) > n }
        if (tok.startsWith('<')) { const n = Number(tok.slice(1)); return !isNaN(n) && (Number(p.vlr_venda1) || 0) < n }
        const haystack = `${p.nom_marca || ''} ${p.cod_referencia || ''} ${p.des_cor || ''} ${p.des_produto || ''}`.toLowerCase()
        return haystack.includes(tok)
      })
    },
    parseSizeFilterPart(part) {
      const s = (part || '').trim()
      if (!s) return () => true
      const num = Number(s)
      if (!isNaN(num) && s === String(num)) return v => Number(v) === num
      if (s.startsWith('>=')) { const n = Number(s.slice(2)); return v => !isNaN(n) && Number(v) >= n }
      if (s.startsWith('<=')) { const n = Number(s.slice(2)); return v => !isNaN(n) && Number(v) <= n }
      if (s.startsWith('>')) { const n = Number(s.slice(1)); return v => !isNaN(n) && Number(v) > n }
      if (s.startsWith('<')) { const n = Number(s.slice(1)); return v => !isNaN(n) && Number(v) < n }
      return () => true
    },
    matchesSizeFilters(p) {
      for (const colKey of Object.keys(this.sizeFilters || {})) {
        const raw = (this.sizeFilters[colKey] || '').trim()
        if (!raw) continue
        const parts = raw.split(';')
        const entradaPart = parts[0] ? this.parseSizeFilterPart(parts[0].trim()) : () => true
        const stockPart = parts[1] ? this.parseSizeFilterPart(parts[1].trim()) : () => true
        const entrada = Number(p[colKey + '_E']) || 0
        const stock = this.formatStock(p[colKey])
        if (!entradaPart(entrada) || !stockPart(stock)) return false
      }
      return true
    },
    advancedFilterMatch(itemVal, filterVal, fieldKey) {
      const itemStr = String(itemVal).toLowerCase()
      const filterStr = String(filterVal).toLowerCase().trim()
      if (filterStr.startsWith('-')) return !itemStr.includes(filterStr.slice(1).trim())
      if (filterStr.includes(':')) {
        const parts = filterStr.split(':')
        if (parts.length === 2) {
          const minStr = parts[0].trim()
          const maxStr = parts[1].trim()
          if (fieldKey && (fieldKey.includes('dat_') || fieldKey.includes('data'))) {
            try {
              const itemDate = moment(itemVal, 'DD/MM/YYYY')
              const minDate = moment(minStr, 'YYYY-MM-DD')
              const maxDate = moment(maxStr, 'YYYY-MM-DD')
              if (itemDate.isValid() && minDate.isValid() && maxDate.isValid()) {
                return itemDate.isSameOrAfter(minDate, 'day') && itemDate.isSameOrBefore(maxDate, 'day')
              }
            } catch (e) { /* ignore */ }
          }
          const itemNum = parseFloat(itemVal)
          const minN = parseFloat(minStr)
          const maxN = parseFloat(maxStr)
          if (!isNaN(itemNum) && !isNaN(minN) && !isNaN(maxN)) return itemNum >= minN && itemNum <= maxN
        }
      }
      if (filterStr.includes('+')) return filterStr.split('+').map(v => v.trim()).some(v => itemStr.includes(v))
      if (filterStr.includes('&')) return filterStr.split('&').map(v => v.trim()).every(v => itemStr.includes(v))
      return itemStr.includes(filterStr)
    },
    formatStock(v) {
      if (v == null || isNaN(v)) return 0
      return Math.max(0, Math.round(Number(v)))
    },
    toggleDetails(item) {
      this.expandedRowId = this.expandedRowId === item._virtualId ? null : item._virtualId
    },
    formatMovimentos(movtos) {
      if (!movtos || !Array.isArray(movtos)) return []
      const gradeKeys = (this.safeActiveCols || []).map(c => c.key)
      return movtos.map(movto => {
        const cod_origem = movto.cod_origem_movto != null ? movto.cod_origem_movto : movto.tipo_movto
        const origem_nome = (this.origemMapping && this.origemMapping[cod_origem]) || `Origem ${cod_origem}`
        let tot = 0
        gradeKeys.forEach(k => { const v = movto[k]; if (typeof v === 'number' && !isNaN(v)) tot += v })
        return { ...movto, cod_origem, origem: origem_nome, origem_nome, tipo_movto: movto.tipo_movto || 'E', tot_movto: tot }
      }).filter(m => m.data_movto)
    },
    getOrigemClass(cod_origem) {
      const map = { 2: 'text-primary', 3: 'text-info', 4: 'text-warning', 7: 'text-success', 9: 'text-primary', 12: 'text-danger', 15: 'text-secondary' }
      return map[cod_origem] || 'text-dark'
    },
    getMovimentoClass(value) {
      if (value == null || value === 0) return 'text-muted'
      return Number(value) > 0 ? 'text-success font-weight-bold' : 'text-danger font-weight-bold'
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      try { return moment(dateStr, 'DD/MM/YYYY').format('DD/MM/YYYY') } catch (e) { return dateStr }
    },
    handleSort(key) {
      if (this.sortKey === key) this.sortDir = -this.sortDir
      else { this.sortKey = key; this.sortDir = 1 }
    },
    sortIcon(key) {
      if (this.sortKey !== key) return '↕'
      return this.sortDir === 1 ? '↑' : '↓'
    },
    productTotalStock(p) {
      let sum = 0
      for (const col of this.safeColsIter) {
        if (col && col.key) sum += Math.max(0, Number(p[col.key]) || 0)
      }
      return sum
    },
    productTotalEntries(p) {
      let sum = 0
      for (const col of this.safeColsIter) {
        if (col && col.key) sum += Number(p[col.key + '_E']) || 0
      }
      return sum
    },
    perfPct(p) {
      const totalE = this.productTotalEntries(p)
      const stock = this.productTotalStock(p)
      if (!totalE) return 0
      const sold = Math.max(0, totalE - stock)
      return Math.round((sold / totalE) * 100)
    },
    perfLabel(p) {
      const pct = this.perfPct(p)
      if (pct >= 60) return 'Rápido'
      if (pct >= 35) return 'Médio'
      return 'Lento'
    },
    perfFillStyle(p) {
      const pct = Math.max(2, this.perfPct(p))
      const colors = { rapid: '#22c55e', medium: '#f59e0b', slow: '#ef4444' }
      const c = pct >= 60 ? colors.rapid : pct >= 35 ? colors.medium : colors.slow
      return { width: pct + '%', background: c }
    },
    perfLabelStyle(p) {
      const pct = this.perfPct(p)
      const color = pct >= 60 ? '#15803d' : pct >= 35 ? '#b45309' : '#b91c1c'
      const bg = pct >= 60 ? '#f0fdf4' : pct >= 35 ? '#fffbeb' : '#fef2f2'
      return { color, background: bg }
    },
    sizeCellClass(stock, sold) {
      const sv = Number(stock || 0)
      const vv = Number(sold || 0)
      if (sv > 0 && vv > 0) return 'lev2-cell-sold'
      if (sv > 0) return 'lev2-cell-stock'
      return 'lev2-cell-empty'
    },
    thSizeStyle(col, i) {
      const prev = this.safeActiveCols[i - 1]
      const catChange = prev && prev.catId !== col.catId
      return {
        background: col.catBg,
        borderBottom: `2px solid ${col.catColor}`,
        borderLeft: catChange ? `2px solid ${col.catColor}` : undefined
      }
    },
    tdTotStyle(col) {
      const s = this.colTotals.stock[col.key]
      return {
        background: s > 0 ? col.catBg : '#fafafa',
        color: s > 0 ? col.catColor : undefined
      }
    },
    tdSizeBorder(col, i) {
      const prev = this.safeActiveCols[i - 1]
      const catChange = prev && prev.catId !== col.catId
      return { borderLeft: catChange ? `2px solid ${col.catColor}33` : undefined }
    },
    formatMoney(v) {
      const n = Number(v)
      return (isNaN(n) ? 0 : n).toFixed(2).replace('.', ',')
    },
    imgForProduct(p) {
      const key = `${String(p.cod_referencia ?? '')}|${String(p.des_cor ?? '')}`
      return this.imagesByKey[key] || p.img
    },
    imgSrc(img) {
      if (!img) return ''
      const s = typeof img === 'string' ? img : ''
      if (!s) return ''
      if (s.startsWith('http') || s.startsWith('data:')) return s
      if (/^[A-Za-z0-9+/=]+$/.test(s) && s.length > 50) return `data:image/jpeg;base64,${s}`
      return s
    },
    imgLinkKey(p) {
      return `${String(p.cod_referencia ?? '')}|${String(p.des_cor ?? '')}`
    },
    getImgLinkDisplayValue(p) {
      const key = this.imgLinkKey(p)
      if (this.imgLinkEditBuffer[key] !== undefined) return this.imgLinkEditBuffer[key]
      const img = this.imgForProduct(p)
      if (!img || typeof img !== 'string') return ''
      if (img.startsWith('http')) return img
      if (img.startsWith('data:')) return '[Imagem]'
      if (/^[A-Za-z0-9+/=]+$/.test(img) && img.length > 50) return '[Imagem]'
      return img
    },
    onImgLinkFocus(p) {
      const key = this.imgLinkKey(p)
      if (this.imgLinkEditBuffer[key] === undefined) {
        const img = this.imgForProduct(p)
        const disp = (img && typeof img === 'string' && img.startsWith('http')) ? img : ''
        this.$set(this.imgLinkEditBuffer, key, disp)
      }
    },
    async onImgLinkPaste(p, e) {
      const items = e.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const blob = item.getAsFile()
          if (!blob) continue
          const base64 = await this.blobToBase64(blob)
          if (base64) {
            this.$delete(this.imgLinkEditBuffer, this.imgLinkKey(p))
            this.setProductImage(p, base64)
            await this.saveProductImage(p, base64)
            this.$bvToast && this.$bvToast.toast('Imagem colada e salva.', { variant: 'success' })
          }
          return
        }
      }
    },
    onImgLinkInput(p, e) {
      const key = this.imgLinkKey(p)
      const val = (e.target && e.target.value) || ''
      this.$set(this.imgLinkEditBuffer, key, val)
    },
    async onImgLinkBlur(p) {
      const key = this.imgLinkKey(p)
      const raw = this.imgLinkEditBuffer[key]
      this.$delete(this.imgLinkEditBuffer, key)
      if (!raw || typeof raw !== 'string') return
      const trimmed = raw.trim()
      if (!trimmed) return
      if (trimmed.startsWith('http')) {
        try {
          const base64 = await this.fetchImageAsBase64(trimmed)
          if (base64) {
            this.setProductImage(p, base64)
            await this.saveProductImage(p, base64)
            this.$bvToast && this.$bvToast.toast('Imagem carregada e salva.', { variant: 'success' })
          }
        } catch (err) {
          this.$bvToast && this.$bvToast.toast('Erro ao carregar imagem da URL.', { variant: 'danger' })
        }
      } else if (trimmed.startsWith('data:image')) {
        const m = trimmed.match(/^data:image\/[^;]+;base64,(.+)$/)
        const base64 = m ? m[1] : trimmed
        if (base64) {
          this.setProductImage(p, base64)
          await this.saveProductImage(p, base64)
        }
      }
    },
    blobToBase64(blob) {
      return new Promise((resolve) => {
        const r = new FileReader()
        r.onload = () => {
          const dataUrl = r.result
          if (typeof dataUrl === 'string' && dataUrl.startsWith('data:')) {
            const m = dataUrl.match(/^data:image\/[^;]+;base64,(.+)$/)
            resolve(m ? m[1] : dataUrl)
          } else resolve(null)
        }
        r.onerror = () => resolve(null)
        r.readAsDataURL(blob)
      })
    },
    fetchImageAsBase64(url) {
      return axios.get(url, { responseType: 'blob' })
        .then(res => {
          if (res.data && res.data.type && res.data.type.startsWith('image/')) {
            return this.blobToBase64(res.data)
          }
          return null
        })
    },
    setProductImage(p, imgVal) {
      const key = this.imgLinkKey(p)
      this.$set(this.imagesByKey, key, imgVal)
      const obj = this.subgrouped_items_bycolor_obj
      const ref = String(p.cod_referencia ?? '')
      const cor = String(p.des_cor ?? '')
      if (obj[ref] && obj[ref][cor] && Array.isArray(obj[ref][cor]) && obj[ref][cor][0]) {
        this.$set(obj[ref][cor][0], 'img', imgVal)
      }
    },
    async saveProductImage(p, imgVal) {
      const ref = String(p.cod_referencia ?? '')
      const cor = String(p.des_cor ?? '')
      const marca = String(p.nom_marca ?? '')
      const des_produto = String(p.des_produto ?? '')
      if (!ref || !marca) {
        this.$bvToast && this.$bvToast.toast('Produto sem referência ou marca.', { variant: 'warning' })
        return
      }
      try {
        await axios.put('/api/produtos/image', {
          cod_referencia: ref,
          nom_marca: marca,
          des_cor: cor,
          des_produto,
          img: imgVal
        })
      } catch (err) {
        this.$bvToast && this.$bvToast.toast('Erro ao salvar imagem.', { variant: 'danger' })
      }
    },
    loadMarcas() {
      axios.get('/api/read/marcas/').then(res => {
        const raw = res.data || []
        this.marcas = raw.map((m, i) => {
          if (!m || typeof m !== 'object') return { cod_marca: i, nom_marca: '(inválido)' }
          const cod = m.cod_marca ?? m.COD_MARCA ?? i
          const nom = (m.nom_marca ?? m.NOM_MARCA ?? '').toString()
          return { cod_marca: cod, nom_marca: nom || '(sem nome)' }
        }).filter(m => m.cod_marca != null)
        // cod_marca sync to child via :value prop
      }).catch(() => {})
    },
    objectify(row) {
      if (!Array.isArray(row)) return null
      let dat_cad = row[20]
      let dat_ult = row[21]
      if (dat_cad && typeof dat_cad === 'object' && dat_cad.toISOString) dat_cad = moment(dat_cad).format('DD/MM/YYYY')
      else if (dat_cad) dat_cad = moment(String(dat_cad).slice(0, 10)).format('DD/MM/YYYY')
      if (dat_ult && typeof dat_ult === 'object' && dat_ult.toISOString) dat_ult = moment(dat_ult).format('DD/MM/YYYY')
      else if (dat_ult) dat_ult = moment(String(dat_ult).slice(0, 10)).format('DD/MM/YYYY')
      return {
        cod_grupo: row[0], des_grupo: row[1], cod_subgrupo: row[2], des_subgrupo: row[3],
        cod_produto: row[4], des_produto: row[5], cod_barra: row[6], cod_referencia: row[7],
        qtd: row[8], saldo_estoque: row[9], vlr_custo_bruto: row[10], vlr_custo_aquis: row[11], vlr_venda1: row[12],
        total: row[13], cod_grade: row[14], des_grade: row[15], cod_tamanho: row[16], des_tamanho: row[17],
        cod_cor: row[18], des_cor: (row[19] || '').toString() || 'padrao',
        dat_cadastro: dat_cad, dat_ultcompra: dat_ult,
        cod_fornecedor: row[22], raz_fornecedor: row[23], fan_fornecedor: row[24],
        cod_marca: row[25], nom_marca: (row[26] || '').toString(),
        tipo_movto: row[27], qtd_movto: row[28], data_movto: row[29] ? moment(row[29]).format('DD/MM/YYYY') : null,
        cod_movto: row[30], cod_origem_movto: row[31],
        img: ''
      }
    },
    groupItemsByRef() {
      const map = new Map()
      this.items.forEach(e => {
        const ref = String(e.cod_referencia ?? '')
        if (!map.has(ref)) map.set(ref, [])
        map.get(ref).push(e)
      })
      this.refs_array = Object.fromEntries(map)
    },
    subgroupItemsByColor() {
      const obj = {}
      for (const ref of Object.keys(this.refs_array)) {
        const arr = this.refs_array[ref]
        arr.forEach(item => { if (!item.des_cor) item.des_cor = 'padrao' })
        const byColor = new Map()
        arr.forEach(e => {
          const cor = String(e.des_cor ?? '')
          if (!byColor.has(cor)) byColor.set(cor, [])
          byColor.get(cor).push(e)
        })
        obj[ref] = Object.fromEntries(byColor)
      }
      this.subgrouped_items_bycolor_obj = obj
    },
    onSubmit() {
      if (!this.cod_marca) return
      const ini = (this.data_cadastro_ini || '').replace(/\//g, '-')
      const fim = (this.data_cadastro_fim || '').replace(/\//g, '-')
      if (!ini || !fim) {
        this.$bvToast && this.$bvToast.toast('Informe data inicial e final.', { variant: 'warning' })
        return
      }
      this.loading = true
      this.loadTime = null
      const start = performance.now()
      const sourceParam = this.useMongo ? '?source=mongo' : ''
      axios.get(`/api/levantamentos/${ini}/${fim}/${this.cod_marca}${sourceParam}`)
        .then(res => {
          this.loadTime = Math.round(performance.now() - start)
          this.imagesByKey = {}
          this.items = (res.data || []).map(r => this.objectify(r)).filter(Boolean)
          this.groupItemsByRef()
          this.subgroupItemsByColor()
          this.$nextTick(() => {
            setTimeout(() => { this.carregarImagens() }, 300)
          })
        })
        .catch(err => {
          this.$bvToast && this.$bvToast.toast('Erro: ' + ((err.response && err.response.data && err.response.data.detail) || err.message), { variant: 'danger' })
          this.items = []
          this.subgrouped_items_bycolor_obj = {}
          this.imagesByKey = {}
        })
        .finally(() => { this.loading = false })
    },
    async forceSync() {
      if (!this.cod_marca) return
      const ini = (this.data_cadastro_ini || '').replace(/\//g, '-')
      const fim = (this.data_cadastro_fim || '').replace(/\//g, '-')
      if (!ini || !fim) {
        this.$bvToast && this.$bvToast.toast('Informe data inicial e final.', { variant: 'warning' })
        return
      }
      this.syncing = true
      try {
        const res = await axios.post(`/api/levantamentos/sync?data_ini=${encodeURIComponent(ini)}&data_fim=${encodeURIComponent(fim)}&cod_marca=${encodeURIComponent(this.cod_marca)}`)
        const msg = res.data?.rows_synced != null ? `${res.data.rows_synced} linhas sincronizadas` : 'Sincronizado'
        this.$bvToast && this.$bvToast.toast(msg, { variant: 'success' })
        this.useMongo = true
      } catch (err) {
        this.$bvToast && this.$bvToast.toast('Erro ao sincronizar: ' + (err.response?.data?.detail || err.message), { variant: 'danger' })
      } finally {
        this.syncing = false
      }
    },
    carregarImagens() {
      if (!this.products.length) return
      const obj = this.subgrouped_items_bycolor_obj
      const payload = this.products.map(p => {
        const ref = String(p.cod_referencia ?? '')
        const cor = String(p.des_cor ?? '')
        const first = obj[ref] && obj[ref][cor] && obj[ref][cor][0] ? obj[ref][cor][0] : null
        const rawDesProduto = first && first.des_produto != null ? String(first.des_produto) : String(p.des_produto ?? '')
        return {
          cod_referencia: ref,
          nom_marca: String(p.nom_marca ?? ''),
          des_cor: cor,
          des_produto: rawDesProduto
        }
      })
      axios.put('/api/produtos/images/', payload)
        .then(res => {
          const data = res.data
          if (!data) return
          const arr = Array.isArray(data) ? data : Object.keys(data).map(k => data[k])
          for (const it of arr) {
            if (!it) continue
            const ref = String(it.cod_referencia ?? '')
            const cor = String(it.des_cor ?? '')
            const key = `${ref}|${cor}`
            const imgVal = it.img
            if (imgVal != null && imgVal !== '') {
              this.$set(this.imagesByKey, key, imgVal)
            }
            const obj = this.subgrouped_items_bycolor_obj
            if (obj[ref] && obj[ref][cor] && Array.isArray(obj[ref][cor]) && obj[ref][cor][0]) {
              this.$set(obj[ref][cor][0], 'img', imgVal)
            }
          }
        })
        .catch(() => {})
    }
  }
}
</script>

<style scoped>
.lev2 { font-family: 'DM Sans', system-ui, sans-serif; background: #f1f5f9; min-height: 100vh; padding: 14px; font-size: 13px; }
.lev2-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.lev2-title { font-size: 19px; font-weight: 700; color: #0f172a; margin: 0; }
.lev2-subtitle { font-size: 11px; color: #64748b; margin-top: 1px; }
.lev2-header-actions { margin-left: auto; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.lev2-load-bar { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-bottom: 12px; padding: 10px; background: #fff; border: 1px solid #e5e7eb; border-radius: 9px; }
.lev2-load-field { display: flex; flex-direction: column; gap: 4px; }
.lev2-label { font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.4px; }
.lev2-input { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 140px; }
.lev2-actions { flex-direction: row; align-items: center; flex-wrap: wrap; gap: 8px; }
.lev2-mongo-toggle { margin-right: 4px; white-space: nowrap; }
.lev2-load-ms { font-size: 12px; color: #6b7280; margin-left: 8px; }
.lev2-marca-wrap { position: relative; min-width: 200px; }
.lev2-marca-combo { position: relative; }
.lev2-marca-input { min-width: 200px; }
.lev2-marca-dropdown { position: absolute; left: 0; right: 0; top: 100%; margin-top: 2px; max-height: 220px; overflow-y: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); z-index: 100; }
.lev2-marca-option { padding: 6px 10px; cursor: pointer; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
.lev2-marca-option:hover, .lev2-marca-option.active { background: #eff6ff; color: #1d4ed8; }
.lev2-marca-cod { font-size: 11px; color: #64748b; margin-left: 4px; }
.lev2-marca-empty { padding: 8px 10px; font-size: 12px; color: #94a3b8; }
.lev2-marca-hint { font-size: 10px; color: #64748b; margin-top: 2px; }
.lev2-hidden-alert { background: #fefce8; border: 1.5px solid #f59e0b; border-radius: 8px; padding: 8px 14px; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.lev2-hidden-icon { font-size: 16px; }
.lev2-controls { display: grid; grid-template-columns: 1fr 280px; gap: 10px; margin-bottom: 12px; align-items: start; }
.lev2-grade-panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; font-size: 12px; }
.lev2-grade-header { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.lev2-grade-title { font-weight: 700; color: #0f172a; }
.lev2-grade-badge { font-size: 10px; background: #e0e7ff; color: #3730a3; padding: 1px 7px; border-radius: 99px; font-weight: 700; }
.lev2-grade-btn-auto { margin-left: auto; }
.lev2-grade-search { padding: 3px 5px; font-size: 11px; border: 1px solid #d1d5db; border-radius: 4px; width: 120px; outline: none; }
.lev2-auto-msg { padding: 4px 12px; background: #eff6ff; font-size: 11px; color: #1d4ed8; border-bottom: 1px solid #bfdbfe; }
.lev2-cats { max-height: 240px; overflow-y: auto; }
.lev2-cat { border-bottom: 1px solid #f0f0f0; }
.lev2-cat-head { padding: 5px 12px; display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; background: #fafafa; }
.lev2-cat-head.lev2-cat-selected { background: var(--cat-bg, #fafafa); }
.lev2-cat-arrow { font-size: 11px; }
.lev2-cat-label { font-weight: 700; color: #374151; }
.lev2-cat-count { font-size: 10px; font-weight: 700; color: #fff; background: var(--cat-color); padding: 1px 6px; border-radius: 99px; }
.lev2-cat-all { margin-left: auto; font-size: 10px; padding: 1px 7px; }
.lev2-cat-all.active { background: var(--cat-color); color: #fff; border-color: var(--cat-color); }
.lev2-cat-groups { padding: 6px 12px 8px; display: flex; flex-wrap: wrap; gap: 4px; background: #fff; border-bottom: 1px solid #f0f0f0; }
.lev2-group-btn { padding: 2px 7px; font-size: 11px; border-radius: 4px; cursor: pointer; border: 1.5px solid; }
.lev2-group-n { font-size: 9px; opacity: 0.5; }
.lev2-right-panel { display: flex; flex-direction: column; gap: 8px; }
.lev2-filter-card, .lev2-pagination-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 9px; padding: 10px; }
.lev2-filter-input { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 11px; width: 100%; outline: none; box-sizing: border-box; }
.lev2-filter-hint { margin-top: 5px; font-size: 10px; color: #94a3b8; line-height: 1.6; }
.lev2-clear-filter { margin-top: 4px; font-size: 10px; padding: 0; color: #ef4444; }
.lev2-pagination-card { display: flex; flex-direction: column; gap: 6px; }
.lev2-per-page-label { font-size: 11px; }
.lev2-per-page { width: 80px; }
.lev2-pagination-bar { display: flex; gap: 4px; justify-content: center; margin-bottom: 8px; flex-wrap: wrap; align-items: center; }
.lev2-page-info { font-size: 11px; color: #64748b; margin-left: 8px; }
.lev2-table-wrap { overflow-x: auto; border-radius: 9px; border: 1px solid #e2e8f0; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.lev2-table-scroll { max-height: 560px; overflow-y: auto; }
.lev2-table { border-collapse: collapse; width: 100%; font-size: 13px; }
.lev2-th { padding: 6px 5px; font-size: 12px; font-weight: 700; color: #374151; background: #f3f4f6; border-bottom: 2px solid #e5e7eb; white-space: nowrap; text-align: center; position: sticky; top: 0; z-index: 2; cursor: pointer; }
.lev2-th-fixed { text-align: left; padding-left: 8px; min-width: 88px; position: sticky; left: 0; z-index: 4; background: #f3f4f6; }
.lev2-th-plus { min-width: 30px; }
.lev2-th-size { min-width: 38px; font-size: 10px; }
.lev2-th-tot { min-width: 50px; border-left: 2px solid #cbd5e1; }
.lev2-totals-row { background: #e0f2fe; border-bottom: 2px solid #93c5fd; }
.lev2-td { padding: 4px 6px; font-size: 12px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.lev2-td-fixed { position: sticky; left: 0; z-index: 1; background: inherit; }
.lev2-totals-row .lev2-td-fixed { background: #bfdbfe; }
.lev2-td-center { text-align: center; }
.lev2-td-has { background: var(--col-bg); }
.lev2-tot-num { font-size: 12px; font-weight: 700; color: #1d4ed8; }
.lev2-tot-sold { font-size: 10px; font-weight: 700; color: #15803d; }
.lev2-tot-entrada { font-size: 10px; color: #94a3b8; line-height: 1.3; font-weight: 400; }
.lev2-size-entrada { font-size: 10px; color: #94a3b8; line-height: 1.3; font-weight: 400; }
.lev2-size-num { font-size: 13px; font-weight: 700; color: #0f172a; line-height: 1.3; }
.lev2-filter-row { background: #f8fafc; }
.lev2-filter-inp { font-size: 12px; padding: 3px 5px; max-width: 100%; }
.lev2-td-date { font-size: 12px; white-space: nowrap; color: #475569; }
.lev2-td-size-filter { padding: 2px; }
.lev2-size-filter-inp { font-size: 10px; padding: 2px 3px; max-width: 52px; }
.lev2-td-details { background: #f1f5f9; padding: 10px; vertical-align: top; }
.lev2-movimentos-wrap { background: #fff; border-radius: 8px; padding: 10px; border: 1px solid #e2e8f0; }
.lev2-movimentos-table { font-size: 11px; }
.lev2-td-tot { border-left: 2px solid #e2e8f0; font-weight: 700; }
.lev2-td-brand { font-weight: 600; color: #0f172a; white-space: nowrap; }
.lev2-td-ref { font-family: monospace; font-size: 11px; color: #4b5563; }
.lev2-badge { font-size: 10px; background: #f3f4f6; padding: 1px 5px; border-radius: 3px; color: #374151; white-space: nowrap; }
.lev2-td-desc { color: #111; max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lev2-th-img { min-width: 60px; }
.lev2-td-img { min-width: 60px; }
.lev2-img { width: 52px; height: 52px; border-radius: 4px; object-fit: cover; border: 1px solid #e5e7eb; display: block; margin: 0 auto; }
.lev2-img-placeholder { display: inline-block; width: 52px; height: 52px; line-height: 52px; text-align: center; font-size: 18px; color: #cbd5e1; background: #f1f5f9; border-radius: 4px; border: 1px dashed #e2e8f0; }
.lev2-img-input { padding: 4px 6px; font-size: 11px; border: 1px solid #d1d5db; border-radius: 4px; min-width: 120px; max-width: 200px; outline: none; }
.lev2-btn-plus { padding: 1px 6px; font-size: 10px; border: 1px solid #d1d5db; border-radius: 3px; cursor: pointer; background: #f9fafb; }
.lev2-td-size { min-width: 38px; padding: 2px 1px; }
.lev2-cell-sold { background: #f0fdf4; }
.lev2-cell-stock { background: #fff; }
.lev2-cell-empty { background: #fafafa; }
.lev2-size-sold { font-size: 11px; font-weight: 700; color: #15803d; }
.lev2-td-right { text-align: right; white-space: nowrap; font-weight: 600; color: #374151; }
.lev2-td-perf { min-width: 120px; }
.lev2-perf { display: flex; align-items: center; gap: 5px; }
.lev2-perf-track { flex: 1; height: 5px; background: #e5e7eb; border-radius: 99px; overflow: hidden; min-width: 50px; }
.lev2-perf-fill { height: 100%; border-radius: 99px; transition: width 0.2s; }
.lev2-perf-label { font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 4px; white-space: nowrap; }
.lev2-data-row.odd { background: #fff; }
.lev2-data-row:not(.odd) { background: #fafafa; }
.lev2-data-row:hover { background: #f0f9ff !important; }
.lev2-td-empty { text-align: center; color: #94a3b8; padding: 40px; }
.lev2-footer { margin-top: 8px; font-size: 10px; color: #94a3b8; }
</style>
