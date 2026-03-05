<template>
  <div class="painel-body" v-if="!notFound">
    <div class="p-header">
      <div class="p-header-left">
        <div class="p-greeting">{{ dateLabel }}</div>
        <div class="p-name">{{ data.nom_vendedor || 'Carregando...' }}</div>
      </div>
      <div class="p-avatar">👤</div>
    </div>

    <div class="p-month-bar">
      <div v-for="m in monthPills" :key="`${m.ano}-${m.mes}`"
        class="p-month-pill" :class="{ active: m.ano === selectedAno && m.mes === selectedMes }"
        @click="selectMonth(m.ano, m.mes)">{{ m.label }}</div>
    </div>

    <div class="p-tab-bar" v-if="loaded">
      <div class="p-tab" :class="{ active: activeTab === 'metas' }" @click="switchTab('metas')">📊 Metas</div>
      <div class="p-tab" :class="{ active: activeTab === 'vendas' }" @click="switchTab('vendas')">🧾 Vendas</div>
    </div>

    <!-- METAS TAB -->
    <div class="p-content" v-show="loaded && activeTab === 'metas'">
      <div v-if="!metasDisponiveis" class="p-metas-unavailable">
        Metas do mês ainda não disponíveis. Por favor aguarde.
      </div>
      <template v-else>
      <div class="p-congrats" v-if="achievedMeta2">🎉 Parabéns! Você atingiu a Meta Máxima!</div>
      <div class="p-congrats congrats-m1" v-else-if="achievedMeta1">🏆 Parabéns! Você atingiu a Meta Intermediária!</div>

      <div class="p-commission" :class="bannerClass">
        <div>
          <div class="p-comm-label">Vendas no mês</div>
          <div class="p-comm-value">R$ {{ formatInt(data.total_vendas) }}<span>reais</span></div>
        </div>
        <div class="p-comm-right">
          <div class="p-comm-sub-label">{{ displayComissaoLabel }}</div>
          <div class="p-comm-sub-value">R$ {{ formatCurrency(displayComissao) }}</div>
        </div>
      </div>

      <div class="p-chart-card">
        <div class="p-chart-header">
          <div>
            <div class="p-chart-title">Evolução do mês</div>
            <div class="p-chart-sub">Acumulado diário vs. metas</div>
          </div>
          <div class="p-today-badge">Dia {{ data.dia_atual }}/{{ data.dias_no_mes }}</div>
        </div>
        <div class="p-chart-wrap">
          <svg class="p-chart-svg" :viewBox="`0 0 ${chartW} ${chartH}`" ref="chartSvg" preserveAspectRatio="none"></svg>
        </div>
        <div class="p-chart-legend">
          <div class="p-legend-item"><div class="p-legend-line solid" style="border-color:#3b6ef5"></div>Realizado</div>
          <div class="p-legend-item"><div class="p-legend-line dashed" style="border-color:#3b6ef5;opacity:.4"></div>Ritmo ideal</div>
          <div class="p-legend-item" v-if="data.meta_1 > 0"><div class="p-legend-line dashed" style="border-color:#e07b00"></div>Meta 1,20%</div>
          <div class="p-legend-item" v-if="data.meta_2 > 0"><div class="p-legend-line dashed" style="border-color:#0a9e6a"></div>Meta 1,50%</div>
        </div>
      </div>

      <div class="p-partial-note" v-if="data.dia_atual < data.dias_no_mes">
        Metas proporcionais calculadas para o dia {{ data.dia_atual }} de {{ data.dias_no_mes }}
      </div>

      <div class="p-progress-grid" v-if="data.meta_1 > 0 || data.meta_2 > 0">
        <div class="p-prog-card card-m1" v-if="data.meta_1 > 0">
          <div class="p-prog-header">
            <div>
              <div class="p-prog-title">Meta intermediária</div>
              <div class="p-prog-main">1,20% — R$ {{ formatInt(data.meta_1) }}</div>
            </div>
            <div class="p-prog-pct-wrap">
              <div class="p-prog-pct">{{ data.pct_meta_1 }}%</div>
              <div class="p-prog-pct-sub">do proporcional</div>
            </div>
          </div>
          <div class="p-prog-track"><div class="p-prog-fill" :style="{ width: Math.min(data.pct_meta_1, 100) + '%' }"></div></div>
          <div class="p-prog-footer" v-if="!achievedMeta1">
            <span>Faltam <strong>R$ {{ formatInt(data.falta_meta_1) }}</strong></span>
            <div class="p-prog-tag" v-if="data.dias_restantes > 0">R$ {{ formatInt(data.por_dia_meta_1) }}/dia</div>
          </div>
          <div class="p-prog-footer" v-else><span style="color:var(--meta1);font-weight:700;">✅ Meta atingida!</span></div>
        </div>

        <div class="p-prog-card card-m2" v-if="data.meta_2 > 0">
          <div class="p-prog-header">
            <div>
              <div class="p-prog-title">Meta máxima</div>
              <div class="p-prog-main">1,50% — R$ {{ formatInt(data.meta_2) }}</div>
            </div>
            <div class="p-prog-pct-wrap">
              <div class="p-prog-pct">{{ data.pct_meta_2 }}%</div>
              <div class="p-prog-pct-sub">do proporcional</div>
            </div>
          </div>
          <div class="p-prog-track"><div class="p-prog-fill" :style="{ width: Math.min(data.pct_meta_2, 100) + '%' }"></div></div>
          <div class="p-prog-footer" v-if="!achievedMeta2">
            <span>Faltam <strong>R$ {{ formatInt(data.falta_meta_2) }}</strong></span>
            <div class="p-prog-tag" v-if="data.dias_restantes > 0">R$ {{ formatInt(data.por_dia_meta_2) }}/dia</div>
          </div>
          <div class="p-prog-footer" v-else><span style="color:var(--meta2);font-weight:700;">✅ Meta atingida!</span></div>
        </div>
      </div>

      <div class="p-stats-row">
        <div class="p-stat-card">
          <div class="p-stat-label">Seu ritmo atual</div>
          <div class="p-stat-val" :class="data.ritmo_atual >= (data.por_dia_meta_1||0) ? 'ok' : 'warn'">R$ {{ formatInt(data.ritmo_atual) }}</div>
          <div class="p-stat-hint">média por dia</div>
        </div>
        <div class="p-stat-card" v-if="data.meta_1 > 0 && !achievedMeta1">
          <div class="p-stat-label">Precisa p/ meta 1,20%</div>
          <div class="p-stat-val warn">R$ {{ formatInt(data.por_dia_meta_1) }}</div>
          <div class="p-stat-hint">nos {{ data.dias_restantes }} dias restantes</div>
        </div>
        <div class="p-stat-card" v-else-if="data.meta_2 > 0 && !achievedMeta2">
          <div class="p-stat-label">Precisa p/ meta 1,50%</div>
          <div class="p-stat-val warn">R$ {{ formatInt(data.por_dia_meta_2) }}</div>
          <div class="p-stat-hint">nos {{ data.dias_restantes }} dias restantes</div>
        </div>
        <div class="p-stat-card" v-else>
          <div class="p-stat-label">Dias restantes</div>
          <div class="p-stat-val ok">{{ data.dias_restantes }}</div>
          <div class="p-stat-hint">dias no mês</div>
        </div>
      </div>
      </template>
    </div>

    <!-- VENDAS TAB -->
    <div class="p-content" v-show="loaded && activeTab === 'vendas'">
      <div class="p-vendas-header">
        <div class="p-vendas-date-row">
          <button class="p-date-btn" @click="changeVendasDate(-1)">◀</button>
          <input type="date" class="p-date-input" v-model="vendasDate" @change="loadVendas" />
          <button class="p-date-btn" @click="changeVendasDate(1)">▶</button>
        </div>
        <div class="p-vendas-total" v-if="vendasGrouped.length > 0">
          Total: <strong>R$ {{ formatCurrency(vendasTotal) }}</strong> ({{ vendasGrouped.length }} vendas)
        </div>
      </div>

      <div v-if="vendasLoading" style="text-align:center;padding:40px;color:#8e90a6;">Carregando vendas...</div>
      <div v-else-if="vendasGrouped.length === 0" style="text-align:center;padding:40px;color:#8e90a6;">Nenhuma venda neste dia</div>

      <div v-else class="p-vendas-list">
        <div class="p-venda-card" v-for="(g, idx) in vendasGrouped" :key="idx" @click="toggleItems(g)">
          <div class="p-venda-row">
            <div class="p-venda-info">
              <div class="p-venda-client">{{ g.nom_cliente }}</div>
              <div class="p-venda-meta">NF {{ g.num_nf || g.nf_interno }} · {{ g.total_itens }} {{ g.total_itens === 1 ? 'item' : 'itens' }}</div>
            </div>
            <div class="p-venda-right">
              <div class="p-venda-valor">R$ {{ formatCurrency(g.vlr_liquido_total) }}</div>
              <div class="p-venda-chevron" :class="{ open: g._open }">▸</div>
            </div>
          </div>
          <!-- Expanded items -->
          <div class="p-venda-items" v-if="g._open">
            <div v-if="g._loadingItems" style="padding:8px 0;font-size:12px;color:#8e90a6;">Carregando itens...</div>
            <div v-else-if="g._items && g._items.length > 0">
              <div class="p-item-row" v-for="(it, ii) in g._items" :key="ii">
                <div class="p-item-info">
                  <div class="p-item-name">{{ it.des_produto }}</div>
                  <div class="p-item-detail">{{ it.cod_referencia }} · {{ it.nom_marca }} · Qtd: {{ it.qtd_produto }}</div>
                </div>
                <div class="p-item-val">R$ {{ formatCurrency(it.vlr_total || (it.vlr_unitario * it.qtd_produto)) }}</div>
              </div>
            </div>
            <div v-else style="padding:8px 0;font-size:12px;color:#8e90a6;">Sem itens detalhados</div>
          </div>
        </div>
      </div>
    </div>

    <div class="p-content" v-if="!loaded">
      <div style="text-align:center;padding:60px 20px;color:#8e90a6;">
        <div style="font-size:32px;margin-bottom:12px;">⏳</div>
        <div>Carregando dados...</div>
      </div>
    </div>

    <!-- PWA install prompt -->
    <div class="p-spacer"></div>
    <div class="p-bottom-nav">
      <div class="p-nav-btn" :class="{ active: activeTab === 'metas' }" @click="switchTab('metas')">
        <div class="p-nav-icon">📊</div><span>Metas</span>
      </div>
      <div class="p-nav-btn" :class="{ active: activeTab === 'vendas' }" @click="switchTab('vendas')">
        <div class="p-nav-icon">🧾</div><span>Vendas</span>
      </div>
    </div>
  </div>

  <div class="painel-body" v-else>
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:20px;text-align:center;">
      <div style="font-size:48px;margin-bottom:16px;">🔒</div>
      <div style="font-size:20px;font-weight:900;margin-bottom:8px;">Link não encontrado</div>
      <div style="color:#8e90a6;font-size:14px;">Verifique o endereço ou entre em contato com seu supervisor.</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'VendedorPainel',
  data() {
    const today = new Date()
    const y = today.getFullYear(), m = today.getMonth() + 1, d = today.getDate()
    return {
      slug: null, data: {}, loaded: false, notFound: false,
      activeTab: 'metas', selectedAno: y, selectedMes: m,
      chartW: 340, chartH: 140,
      vendas: [], vendasLoading: false,
      vendasDate: `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`,
    }
  },
  computed: {
    dateLabel() {
      const d = new Date()
      const dias = ['Domingo','Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sábado']
      const meses = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
      return `${dias[d.getDay()]}, ${d.getDate()} de ${meses[d.getMonth()]}`
    },
    monthPills() {
      const pills = [], today = new Date()
      const m = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
      for (let i = 5; i >= 0; i--) {
        const d = new Date(today.getFullYear(), today.getMonth() - i, 1)
        pills.push({ ano: d.getFullYear(), mes: d.getMonth() + 1, label: `${m[d.getMonth()]}/${String(d.getFullYear()).slice(-2)}` })
      }
      return pills
    },
    metasDisponiveis() { return (this.data.meta_1 > 0 || this.data.meta_2 > 0) },
    achievedMeta1() { return this.data.meta_1 > 0 && this.data.total_vendas >= this.data.meta_1 },
    achievedMeta2() { return this.data.meta_2 > 0 && this.data.total_vendas >= this.data.meta_2 },
    bannerClass() { if (this.achievedMeta2) return 'banner-meta2'; if (this.achievedMeta1) return 'banner-meta1'; return '' },
    displayComissaoLabel() {
      if (this.achievedMeta2) return 'Comissão (1,50%)'
      if (this.achievedMeta1) return 'Comissão (1,20%)'
      return 'Comissão (1%)'
    },
    displayComissao() {
      if (this.achievedMeta2 && this.data.total_vendas != null) {
        return Math.round(this.data.total_vendas * 0.015 * 100) / 100
      }
      if (this.achievedMeta1 && this.data.total_vendas != null) {
        return Math.round(this.data.total_vendas * 0.012 * 100) / 100
      }
      return this.data.comissao_1pct != null ? this.data.comissao_1pct : 0
    },
    vendasGrouped() {
      const map = {}
      for (const v of this.vendas) {
        const key = `${v.nf_interno}_${v.cod_cliente}`
        if (!map[key]) {
          map[key] = { ...v, _open: false, _items: null, _loadingItems: false }
        } else {
          map[key].vlr_liquido_total = parseFloat(map[key].vlr_liquido_total || 0) + parseFloat(v.vlr_liquido_total || 0)
          map[key].total_itens = (parseInt(map[key].total_itens) || 0) + (parseInt(v.total_itens) || 0)
        }
      }
      return Object.values(map)
    },
    vendasTotal() { return this.vendasGrouped.reduce((s, v) => s + parseFloat(v.vlr_liquido_total || 0), 0) },
  },
  methods: {
    async loadData() {
      try {
        const resp = await axios.get(`/api/painel/${this.slug}`, { params: { ano: this.selectedAno, mes: this.selectedMes } })
        this.data = resp.data
        this.loaded = true
        this.notFound = false
        this.$nextTick(() => this.drawChart())
      } catch (e) {
        if (e.response && e.response.status === 404) this.notFound = true
        else console.error('Error loading painel:', e)
      }
    },
    selectMonth(ano, mes) {
      this.selectedAno = ano; this.selectedMes = mes; this.loaded = false; this.loadData()
    },
    switchTab(tab) {
      this.activeTab = tab
      if (tab === 'vendas') this.loadVendas()
      if (tab === 'metas') this.$nextTick(() => this.drawChart())
    },
    async loadVendas() {
      if (!this.data.cod_vendedor) return
      this.vendasLoading = true
      try {
        const resp = await axios.get(`/api/vendedor/${this.data.cod_vendedor}/vendas`, { params: { data_ini: this.vendasDate, data_fim: this.vendasDate } })
        this.vendas = resp.data || []
      } catch (e) { this.vendas = [] } finally { this.vendasLoading = false }
    },
    async toggleItems(g) {
      if (g._open) { g._open = false; this.$forceUpdate(); return }
      g._open = true
      if (!g._items) {
        g._loadingItems = true; this.$forceUpdate()
        try {
          const resp = await axios.get(`/api/vendedor/${this.data.cod_vendedor}/vendas/${g.nf_interno}/items`)
          g._items = resp.data || []
        } catch (e) { g._items = [] }
        g._loadingItems = false
      }
      this.$forceUpdate()
    },
    changeVendasDate(delta) {
      const d = new Date(this.vendasDate + 'T12:00:00')
      d.setDate(d.getDate() + delta)
      this.vendasDate = d.toISOString().split('T')[0]
      this.loadVendas()
    },
    drawChart() {
      const svg = this.$refs.chartSvg
      if (!svg || !this.data.dias || this.data.dias.length === 0) return
      while (svg.firstChild) svg.removeChild(svg.firstChild)

      const W = this.chartW, H = this.chartH
      const PT = 14, PB = 18, PL = 4, PR = 4
      const cW = W - PL - PR, cH = H - PT - PB
      const TOTAL_DAYS = this.data.dias_no_mes, TODAY = this.data.dia_atual
      const M1 = this.data.meta_1 || 0, M2 = this.data.meta_2 || 0
      const cum = this.data.vendas_cumulativas
      const maxCum = cum.length > 0 ? cum[cum.length - 1] : 0
      const maxVal = Math.max(M2, M1, maxCum) * 1.15 || 1

      const xFor = (day) => PL + (day / (TOTAL_DAYS - 1)) * cW
      const yFor = (val) => PT + cH - (val / maxVal) * cH
      const ns = 'http://www.w3.org/2000/svg'

      const mkLine = (x1,y1,x2,y2,c,dash,w,op) => { const el = document.createElementNS(ns,'line');el.setAttribute('x1',x1);el.setAttribute('y1',y1);el.setAttribute('x2',x2);el.setAttribute('y2',y2);el.setAttribute('stroke',c);el.setAttribute('stroke-width',w||1.5);if(dash)el.setAttribute('stroke-dasharray',dash);el.setAttribute('opacity',op||1);svg.appendChild(el) }
      const mkPath = (d,c,dash,w,op) => { const el = document.createElementNS(ns,'path');el.setAttribute('d',d);el.setAttribute('fill','none');el.setAttribute('stroke',c);el.setAttribute('stroke-width',w||1.5);el.setAttribute('stroke-linecap','round');el.setAttribute('stroke-linejoin','round');if(dash)el.setAttribute('stroke-dasharray',dash);el.setAttribute('opacity',op||1);svg.appendChild(el) }
      const mkText = (x,y,txt,c,anch,sz) => { const el = document.createElementNS(ns,'text');el.setAttribute('x',x);el.setAttribute('y',y);el.setAttribute('fill',c);el.setAttribute('font-size',sz||9);el.setAttribute('font-family','Nunito,sans-serif');el.setAttribute('font-weight','700');el.setAttribute('text-anchor',anch||'start');el.textContent = txt;svg.appendChild(el) }
      const mkRect = (x,y,w2,h2,fill) => { const el = document.createElementNS(ns,'rect');el.setAttribute('x',x);el.setAttribute('y',y);el.setAttribute('width',w2);el.setAttribute('height',h2);el.setAttribute('fill',fill);el.setAttribute('rx','2');svg.appendChild(el) }

      ;[0.25,0.5,0.75,1].forEach(r => mkLine(PL,yFor(maxVal*r),W-PR,yFor(maxVal*r),'#e4e6ef','0',1,0.7))

      // Meta 2 (green) - label on right, ABOVE the line
      if (M2 > 0) {
        const y2 = yFor(M2)
        mkLine(PL,y2,W-PR,y2,'#0a9e6a','5,4',1.5,1)
        mkRect(W-PR-36, y2-13, 34, 12, 'rgba(255,255,255,0.85)')
        mkText(W-PR-4, y2-4,'1,50%','#0a9e6a','end',8)
      }
      // Meta 1 (orange) - label on LEFT, BELOW the line
      if (M1 > 0) {
        const y1 = yFor(M1)
        mkLine(PL,y1,W-PR,y1,'#e07b00','5,4',1.5,1)
        mkRect(PL+2, y1+2, 34, 12, 'rgba(255,255,255,0.85)')
        mkText(PL+4, y1+11,'1,20%','#e07b00','start',8)
      }

      const idealEnd = M2 > 0 ? M2 : (M1 > 0 ? M1 : maxCum)
      if (idealEnd > 0) mkPath(`M ${xFor(0)},${yFor(0)} L ${xFor(TOTAL_DAYS-1)},${yFor(idealEnd)}`,'#3b6ef5','4,4',1.5,0.35)

      if (cum.length > 0) {
        const defs = document.createElementNS(ns,'defs')
        const grad = document.createElementNS(ns,'linearGradient')
        grad.setAttribute('id','aG');grad.setAttribute('x1','0');grad.setAttribute('y1','0');grad.setAttribute('x2','0');grad.setAttribute('y2','1')
        const s1 = document.createElementNS(ns,'stop');s1.setAttribute('offset','0%');s1.setAttribute('stop-color','#3b6ef5');s1.setAttribute('stop-opacity','0.15')
        const s2 = document.createElementNS(ns,'stop');s2.setAttribute('offset','100%');s2.setAttribute('stop-color','#3b6ef5');s2.setAttribute('stop-opacity','0')
        grad.appendChild(s1);grad.appendChild(s2);defs.appendChild(grad);svg.insertBefore(defs,svg.firstChild)

        const pts = cum.map((v,i) => `${xFor(i)},${yFor(v)}`)
        const aEl = document.createElementNS(ns,'path')
        aEl.setAttribute('d',`M ${xFor(0)},${yFor(0)} L ${pts.join(' L ')} L ${xFor(TODAY-1)},${yFor(0)} Z`)
        aEl.setAttribute('fill','url(#aG)');svg.appendChild(aEl)
        mkPath(`M ${pts.join(' L ')}`,'#3b6ef5',null,2.5,1)

        const cx = xFor(TODAY-1), cy = yFor(cum[TODAY-1])
        const dot = document.createElementNS(ns,'circle');dot.setAttribute('cx',cx);dot.setAttribute('cy',cy);dot.setAttribute('r','5')
        dot.setAttribute('fill','#3b6ef5');dot.setAttribute('stroke','#fff');dot.setAttribute('stroke-width','2.5');svg.appendChild(dot)
      }

      const ld = [1]; if(TOTAL_DAYS>7) ld.push(7); if(TOTAL_DAYS>14) ld.push(14)
      if(TODAY>1 && !ld.includes(TODAY)) ld.push(TODAY); if(TOTAL_DAYS>21) ld.push(21); ld.push(TOTAL_DAYS)
      ld.sort((a,b)=>a-b)
      ld.forEach(d => mkText(xFor(d-1),H-3,d.toString(),d===TODAY?'#3b6ef5':'#8e90a6','middle',9))
    },
    formatCurrency(v) { if(!v&&v!==0) return '0,00'; return parseFloat(v).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}) },
    formatInt(v) { if(!v&&v!==0) return '0'; return Math.round(parseFloat(v)).toLocaleString('pt-BR') },
  },
  mounted() {
    this.slug = this.$route.params.slug
    if (this.slug) this.loadData()
    else this.notFound = true
  },
  watch: {
    '$route.params.slug'(s) { this.slug = s; if(s){this.loaded=false;this.notFound=false;this.loadData()} }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&family=IBM+Plex+Mono:wght@400;600&display=swap');
.painel-body{--bg:#f2f3f7;--surface:#fff;--border:#e4e6ef;--text:#1a1b2e;--muted:#8e90a6;--base:#3b6ef5;--base-light:#ebefff;--meta1:#e07b00;--meta1-light:#fff4e0;--meta2:#0a9e6a;--meta2-light:#e0f7ef;--font:'Nunito',sans-serif;--mono:'IBM Plex Mono',monospace;background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;overflow-x:hidden;max-width:600px;margin:0 auto;padding:0;}
.p-header{background:var(--surface);padding:24px 20px 16px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;}
.p-greeting{font-size:12px;color:var(--muted);letter-spacing:.04em;margin-bottom:2px;}
.p-name{font-size:22px;font-weight:900;letter-spacing:-.02em;}
.p-avatar{width:40px;height:40px;border-radius:50%;background:var(--base-light);border:2px solid var(--base);display:flex;align-items:center;justify-content:center;font-size:18px;}
.p-month-bar{background:var(--surface);padding:10px 16px;display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;border-bottom:1px solid var(--border);}
.p-month-bar::-webkit-scrollbar{display:none;}
.p-month-pill{flex-shrink:0;padding:5px 14px;border-radius:100px;border:1.5px solid var(--border);background:transparent;color:var(--muted);font-family:var(--font);font-size:13px;font-weight:700;cursor:pointer;transition:all .18s;}
.p-month-pill.active{background:var(--base);border-color:var(--base);color:#fff;}
.p-tab-bar{display:flex;background:var(--surface);border-bottom:1px solid var(--border);}
.p-tab{flex:1;text-align:center;padding:10px;font-size:13px;font-weight:700;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;transition:all .18s;}
.p-tab.active{color:var(--base);border-bottom-color:var(--base);}
.p-content{padding:14px 14px 0;}
.p-congrats{background:linear-gradient(135deg,#059669,#10b981);color:#fff;border-radius:14px;padding:12px 18px;margin-bottom:12px;font-size:14px;font-weight:800;text-align:center;animation:fadeUp .3s ease both;}
.p-congrats.congrats-m1{background:linear-gradient(135deg,#d97706,#f59e0b);}
.p-commission{background:linear-gradient(135deg,#1d4ed8 0%,#3b6ef5 60%,#6189ff 100%);border-radius:18px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;box-shadow:0 4px 20px rgba(59,110,245,.25);animation:fadeUp .35s ease both;}
.p-commission.banner-meta1{background:linear-gradient(135deg,#b45309 0%,#d97706 60%,#f59e0b 100%);box-shadow:0 4px 20px rgba(217,119,6,.3);}
.p-commission.banner-meta2{background:linear-gradient(135deg,#047857 0%,#059669 60%,#10b981 100%);box-shadow:0 4px 20px rgba(5,150,105,.3);}
.p-comm-label{font-size:12px;color:rgba(255,255,255,.7);margin-bottom:2px;}
.p-comm-value{font-size:28px;font-weight:900;color:#fff;letter-spacing:-.02em;}
.p-comm-value span{font-size:14px;font-weight:600;opacity:.8;margin-left:4px;}
.p-comm-right{text-align:right;}
.p-comm-sub-label{font-size:11px;color:rgba(255,255,255,.6);margin-bottom:2px;}
.p-comm-sub-value{font-size:16px;font-weight:700;color:#fff;font-family:var(--mono);}
.p-chart-card{background:var(--surface);border-radius:18px;border:1px solid var(--border);overflow:hidden;margin-bottom:12px;animation:fadeUp .4s .05s ease both;}
.p-chart-header{padding:16px 18px 10px;display:flex;justify-content:space-between;align-items:center;}
.p-chart-title{font-size:14px;font-weight:900;}
.p-chart-sub{font-size:11px;color:var(--muted);margin-top:1px;}
.p-today-badge{background:var(--base-light);color:var(--base);font-size:11px;font-weight:700;padding:4px 10px;border-radius:8px;font-family:var(--mono);}
.p-chart-wrap{padding:0 12px 4px;}
.p-chart-svg{width:100%;overflow:visible;}
.p-chart-legend{display:flex;gap:14px;padding:8px 18px 16px;flex-wrap:wrap;}
.p-legend-item{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--muted);font-weight:600;}
.p-legend-line{width:18px;height:0;border-top-width:2px;border-top-style:solid;}
.p-legend-line.dashed{border-top-style:dashed;}
.p-partial-note{display:flex;align-items:center;gap:6px;background:var(--base-light);border-radius:10px;padding:7px 12px;margin-bottom:12px;font-size:12px;color:var(--base);font-weight:600;animation:fadeUp .4s .08s ease both;}
.p-partial-note::before{content:'';width:7px;height:7px;border-radius:50%;background:var(--base);flex-shrink:0;animation:blink 2s infinite;}
.p-progress-grid{display:flex;flex-direction:column;gap:10px;margin-bottom:12px;}
.p-prog-card{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:16px 18px;overflow:hidden;}
.p-prog-card:nth-child(1){animation:fadeUp .4s .1s ease both;}
.p-prog-card:nth-child(2){animation:fadeUp .4s .15s ease both;}
.p-prog-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.p-prog-title{font-size:13px;font-weight:700;color:var(--muted);}
.p-prog-main{font-size:18px;font-weight:900;letter-spacing:-.02em;margin-top:1px;}
.p-prog-pct-wrap{text-align:right;}
.p-prog-pct{font-size:28px;font-weight:900;letter-spacing:-.03em;font-family:var(--mono);line-height:1;}
.p-prog-pct-sub{font-size:10px;color:var(--muted);margin-top:1px;text-align:right;}
.p-prog-track{height:8px;background:var(--bg);border-radius:100px;overflow:hidden;margin-bottom:8px;}
.p-prog-fill{height:100%;border-radius:100px;transition:width 1.3s cubic-bezier(.16,1,.3,1);}
.p-prog-footer{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--muted);}
.p-prog-footer strong{color:var(--text);font-weight:700;}
.p-prog-tag{font-size:11px;font-weight:700;padding:2px 9px;border-radius:6px;}
.card-m1 .p-prog-pct{color:var(--meta1);}.card-m1 .p-prog-fill{background:linear-gradient(90deg,#c86800,var(--meta1));}.card-m1 .p-prog-tag{background:var(--meta1-light);color:var(--meta1);}
.card-m2 .p-prog-pct{color:var(--meta2);}.card-m2 .p-prog-fill{background:linear-gradient(90deg,#077a51,var(--meta2));}.card-m2 .p-prog-tag{background:var(--meta2-light);color:var(--meta2);}
.p-stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;}
.p-stat-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:14px 16px;}
.p-stat-label{font-size:11px;color:var(--muted);font-weight:600;margin-bottom:4px;}
.p-stat-val{font-size:19px;font-weight:900;letter-spacing:-.02em;font-family:var(--mono);}
.p-stat-val.ok{color:var(--meta2);}.p-stat-val.warn{color:var(--meta1);}
.p-stat-hint{font-size:10px;color:var(--muted);margin-top:2px;}

/* Vendas */
.p-vendas-header{margin-bottom:12px;}
.p-vendas-date-row{display:flex;align-items:center;gap:8px;margin-bottom:8px;}
.p-date-btn{background:var(--surface);border:1px solid var(--border);border-radius:10px;width:36px;height:36px;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;}
.p-date-input{flex:1;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:6px 12px;font-family:var(--font);font-size:14px;font-weight:700;text-align:center;}
.p-vendas-total{font-size:13px;color:var(--muted);text-align:center;}
.p-vendas-total strong{color:var(--text);}
.p-vendas-list{display:flex;flex-direction:column;gap:8px;}
.p-venda-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px 16px;cursor:pointer;transition:box-shadow .15s;}
.p-venda-card:active{box-shadow:0 0 0 2px var(--base-light);}
.p-venda-row{display:flex;justify-content:space-between;align-items:center;}
.p-venda-info{flex:1;min-width:0;}
.p-venda-client{font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.p-venda-meta{font-size:11px;color:var(--muted);margin-top:2px;}
.p-venda-right{display:flex;align-items:center;gap:8px;flex-shrink:0;}
.p-venda-valor{font-size:16px;font-weight:900;font-family:var(--mono);color:var(--base);}
.p-venda-chevron{font-size:14px;color:var(--muted);transition:transform .2s;}
.p-venda-chevron.open{transform:rotate(90deg);}

.p-venda-items{border-top:1px solid var(--border);margin-top:10px;padding-top:8px;}
.p-item-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #f0f0f5;}
.p-item-row:last-child{border-bottom:none;}
.p-item-info{flex:1;min-width:0;}
.p-item-name{font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.p-item-detail{font-size:10px;color:var(--muted);margin-top:1px;}
.p-item-val{font-size:13px;font-weight:700;font-family:var(--mono);color:var(--text);margin-left:8px;flex-shrink:0;}

.p-metas-unavailable{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:24px 20px;text-align:center;font-size:15px;font-weight:700;color:var(--muted);}
.p-spacer{height:86px;}
.p-bottom-nav{position:fixed;bottom:0;left:0;right:0;background:rgba(255,255,255,.95);backdrop-filter:blur(16px);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:10px 0 24px;max-width:600px;margin:0 auto;}
.p-nav-btn{display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px;font-weight:700;color:var(--muted);cursor:pointer;transition:color .18s;}
.p-nav-btn.active{color:var(--base);}
.p-nav-icon{font-size:20px;line-height:1;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
</style>
