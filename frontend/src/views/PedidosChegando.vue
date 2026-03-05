<template>
  <div class="pc">
    <div class="pc-header">
      <h1 class="pc-title">Pedidos Chegando</h1>
      <div class="pc-subtitle">Pedidos a receber · busca por marca, ref, cor ou descrição</div>
    </div>

    <div class="pc-main">
      <aside class="pc-sidebar">
        <section class="pc-ss">
          <div class="pc-sl">Busca</div>
          <input
            v-model="search"
            class="pc-search-input"
            placeholder="ex: bota marrom, Grendene 2025…"
          />
        </section>

        <section class="pc-ss">
          <div class="pc-sl">Status</div>
          <div
            v-for="f in statusFilters"
            :key="f.val"
            class="pc-fpill"
            :class="{ on: statusFilter === f.val }"
            @click="statusFilter = f.val"
          >
            <span class="pc-fpill-left">
              <span v-if="f.dot" class="pc-dot" :class="f.dot"></span>
              {{ f.label }}
            </span>
            <span class="pc-cnt">{{ f.val === 'all' ? orders.length : countByStatus(f.val) }}</span>
          </div>
        </section>

        <section class="pc-ss" v-if="years.length > 1">
          <div class="pc-sl">Ano</div>
          <div class="pc-ypill" :class="{ on: yearFilter === null }" @click="yearFilter = null">
            Todos <span class="pc-cnt">{{ orders.length }}</span>
          </div>
          <div
            v-for="y in years"
            :key="y.year"
            class="pc-ypill"
            :class="{ on: yearFilter === y.year }"
            @click="yearFilter = y.year"
          >
            <span>{{ y.year }}</span>
            <span v-if="y.hist" class="pc-htag">hist.</span>
            <span class="pc-cnt">{{ y.count }}</span>
          </div>
        </section>

        <section class="pc-ss">
          <div class="pc-sl">Entrega prevista</div>
          <div
            v-for="m in months"
            :key="m.key"
            class="pc-mpill"
            :class="{ on: monthFilter === m.key }"
            @click="monthFilter = monthFilter === m.key ? null : m.key"
          >
            <span class="pc-mlabel">{{ m.label }}</span>
            <div class="pc-mbar"><div class="pc-mbar-fill" :style="{ width: m.pct + '%' }"></div></div>
            <span class="pc-mcount">{{ m.count }}</span>
          </div>
        </section>

        <section class="pc-ss">
          <div class="pc-sl">Gmail / Importar</div>
          <b-button class="pc-sync-btn" variant="primary" block :disabled="syncing" @click="startSync()">
            <b-spinner v-if="syncing" small class="mr-2"></b-spinner>
            {{ syncing ? 'Buscando…' : '↻ Sincronizar agora' }}
          </b-button>
          <div class="pc-sync-hint">
            Detecta <strong>pedidos</strong> no assunto (pedido, order, encomenda…). NF-e em aba separada.<br>
            Última sync: <strong>{{ lastSyncLabel }}</strong>
          </div>
          <b-button class="pc-obtn pc-obtn-warn" variant="outline-warning" block @click="showBackfill = true">
            ⏳ Importar histórico (desde jan/2026)
          </b-button>
          <b-button class="pc-obtn" variant="outline-secondary" block @click="showManual = true">
            + Adicionar manualmente
          </b-button>
          <b-button class="pc-obtn" variant="outline-secondary" block :disabled="!orders.length" @click="carregarImagens" title="Buscar imagens dos produtos na base">
            🖼 Recarregar Imagens
          </b-button>
          <b-button class="pc-obtn" variant="outline-secondary" block :disabled="!orders.length" @click="reExtractPdfImages" title="Extrair imagens dos PDFs salvos (para pedidos antigos)">
            📷 Re-extrair imagens do PDF
          </b-button>
        </section>

        <section class="pc-ss" v-if="feedbackAnalytics.summary.total_products_with_feedback > 0">
          <div class="pc-sl">Erros por marca</div>
          <div class="pc-fb-analytics">
            <div v-for="(stats, brand) in feedbackAnalytics.by_brand" :key="brand" class="pc-fb-brand" v-show="(stats.img_ok_false + stats.ref_ok_false + stats.color_ok_false + stats.sizes_ok_false) > 0">
              <div class="pc-fb-brand-name">{{ brand }}</div>
              <div class="pc-fb-stats">
                <span v-if="stats.img_ok_false" class="pc-fb-stat err" title="Imagem incorreta">Img {{ stats.img_ok_false }}</span>
                <span v-if="stats.ref_ok_false" class="pc-fb-stat err" title="Ref incorreta">Ref {{ stats.ref_ok_false }}</span>
                <span v-if="stats.color_ok_false" class="pc-fb-stat err" title="Cor incorreta">Cor {{ stats.color_ok_false }}</span>
                <span v-if="stats.sizes_ok_false" class="pc-fb-stat err" title="Grade incorreta">Grade {{ stats.sizes_ok_false }}</span>
              </div>
            </div>
          </div>
          <div class="pc-fb-summary small text-muted">
            {{ feedbackAnalytics.summary.total_products_with_feedback }} itens com feedback
          </div>
        </section>
      </aside>

      <div class="pc-content">
        <div class="pc-smbar">
          <div class="pc-si"><div class="pc-val">{{ filtered.length }}</div><div class="pc-lbl">pedidos filtrados</div></div>
          <div class="pc-si"><div class="pc-val">{{ totalPairs }}</div><div class="pc-lbl">pares a receber</div></div>
          <div class="pc-si"><div class="pc-val pc-val-green">{{ arrivingSoon }}</div><div class="pc-lbl">chegando em ≤3 dias</div></div>
          <div class="pc-si"><div class="pc-val pc-val-yellow">{{ reviewCount }}</div><div class="pc-lbl">para revisar</div></div>
          <div class="pc-si" v-if="histCount"><div class="pc-val pc-val-muted">{{ histCount }}</div><div class="pc-lbl">histórico importado</div></div>
        </div>

        <div v-for="o in filtered" :key="o.id" class="pc-card" :class="o.status">
          <div class="pc-ch" :class="{ open: openIds.includes(o.id) }" @click="toggleOpen(o.id)">
            <div class="pc-blogo">{{ (o.brand || '').slice(0, 3).toUpperCase() }}</div>
            <div class="pc-cmeta">
              <div class="pc-cbrand">
                {{ o.brand || 'Desconhecida' }}{{ o.subjectSnippet ? ` · ${o.subjectSnippet}` : '' }}
                <span v-if="o.hist" class="pc-htag">histórico</span>
              </div>
              <div class="pc-csub">
                <span>Pedido #{{ o.ref }}</span>
                <span class="pc-sep">·</span>
                <span>{{ o.products.length }} itens · {{ o.totalPairs }} pares</span>
                <span class="pc-sep">·</span>
                <span>{{ o.deliveryMonth }}</span>
                <span v-if="o.estArrival" :class="['pc-acchip', arrCls(o)]">{{ arrLbl(o) }}</span>
              </div>
            </div>
            <div class="pc-cright">
              <span v-if="o.invoice" title="NF-e recebida">📄</span>
              <span class="pc-stag" :class="'st-' + o.source">{{ o.source === 'email' ? '✉ email' : '✎ manual' }}</span>
              <span class="pc-sbadge" :class="badgeCls(o.status)">{{ statusLabel(o.status) }}</span>
              <span class="pc-chev" :class="{ open: openIds.includes(o.id) }">▼</span>
            </div>
          </div>

          <div class="pc-cbody" v-if="openIds.includes(o.id)">
            <div class="pc-inv-bar" v-if="o.invoice">
              📄 NF-e recebida {{ o.invDate }}
              <span class="pc-sep">·</span>
              Saiu de <strong>{{ o.city }}</strong>
              <span class="pc-sep">·</span>
              Chegada estimada: <strong>{{ o.estArrival }}</strong>
              <span v-if="o.track" class="pc-track">🔗 {{ o.track }}</span>
            </div>

            <div class="pc-rev-alert" v-if="o.status === 'needs-review'">
              <span class="pc-rev-icon">⚠</span>
              <div class="pc-rat">
                <strong>Extração automática — revise antes de confirmar.</strong>
                Extraído por <strong class="pc-provider-toggle" @click.stop="toggleProvider(o)">{{ o.provider || 'Gemini' }}</strong> (conf. {{ Math.round((o.conf || 0.8) * 100) }}%).
                <span v-if="o.flagged">{{ o.flagged }} item(s) marcado(s).</span>
                <div class="pc-raa">
                  <b-button size="sm" variant="primary" @click="confirmOrder(o)">✓ Confirmar</b-button>
                  <b-button size="sm" variant="outline-secondary" @click="openPdf(o)">Abrir PDF</b-button>
                  <b-button size="sm" variant="outline-secondary" @click="openEditOrder(o)">✎ Editar</b-button>
                  <b-button size="sm" variant="outline-secondary" :disabled="reextractingId === o.id" @click="reExtractImagesOrder(o)" title="Re-extrair imagens do PDF deste pedido">
                    <b-spinner v-if="reextractingId === o.id" small class="mr-1"></b-spinner>
                    {{ reextractingId === o.id ? 'Extraindo…' : '↺ Re-extrair imagens' }}
                  </b-button>
                  <b-button size="sm" variant="outline-primary" :disabled="reextractingId === o.id" @click="reExtractFeedbackOrder(o)" :title="hasFeedbackErrors(o) ? 'Re-extrair só os campos marcados como incorretos (✗)' : 'Marque ✗ nos itens incorretos (dropdown ✎) e clique aqui para corrigir'">
                    <b-spinner v-if="reextractingId === o.id" small class="mr-1"></b-spinner>
                    {{ reextractingId === o.id ? 'Corrigindo…' : '🔧 Corrigir marcados' }}
                  </b-button>
                  <b-button size="sm" variant="outline-danger" @click="deleteOrder(o)">🗑 Excluir</b-button>
                </div>
              </div>
            </div>
            <div class="pc-actions" v-if="o.status !== 'needs-review'">
              <b-button size="sm" variant="outline-secondary" @click="sendBackToInbox(o)">↩ Voltar para revisar</b-button>
              <b-button size="sm" variant="outline-secondary" @click="openPdf(o)">Abrir PDF</b-button>
              <b-button size="sm" variant="outline-secondary" @click="openEditOrder(o)">✎ Editar</b-button>
              <b-button size="sm" variant="outline-secondary" :disabled="reextractingId === o.id" @click="reExtractImagesOrder(o)" title="Re-extrair imagens do PDF">
                📷 Re-extrair imagens
              </b-button>
              <b-button size="sm" variant="outline-primary" :disabled="reextractingId === o.id" @click="reExtractFeedbackOrder(o)" :title="hasFeedbackErrors(o) ? 'Re-extrair só os campos marcados como incorretos' : 'Marque ✗ nos itens incorretos e clique aqui'">
                🔧 Corrigir marcados
              </b-button>
              <b-button size="sm" variant="outline-danger" @click="deleteOrder(o)">🗑 Excluir</b-button>
            </div>

            <div v-if="!o.products.length" class="pc-no-items text-muted small mb-2">
              0 itens — extração não retornou itens (PDF só imagem, modelo indisponível ou chave não carregada). Reinicie o backend e use «Sincronizar agora» para tentar de novo com o modelo atual.
            </div>
            <div class="pc-table-wrap">
              <table class="pc-table">
                <thead>
                  <tr>
                    <th class="pc-th">Ref.</th>
                    <th class="pc-th">Cor</th>
                    <th class="pc-th">Descrição</th>
                    <th class="pc-th pc-th-img">Img.</th>
                    <th class="pc-th pc-th-grade">Grade</th>
                    <th class="pc-th pc-th-qty">Qtd</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="g in groupedProducts(o)" :key="g.key + '-' + o.id + '-' + ordersVersion" class="pc-trow" :class="{ fl: g.flag }">
                    <td class="pc-td pc-td-ref">
                      {{ g.baseRef || g.ref }}
                      <b-dropdown v-if="o.status === 'needs-review'" size="sm" variant="link" no-caret class="pc-feedback-dd" right>
                        <template #button-content>
                          <span class="pc-fb-icon" title="Marcar o que está correto/incorreto">✎</span>
                        </template>
                        <div class="pc-feedback-pop p-2">
                          <div class="small mb-1"><strong>Revisar:</strong></div>
                          <div class="pc-fb-row" v-for="f in ['img_ok','ref_ok','color_ok','sizes_ok']" :key="f">
                            <span class="pc-fb-lbl">{{ f === 'img_ok' ? 'Img' : f === 'ref_ok' ? 'Ref' : f === 'color_ok' ? 'Cor' : 'Grade' }}</span>
                            <button type="button" class="pc-fb-btn" :class="{ ok: getFeedback(o, g, f) === true }" @click="setFeedback(o, g, f, true)">✓</button>
                            <button type="button" class="pc-fb-btn" :class="{ err: getFeedback(o, g, f) === false }" @click="setFeedback(o, g, f, false)">✗</button>
                          </div>
                        </div>
                      </b-dropdown>
                    </td>
                    <td class="pc-td">
                      <span class="pc-csw" :style="{ background: g.hex || '#888' }"></span>
                      {{ g.color || '—' }}
                    </td>
                    <td class="pc-td pc-td-desc" :title="g.name">{{ g.name || '—' }}</td>
                    <td class="pc-td pc-td-img">
                      <div class="pc-img-cell">
                        <template v-if="imgForProduct(o, g)">
                          <img :key="'img-' + o.id + '-' + g.key + '-' + ordersVersion" :src="imgSrc(imgForProduct(o, g))" alt="" class="pc-table-img" @error="$event.target.style.display='none'; $event.target.nextElementSibling && ($event.target.nextElementSibling.style.display='inline')" />
                          <span class="pc-img-placeholder" style="display:none">—</span>
                        </template>
                        <span v-else class="pc-img-placeholder">—</span>
                        <span v-if="g.flag" class="pc-pflag">⚠️</span>
                        <span class="pc-isrc" :class="g.src || 'auto'">{{ (g.src === 'pdf' ? 'PDF' : g.src === 'manual' ? 'manual' : 'auto') }}</span>
                      </div>
                    </td>
                    <td class="pc-td pc-td-grade">
                      <div v-if="gradeEntries(g.sizes).length" class="pc-grade-grid" :style="{ gridTemplateColumns: `repeat(${gradeEntries(g.sizes).length}, minmax(24px, 1fr))` }">
                        <template v-for="e in gradeEntries(g.sizes)">
                          <span :key="'s-' + e.size" class="pc-grade-cell pc-grade-size">{{ e.size }}</span>
                        </template>
                        <template v-for="e in gradeEntries(g.sizes)">
                          <span :key="'q-' + e.size" class="pc-grade-cell pc-grade-qty">{{ e.qty }}</span>
                        </template>
                      </div>
                      <span v-else class="pc-grade-empty">—</span>
                    </td>
                    <td class="pc-td pc-td-qty">{{ qtyLabel(g) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="pc-empty" v-if="!filtered.length">
          <div class="pc-empty-icon">📦</div>
          <p>Nenhum pedido encontrado. Tente outros filtros ou sincronize o Gmail.</p>
        </div>
      </div>
    </div>

    <!-- Sync modal -->
    <b-modal v-model="showSyncModal" title="Sincronizando Gmail" hide-footer size="sm" no-close-on-backdrop>
      <p class="mb-2">Buscando pedidos e NF-e…</p>
      <b-progress :value="syncPct" max="100" class="mb-2"></b-progress>
      <div class="pc-slog">
        <div v-for="(l, i) in syncDone" :key="i" class="pc-sll ok">{{ l }}</div>
        <div v-if="syncCur" class="pc-sll run">{{ syncCur }}</div>
      </div>
    </b-modal>

    <!-- Backfill modal -->
    <b-modal v-model="showBackfill" title="Importar histórico de pedidos" size="lg" @hidden="showBackfill = false">
      <div class="pc-ibox">
        <strong>Como funciona:</strong> o sistema varre seu Gmail desde a data escolhida, processa e-mails com "pedido", "order", "encomenda" etc. e importa automaticamente (PDFs são extraídos com Gemini quando GEMINI_API_KEY está configurado). Faturas CDL e NF-e ficam em aba separada. Pedidos são salvos em MongoDB quando MONGODB_URL está configurado.
      </div>
      <b-form-group label="Importar e-mails desde" class="mt-3">
        <b-form-input v-model="backfillFrom" type="date"></b-form-input>
      </b-form-group>
      <template #modal-footer>
        <b-button variant="secondary" @click="showBackfill = false">Fechar</b-button>
        <b-button variant="primary" :disabled="backfillRunning" @click="startBackfill">
          <b-spinner v-if="backfillRunning" small class="mr-2"></b-spinner>
          {{ backfillRunning ? 'Importando…' : 'Iniciar importação' }}
        </b-button>
      </template>
    </b-modal>

    <!-- Edit order modal -->
    <b-modal v-model="showEditOrder" title="Editar pedido" @ok="onEditOk" size="md" @hidden="editOrder = null">
      <template v-if="editOrder">
        <b-form-group label="Marca">
          <b-form-input v-model="editForm.brand" placeholder="ex: Kolosh"></b-form-input>
        </b-form-group>
        <b-form-group label="Título / Assunto (snippet)">
          <b-form-input v-model="editForm.subjectSnippet" placeholder="ex: Dakota - Pre-Pedido 109-5489"></b-form-input>
        </b-form-group>
        <b-form-group label="Ref. do pedido">
          <b-form-input v-model="editForm.ref" placeholder="ex: 5489"></b-form-input>
        </b-form-group>
      </template>
    </b-modal>

    <!-- Manual add modal -->
    <b-modal v-model="showManual" title="Adicionar pedido manualmente" @ok="saveManual" size="lg">
      <b-form-group label="Marca">
        <b-form-input v-model="manualForm.brand" placeholder="ex: Grendene"></b-form-input>
      </b-form-group>
      <b-form-group label="Nº Pedido">
        <b-form-input v-model="manualForm.ref" placeholder="ex: 2024-089"></b-form-input>
      </b-form-group>
      <b-row>
        <b-col md="6">
          <b-form-group label="Data do Pedido">
            <b-form-input v-model="manualForm.oDate" type="date"></b-form-input>
          </b-form-group>
        </b-col>
        <b-col md="6">
          <b-form-group label="Entrega Prevista">
            <b-form-input v-model="manualForm.dDate" type="date"></b-form-input>
          </b-form-group>
        </b-col>
      </b-row>
      <b-form-group label="Produtos">
        <div v-for="(p, i) in manualForm.products" :key="i" class="mb-2 d-flex gap-2 align-items-center">
          <b-form-input v-model="p.ref" placeholder="Ref." size="sm"></b-form-input>
          <b-form-input v-model="p.name" placeholder="Descrição" size="sm"></b-form-input>
          <b-form-input v-model="p.color" placeholder="Cor" size="sm"></b-form-input>
          <b-form-input v-model.number="p.qty" type="number" placeholder="Pares" size="sm" style="width:80px"></b-form-input>
          <b-button size="sm" variant="outline-danger" @click="manualForm.products.splice(i, 1)">×</b-button>
        </div>
        <b-button size="sm" variant="outline-secondary" @click="manualForm.products.push({ ref: '', name: '', color: '', qty: 0 })">+ Adicionar produto</b-button>
      </b-form-group>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios'

const STATUS_FILTERS = [
  { val: 'all', label: 'Todos', dot: '' },
  { val: 'needs-review', label: 'Revisar', dot: 'd-rev' },
  { val: 'confirmed', label: 'Confirmado', dot: 'd-conf' },
  { val: 'in-transit', label: 'Em trânsito', dot: 'd-tr' },
  { val: 'partial', label: 'Parcial', dot: 'd-part' },
  { val: 'complete', label: 'Completo', dot: 'd-done' }
]

export default {
  name: 'PedidosChegando',
  data() {
    return {
      search: '',
      statusFilter: 'all',
      yearFilter: null,
      monthFilter: null,
      openIds: [1, 2],
      orders: [
        { id: 1, brand: 'Grendene', ref: '2025-441', status: 'needs-review', source: 'email', deliveryMonth: 'Março 2025', totalPairs: 234, flagged: 2, conf: 0.68, provider: 'Gemini', hist: false, invoice: false, products: [
          { ref: '23285', name: 'Slide Stitch', color: 'Azul Royal', hex: '#2f5fc9', qty: 48, img: '', src: 'pdf', flag: false },
          { ref: '27248', name: 'Chinelo Ipanema', color: 'Rosa', hex: '#e87fa3', qty: 60, img: '', src: 'pdf', flag: true },
          { ref: '21934', name: 'Papete Cartago', color: 'Laranja', hex: '#e8882f', qty: 72, img: '', src: 'auto', flag: true },
          { ref: '22110', name: 'Sandália Grendha', color: 'Dourado', hex: '#c9a02f', qty: 54, img: '', src: 'auto', flag: false }
        ]},
        { id: 2, brand: 'Ramarim', ref: '2025-029', status: 'in-transit', source: 'email', deliveryMonth: 'Março 2025', totalPairs: 144, flagged: 0, conf: 0.94, provider: 'Gemini', hist: false, invoice: true, invDate: '03/03/2025', city: 'Nova Serrana/MG', estArrival: '07/03/2025', track: 'OD381929425BR', products: [
          { ref: 'RM1190', name: 'Tênis Chunky', color: 'Branco', hex: '#f5f5f0', qty: 96, img: '', src: 'pdf', flag: false },
          { ref: 'RM2041', name: 'Sapatilha Ballet', color: 'Rosa Bebê', hex: '#f5c4c4', qty: 48, img: '', src: 'pdf', flag: false }
        ]},
        { id: 3, brand: 'Arezzo', ref: '2025-112', status: 'confirmed', source: 'email', deliveryMonth: 'Abril 2025', totalPairs: 180, flagged: 0, conf: 0.91, provider: 'Gemini', hist: false, invoice: false, products: [
          { ref: 'AR8821', name: 'Scarpin Classic', color: 'Preto', hex: '#222', qty: 60, img: '', src: 'auto', flag: false },
          { ref: 'AR9034', name: 'Bota Ankle', color: 'Marrom', hex: '#8B4513', qty: 48, img: '', src: 'auto', flag: false },
          { ref: 'AR7720', name: 'Mule Salto Bloco', color: 'Nude', hex: '#e8c9a0', qty: 72, img: '', src: 'auto', flag: false }
        ]}
      ],
      syncing: false,
      showSyncModal: false,
      syncPct: 0,
      syncDone: [],
      syncCur: '',
      lastSyncAt: null,
      showBackfill: false,
      backfillFrom: '2026-01-01',
      backfillRunning: false,
      showManual: false,
      manualForm: { brand: '', ref: '', oDate: '', dDate: '', products: [{ ref: '', name: '', color: '', qty: 0 }] },
      showEditOrder: false,
      editOrder: null,
      editForm: { brand: '', subjectSnippet: '', ref: '' },
      statusFilters: STATUS_FILTERS,
      imagesByKey: {},
      reextractingId: null,
      feedbackAnalytics: { by_brand: {}, summary: {} },
      ordersVersion: 0
    }
  },
  computed: {
    filtered() {
      return this.orders.filter(o => {
        if (this.statusFilter !== 'all' && o.status !== this.statusFilter) return false
        if (this.yearFilter != null) {
          const y = parseInt(String(o.deliveryMonth).split(' ').pop(), 10)
          if (y !== this.yearFilter) return false
        }
        if (this.monthFilter) {
          if (!o.deliveryMonth || !String(o.deliveryMonth).toLowerCase().includes(this.monthFilter)) return false
        }
        if (this.search.trim()) {
          const q = this.search.toLowerCase()
          const hay = [o.brand, o.ref, o.deliveryMonth, ...o.products.map(p => [p.ref, p.name, p.color].join(' '))].join(' ').toLowerCase()
          if (!hay.includes(q)) return false
        }
        return true
      })
    },
    reviewCount() {
      return this.orders.filter(o => o.status === 'needs-review').length
    },
    totalPairs() {
      return this.filtered.filter(o => o.status !== 'complete').reduce((a, o) => a + o.totalPairs, 0)
    },
    arrivingSoon() {
      return this.orders.filter(o => o.status === 'in-transit' && o.estArrival).length
    },
    histCount() {
      return this.orders.filter(o => o.hist).length
    },
    years() {
      const map = {}
      this.orders.forEach(o => {
        const y = parseInt(String(o.deliveryMonth).split(' ').pop(), 10)
        if (!map[y]) map[y] = { year: y, count: 0, hist: false }
        map[y].count++
        if (o.hist) map[y].hist = true
      })
      return Object.values(map).sort((a, b) => b.year - a.year)
    },
    months() {
      const map = {}
      this.orders.forEach(o => {
        const k = String(o.deliveryMonth).split(' ')[0].toLowerCase()
        if (k) map[k] = (map[k] || 0) + 1
      })
      const max = Math.max(...Object.values(map), 1)
      return Object.entries(map).map(([key, count]) => ({
        key,
        label: key.charAt(0).toUpperCase() + key.slice(1, 3),
        count,
        pct: Math.round((count / max) * 100)
      }))
    },
    lastSyncLabel() {
      if (!this.lastSyncAt) return 'nunca'
      const min = Math.round((Date.now() - this.lastSyncAt) / 60000)
      if (min < 1) return 'agora'
      if (min < 60) return `há ${min} min`
      return `há ${Math.round(min / 60)} h`
    }
  },
  methods: {
    countByStatus(s) {
      return this.orders.filter(o => o.status === s).length
    },
    statusLabel(s) {
      return { 'needs-review': 'Revisar', confirmed: 'Confirmado', 'in-transit': 'Em trânsito', partial: 'Parcial', complete: 'Completo' }[s] || s
    },
    badgeCls(s) {
      return { 'needs-review': 'b-rev', confirmed: 'b-conf', 'in-transit': 'b-tr', partial: 'b-part', complete: 'b-done' }[s] || 'b-done'
    },
    arrCls(o) {
      if (o.status === 'complete') return 'ac-late'
      if (!o.estArrival) return 'ac-late'
      const p = String(o.estArrival).split('/')
      if (p.length < 3) return 'ac-late'
      const d = new Date(parseInt(p[2], 10), parseInt(p[1], 10) - 1, parseInt(p[0], 10))
      const t = new Date()
      const diff = (d - t) / 86400000
      return diff <= 3 ? 'ac-soon' : diff <= 10 ? 'ac-week' : 'ac-late'
    },
    arrLbl(o) {
      return o.status === 'complete' ? `chegou ~${o.estArrival}` : `chega ~${o.estArrival}`
    },
    toggleOpen(id) {
      const i = this.openIds.indexOf(id)
      if (i >= 0) this.openIds.splice(i, 1)
      else this.openIds.push(id)
    },
    async confirmOrder(o) {
      if (!o || !o.id) return
      try {
        const res = await axios.patch(`/api/pedidos-chegando/order/${o.id}`, { status: 'confirmed' })
        if (res.data && res.data.ok) {
          o.status = 'confirmed'
          o.flagged = 0
          if (o.products) o.products.forEach(p => { p.flag = false })
          this.$bvToast && this.$bvToast.toast('Pedido confirmado.', { variant: 'success', autoHideDelay: 2000 })
        } else {
          this.$bvToast && this.$bvToast.toast(res.data?.error || 'Erro ao confirmar', { variant: 'danger' })
        }
      } catch (err) {
        this.$bvToast && this.$bvToast.toast('Erro ao confirmar: ' + (err.response?.data?.detail || err.message), { variant: 'danger' })
      }
    },
    async sendBackToInbox(o) {
      if (!o || !o.id) return
      try {
        const res = await axios.patch(`/api/pedidos-chegando/order/${o.id}`, { status: 'needs-review' })
        if (res.data && res.data.ok) {
          o.status = 'needs-review'
          this.$bvToast && this.$bvToast.toast('Pedido enviado de volta para revisar.', { variant: 'info', autoHideDelay: 2000 })
        } else {
          this.$bvToast && this.$bvToast.toast(res.data?.error || 'Erro', { variant: 'danger' })
        }
      } catch (err) {
        this.$bvToast && this.$bvToast.toast('Erro: ' + (err.response?.data?.detail || err.message), { variant: 'danger' })
      }
    },
    openEditOrder(o) {
      if (!o || !o.id) return
      this.editOrder = o
      this.editForm = { brand: o.brand || '', subjectSnippet: o.subjectSnippet || '', ref: o.ref || '' }
      this.showEditOrder = true
    },
    onEditOk(bvModalEvt) {
      bvModalEvt.preventDefault()
      this.saveEditOrder().finally(() => {
        this.showEditOrder = false
        this.editOrder = null
      })
    },
    async saveEditOrder() {
      if (!this.editOrder || !this.editOrder.id) return
      const body = {}
      if (this.editForm.brand !== undefined) body.brand = this.editForm.brand
      if (this.editForm.subjectSnippet !== undefined) body.subject_snippet = this.editForm.subjectSnippet
      if (this.editForm.ref !== undefined) body.order_ref = this.editForm.ref
      if (Object.keys(body).length === 0) return
      try {
        const res = await axios.patch(`/api/pedidos-chegando/order/${this.editOrder.id}`, body)
        if (res.data && res.data.ok) {
          this.editOrder.brand = this.editForm.brand
          this.editOrder.subjectSnippet = this.editForm.subjectSnippet
          this.editOrder.ref = this.editForm.ref
          this.$bvToast && this.$bvToast.toast('Pedido atualizado.', { variant: 'success', autoHideDelay: 2000 })
        } else {
          this.$bvToast && this.$bvToast.toast(res.data?.error || 'Erro ao atualizar', { variant: 'danger' })
        }
      } catch (err) {
        this.$bvToast && this.$bvToast.toast('Erro: ' + (err.response?.data?.detail || err.message), { variant: 'danger' })
      }
    },
    async deleteOrder(o) {
      if (!o || !o.id) return
      if (!confirm(`Excluir pedido #${o.ref} (${o.brand})? Esta ação não pode ser desfeita.`)) return
      try {
        const res = await axios.delete(`/api/pedidos-chegando/order/${o.id}`)
        if (res.data && res.data.ok) {
          const i = this.orders.findIndex(x => x.id === o.id)
          if (i >= 0) this.orders.splice(i, 1)
          this.$bvToast && this.$bvToast.toast('Pedido excluído.', { variant: 'success', autoHideDelay: 2000 })
        } else {
          this.$bvToast && this.$bvToast.toast(res.data?.error || 'Erro ao excluir', { variant: 'danger' })
        }
      } catch (err) {
        this.$bvToast && this.$bvToast.toast('Erro: ' + (err.response?.data?.detail || err.message), { variant: 'danger' })
      }
    },
    async openPdf(o) {
      if (!o || !o.id) return
      try {
        const res = await axios.get(`/api/pedidos-chegando/order/${o.id}/pdf`, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        window.open(url, '_blank')
      } catch (err) {
        if (err.response?.status === 404) {
          this.$bvToast && this.$bvToast.toast('PDF não disponível para este pedido (sincronize de novo para guardar o PDF).', { variant: 'warning' })
        } else {
          this.$bvToast && this.$bvToast.toast('Erro ao abrir PDF.', { variant: 'danger' })
        }
      }
    },
    toggleProvider(o) {
      if (!o || !o.id) return
      const next = (o.provider || 'Gemini') === 'Gemini' ? 'Claude' : 'Gemini'
      axios.patch(`/api/pedidos-chegando/order/${o.id}`, { provider: next }).then(res => {
        if (res.data && res.data.ok) {
          o.provider = next
          this.$bvToast && this.$bvToast.toast(`Provedor alterado para ${next}.`, { variant: 'info', autoHideDelay: 2000 })
        }
      }).catch(() => {})
    },
    async reExtractImagesOrder(o) {
      if (!o || !o.id || this.reextractingId) return
      this.reextractingId = o.id
      try {
        const res = await axios.post(`/api/pedidos-chegando/order/${o.id}/re-extract-images`)
        if (res.data && res.data.ok) {
          const updated = res.data.order
          if (updated) {
            const idx = this.orders.findIndex(x => String(x.id) === String(o.id))
            if (idx >= 0) {
              this.$set(this.orders, idx, { ...updated, products: (updated.products || []).map(p => ({ ...p })) })
            }
            for (const g of this.groupedProducts(updated)) {
              const ref = String(g.baseRef || g.ref || '')
              const cor = String(g.color || '').trim() || '—'
              ;[`${ref}|${cor}`, `${ref}|—`, ref].forEach(k => this.$delete(this.imagesByKey, k))
            }
            this.ordersVersion += 1
            this.$nextTick(() => { this.$forceUpdate() })
          }
          this.$bvToast && this.$bvToast.toast(`Imagens extraídas: ${res.data.images_found} encontradas.`, { variant: 'success', autoHideDelay: 3000 })
        } else {
          this.$bvToast && this.$bvToast.toast(res.data?.error || 'Erro ao re-extrair', { variant: 'danger' })
        }
      } catch (err) {
        const msg = err.response?.status === 404 ? 'PDF não disponível para este pedido.' : (err.response?.data?.detail || err.message)
        this.$bvToast && this.$bvToast.toast(msg, { variant: 'danger' })
      } finally {
        this.reextractingId = null
      }
    },
    hasFeedbackErrors(o) {
      if (!o || !o.products) return false
      return o.products.some(p => {
        const fb = p.feedback || {}
        return fb.img_ok === false || fb.ref_ok === false || fb.color_ok === false || fb.sizes_ok === false
      })
    },
    async reExtractFeedbackOrder(o) {
      if (!o || !o.id || this.reextractingId) return
      this.reextractingId = o.id
      try {
        const res = await axios.post(`/api/pedidos-chegando/order/${o.id}/re-extract-feedback`)
        if (res.data && res.data.ok) {
          const updated = res.data.order
          if (updated) {
            const idx = this.orders.findIndex(x => String(x.id) === String(o.id))
            if (idx >= 0) {
              this.$set(this.orders, idx, { ...updated, products: (updated.products || []).map(p => ({ ...p })) })
            }
            for (const g of this.groupedProducts(updated)) {
              const ref = String(g.baseRef || g.ref || '')
              const cor = String(g.color || '').trim() || '—'
              ;[`${ref}|${cor}`, `${ref}|—`, ref].forEach(k => this.$delete(this.imagesByKey, k))
            }
            this.ordersVersion += 1
            this.$nextTick(() => { this.$forceUpdate() })
          }
          const msg = res.data.updated > 0 ? `${res.data.updated} campo(s) corrigido(s).` : (res.data.message || 'Concluído.')
          this.$bvToast && this.$bvToast.toast(msg, { variant: 'success', autoHideDelay: 3000 })
          this.loadFeedbackAnalytics()
        } else {
          this.$bvToast && this.$bvToast.toast(res.data?.error || 'Erro ao corrigir', { variant: 'danger' })
        }
      } catch (err) {
        const msg = err.response?.status === 404 ? 'PDF não disponível.' : (err.response?.data?.detail || err.message)
        this.$bvToast && this.$bvToast.toast(msg, { variant: 'danger' })
      } finally {
        this.reextractingId = null
      }
    },
    baseRef(ref) {
      if (!ref) return ''
      const parts = ref.split('-')
      if (parts.length > 1 && /^\d{1,3}$/.test(parts[parts.length - 1])) {
        return parts.slice(0, -1).join('-')
      }
      if (/\.\d{2}[A-Za-z]$/.test(ref)) {
        return ref.slice(0, -1)
      }
      return ref
    },
    groupedProducts(o) {
      const map = new Map()
      for (const p of o.products || []) {
        const base = this.baseRef(p.ref || '')
        const color = (p.color || '—').trim() || '—'
        const key = `${base}|${color}`
        if (!map.has(key)) {
          map.set(key, {
            key,
            baseRef: base,
            ref: p.ref,
            name: p.name,
            color: p.color,
            hex: p.hex,
            qty: 0,
            unit: p.unit || 'par',
            sizes: {},
            img: p.img,
            src: p.src,
            flag: p.flag
          })
        }
        const g = map.get(key)
        g.qty += Number(p.qty) || 0
        if (p.flag) g.flag = true
        if (!g.img && p.img) g.img = p.img
        const sz = p.sizes || {}
        if (typeof sz === 'object') {
          for (const [k, v] of Object.entries(sz)) {
            g.sizes[k] = (g.sizes[k] || 0) + (Number(v) || 0)
          }
        }
        if (p.unit && p.unit === 'unidade') g.unit = 'unidade'
      }
      return Array.from(map.values())
    },
    hasAnySizes(o) {
      for (const g of this.groupedProducts(o)) {
        const s = g.sizes || {}
        if (Object.keys(s).length > 0) return true
      }
      return false
    },
    formatSizes(sizes) {
      if (!sizes || typeof sizes !== 'object') return ''
      const entries = Object.entries(sizes).filter(([, v]) => v && Number(v) > 0)
      if (!entries.length) return ''
      return entries.sort((a, b) => String(a[0]).localeCompare(String(b[0]))).map(([k, v]) => `${k}:${v}`).join(' ')
    },
    gradeEntries(sizes) {
      if (!sizes || typeof sizes !== 'object') return []
      return Object.entries(sizes)
        .filter(([, v]) => v && Number(v) > 0)
        .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
        .map(([size, qty]) => ({ size, qty: Number(qty) }))
    },
    qtyLabel(g) {
      const q = Number(g.qty) || 0
      let unit = (g.unit || 'par').toLowerCase()
      if (unit === 'par') {
        const n = (g.name || '').toLowerCase()
        if (['bola', 'ball', 'mochila', 'backpack', 'bkpk', 'bolsa', 'bag', 'boné', 'cinto', 'belt'].some(kw => n.includes(kw))) unit = 'unidade'
      }
      return unit === 'unidade' ? `${q} un.` : `${q} pares`
    },
    async reExtractPdfImages() {
      if (!this.orders.length) return
      let done = 0
      let errs = 0
      for (const o of this.orders) {
        if (!o.id) continue
        try {
          const res = await axios.post(`/api/pedidos-chegando/order/${o.id}/re-extract-images`)
          if (res.data && res.data.ok) done += 1
        } catch (e) {
          errs += 1
        }
      }
      if (done) {
        const res = await axios.get('/api/pedidos-chegando')
        if (res.data && Array.isArray(res.data)) this.orders = res.data
      }
      const msg = done ? `Imagens extraídas para ${done} pedido(s).` : (errs ? 'Nenhum PDF encontrado ou erro.' : '')
      if (msg) this.$bvToast && this.$bvToast.toast(msg, { variant: done ? 'success' : 'warning', autoHideDelay: 3000 })
    },
    getFeedback(o, g, field) {
      const base = g.baseRef || g.ref || ''
      const color = (g.color || '').trim() || '—'
      const p = (o.products || []).find(pr => {
        const b = this.baseRef(pr.ref || '')
        const c = (pr.color || '').trim() || '—'
        return b === base && c === color
      })
      return p && p.feedback ? p.feedback[field] : null
    },
    async setFeedback(o, g, field, value) {
      if (!o || !o.id) return
      const body = { base_ref: g.baseRef || g.ref || '', color: (g.color || '').trim() || '—', [field]: value }
      try {
        const res = await axios.patch(`/api/pedidos-chegando/order/${o.id}/product-feedback`, body)
        if (res.data && res.data.ok) {
          const base = g.baseRef || g.ref || ''
          const color = (g.color || '').trim() || '—'
          for (const p of o.products || []) {
            const b = this.baseRef(p.ref || '')
            const c = (p.color || '').trim() || '—'
            if (b === base && c === color) {
              this.$set(p, 'feedback', { ...(p.feedback || {}), [field]: value })
              break
            }
          }
          this.loadFeedbackAnalytics()
        }
      } catch (e) { /* ignore */ }
    },
    loadFeedbackAnalytics() {
      axios.get('/api/pedidos-chegando/feedback-analytics', { timeout: 5000 })
        .then(res => {
          if (res.data && res.data.by_brand) {
            this.feedbackAnalytics = { by_brand: res.data.by_brand, summary: res.data.summary || {} }
          }
        })
        .catch(() => {})
    },
    imgForProduct(o, g) {
      const fromPdf = g.src === 'pdf' && g.img
      if (fromPdf) return g.img
      if (g.img && (g.img.startsWith('data:') || g.img.startsWith('http'))) return g.img
      const ref = String(g.baseRef || g.ref || '')
      const cor = String(g.color || '').trim() || '—'
      const keys = [`${ref}|${cor}`, `${ref}|—`, `${ref}|`, ref]
      for (const k of keys) {
        if (this.imagesByKey[k]) return this.imagesByKey[k]
      }
      return g.img
    },
    imgSrc(img) {
      if (!img) return ''
      if (typeof img !== 'string') return ''
      if (img.startsWith('http') || img.startsWith('data:')) return img
      if (/^[A-Za-z0-9+/=]+$/.test(img) && img.length > 50) return `data:image/jpeg;base64,${img}`
      return img
    },
    carregarImagens() {
      const payload = []
      for (const o of this.orders) {
        for (const g of this.groupedProducts(o)) {
          const cor = String(g.color || '').trim() || '—'
          payload.push({
            cod_referencia: String(g.baseRef || g.ref || ''),
            nom_marca: String(o.brand || ''),
            des_cor: cor,
            des_produto: String(g.name || '')
          })
        }
      }
      if (!payload.length) return
      axios.put('/api/produtos/images/', payload)
        .then(res => {
          const data = res.data
          if (!data) return
          const arr = Array.isArray(data) ? data : Object.keys(data).map(k => data[k])
          for (const it of arr) {
            if (!it) continue
            const ref = String(it.cod_referencia ?? '')
            const cor = String(it.des_cor ?? '').trim() || '—'
            const imgVal = it.img
            if (imgVal != null && imgVal !== '') {
              this.$set(this.imagesByKey, `${ref}|${cor}`, imgVal)
              this.$set(this.imagesByKey, `${ref}|—`, imgVal)
              this.$set(this.imagesByKey, ref, imgVal)
            }
          }
        })
        .catch(() => {})
    },
    async startSync(backfillFrom) {
      // Only treat as backfill if it's a date string (YYYY-MM-DD), not e.g. event object
      const isBackfill = typeof backfillFrom === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(backfillFrom)
      const fromParam = isBackfill ? backfillFrom : null
      this.syncing = true
      this.backfillRunning = !!fromParam
      this.showSyncModal = true
      this.syncPct = 0
      this.syncDone = []
      this.syncCur = fromParam ? 'Importando histórico…' : 'Conectando…'
      const url = fromParam
        ? `/api/pedidos-chegando/sync?backfill_from=${encodeURIComponent(fromParam)}`
        : '/api/pedidos-chegando/sync'
      const timeout = fromParam ? 120000 : 60000
      try {
        const res = await axios.post(url, null, { timeout }).catch(err => ({ data: null, err }))
        if (res && res.data) {
          this.syncDone = res.data.log || ['Concluído.']
          this.syncPct = 100
          if (Array.isArray(res.data.orders) && res.data.orders.length) {
            this.orders = res.data.orders
            this.$nextTick(() => { this.carregarImagens() })
          }
        } else {
          const err = res && res.err
          let msg = 'Erro ao conectar. Verifique se o backend está no ar e Gmail no .env.'
          if (err) {
            if (err.code === 'ECONNABORTED' || err.message && err.message.includes('timeout')) msg = 'Tempo limite. A importação demorou muito; tente uma data mais recente (ex: último ano).'
            else if (err.message === 'Network Error' || (err.message && err.message.includes('fetch'))) msg = 'Erro de rede. Backend está rodando? (ex: docker ou uvicorn na porta 8000).'
            else if (err.message) msg = err.message
          }
          this.syncDone = [msg]
          this.syncPct = 100
        }
      } finally {
        this.lastSyncAt = Date.now()
        this.syncing = false
        this.backfillRunning = false
        setTimeout(() => { this.showSyncModal = false }, 1500)
      }
    },
    startBackfill() {
      this.showBackfill = false
      this.startSync(this.backfillFrom || '2026-01-01')
    },
    saveManual() {
      const f = this.manualForm
      const totalPairs = f.products.reduce((a, p) => a + (Number(p.qty) || 0), 0)
      const dDate = f.dDate ? new Date(f.dDate).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }) : '—'
      this.orders.unshift({
        id: Date.now(),
        brand: f.brand || 'Marca',
        ref: f.ref || '—',
        status: 'confirmed',
        source: 'manual',
        hist: false,
        deliveryMonth: dDate,
        totalPairs,
        flagged: 0,
        conf: 1,
        provider: 'manual',
        invoice: false,
        products: f.products.filter(p => p.ref || p.name).map(p => ({
          ref: p.ref,
          name: p.name,
          color: p.color,
          hex: '#888',
          qty: Number(p.qty) || 0,
          unit: p.unit || 'par',
          sizes: p.sizes || {},
          img: '',
          src: 'manual',
          flag: false
        }))
      })
      this.showManual = false
      this.manualForm = { brand: '', ref: '', oDate: '', dDate: '', products: [{ ref: '', name: '', color: '', qty: 0 }] }
    }
  },
  mounted() {
    // Load from backend when available (optional; page shows mock data immediately)
    axios.get('/api/pedidos-chegando', { timeout: 3000 })
      .then(res => {
        if (res.data && Array.isArray(res.data)) {
          this.orders = res.data
          if (res.data.length) this.$nextTick(() => { this.carregarImagens() })
          this.loadFeedbackAnalytics()
        }
      })
      .catch(() => {})
  }
}
</script>

<style scoped>
.pc { font-family: 'DM Sans', system-ui, sans-serif; background: #f1f5f9; min-height: 100vh; padding: 14px; font-size: 14px; color: #0f172a; }
.pc-header { margin-bottom: 14px; }
.pc-title { font-size: 19px; font-weight: 700; color: #0f172a; margin: 0; }
.pc-subtitle { font-size: 11px; color: #64748b; margin-top: 2px; }
.pc-main { display: flex; gap: 14px; overflow: hidden; min-height: calc(100vh - 100px); }
.pc-sidebar { width: 272px; flex-shrink: 0; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow-y: auto; padding: 0; }
.pc-ss { padding: 14px 16px; border-bottom: 1px solid #e5e7eb; }
.pc-sl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 10px; font-weight: 600; }
.pc-search-input { width: 100%; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #f8fafc; color: #0f172a; font-size: 13px; outline: none; }
.pc-search-input:focus { border-color: #1d4ed8; }
.pc-fpill { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 13px; color: #64748b; }
.pc-fpill:hover { background: #f1f5f9; color: #0f172a; }
.pc-fpill.on { background: #e0e7ff; color: #1d4ed8; font-weight: 500; }
.pc-fpill-left { display: flex; align-items: center; gap: 7px; }
.pc-cnt { font-size: 11px; background: #f1f5f9; border-radius: 10px; padding: 1px 7px; }
.pc-fpill.on .pc-cnt { background: #c7d2fe; }
.pc-dot { width: 8px; height: 8px; border-radius: 50%; }
.pc-dot.d-rev { background: #f59e0b; }
.pc-dot.d-conf { background: #2563eb; }
.pc-dot.d-tr { background: #15803d; }
.pc-dot.d-part { background: #ea580c; }
.pc-dot.d-done { background: #94a3b8; }
.pc-ypill { display: flex; align-items: center; justify-content: space-between; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; color: #64748b; }
.pc-ypill:hover { background: #f1f5f9; }
.pc-ypill.on { background: #e0e7ff; color: #0f172a; font-weight: 500; }
.pc-htag { background: rgba(0,0,0,.07); border-radius: 3px; padding: 1px 6px; font-size: 10px; margin-left: 4px; color: #64748b; }
.pc-mpill { display: flex; align-items: center; gap: 8px; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; color: #64748b; }
.pc-mpill:hover { background: #f1f5f9; }
.pc-mpill.on { background: #e0e7ff; color: #0f172a; font-weight: 500; }
.pc-mlabel { width: 40px; }
.pc-mbar { flex: 1; height: 3px; border-radius: 2px; background: #e5e7eb; overflow: hidden; }
.pc-mbar-fill { height: 100%; background: #1d4ed8; border-radius: 2px; }
.pc-mcount { font-size: 11px; color: #64748b; }
.pc-sync-btn { margin-bottom: 8px; }
.pc-sync-hint { font-size: 11px; color: #64748b; line-height: 1.5; margin-bottom: 10px; }
.pc-obtn { margin-top: 6px; }
.pc-obtn-warn { border-color: #f59e0b; color: #b45309; }
.pc-content { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.pc-smbar { display: flex; gap: 20px; flex-wrap: wrap; padding: 12px 18px; background: #e2e8f0; border-radius: 8px; font-size: 12px; }
.pc-si .pc-val { font-size: 16px; font-weight: 600; color: #0f172a; }
.pc-si .pc-lbl { color: #64748b; font-size: 11px; margin-top: 2px; }
.pc-val-green { color: #15803d !important; }
.pc-val-yellow { color: #b45309 !important; }
.pc-val-muted { color: #64748b !important; }
.pc-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.pc-card.needs-review { border-left: 3px solid #f59e0b; }
.pc-card.confirmed { border-left: 3px solid #2563eb; }
.pc-card.in-transit { border-left: 3px solid #15803d; }
.pc-card.partial { border-left: 3px solid #ea580c; }
.pc-card.complete { border-left: 3px solid #94a3b8; opacity: .85; }
.pc-ch { display: flex; align-items: center; gap: 12px; padding: 13px 16px; cursor: pointer; border-bottom: 1px solid transparent; }
.pc-ch:hover { background: rgba(0,0,0,.02); }
.pc-ch.open { border-bottom-color: #e5e7eb; }
.pc-blogo { width: 38px; height: 38px; border-radius: 6px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 11px; color: #64748b; flex-shrink: 0; }
.pc-cmeta { flex: 1; min-width: 0; }
.pc-cbrand { font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 6px; }
.pc-csub { font-size: 12px; color: #64748b; margin-top: 3px; display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.pc-sep { opacity: .5; }
.pc-cright { display: flex; align-items: center; gap: 7px; flex-shrink: 0; }
.pc-chev { font-size: 11px; color: #64748b; transition: transform .2s; }
.pc-chev.open { transform: rotate(180deg); }
.pc-stag { font-size: 11px; padding: 2px 6px; border-radius: 3px; }
.pc-stag.st-email { background: #dbeafe; color: #1d4ed8; }
.pc-stag.st-manual { background: #ffedd5; color: #ea580c; }
.pc-sbadge { font-size: 11px; font-weight: 500; padding: 3px 9px; border-radius: 20px; white-space: nowrap; }
.pc-sbadge.b-rev { background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }
.pc-sbadge.b-conf { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
.pc-sbadge.b-tr { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.pc-sbadge.b-part { background: #ffedd5; color: #ea580c; border: 1px solid #fdba74; }
.pc-sbadge.b-done { background: #f1f5f9; color: #64748b; border: 1px solid #e5e7eb; }
.pc-acchip { font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-left: 4px; }
.pc-acchip.ac-soon { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.pc-acchip.ac-week { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
.pc-acchip.ac-late { background: #f1f5f9; color: #64748b; border: 1px solid #e5e7eb; }
.pc-cbody { padding: 14px 16px; }
.pc-inv-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; background: #dcfce7; border: 1px solid #86efac; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; font-size: 12px; color: #15803d; }
.pc-track { margin-left: auto; font-size: 11px; font-family: monospace; }
.pc-rev-alert { display: flex; align-items: flex-start; gap: 10px; background: #fefce8; border: 1px solid #fde047; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; font-size: 12px; }
.pc-rev-icon { font-size: 15px; flex-shrink: 0; }
.pc-rat { flex: 1; line-height: 1.5; }
.pc-provider-toggle { cursor: pointer; text-decoration: underline; text-decoration-style: dotted; }
.pc-provider-toggle:hover { color: #1d4ed8; }
.pc-raa { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.pc-actions { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
.pc-table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }
.pc-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.pc-th { text-align: left; padding: 10px 12px; background: #f8fafc; font-weight: 600; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e5e7eb; }
.pc-th-img { width: 80px; text-align: center; }
.pc-th-qty { width: 90px; text-align: right; }
.pc-trow { border-bottom: 1px solid #f1f5f9; }
.pc-trow:hover { background: #f8fafc; }
.pc-trow.fl { background: #fefce8; }
.pc-td { padding: 8px 12px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; }
.pc-td-ref { font-family: monospace; font-size: 12px; color: #475569; }
.pc-td-desc { max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #0f172a; }
.pc-td-img { text-align: center; }
.pc-img-cell { position: relative; display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.pc-table-img { width: 100%; height: 100%; object-fit: contain; background: #fff; }
.pc-img-placeholder { color: #94a3b8; font-size: 12px; }
.pc-pflag { position: absolute; top: 2px; left: 2px; font-size: 10px; }
.pc-isrc { position: absolute; bottom: 2px; right: 2px; font-size: 8px; background: rgba(0,0,0,.5); color: #fff; padding: 1px 3px; border-radius: 2px; }
.pc-isrc.pdf { background: #15803d; }
.pc-isrc.auto { background: #1d4ed8; }
.pc-isrc.manual { background: #ea580c; }
.pc-csw { display: inline-block; width: 10px; height: 10px; border-radius: 50%; border: 1px solid rgba(0,0,0,.15); margin-right: 6px; vertical-align: middle; }
.pc-td-qty { text-align: right; font-weight: 500; color: #1d4ed8; font-family: monospace; }
.pc-th-grade { min-width: 80px; }
.pc-td-grade { font-size: 11px; color: #475569; }
.pc-grade-text { font-family: monospace; }
.pc-grade-empty { color: #94a3b8; }
.pc-grade-grid { display: grid; grid-template-rows: auto auto; gap: 2px 4px; justify-items: center; }
.pc-grade-cell { min-width: 20px; text-align: center; }
.pc-grade-size { font-weight: 600; font-size: 0.85em; }
.pc-grade-qty { font-size: 0.8em; color: #64748b; }
.pc-feedback-dd { display: inline-block; margin-left: 4px; }
.pc-fb-icon { font-size: 11px; opacity: 0.6; cursor: pointer; }
.pc-fb-icon:hover { opacity: 1; }
.pc-feedback-pop { min-width: 140px; }
.pc-fb-row { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.pc-fb-row:last-child { margin-bottom: 0; }
.pc-fb-lbl { width: 36px; font-size: 11px; }
.pc-fb-btn { width: 22px; height: 20px; padding: 0; font-size: 11px; border: 1px solid #e5e7eb; border-radius: 3px; background: #fff; cursor: pointer; }
.pc-fb-btn:hover { background: #f1f5f9; }
.pc-fb-btn.ok { background: #dcfce7; border-color: #86efac; color: #15803d; }
.pc-fb-btn.err { background: #fee2e2; border-color: #fca5a5; color: #b91c1c; }
.pc-fb-analytics { max-height: 120px; overflow-y: auto; }
.pc-fb-brand { margin-bottom: 6px; padding: 6px 8px; background: #f8fafc; border-radius: 6px; }
.pc-fb-brand-name { font-weight: 600; font-size: 12px; margin-bottom: 2px; }
.pc-fb-stats { display: flex; flex-wrap: wrap; gap: 4px; }
.pc-fb-stat { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: #e2e8f0; color: #475569; }
.pc-fb-stat.err { background: #fee2e2; color: #b91c1c; }
.pc-fb-summary { margin-top: 6px; }
.pc-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: #64748b; padding: 60px 20px; text-align: center; }
.pc-empty-icon { font-size: 44px; opacity: .3; }
.pc-ibox { background: #eff6ff; border: 1px solid #93c5fd; border-radius: 8px; padding: 12px 16px; font-size: 12px; color: #1d4ed8; line-height: 1.6; }
.pc-slog { font-size: 11px; color: #64748b; max-height: 120px; overflow-y: auto; }
.pc-sll.ok::before { content: '✓ '; color: #15803d; }
.pc-sll.run::before { content: '↻ '; color: #1d4ed8; }
</style>
