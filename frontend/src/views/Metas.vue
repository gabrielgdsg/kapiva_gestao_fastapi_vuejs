<template>
  <div class="page-layout metas-container">
    <div class="page-header">
      <h1 class="page-title">Metas</h1>
      <div class="page-subtitle">Administração de metas por vendedor e período</div>
    </div>
    <div class="page-main">
    
    <!-- Compact Year/Month bar -->
    <div class="metas-top-bar d-flex align-items-center flex-wrap mb-3">
      <span class="metas-period-label">Período:</span>
      <b-form-select v-model="ano" :options="anoOptions" size="sm" class="metas-period-select" @change="onAnoMesChange"></b-form-select>
      <b-form-select v-model="mes" :options="mesOptions" size="sm" class="metas-period-select ml-2" @change="onAnoMesChange"></b-form-select>
      <b-button v-b-toggle.collapse-config variant="outline-secondary" size="sm" class="ml-3">
        Configuração ▾
      </b-button>
      <div class="ml-3 d-flex align-items-center">
        <span class="small text-muted mr-2">Metas para vendedores:</span>
        <b-form-radio-group v-model="metasLiberadas" buttons button-variant="outline-primary" size="sm" @change="onMetasLiberadasChange">
          <b-form-radio :value="false">Bloqueadas</b-form-radio>
          <b-form-radio :value="true">Liberadas</b-form-radio>
        </b-form-radio-group>
      </div>
    </div>

    <!-- Configuration (collapsed by default) — Meta 1 / Meta 2 rows with Margem crescimento % -->
    <b-collapse id="collapse-config" class="mb-3">
      <b-card body-class="py-2 px-3" class="metas-config-card">
        <div class="config-row config-two-rows">
          <div class="config-row-inner">
            <span class="config-group-label">Meta 1</span>
            <div class="config-field">
              <label class="small">Margem crescimento %</label>
              <b-form-input v-model.number="margemCrescimentoMeta1" type="number" step="0.5" min="-100" max="200" size="sm" @input="onConfigInput"></b-form-input>
            </div>
          </div>
          <div class="config-row-inner">
            <span class="config-group-label">Meta 2</span>
            <div class="config-field">
              <label class="small">Margem crescimento %</label>
              <b-form-input v-model.number="margemCrescimentoMeta2" type="number" step="0.5" min="-100" max="200" size="sm" @input="onConfigInput"></b-form-input>
            </div>
          </div>
          <div class="config-extra">
            <b-button variant="outline-primary" size="sm" @click="toggleMetasAdicionais">
              {{ showMetasAdicionais ? 'Ocultar' : 'Adicionar' }} Metas
            </b-button>
          </div>
        </div>
        <div class="config-row mt-2" v-if="showMetasAdicionais">
          <div class="config-field" v-for="(meta, index) in metasAdicionais" :key="index">
            <label class="small">Meta {{ index + 3 }}</label>
            <b-form-input v-model.number="meta.value" type="number" step="0.1" min="0" placeholder="Mult." size="sm"></b-form-input>
          </div>
        </div>
      </b-card>
    </b-collapse>

    <!-- Calculated Targets -->
    <b-card class="mb-3 metas-calculadas-card">
      <div class="d-flex justify-content-between align-items-center flex-wrap mb-3">
        <div class="d-flex align-items-center flex-wrap">
          <h4 class="mb-0 mr-3">Cálculo das Metas</h4>
          <small v-if="metasCalculadas" class="text-muted">Base: {{ getMonthYearLabel(metasCalculadas.ano_anterior, metasCalculadas.mes) }}</small>
        </div>
        <div class="d-flex align-items-center mt-1 mt-sm-0">
          <b-button variant="outline-secondary" size="sm" @click="toggleEditarMetas" :disabled="loading || !metasCalculadas" class="mr-2">
            {{ metasEditMode ? 'Desativar edição' : 'Editar Metas' }}
          </b-button>
          <b-button variant="primary" size="sm" @click="estimarMetas" :disabled="loading">
            Estimar Metas
          </b-button>
        </div>
      </div>

      <p v-if="!metasCalculadas" class="text-muted small mb-0">Selecione o período acima e clique em <strong>Estimar Metas</strong> para calcular.</p>

      <div v-if="metasCalculadas">
      <b-button v-b-toggle.collapse-incluir-vendedor variant="outline-secondary" size="sm" class="mb-3">
        Incluir vendedor/Alterar Grupo ▾
      </b-button>
      <b-collapse id="collapse-incluir-vendedor" class="mb-3">
        <b-card body-class="py-2">
          <h6 class="mb-2">Incluir vendedor/Alterar Grupo</h6>
          <p class="small text-muted mb-2">Tipo por ano: vendas ano ant. usam config {{ ano - 1 }}/{{ mes }}; metas usam tipo atual. Ex.: vendedor que mudou Roupa→Calçado: config {{ ano - 1 }} com Roupa, {{ ano }} com Calçado.</p>
          <b-row align-v="center">
            <b-col sm="4">
              <label class="small">Vendedor</label>
              <b-form-select
                v-model="novoVendedorCod"
                :options="vendedoresIncluirOptions"
                size="sm"
                value-field="value"
                text-field="text"
                @input="onVendedorIncluirSelected"
              >
                <template v-slot:first>
                  <option :value="null">— Selecione —</option>
                </template>
              </b-form-select>
            </b-col>
            <b-col sm="3">
              <label class="small">Grupo</label>
              <b-form-select v-model="novoVendedorGrupo" :options="tipoFilterOptions" size="sm" value-field="value" text-field="text"></b-form-select>
            </b-col>
            <b-col sm="3">
              <b-button size="sm" variant="primary" @click="addVendedorToGroup" :disabled="!novoVendedorCod || !novoVendedorGrupo">
                {{ getVendedorTipoInMetas(novoVendedorCod) ? 'Alterar grupo' : 'Adicionar' }}
              </b-button>
            </b-col>
          </b-row>
        </b-card>
      </b-collapse>

      <!-- Compact Summary Table -->
      <table class="table table-sm table-bordered mb-3" style="font-size:13px;">
        <thead class="thead-light">
          <tr>
            <th>Grupo</th>
            <th class="text-right">Vendedores</th>
            <th class="text-right">Vendas Ano Ant.</th>
            <th class="text-right">Média/Vendedor</th>
            <th class="text-right">Meta 1 (1,20%)</th>
            <th class="text-right">Meta 2 (1,50%)</th>
            <th class="text-right">Share %</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><b-badge variant="primary">Calçado</b-badge></td>
            <td class="text-right">{{ activeCount('calcado') }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.calcado.sales_anterior) }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.calcado.media) }}</td>
            <td class="text-right">{{ formatMoney(groupSumMeta('calcado', 'meta_1')) }}</td>
            <td class="text-right">{{ formatMoney(groupSumMeta('calcado', 'meta_2')) }}</td>
            <td class="text-right">{{ marketSharePct('calcado') }}</td>
          </tr>
          <tr>
            <td><b-badge variant="success">Roupa</b-badge></td>
            <td class="text-right">{{ activeCount('roupa') }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.roupa.sales_anterior) }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.roupa.media) }}</td>
            <td class="text-right">{{ formatMoney(groupSumMeta('roupa', 'meta_1')) }}</td>
            <td class="text-right">{{ formatMoney(groupSumMeta('roupa', 'meta_2')) }}</td>
            <td class="text-right">{{ marketSharePct('roupa') }}</td>
          </tr>
          <tr v-if="metasCalculadas.loja">
            <td><b-badge variant="secondary">Loja</b-badge></td>
            <td class="text-right">{{ activeCount('loja') }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.loja.sales_anterior) }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.loja.media) }}</td>
            <td class="text-right">{{ formatMoney(groupSumMeta('loja', 'meta_1')) }}</td>
            <td class="text-right">{{ formatMoney(groupSumMeta('loja', 'meta_2')) }}</td>
            <td class="text-right">{{ marketSharePct('loja') }}</td>
          </tr>
        </tbody>
        <tfoot style="font-weight:bold;background:#f8f9fa;">
          <tr>
            <td>Totais Esperados</td>
            <td class="text-right">{{ activeCount('calcado') + activeCount('roupa') + activeCount('loja') }}</td>
            <td class="text-right">{{ formatMoney(metasCalculadas.total_sales_anterior) }}</td>
            <td></td>
            <td class="text-right">{{ formatMoney(summaryTotalsExpected().total_expected_1) }}</td>
            <td class="text-right">{{ formatMoney(summaryTotalsExpected().total_expected_2) }}</td>
            <td class="text-right">100%</td>
          </tr>
          <tr v-if="metasAtual" style="color:#0a9e6a;">
            <td>Totais Atuais</td>
            <td></td>
            <td class="text-right">{{ formatMoney(totalAtualVendas) }}</td>
            <td></td>
            <td class="text-right"><small>{{ totalAtualPctMeta1 }}% da Meta 1</small></td>
            <td class="text-right"><small>{{ totalAtualPctMeta2 }}% da Meta 2</small></td>
            <td></td>
          </tr>
        </tfoot>
      </table>
      
      <b-row>
        <b-col sm="6">
          <h5 class="mb-2 mt-2"><b-badge variant="primary">Calçado</b-badge></h5>
          <b-table 
            v-if="metasCalculadas.calcado.vendedores_detalhes && metasCalculadas.calcado.vendedores_detalhes.length > 0"
            :items="metasCalculadas.calcado.vendedores_detalhes" 
            :fields="vendedorSalesFields"
            :tbody-tr-class="rowClassByTipo"
            small
            striped
            class="mt-2 mb-3"
          >
            <template v-slot:cell(ativo)="data">
              <b-form-checkbox
                :checked="data.item.ativo !== false"
                switch
                size="sm"
                @change="setVendedorAtivo(data.item, $event)"
              />
            </template>
            <template v-slot:cell(vlr_sales_anterior)="data">
              {{ formatMoney(data.value) }}
            </template>
            <template v-slot:cell(tipo)="data">
              <span v-if="!editTipoMode || editTipoMode !== data.item.cod_vendedor">
                <b-badge :variant="data.value === 'Calçado' ? 'primary' : data.value === 'Roupa' ? 'success' : 'secondary'">
                  {{ data.value || 'Calçado' }}
                </b-badge>
                <b-button variant="link" size="sm" @click="editTipoMode = data.item.cod_vendedor" class="p-0 ml-1">
                  <small>✏️</small>
                </b-button>
              </span>
              <b-form-select
                v-else
                v-model="data.item.tipo"
                :options="tipoFilterOptions"
                size="sm"
                @change="saveTipoMetasCalculadas(data.item)"
                style="max-width: 120px;"
              ></b-form-select>
            </template>
            <template v-slot:cell(meta_1)="data">
              <span v-if="!metasEditMode" class="text-right d-inline-block" style="min-width:80px;">{{ displayMetaValue(data.item, 'meta_1') }}</span>
              <b-form-input
                v-else
                :value="getMetaInputValue(data.item, 'meta_1')"
                type="text"
                size="sm"
                class="text-right"
                style="max-width: 120px;"
                placeholder=""
                @focus="onMetaFocus(data.item, 'meta_1')"
                @input="onMetaInput(data.item, 'meta_1', $event)"
                @blur="onMetaBlur(data.item, 'meta_1')"
              ></b-form-input>
            </template>
            <template v-slot:cell(meta_2)="data">
              <span v-if="!metasEditMode" class="text-right d-inline-block" style="min-width:80px;">{{ displayMetaValue(data.item, 'meta_2') }}</span>
              <b-form-input
                v-else
                :value="getMetaInputValue(data.item, 'meta_2')"
                type="text"
                size="sm"
                class="text-right"
                style="max-width: 120px;"
                placeholder=""
                @focus="onMetaFocus(data.item, 'meta_2')"
                @input="onMetaInput(data.item, 'meta_2', $event)"
                @blur="onMetaBlur(data.item, 'meta_2')"
              ></b-form-input>
            </template>
          </b-table>
          <div v-if="metasEditMode" class="metas-edit-group mt-2 p-2 border rounded bg-light">
            <h6 class="mb-2">Metas – Calçado</h6>
            <div class="d-flex align-items-center mb-2 small">
              <span class="mr-2">Modo:</span>
              <b-form-radio-group v-model="metaAutoByGroup.calcado" buttons button-variant="outline-primary" size="sm" :options="[{ value: true, text: 'Auto' }, { value: false, text: 'Manual' }]" @change="hasChanges = true" />
            </div>
            <b-row class="small align-items-end">
              <b-col cols="12" md="4">
                <label class="mb-0">Meta 2</label>
                <b-form-input :value="getGroupMetaInputValue('calcado', 'meta_2')" size="sm" class="text-right" placeholder="0" @focus="onGroupMetaFocus('calcado', 'meta_2')" @input="onGroupMetaInputOnlyBuffer('calcado', 'meta_2', $event)" />
              </b-col>
              <b-col cols="12" md="4">
                <label class="mb-0">Meta 1</label>
                <b-form-input :value="getGroupMetaInputValue('calcado', 'meta_1')" size="sm" class="text-right" placeholder="0" @focus="onGroupMetaFocus('calcado', 'meta_1')" @input="onGroupMetaInputOnlyBuffer('calcado', 'meta_1', $event)" />
              </b-col>
              <b-col cols="12" md="4">
                <b-button size="sm" variant="primary" @click="aplicarGroupMetas('calcado')">Aplicar</b-button>
              </b-col>
            </b-row>
          </div>
        </b-col>
        <b-col sm="6">
          <h5 class="mb-2 mt-2"><b-badge variant="success">Roupa</b-badge></h5>
          <b-table 
            v-if="metasCalculadas.roupa.vendedores_detalhes && metasCalculadas.roupa.vendedores_detalhes.length > 0"
            :items="metasCalculadas.roupa.vendedores_detalhes" 
            :fields="vendedorSalesFields"
            :tbody-tr-class="rowClassByTipo"
            small
            striped
            class="mt-2 mb-3"
          >
            <template v-slot:cell(ativo)="data">
              <b-form-checkbox
                :checked="data.item.ativo !== false"
                switch
                size="sm"
                @change="setVendedorAtivo(data.item, $event)"
              />
            </template>
            <template v-slot:cell(vlr_sales_anterior)="data">
              {{ formatMoney(data.value) }}
            </template>
            <template v-slot:cell(tipo)="data">
              <span v-if="!editTipoMode || editTipoMode !== data.item.cod_vendedor">
                <b-badge :variant="data.value === 'Calçado' ? 'primary' : data.value === 'Roupa' ? 'success' : 'secondary'">
                  {{ data.value || 'Calçado' }}
                </b-badge>
                <b-button variant="link" size="sm" @click="editTipoMode = data.item.cod_vendedor" class="p-0 ml-1">
                  <small>✏️</small>
                </b-button>
              </span>
              <b-form-select
                v-else
                v-model="data.item.tipo"
                :options="tipoFilterOptions"
                size="sm"
                @change="saveTipoMetasCalculadas(data.item)"
                style="max-width: 120px;"
              ></b-form-select>
            </template>
            <template v-slot:cell(meta_1)="data">
              <span v-if="!metasEditMode" class="text-right d-inline-block" style="min-width:80px;">{{ displayMetaValue(data.item, 'meta_1') }}</span>
              <b-form-input
                v-else
                :value="getMetaInputValue(data.item, 'meta_1')"
                type="text"
                size="sm"
                class="text-right"
                style="max-width: 120px;"
                placeholder=""
                @focus="onMetaFocus(data.item, 'meta_1')"
                @input="onMetaInput(data.item, 'meta_1', $event)"
                @blur="onMetaBlur(data.item, 'meta_1')"
              ></b-form-input>
            </template>
            <template v-slot:cell(meta_2)="data">
              <span v-if="!metasEditMode" class="text-right d-inline-block" style="min-width:80px;">{{ displayMetaValue(data.item, 'meta_2') }}</span>
              <b-form-input
                v-else
                :value="getMetaInputValue(data.item, 'meta_2')"
                type="text"
                size="sm"
                class="text-right"
                style="max-width: 120px;"
                placeholder=""
                @focus="onMetaFocus(data.item, 'meta_2')"
                @input="onMetaInput(data.item, 'meta_2', $event)"
                @blur="onMetaBlur(data.item, 'meta_2')"
              ></b-form-input>
            </template>
          </b-table>
          <div v-if="metasEditMode" class="metas-edit-group mt-2 p-2 border rounded bg-light">
            <h6 class="mb-2">Metas – Roupa</h6>
            <div class="d-flex align-items-center mb-2 small">
              <span class="mr-2">Modo:</span>
              <b-form-radio-group v-model="metaAutoByGroup.roupa" buttons button-variant="outline-success" size="sm" :options="[{ value: true, text: 'Auto' }, { value: false, text: 'Manual' }]" @change="hasChanges = true" />
            </div>
            <b-row class="small align-items-end">
              <b-col cols="12" md="4">
                <label class="mb-0">Meta 2</label>
                <b-form-input :value="getGroupMetaInputValue('roupa', 'meta_2')" size="sm" class="text-right" placeholder="0" @focus="onGroupMetaFocus('roupa', 'meta_2')" @input="onGroupMetaInputOnlyBuffer('roupa', 'meta_2', $event)" />
              </b-col>
              <b-col cols="12" md="4">
                <label class="mb-0">Meta 1</label>
                <b-form-input :value="getGroupMetaInputValue('roupa', 'meta_1')" size="sm" class="text-right" placeholder="0" @focus="onGroupMetaFocus('roupa', 'meta_1')" @input="onGroupMetaInputOnlyBuffer('roupa', 'meta_1', $event)" />
              </b-col>
              <b-col cols="12" md="4">
                <b-button size="sm" variant="success" @click="aplicarGroupMetas('roupa')">Aplicar</b-button>
              </b-col>
            </b-row>
          </div>

          <!-- Loja: below Roupa (right column) -->
          <div v-if="metasCalculadas.loja" class="mt-5 pt-4 border-top" style="margin-top: 1.5rem !important;">
            <h5 class="mb-2 mt-2"><b-badge variant="secondary">Loja</b-badge></h5>
            <b-table
              v-if="metasCalculadas.loja.vendedores_detalhes && metasCalculadas.loja.vendedores_detalhes.length > 0"
              :items="metasCalculadas.loja.vendedores_detalhes" 
              :fields="vendedorSalesFields"
              :tbody-tr-class="rowClassByTipo"
              small
              striped
              class="mt-2 mb-3"
            >
              <template v-slot:cell(ativo)="data">
                <b-form-checkbox
                  :checked="data.item.ativo !== false"
                  switch
                  size="sm"
                  @change="setVendedorAtivo(data.item, $event)"
                />
              </template>
              <template v-slot:cell(vlr_sales_anterior)="data">
                {{ formatMoney(data.value) }}
              </template>
              <template v-slot:cell(tipo)="data">
                <span v-if="!editTipoMode || editTipoMode !== data.item.cod_vendedor">
                  <b-badge variant="secondary">
                    {{ data.value || 'Loja' }}
                  </b-badge>
                  <b-button variant="link" size="sm" @click="editTipoMode = data.item.cod_vendedor" class="p-0 ml-1">
                    <small>✏️</small>
                  </b-button>
                </span>
                <b-form-select
                  v-else
                  v-model="data.item.tipo"
                  :options="tipoFilterOptions"
                  size="sm"
                  @change="saveTipoMetasCalculadas(data.item)"
                  style="max-width: 120px;"
                ></b-form-select>
              </template>
              <template v-slot:cell(meta_1)="data">
                <span v-if="!metasEditMode" class="text-right d-inline-block" style="min-width:80px;">{{ displayMetaValue(data.item, 'meta_1') }}</span>
                <b-form-input
                  v-else
                  :value="getMetaInputValue(data.item, 'meta_1')"
                  type="text"
                  size="sm"
                  class="text-right"
                  style="max-width: 120px;"
                  placeholder=""
                  @focus="onMetaFocus(data.item, 'meta_1')"
                  @input="onMetaInput(data.item, 'meta_1', $event)"
                  @blur="onMetaBlur(data.item, 'meta_1')"
                ></b-form-input>
              </template>
              <template v-slot:cell(meta_2)="data">
                <span v-if="!metasEditMode" class="text-right d-inline-block" style="min-width:80px;">{{ displayMetaValue(data.item, 'meta_2') }}</span>
                <b-form-input
                  v-else
                  :value="getMetaInputValue(data.item, 'meta_2')"
                  type="text"
                  size="sm"
                  class="text-right"
                  style="max-width: 120px;"
                  placeholder=""
                  @focus="onMetaFocus(data.item, 'meta_2')"
                  @input="onMetaInput(data.item, 'meta_2', $event)"
                  @blur="onMetaBlur(data.item, 'meta_2')"
                ></b-form-input>
              </template>
            </b-table>
            <div v-if="metasEditMode" class="metas-edit-group mt-2 p-2 border rounded bg-light">
              <h6 class="mb-2">Metas – Loja</h6>
              <div class="d-flex align-items-center mb-2 small">
                <span class="mr-2">Modo:</span>
                <b-form-radio-group v-model="metaAutoByGroup.loja" buttons button-variant="outline-secondary" size="sm" :options="[{ value: true, text: 'Auto' }, { value: false, text: 'Manual' }]" @change="hasChanges = true" />
              </div>
              <b-row class="small align-items-end">
                <b-col cols="12" md="4">
                  <label class="mb-0">Meta 2</label>
                  <b-form-input :value="getGroupMetaInputValue('loja', 'meta_2')" size="sm" class="text-right" placeholder="0" @focus="onGroupMetaFocus('loja', 'meta_2')" @input="onGroupMetaInputOnlyBuffer('loja', 'meta_2', $event)" />
                </b-col>
                <b-col cols="12" md="4">
                  <label class="mb-0">Meta 1</label>
                  <b-form-input :value="getGroupMetaInputValue('loja', 'meta_1')" size="sm" class="text-right" placeholder="0" @focus="onGroupMetaFocus('loja', 'meta_1')" @input="onGroupMetaInputOnlyBuffer('loja', 'meta_1', $event)" />
                </b-col>
                <b-col cols="12" md="4">
                  <b-button size="sm" variant="secondary" @click="aplicarGroupMetas('loja')">Aplicar</b-button>
                </b-col>
              </b-row>
            </div>
          </div>
      </b-col>
      </b-row>
      <div class="d-flex justify-content-end mt-3 pt-3 border-top">
        <b-button variant="outline-danger" size="sm" @click="limparMetas" :disabled="loading" class="mr-2">
          Limpar Metas
        </b-button>
        <b-button variant="success" size="sm" @click="salvarMetas" :disabled="loading" title="Gravar alterações nos valores de Meta 1 / Meta 2 da tabela">
          Salvar Metas
        </b-button>
      </div>
      </div>
    </b-card>

    <!-- Current Month Chart -->
    <b-card v-if="metasAtual" class="mb-3">
      <h4>Mês Atual - Vendas vs Metas</h4>
      <div v-if="chartData" style="height: 400px;">
        <canvas ref="chartCanvas"></canvas>
      </div>
      <b-table :items="metasAtual.vendedores" :fields="vendedorTableFields" striped hover class="mt-3" show-empty>
        <template v-slot:cell(nom_vendedor)="data">
          {{ data.value || getVendedorName(data.item.cod_vendedor) }}
        </template>
        <template v-slot:cell(vlr_atual)="data">
          {{ formatMoney(data.value) }}
        </template>
        <template v-slot:cell(meta_final)="data">
          {{ formatMoney(data.value) }}
        </template>
        <template v-slot:cell(meta_proporcional)="data">
          {{ formatMoney(data.value) }}
        </template>
        <template v-slot:cell(tipo)="data">
          <b-badge :variant="(data.value || 'Calçado') === 'Calçado' ? 'primary' : (data.value || 'Calçado') === 'Roupa' ? 'success' : 'secondary'">
            {{ data.value || 'Calçado' }}
          </b-badge>
        </template>
        <template v-slot:cell(percentual)="data">
          <b-badge :variant="data.value >= 100 ? 'success' : data.value >= 80 ? 'warning' : 'danger'">
            {{ (data.value || 0).toFixed ? (data.value || 0).toFixed(1) : data.value }}%
          </b-badge>
        </template>
        <template v-slot:foot>
          <tr class="font-weight-bold bg-light">
            <td>Total</td>
            <td></td>
            <td></td>
            <td class="text-right">{{ formatMoney(metasAtualSums.vendas_atuais) }}</td>
            <td class="text-right">{{ formatMoney(metasAtualSums.meta_proporcional) }}</td>
            <td class="text-right">{{ formatMoney(metasAtualSums.meta_final) }}</td>
            <td></td>
          </tr>
        </template>
      </b-table>
    </b-card>

    <!-- Sales Verification -->
    <b-card v-if="vendasVerificacao" class="mb-3">
      <h4>Verificação de Vendas - {{ vendasVerificacao.ano_anterior }}/{{ vendasVerificacao.mes.toString().padStart(2, '0') }}</h4>
      <b-row class="mb-3">
        <b-col sm="6">
          <p><strong>Período:</strong> {{ vendasVerificacao.data_ini }} até {{ vendasVerificacao.data_fim }}</p>
          <p><strong>Total de Vendedores Verificados:</strong> {{ vendasVerificacao.total_vendedores_verificados }}</p>
          <p><strong>Vendedores com Vendas:</strong> {{ filteredVendasDetalhadas.length }}</p>
          <p><strong>Total de Vendas:</strong> {{ formatMoney(filteredTotalVendas) }}</p>
        </b-col>
        <b-col sm="6">
          <label>Filtrar por Tipo:</label>
          <b-form-select v-model="filtroTipoVerificacao" :options="tipoFilterOptions" class="mt-1">
            <template v-slot:first>
              <option :value="null">Todos</option>
            </template>
          </b-form-select>
        </b-col>
      </b-row>
      <p><strong>Fonte:</strong> {{ vendasVerificacao.fonte }}</p>
      
      <b-table 
        v-if="filteredVendasDetalhadas && filteredVendasDetalhadas.length > 0"
        :items="filteredVendasDetalhadas" 
        :fields="verificacaoFields"
        striped
        hover
        class="mt-3"
      >
        <template v-slot:cell(vlr_monthly_summary)="data">
          {{ formatMoney(data.value) }}
        </template>
        <template v-slot:cell(vlr_direct_query)="data">
          {{ formatMoney(data.value) }}
        </template>
        <template v-slot:cell(diferenca)="data">
          <b-badge :variant="data.value < 0.01 ? 'success' : 'warning'">
            {{ formatMoney(data.value) }}
          </b-badge>
        </template>
        <template v-slot:cell(tipo)="data">
          <span v-if="!editTipoMode || editTipoMode !== data.item.cod_vendedor">
            <b-badge :variant="data.value === 'Calçado' ? 'primary' : data.value === 'Roupa' ? 'success' : 'secondary'">
              {{ data.value }}
            </b-badge>
            <b-button variant="link" size="sm" @click="editTipoMode = data.item.cod_vendedor" class="p-0 ml-1">
              <small>✏️</small>
            </b-button>
          </span>
          <b-form-select
            v-else
            v-model="data.item.tipo"
            :options="tipoFilterOptions"
            size="sm"
            @change="saveTipoVerificacao(data.item)"
            style="max-width: 120px;"
          ></b-form-select>
        </template>
        <template v-slot:cell(tipo)="data">
          <span v-if="!editTipoMode || editTipoMode !== data.item.cod_vendedor">
            <b-badge :variant="data.value === 'Calçado' ? 'primary' : data.value === 'Roupa' ? 'success' : 'secondary'">
              {{ data.value }}
            </b-badge>
            <b-button variant="link" size="sm" @click="editTipoMode = data.item.cod_vendedor" class="p-0 ml-1">
              <small>✏️</small>
            </b-button>
          </span>
          <b-form-select
            v-else
            v-model="data.item.tipo"
            :options="tipoFilterOptions"
            size="sm"
            @change="saveTipoVerificacao(data.item)"
            style="max-width: 120px;"
          ></b-form-select>
        </template>
        <template v-slot:cell(actions)="data">
          <b-button variant="info" size="sm" @click="showSellerChart(data.item.cod_vendedor, data.item.nom_vendedor)">
            Ver Gráfico
          </b-button>
        </template>
      </b-table>
      <b-alert v-else variant="warning" show>
        Nenhuma venda encontrada para o período {{ vendasVerificacao.data_ini }} até {{ vendasVerificacao.data_fim }}
      </b-alert>
    </b-card>
    
    <!-- Show/Hide All Charts Button -->
    <b-card v-if="metasAtual && metasAtual.vendedores && metasAtual.vendedores.length > 0" class="mb-3">
      <b-button 
        variant="primary" 
        @click="toggleAllCharts"
        class="w-100"
      >
        {{ showAllCharts ? 'Ocultar Todos os Gráficos' : 'Mostrar Todos os Gráficos' }}
      </b-button>
    </b-card>
    
    <!-- Individual Seller Charts (shown when showAllCharts is true or when manually opened) -->
    <div v-if="showAllCharts || Object.keys(sellerCharts).length > 0">
      <b-card 
        v-for="(chartData, cod_vendedor) in sellerCharts" 
        :key="cod_vendedor" 
        class="mb-3"
        :data-seller-chart="cod_vendedor"
        v-show="showAllCharts || chartData.visible !== false"
      >
      <h5>{{ chartData.nom_vendedor }} ({{ cod_vendedor }}) - {{ chartData.tipo }}</h5>
      <b-row class="mb-2">
        <b-col sm="4">
          <strong>Vendas Atuais:</strong> {{ formatMoney(chartData.vendas_atual) }}
        </b-col>
        <b-col sm="4">
          <strong>Meta Proporcional:</strong> {{ formatMoney(chartData.meta_proporcional_atual) }}
        </b-col>
        <b-col sm="2">
          <strong>Meta Final:</strong> {{ formatMoney(chartData.meta_final) }}
        </b-col>
        <b-col sm="2">
          <strong>Meta 1:</strong> {{ formatMoney(chartData.meta_1) }}
        </b-col>
        <b-col sm="2">
          <strong>Meta 2:</strong> {{ formatMoney(chartData.meta_2) }}
        </b-col>
      </b-row>
      <b-row class="mb-2">
        <b-col>
          <b-badge :variant="chartData.vendas_atual >= chartData.meta_proporcional_atual ? 'success' : 'warning'">
            {{ chartData.dia_atual }} de {{ chartData.dias_no_mes }} dias
          </b-badge>
          <span class="ml-2">
            {{ chartData.meta_proporcional_atual > 0 ? ((chartData.vendas_atual / chartData.meta_proporcional_atual) * 100).toFixed(1) : '0.0' }}% da meta proporcional
          </span>
        </b-col>
      </b-row>
      <div style="height: 400px;">
        <canvas :id="`seller-chart-${cod_vendedor}`"></canvas>
      </div>
      </b-card>
    </div>

    <b-alert v-if="loading" show variant="info">Carregando...</b-alert>
    <b-alert v-if="error" show variant="danger" dismissible @dismissed="error = null">
      {{ error }}
    </b-alert>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Chart from 'chart.js'

export default {
  name: 'Metas',
  data() {
    const currentDate = new Date()
    return {
      ano: currentDate.getFullYear(),
      mes: currentDate.getMonth() + 1,
      loading: false,
      error: null,
      vendedores: [],
      calcadoVendedores: [],
      roupaVendedores: [],
      vendedoresAtivos: [],
      margemCrescimentoMeta1: 5,
      margemCrescimentoMeta2: 10,
      meta1: 1.05,
      meta2: 1.10,
      metasAdicionais: [],
      showMetasAdicionais: false,
      showAgruparVendedores: false,
      metasCalculadas: null,
      metasAtual: null,
      chart: null,
      chartData: null,
      hasChanges: false,
      vendasVerificacao: null,
      filtroTipoVerificacao: null, // 'Calçado', 'Roupa', 'Loja', or null for all
      sellerCharts: {}, // Store individual charts for each seller
      editTipoMode: null, // Track which seller's tipo is being edited
      showAllCharts: false, // Toggle for showing all charts
      incluirLoja: true, // Include Loja vendedores in calculations and show Loja group
      metasEditMode: false, // When false, meta input boxes are hidden; show after "Editar Metas", hide after "Salvar Metas"
      metaEditBuffer: {}, // key: 'meta_${cod_vendedor}_meta_1' -> raw string while editing (avoids format-on-keystroke)
      metaAutoByGroup: { calcado: true, roupa: true, loja: true }, // true = Auto (Meta1/Meta2 linked by config %), false = Manual
      configApplyTimer: null, // debounce for auto-apply config → recalc Meta 1/Meta 2 in table
      vendedorTableFields: [
        {key: 'cod_vendedor', label: 'Código'},
        {key: 'nom_vendedor', label: 'Nome'},
        {key: 'tipo', label: 'Tipo'},
        {key: 'vlr_atual', label: 'Vendas Atuais'},
        {key: 'meta_proporcional', label: 'Meta Proporcional'},
        {key: 'meta_final', label: 'Meta Final'},
        {key: 'percentual', label: '% Atingido'}
      ],
      vendedorSalesFields: [
        {key: 'cod_vendedor', label: 'Código'},
        {key: 'nom_vendedor', label: 'Nome'},
        {key: 'ativo', label: 'Ativo'},
        {key: 'vlr_sales_anterior', label: 'Vendas Ano Anterior'},
        {key: 'meta_1', label: 'Meta 1'},
        {key: 'meta_2', label: 'Meta 2'},
        {key: 'mes_ano', label: 'Período'}
      ],
      verificacaoFields: [
        {key: 'cod_vendedor', label: 'Código'},
        {key: 'nom_vendedor', label: 'Nome'},
        {key: 'tipo', label: 'Tipo'},
        {key: 'vlr_monthly_summary', label: 'Monthly Summary'},
        {key: 'vlr_direct_query', label: 'Direct Query'},
        {key: 'diferenca', label: 'Diferença'},
        {key: 'actions', label: 'Ações', thClass: 'text-center', tdClass: 'text-center'}
      ],
      tipoFilterOptions: [
        {value: 'Calçado', text: 'Calçado'},
        {value: 'Roupa', text: 'Roupa'},
        {value: 'Loja', text: 'Loja'}
      ],
      novoVendedorCod: null,
      novoVendedorGrupo: 'Calçado',
      metasLiberadas: false
    }
  },
  computed: {
    vendedoresIncluirOptions() {
      if (!this.vendedores.length) return []
      return this.vendedores
        .filter(v => v.cod_vendedor != null)
        .map(v => {
          const tipo = this.getVendedorTipoInMetas(Number(v.cod_vendedor))
          const tipoLabel = tipo ? ` (${tipo})` : ' (—)'
          return { value: v.cod_vendedor, text: `${v.cod_vendedor} - ${v.nom_vendedor || 'Vendedor'}${tipoLabel}` }
        })
    },
    totalVendasEspMeta1() {
      return this.groupSumMeta('calcado', 'meta_1') + this.groupSumMeta('roupa', 'meta_1') + this.groupSumMeta('loja', 'meta_1')
    },
    totalVendasEspMeta2() {
      return this.groupSumMeta('calcado', 'meta_2') + this.groupSumMeta('roupa', 'meta_2') + this.groupSumMeta('loja', 'meta_2')
    },
    anoOptions() {
      const currentYear = new Date().getFullYear()
      const years = []
      // Start from 2019 onwards
      for (let i = 2019; i <= currentYear + 2; i++) {
        years.push({value: i, text: i.toString()})
      }
      return years
    },
    mesOptions() {
      return [
        {value: 1, text: 'Janeiro'},
        {value: 2, text: 'Fevereiro'},
        {value: 3, text: 'Março'},
        {value: 4, text: 'Abril'},
        {value: 5, text: 'Maio'},
        {value: 6, text: 'Junho'},
        {value: 7, text: 'Julho'},
        {value: 8, text: 'Agosto'},
        {value: 9, text: 'Setembro'},
        {value: 10, text: 'Outubro'},
        {value: 11, text: 'Novembro'},
        {value: 12, text: 'Dezembro'}
      ]
    },
    vendedorOptions() {
      return this.vendedores.map(v => ({
        value: v.cod_vendedor,
        text: `${v.cod_vendedor} - ${v.nom_vendedor}`
      }))
    },
    filteredVendasDetalhadas() {
      if (!this.vendasVerificacao || !this.vendasVerificacao.vendas_detalhadas) {
        return []
      }
      if (!this.filtroTipoVerificacao) {
        return this.vendasVerificacao.vendas_detalhadas
      }
      // Filter by tipo - use the tipo field directly from the data (backend already includes it)
      const filtered = this.vendasVerificacao.vendas_detalhadas.filter(v => {
        const tipo = v.tipo || 'Calçado'  // Default to Calçado if not set
        return tipo === this.filtroTipoVerificacao
      })
      return filtered
    },
    filteredTotalVendas() {
      return this.filteredVendasDetalhadas.reduce((sum, v) => {
        return sum + Math.max(v.vlr_monthly_summary || 0, v.vlr_direct_query || 0)
      }, 0)
    },
    totalAtualVendas() {
      if (!this.metasAtual || !this.metasAtual.vendedores) return 0
      return this.metasAtual.vendedores.reduce((s, v) => s + (v.vlr_atual || 0), 0)
    },
    totalAtualPctMeta1() {
      if (!this.metasCalculadas) return 0
      const t = this.summaryTotalsExpected().total_expected_1
      if (!t) return 0
      return ((this.totalAtualVendas / t) * 100).toFixed(1)
    },
    totalAtualPctMeta2() {
      if (!this.metasCalculadas) return 0
      const t = this.summaryTotalsExpected().total_expected_2
      if (!t) return 0
      return ((this.totalAtualVendas / t) * 100).toFixed(1)
    },
    metasAtualSums() {
      if (!this.metasAtual || !this.metasAtual.vendedores) return { vendas_atuais: 0, meta_proporcional: 0, meta_final: 0 }
      const v = this.metasAtual.vendedores
      return {
        vendas_atuais: v.reduce((s, r) => s + (r.vlr_atual || 0), 0),
        meta_proporcional: v.reduce((s, r) => s + (r.meta_proporcional || 0), 0),
        meta_final: v.reduce((s, r) => s + (r.meta_final || 0), 0)
      }
    }
  },
  async mounted() {
    await this.loadVendedores()
    await this.loadSaved()
    await this.loadMetasAtual()
  },
  methods: {
    marketSharePct(groupKey) {
      const total = this.totalVendasEspMeta2
      if (!total || total <= 0) return '0%'
      const sum = this.groupSumMeta(groupKey, 'meta_2')
      const pct = (sum / total) * 100
      return (Math.round(pct * 10) / 10) + '%'
    },
    buildConfigPayloadForCalcular() {
      const tipoSeen = {}
      const vendedoresTipo = []
      const addTipo = (cod, tipo) => {
        if (cod != null && tipo && !tipoSeen[cod]) {
          tipoSeen[cod] = true
          vendedoresTipo.push({ cod_vendedor: cod, tipo, ano: this.ano })
        }
      }
      if (this.metasCalculadas) {
        ['calcado', 'roupa', 'loja'].forEach(g => {
          const det = (this.metasCalculadas[g] || {}).vendedores_detalhes || []
          det.forEach(v => addTipo(v.cod_vendedor, v.tipo))
        })
      }
      if (this.metasAtual && this.metasAtual.vendedores) {
        this.metasAtual.vendedores.forEach(v => addTipo(v.cod_vendedor, v.tipo || 'Calçado'))
      }
      this.calcadoVendedores.forEach(cod => addTipo(cod, 'Calçado'))
      this.roupaVendedores.forEach(cod => addTipo(cod, 'Roupa'))
      let ativos = this.buildVendedoresAtivosFromCalculadas()
      if ((!ativos || ativos.length === 0) && this.metasAtual && this.metasAtual.vendedores) {
        ativos = this.metasAtual.vendedores.map(v => v.cod_vendedor)
      }
      return {
        vendedores_tipo: vendedoresTipo,
        vendedores_ativos: ativos || [],
        margem_padrao: (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100,
        meta_1: 1 + (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100,
        meta_2: 1 + (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100
      }
    },
    /** Update only top-table aggregates (Vendedores, Vendas Ano Ant., Média/Vendedor). Does not set meta_1/meta_2. */
    recalcGroupAggregatesOnly() {
      if (!this.metasCalculadas) return
      for (const gk of ['calcado', 'roupa', 'loja']) {
        const g = this.metasCalculadas[gk]
        if (!g || !g.vendedores_detalhes) continue
        const det = g.vendedores_detalhes
        const totalSales = det.reduce((s, v) => s + (v.vlr_sales_anterior || 0), 0)
        const activeCount = det.filter(v => v.ativo !== false).length
        const media = activeCount > 0 ? Math.round(totalSales / activeCount * 100) / 100 : 0
        const salesRounded = Math.round(totalSales * 100) / 100
        this.$set(this.metasCalculadas, gk, { ...g, sales_anterior: salesRounded, media, count_atual: det.length })
      }
      const tc = (this.metasCalculadas.calcado && this.metasCalculadas.calcado.sales_anterior) || 0
      const tr = (this.metasCalculadas.roupa && this.metasCalculadas.roupa.sales_anterior) || 0
      const tl = (this.metasCalculadas.loja && this.metasCalculadas.loja.sales_anterior) || 0
      this.$set(this.metasCalculadas, 'total_sales_anterior', Math.round((tc + tr + tl) * 100) / 100)
    },
    recalcGroupMedias() {
      if (!this.metasCalculadas) return
      const mult1 = 1 + (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100
      const mult2 = 1 + (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100
      const roundUp1000 = x => x <= 0 ? 0 : Math.ceil(x / 1000) * 1000
      for (const gk of ['calcado', 'roupa', 'loja']) {
        const g = this.metasCalculadas[gk]
        if (!g || !g.vendedores_detalhes) continue
        const det = g.vendedores_detalhes
        const totalSales = det.reduce((s, v) => s + (v.vlr_sales_anterior || 0), 0)
        const activeCount = det.filter(v => v.ativo !== false).length
        const media = activeCount > 0 ? Math.round(totalSales / activeCount * 100) / 100 : 0
        const grpMeta1 = roundUp1000(media * mult1)
        const grpMeta2 = roundUp1000(media * mult2)
        this.$set(g, 'sales_anterior', Math.round(totalSales * 100) / 100)
        this.$set(g, 'media', media)
        this.$set(g, 'meta_1', grpMeta1)
        this.$set(g, 'meta_2', grpMeta2)
        this.$set(g, 'meta_base', grpMeta2)
        det.forEach(v => {
          this.$set(v, 'meta_1', Math.round(grpMeta1 * 100) / 100)
          this.$set(v, 'meta_2', Math.round(grpMeta2 * 100) / 100)
        })
      }
      const tc = (this.metasCalculadas.calcado && this.metasCalculadas.calcado.sales_anterior) || 0
      const tr = (this.metasCalculadas.roupa && this.metasCalculadas.roupa.sales_anterior) || 0
      const tl = (this.metasCalculadas.loja && this.metasCalculadas.loja.sales_anterior) || 0
      this.$set(this.metasCalculadas, 'total_sales_anterior', Math.round((tc + tr + tl) * 100) / 100)
    },
    async loadSaved() {
      try {
        this.loading = true
        const response = await axios.get(`/api/metas/saved/${this.ano}/${this.mes}`)
        const { config, metas_calculadas } = response.data
        if (config) {
          this.meta1 = config.meta_1 != null ? config.meta_1 : 1.05
          this.meta2 = config.meta_2 != null ? config.meta_2 : 1.10
          this.margemCrescimentoMeta1 = this.meta1 != null ? Math.round((this.meta1 - 1) * 1000) / 10 : 5
          this.margemCrescimentoMeta2 = this.meta2 != null ? Math.round((this.meta2 - 1) * 1000) / 10 : 10
          this.metasAdicionais = []
          if (config.meta_3) this.metasAdicionais.push({ value: config.meta_3 })
          if (config.meta_4) this.metasAdicionais.push({ value: config.meta_4 })
          if (config.meta_5) this.metasAdicionais.push({ value: config.meta_5 })
          this.showMetasAdicionais = this.metasAdicionais.length > 0
          this.calcadoVendedores = (config.vendedores_tipo || []).filter(vt => vt.tipo === 'Calçado').map(vt => vt.cod_vendedor)
          this.roupaVendedores = (config.vendedores_tipo || []).filter(vt => vt.tipo === 'Roupa').map(vt => vt.cod_vendedor)
          this.vendedoresAtivos = config.vendedores_ativos || []
          this.metasLiberadas = config.metas_liberadas === true
        }
        this.metasCalculadas = metas_calculadas || null
        this.applyAtivoFromConfig()
        this.metaEditBuffer = {}
        this.metasEditMode = false
        this.hasChanges = false
      } catch (error) {
        console.warn('Could not load saved metas, using defaults:', error)
        await this.loadConfig()
        this.metasCalculadas = null
      } finally {
        this.loading = false
      }
    },
    applyAtivoFromConfig() {
      if (!this.metasCalculadas) return
      const ativos = this.vendedoresAtivos || []
      const isActive = cod => ativos.length === 0 || ativos.includes(Number(cod))
      for (const g of ['calcado', 'roupa', 'loja']) {
        const det = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
        det.forEach(v => {
          if (v && v.cod_vendedor != null) this.$set(v, 'ativo', isActive(v.cod_vendedor))
        })
      }
    },
    async loadVendedores() {
      try {
        const response = await axios.get('/api/vendedor/ativos')
        this.vendedores = response.data || []
      } catch (error) {
        this.error = 'Erro ao carregar vendedores: ' + error.message
        console.error(error)
      }
    },
    async loadConfig() {
      try {
        this.loading = true
        const response = await axios.get(`/api/metas/config/${this.ano}/${this.mes}`)
        const config = response.data
        
        this.meta1 = config.meta_1 != null ? config.meta_1 : 1.05
        this.meta2 = config.meta_2 != null ? config.meta_2 : 1.10
        this.margemCrescimentoMeta1 = this.meta1 != null ? Math.round((this.meta1 - 1) * 1000) / 10 : 5
        this.margemCrescimentoMeta2 = this.meta2 != null ? Math.round((this.meta2 - 1) * 1000) / 10 : 10
        
        // Load additional metas (3, 4, 5, etc.)
        this.metasAdicionais = []
        if (config.meta_3) this.metasAdicionais.push({value: config.meta_3})
        if (config.meta_4) this.metasAdicionais.push({value: config.meta_4})
        if (config.meta_5) this.metasAdicionais.push({value: config.meta_5})
        this.showMetasAdicionais = this.metasAdicionais.length > 0
        
        this.calcadoVendedores = config.vendedores_tipo
          .filter(vt => vt.tipo === 'Calçado')
          .map(vt => vt.cod_vendedor)
        this.roupaVendedores = config.vendedores_tipo
          .filter(vt => vt.tipo === 'Roupa')
          .map(vt => vt.cod_vendedor)
        this.vendedoresAtivos = config.vendedores_ativos || []
        this.metasLiberadas = config.metas_liberadas === true
        this.hasChanges = false
      } catch (error) {
        console.warn('Config not found, using defaults:', error)
      } finally {
        this.loading = false
      }
    },
    onMetasLiberadasChange() {
      this.$nextTick(() => this.salvarConfig(true))
    },
    onConfigInput() {
      if (this.configApplyTimer) clearTimeout(this.configApplyTimer)
      this.configApplyTimer = setTimeout(() => this.applyConfigAndRecalc(), 600)
    },
    async applyConfigAndRecalc() {
      this.configApplyTimer = null
      try {
        await this.salvarConfig(true)
        if (this.metasCalculadas) await this.estimarMetas()
      } catch (e) {
        console.warn('Auto-apply config:', e)
      }
    },
    toggleEditarMetas() {
      if (!this.metasCalculadas) return
      this.metasEditMode = !this.metasEditMode
      if (!this.metasEditMode) this.metaEditBuffer = {}
      this.hasChanges = false
    },
    editarMetas() {
      if (!this.metasCalculadas) return
      this.metaEditBuffer = {}
      this.metasEditMode = true
      this.hasChanges = false
    },
    async estimarMetas() {
      try {
        this.loading = true
        this.error = null
        // Build current state from UI so backend uses it (avoids rollback when save is slow or fails)
        const body = this.buildConfigPayloadForCalcular()
        const response = await axios.post(`/api/metas/calcular/${this.ano}/${this.mes}`, body)
        this.metasCalculadas = response.data
        if (!this.metasCalculadas) return
        if (!this.metasCalculadas.loja) {
          this.metasCalculadas.loja = { count_atual: 0, sales_anterior: 0, media: 0, meta_1: null, meta_2: null, vendedores_detalhes: [] }
        }
        this.applyAtivoFromConfig()
        this.metaEditBuffer = {}
        this.hasChanges = false
        this.syncMetasAtualFromCalculadas()
        this.$nextTick(() => this.salvarConfig(true))
      } catch (error) {
        this.error = 'Erro ao estimar metas: ' + (error.response?.data?.detail || error.message)
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    async calcularMetas() {
      await this.estimarMetas()
    },
    async limparMetas() {
      if (!confirm(`Limpar todas as metas (valores) de ${this.mes}/${this.ano}? Configuração (grupos, ativos) será mantida.`)) return
      try {
        this.loading = true
        this.error = null
        await axios.post(`/api/metas/clear/${this.ano}/${this.mes}`)
        if (this.metasCalculadas) {
          for (const gk of ['calcado', 'roupa', 'loja']) {
            const g = this.metasCalculadas[gk]
            if (!g) continue
            this.$set(g, 'meta_1', null)
            this.$set(g, 'meta_2', null)
            if (g.vendedores_detalhes) {
              g.vendedores_detalhes.forEach(v => {
                this.$set(v, 'meta_1', null)
                this.$set(v, 'meta_2', null)
              })
            }
          }
          this.metaEditBuffer = {}
        }
        alert('Metas limpas. Os valores foram removidos; configuração (grupos, ativos) mantida.')
      } catch (error) {
        this.error = 'Erro ao limpar metas: ' + (error.response?.data?.detail || error.message)
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    async recalcularMetasComLoja() {
      // Recalculate metas when Loja toggle changes
      if (this.metasCalculadas) {
        await this.calcularMetas()
      }
    },
    // Resolve effective meta value: use edit buffer if active, else item (so in-progress edits are saved)
    getEffectiveMeta(v, field) {
      const key = this.metaEditKey(v && v.cod_vendedor, field)
      if (this.metaEditBuffer[key] !== undefined && this.metaEditBuffer[key] !== '') {
        const n = this.parseNumber(this.metaEditBuffer[key])
        if (n !== null) return n
      }
      const val = v && v[field]
      return (val !== null && val !== undefined && val !== '') ? Number(val) : null
    },
    async salvarMetas(silent = false) {
      try {
        this.loading = true
        this.error = null

        const bufferSnapshot = {}
        const metas_por_vendedor = {}
        if (this.metasCalculadas) {
          Object.keys(this.metaEditBuffer || {}).forEach(key => {
            const match = /^meta_(\d+)_(meta_\d+)$/.exec(key)
            if (!match) return
            const cod = parseInt(match[1], 10)
            const field = match[2]
            const raw = this.metaEditBuffer[key]
            if (raw === undefined || raw === '') return
            const num = this.parseNumber(raw)
            if (num === null) return
            if (!bufferSnapshot[cod]) bufferSnapshot[cod] = {}
            bufferSnapshot[cod][field] = num
          })

          const addFromGroup = (groupKey) => {
            const g = this.metasCalculadas[groupKey]
            if (!g || !g.vendedores_detalhes) return
            g.vendedores_detalhes.forEach(v => {
              if (v.cod_vendedor == null) return
              const cod = Number(v.cod_vendedor)
              const meta_1 = (bufferSnapshot[cod] && bufferSnapshot[cod].meta_1 !== undefined)
                ? bufferSnapshot[cod].meta_1
                : this.getEffectiveMeta(v, 'meta_1')
              const meta_2 = (bufferSnapshot[cod] && bufferSnapshot[cod].meta_2 !== undefined)
                ? bufferSnapshot[cod].meta_2
                : this.getEffectiveMeta(v, 'meta_2')
              metas_por_vendedor[cod] = { meta_1, meta_2 }
            })
          }
          addFromGroup('calcado')
          addFromGroup('roupa')
          addFromGroup('loja')
        }

        const tipoSeen = {}
        const vendedoresTipo = []
        const addTipo = (cod, tipo) => {
          if (cod != null && tipo && !tipoSeen[cod]) {
            tipoSeen[cod] = true
            vendedoresTipo.push({ cod_vendedor: cod, tipo, ano: this.ano })
          }
        }
        if (this.metasAtual && this.metasAtual.vendedores) {
          this.metasAtual.vendedores.forEach(v => addTipo(v.cod_vendedor, v.tipo || 'Calçado'))
        }
        if (this.metasCalculadas) {
          ['calcado', 'roupa', 'loja'].forEach(g => {
            const det = (this.metasCalculadas[g] || {}).vendedores_detalhes || []
            det.forEach(v => addTipo(v.cod_vendedor, v.tipo))
          })
        }
        this.calcadoVendedores.forEach(cod => addTipo(cod, 'Calçado'))
        this.roupaVendedores.forEach(cod => addTipo(cod, 'Roupa'))

        let ativos = this.buildVendedoresAtivosFromCalculadas()
        if ((!ativos || ativos.length === 0) && this.metasAtual && this.metasAtual.vendedores) {
          ativos = this.metasAtual.vendedores.map(v => v.cod_vendedor)
        }

        const config = {
          vendedores_tipo: vendedoresTipo,
          vendedores_ativos: ativos,
          margem_padrao: (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100,
          meta_1: 1 + (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100,
          meta_2: 1 + (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100,
          meta_3: this.metasAdicionais.length > 0 ? this.metasAdicionais[0].value : null,
          meta_4: this.metasAdicionais.length > 1 ? this.metasAdicionais[1].value : null,
          meta_5: this.metasAdicionais.length > 2 ? this.metasAdicionais[2].value : null,
          metas_por_vendedor
        }

        const res = await axios.post(`/api/metas/config/${this.ano}/${this.mes}`, config)
        this.hasChanges = false
        this.metasEditMode = false
        if (this.metasCalculadas) {
          this.applyMetasPorVendedorToCalculadas(metas_por_vendedor)
          this.metaEditBuffer = {}
        }
        if (!silent) {
          const n = res.data && res.data.metas_synced
          const msg = n !== undefined ? `Metas salvas: ${n} vendedor(es) atualizado(s).` : 'Metas salvas com sucesso!'
          alert(msg)
        }
      } catch (error) {
        this.error = 'Erro ao salvar metas: ' + (error.response?.data?.detail || error.message)
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    async verificarVendas() {
      try {
        this.loading = true
        this.error = null
        
        const response = await axios.get(`/api/metas/verificar-vendas/${this.ano}/${this.mes}`)
        this.vendasVerificacao = response.data
      } catch (error) {
        this.error = 'Erro ao verificar vendas: ' + (error.response?.data?.detail || error.message)
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    async loadSalesAnoAnterior() {
      // Auto-load sales from previous year when year/month changes
      // This is handled automatically by calcularMetas, so no action needed here
      if (this.ano > 2019) {
        const anoAnterior = this.ano - 1
        console.log(`Will analyze sales from ${anoAnterior}/${this.mes} for ${this.ano}/${this.mes} targets`)
      }
    },
    async salvarConfig(silent) {
      try {
        this.loading = true
        this.error = null
        
        // Build vendedores_tipo: prefer metas calculadas tables (source of group edits), then fallbacks
        const tipoSeen = {}
        const vendedoresTipo = []
        const addTipo = (cod, tipo) => {
          if (cod != null && tipo && !tipoSeen[cod]) {
            tipoSeen[cod] = true
            vendedoresTipo.push({ cod_vendedor: cod, tipo, ano: this.ano })
          }
        }
        // 1) Metas calculadas tables first (user edits groups here)
        if (this.metasCalculadas) {
          const groups = ['calcado', 'roupa', 'loja']
          groups.forEach(g => {
            const det = (this.metasCalculadas[g] || {}).vendedores_detalhes || []
            det.forEach(v => addTipo(v.cod_vendedor, v.tipo))
          })
        }
        // 2) Metas atual (current month)
        if (this.metasAtual && this.metasAtual.vendedores) {
          this.metasAtual.vendedores.forEach(v => addTipo(v.cod_vendedor, v.tipo || 'Calçado'))
        }
        // 3) Verificação de vendas
        if (this.vendasVerificacao && this.vendasVerificacao.vendas_detalhadas) {
          this.vendasVerificacao.vendas_detalhadas.forEach(v => addTipo(v.cod_vendedor, v.tipo))
        }
        // 4) Legacy arrays as fallback
        this.calcadoVendedores.forEach(cod => addTipo(cod, 'Calçado'))
        this.roupaVendedores.forEach(cod => addTipo(cod, 'Roupa'))
        
        // Build vendedores_ativos from active toggles in Metas Calculadas
        let ativos = this.buildVendedoresAtivosFromCalculadas()
        if ((!ativos || ativos.length === 0) && this.metasAtual && this.metasAtual.vendedores) {
          ativos = this.metasAtual.vendedores.map(v => v.cod_vendedor)
        }

        const config = {
          vendedores_tipo: vendedoresTipo,
          vendedores_ativos: ativos,
          margem_padrao: (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100,
          meta_1: 1 + (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100,
          meta_2: 1 + (this.margemCrescimentoMeta2 != null ? this.margemCrescimentoMeta2 : 10) / 100,
          meta_3: this.metasAdicionais.length > 0 ? this.metasAdicionais[0].value : null,
          meta_4: this.metasAdicionais.length > 1 ? this.metasAdicionais[1].value : null,
          meta_5: this.metasAdicionais.length > 2 ? this.metasAdicionais[2].value : null,
          metas_liberadas: this.metasLiberadas
        }

        // Always include per-seller metas when we have calculated metas (same as Salvar Metas Editadas).
        // Use getEffectiveMeta so inline edits in the table are saved and we don't overwrite with formula values.
        if (this.metasCalculadas) {
          const metas_por_vendedor = {}
          const groups = ['calcado', 'roupa', 'loja']
          groups.forEach(g => {
            const det = (this.metasCalculadas[g] || {}).vendedores_detalhes || []
            det.forEach(v => {
              if (v.cod_vendedor != null) {
                metas_por_vendedor[v.cod_vendedor] = {
                  meta_1: this.getEffectiveMeta(v, 'meta_1'),
                  meta_2: this.getEffectiveMeta(v, 'meta_2')
                }
              }
            })
          })
          config.metas_por_vendedor = metas_por_vendedor
        }

        await axios.post(`/api/metas/config/${this.ano}/${this.mes}`, config)
        this.hasChanges = false
        if (!silent) alert('Configuração salva com sucesso!')
      } catch (error) {
        this.error = 'Erro ao salvar configuração: ' + (error.response?.data?.detail || error.message)
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    /** Sync Mês Atual table/chart to use meta values from the above tables (metasCalculadas). */
    syncMetasAtualFromCalculadas() {
      if (!this.metasAtual || !this.metasAtual.vendedores || !this.metasCalculadas) return
      const map = {}
      for (const gk of ['calcado', 'roupa', 'loja']) {
        const g = this.metasCalculadas[gk]
        if (!g || !g.vendedores_detalhes) continue
        for (const d of g.vendedores_detalhes) {
          const cod = d.cod_vendedor
          if (cod != null) map[cod] = { meta_1: d.meta_1, meta_2: d.meta_2 }
        }
      }
      const proporcao = this.metasAtual.proporcao != null ? this.metasAtual.proporcao : 1
      this.metasAtual.vendedores.forEach(v => {
        const cod = v.cod_vendedor
        const m = map[cod] || map[String(cod)]
        const meta2 = m && (m.meta_2 != null && m.meta_2 !== '') ? Number(m.meta_2) : (v.meta_final != null ? Number(v.meta_final) : 0)
        const metaFinal = Math.round(meta2 * 100) / 100
        const metaProporcional = Math.round(metaFinal * proporcao * 100) / 100
        const vlr = v.vlr_atual != null ? Number(v.vlr_atual) : 0
        const pct = metaFinal > 0 ? Math.round((vlr / metaFinal) * 1000) / 10 : 0
        this.$set(v, 'meta_final', metaFinal)
        this.$set(v, 'meta_proporcional', metaProporcional)
        this.$set(v, 'percentual', pct)
      })
      this.updateChart()
    },
    async loadMetasAtual() {
      try {
        const response = await axios.get(`/api/metas/atual/${this.ano}/${this.mes}`)
        this.metasAtual = response.data
        
        // Ensure all vendedores have a tipo, defaulting to "Calçado" if missing
        if (this.metasAtual && this.metasAtual.vendedores) {
          this.metasAtual.vendedores.forEach(v => {
            if (!v.tipo || !["Calçado", "Roupa", "Loja"].includes(v.tipo)) {
              v.tipo = "Calçado"
            }
          })
          if (this.metasCalculadas) this.syncMetasAtualFromCalculadas()
          else this.updateChart()
        }
      } catch (error) {
        console.warn('Could not load current metas:', error)
      }
    },
    updateChart() {
      if (!this.metasAtual || !this.metasAtual.vendedores) return
      
      const ctx = this.$refs.chartCanvas
      if (!ctx) return
      
      if (this.chart) {
        this.chart.destroy()
      }
      
      const labels = this.metasAtual.vendedores.map(v => 
        `${v.cod_vendedor} - ${this.getVendedorName(v.cod_vendedor)}`
      )
      const atual = this.metasAtual.vendedores.map(v => v.vlr_atual)
      const proporcional = this.metasAtual.vendedores.map(v => v.meta_proporcional)
      const final = this.metasAtual.vendedores.map(v => v.meta_final)
      
      this.chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Vendas Atuais',
              data: atual,
              backgroundColor: 'rgba(54, 162, 235, 0.5)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1
            },
            {
              label: 'Meta Proporcional',
              data: proporcional,
              backgroundColor: 'rgba(255, 206, 86, 0.5)',
              borderColor: 'rgba(255, 206, 86, 1)',
              borderWidth: 1
            },
            {
              label: 'Meta Final',
              data: final,
              backgroundColor: 'rgba(75, 192, 192, 0.5)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      })
    },
    getVendedorName(cod_vendedor) {
      const vendedor = this.vendedores.find(v => v.cod_vendedor === cod_vendedor)
      return vendedor ? vendedor.nom_vendedor : 'Desconhecido'
    },
    async showSellerChart(cod_vendedor, nom_vendedor) {
      // Check if chart already exists
      if (this.sellerCharts[cod_vendedor]) {
        // Chart already exists, scroll to it
        this.$nextTick(() => {
          const element = document.querySelector(`[data-seller-chart="${cod_vendedor}"]`)
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        })
        return
      }
      
      // Load daily progress data for this seller in the selected month
      try {
        this.loading = true
        const response = await axios.get(`/api/metas/vendedor/${cod_vendedor}/progresso/${this.ano}/${this.mes}`)
        const progressData = response.data
        
        // Store chart data
        this.$set(this.sellerCharts, cod_vendedor, {
          nom_vendedor: progressData.nom_vendedor || nom_vendedor,
          tipo: progressData.tipo,
          ano: progressData.ano,
          mes: progressData.mes,
          dias: progressData.dias,
          vendas_cumulativas: progressData.vendas_cumulativas,
          meta_proporcional_diaria: progressData.meta_proporcional_diaria,
          meta_1_diaria: progressData.meta_1_diaria || [],
          meta_2_diaria: progressData.meta_2_diaria || [],
          meta_final: progressData.meta_final,
          meta_1: progressData.meta_1 || 0,
          meta_2: progressData.meta_2 || 0,
          vendas_atual: progressData.vendas_atual,
          meta_proporcional_atual: progressData.meta_proporcional_atual,
          dia_atual: progressData.dia_atual,
          dias_no_mes: progressData.dias_no_mes,
          visible: true,
          chart: null
        })
        
        // Create chart after Vue updates DOM
        this.$nextTick(() => {
          this.createSellerChart(cod_vendedor)
        })
      } catch (error) {
        console.error('Error loading seller chart data:', error)
        this.error = 'Erro ao carregar dados do gráfico: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.loading = false
      }
    },
    createSellerChart(cod_vendedor) {
      const chartData = this.sellerCharts[cod_vendedor]
      if (!chartData || !chartData.dias) return
      
      // Wait for DOM to be ready
      setTimeout(() => {
        const canvasId = `seller-chart-${cod_vendedor}`
        const canvas = document.getElementById(canvasId)
        
        if (!canvas) {
          console.warn(`Canvas not found for seller ${cod_vendedor}, retrying...`)
          // Retry after a short delay
          setTimeout(() => this.createSellerChart(cod_vendedor), 100)
          return
        }
        
        // Destroy existing chart if it exists
        if (chartData.chart) {
          chartData.chart.destroy()
        }
        
        // Prepare labels (day numbers)
        const labels = chartData.dias.map(dia => `Dia ${dia}`)
        
        // Create target lines (constant values for all days)
        const meta_final_line = new Array(chartData.dias.length).fill(chartData.meta_final)
        const meta_1_line = new Array(chartData.dias.length).fill(chartData.meta_1)
        const meta_2_line = new Array(chartData.dias.length).fill(chartData.meta_2)
        
        // Create new chart
        chartData.chart = new Chart(canvas, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Vendas Acumuladas',
                data: chartData.vendas_cumulativas,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.1,
                fill: false,
                borderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
              },
              {
                label: 'Meta Proporcional',
                data: chartData.meta_proporcional_diaria,
                borderColor: 'rgba(255, 206, 86, 1)',
                backgroundColor: 'rgba(255, 206, 86, 0.1)',
                tension: 0.1,
                fill: false,
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 3,
                pointHoverRadius: 5
              },
              {
                label: 'Meta 1',
                data: chartData.meta_1_diaria && chartData.meta_1_diaria.length > 0 ? chartData.meta_1_diaria : meta_1_line,
                borderColor: 'rgba(153, 102, 255, 1)',
                backgroundColor: 'rgba(153, 102, 255, 0.1)',
                tension: 0.1,
                fill: false,
                borderWidth: 2,
                borderDash: [8, 4],
                pointRadius: 2,
                pointHoverRadius: 4
              },
              {
                label: 'Meta 2',
                data: chartData.meta_2_diaria && chartData.meta_2_diaria.length > 0 ? chartData.meta_2_diaria : meta_2_line,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.1,
                fill: false,
                borderWidth: 2,
                borderDash: [8, 4],
                pointRadius: 2,
                pointHoverRadius: 4
              },
              {
                label: 'Meta Final',
                data: meta_final_line,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0,
                fill: false,
                borderWidth: 2,
                borderDash: [10, 5],
                pointRadius: 0
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index',
              intersect: false
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function(value) {
                    return 'R$ ' + value.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})
                  }
                },
                title: {
                  display: true,
                  text: 'Valor (R$)'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Dia do Mês'
                }
              }
            },
            plugins: {
              legend: {
                display: true,
                position: 'top'
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.dataset.label || ''
                    const value = context.parsed.y
                    return `${label}: R$ ${value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`
                  }
                }
              },
              title: {
                display: true,
                text: `${chartData.nom_vendedor} - Progresso ${chartData.mes.toString().padStart(2, '0')}/${chartData.ano}`,
                font: {
                  size: 16
                }
              }
            }
          }
        })
      }, 100)
    },
    toggleMetasAdicionais() {
      this.showMetasAdicionais = !this.showMetasAdicionais
      if (this.showMetasAdicionais && this.metasAdicionais.length === 0) {
        // Initialize with empty metas if showing for first time
        this.metasAdicionais = [{value: null}, {value: null}, {value: null}]
      }
      this.hasChanges = true
    },
    formatMoney(value) {
      if (!value && value !== 0) return 'R$ 0,00'
      const num = typeof value === 'string' ? parseFloat(value) : value
      // Use pt-BR locale which uses comma as decimal separator
      return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num)
    },
    getMonthYearLabel(ano, mes) {
      const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
      const monthName = monthNames[mes - 1] || `Mês ${mes}`
      const yearShort = ano.toString().slice(-2)
      return `${monthName}-${yearShort}`
    },
    formatNumber(value) {
      // Format number with comma as decimal separator (for input fields)
      if (value === null || value === undefined) return ''
      const num = typeof value === 'string' ? parseFloat(value.replace(',', '.')) : value
      if (isNaN(num)) return ''
      return num.toFixed(2).replace('.', ',')
    },
    // Display value for meta inputs: empty when null/undefined/0 so field stays blank when cleared
    formatNumberDisplay(value) {
      if (value === null || value === undefined || value === '') return ''
      const num = typeof value === 'string' ? parseFloat(value.replace(',', '.')) : value
      if (isNaN(num) || num === 0) return ''
      return this.formatNumber(num)
    },
    parseNumber(value) {
      // Parse number with comma as decimal separator (for input fields)
      if (!value) return null
      const str = typeof value === 'string' ? value.replace(',', '.') : String(value)
      const num = parseFloat(str)
      return isNaN(num) ? null : num
    },
    // b-form-input emits the value on @input, not the native event; native input gives event.target.value
    inputVal(ev) {
      return (ev && ev.target != null) ? ev.target.value : ev
    },
    metaEditKey(cod, field) {
      // Normalize so 1, "1", 1.0 all yield the same key (buffer lookup when building save payload).
      const c = cod != null && cod !== '' ? Number(cod) : ''
      return `meta_${c}_${field}`
    },
    groupMetaEditKey(groupKey, field) {
      return `group_${groupKey}_${field}`
    },
    summaryGroupMeta(group, field) {
      if (!group || !this.metasCalculadas) return group ? group[field] : null
      const groupKey = ['calcado', 'roupa', 'loja'].find(k => this.metasCalculadas[k] === group)
      if (!groupKey) return group[field] != null ? Number(group[field]) : null
      const key = this.groupMetaEditKey(groupKey, field)
      if (this.metaEditBuffer[key] !== undefined && this.metaEditBuffer[key] !== '') {
        const n = this.parseNumber(this.metaEditBuffer[key])
        if (n !== null) return n
      }
      const val = group[field]
      return (val !== null && val !== undefined && val !== '') ? Number(val) : null
    },
    setVendedorAtivo(item, value) {
      if (item && item.cod_vendedor != null) {
        this.$set(item, 'ativo', !!value)
        this.hasChanges = true
        this.$nextTick(() => this.salvarConfig(true))
      }
    },
    buildVendedoresAtivosFromCalculadas() {
      if (!this.metasCalculadas) return this.vendedoresAtivos || []
      const ativos = []
      for (const g of ['calcado', 'roupa', 'loja']) {
        const det = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
        det.forEach(v => {
          if (v && v.cod_vendedor != null && v.ativo !== false) ativos.push(Number(v.cod_vendedor))
        })
      }
      return ativos
    },
    activeCount(groupKey) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g || !g.vendedores_detalhes) return 0
      return g.vendedores_detalhes.filter(v => v.ativo !== false).length
    },
    groupSumMeta(groupKey, field) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g || !g.vendedores_detalhes) return 0
      let sum = 0
      g.vendedores_detalhes.forEach(v => {
        if (v.ativo === false) return
        const val = this.getEffectiveMeta(v, field)
        if (val !== null && val !== undefined) sum += Number(val)
      })
      return Math.round(sum * 100) / 100
    },
    getVendedorTipoInMetas(cod) {
      if (cod == null || !this.metasCalculadas) return null
      const c = Number(cod)
      for (const g of ['calcado', 'roupa', 'loja']) {
        const det = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
        const v = det.find(d => d && Number(d.cod_vendedor) === c)
        if (v && v.tipo) return v.tipo
      }
      return null
    },
    rowClassByTipo(item) {
      if (!item || !item.tipo) return 'metas-row-calcado'
      if (item.tipo === 'Roupa') return 'metas-row-roupa'
      if (item.tipo === 'Loja') return 'metas-row-loja'
      return 'metas-row-calcado'
    },
    onVendedorIncluirSelected(cod) {
      const tipo = this.getVendedorTipoInMetas(cod)
      this.novoVendedorGrupo = tipo || 'Calçado'
    },
    addVendedorToGroup() {
      if (!this.novoVendedorCod || !this.novoVendedorGrupo || !this.metasCalculadas) return
      const cod = Number(this.novoVendedorCod)
      const tipo = this.novoVendedorGrupo
      const vendedor = this.vendedores.find(v => Number(v.cod_vendedor) === cod)
      const nom = (vendedor && vendedor.nom_vendedor) || `Vendedor ${cod}`
      const targetKey = tipo === 'Roupa' ? 'roupa' : (tipo === 'Loja' ? 'loja' : 'calcado')

      let existingItem = null
      let sourceKey = null
      for (const g of ['calcado', 'roupa', 'loja']) {
        const det = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
        const idx = det.findIndex(d => d && Number(d.cod_vendedor) === cod)
        if (idx >= 0) {
          existingItem = det[idx]
          sourceKey = g
          break
        }
      }

      if (sourceKey !== null && existingItem) {
        if (sourceKey === targetKey) {
          this.novoVendedorCod = null
          return
        }
        const det = this.metasCalculadas[sourceKey].vendedores_detalhes
        det.splice(det.findIndex(d => Number(d.cod_vendedor) === cod), 1)
        this.metasCalculadas[sourceKey].count_atual = det.length
        existingItem.tipo = tipo
        if (!this.metasCalculadas[targetKey]) {
          this.$set(this.metasCalculadas, targetKey, { count_atual: 0, sales_anterior: 0, media: 0, meta_1: null, meta_2: null, vendedores_detalhes: [] })
        }
        this.metasCalculadas[targetKey].vendedores_detalhes = this.metasCalculadas[targetKey].vendedores_detalhes || []
        this.metasCalculadas[targetKey].vendedores_detalhes.push(existingItem)
        this.metasCalculadas[targetKey].count_atual = this.metasCalculadas[targetKey].vendedores_detalhes.length
      } else {
        if (!this.metasCalculadas[targetKey]) {
          this.$set(this.metasCalculadas, targetKey, { count_atual: 0, sales_anterior: 0, media: 0, meta_1: null, meta_2: null, vendedores_detalhes: [] })
        }
        const mesAno = this.metasCalculadas.ano_anterior && this.metasCalculadas.mes ? `${this.metasCalculadas.ano_anterior}-${String(this.metasCalculadas.mes).padStart(2, '0')}` : ''
        const item = { cod_vendedor: cod, nom_vendedor: nom, tipo, ativo: true, vlr_sales_anterior: 0, meta_1: null, meta_2: null, mes_ano: mesAno }
        this.metasCalculadas[targetKey].vendedores_detalhes = this.metasCalculadas[targetKey].vendedores_detalhes || []
        this.metasCalculadas[targetKey].vendedores_detalhes.push(item)
        this.metasCalculadas[targetKey].count_atual = this.metasCalculadas[targetKey].vendedores_detalhes.length
      }

      if (tipo === 'Calçado') {
        if (!this.calcadoVendedores.includes(cod)) this.calcadoVendedores.push(cod)
        this.roupaVendedores = this.roupaVendedores.filter(v => v !== cod)
      } else if (tipo === 'Roupa') {
        if (!this.roupaVendedores.includes(cod)) this.roupaVendedores.push(cod)
        this.calcadoVendedores = this.calcadoVendedores.filter(v => v !== cod)
      } else {
        this.calcadoVendedores = this.calcadoVendedores.filter(v => v !== cod)
        this.roupaVendedores = this.roupaVendedores.filter(v => v !== cod)
      }
      this.novoVendedorCod = null
      this.hasChanges = true
      this.recalcGroupAggregatesOnly()
      this.$nextTick(() => this.salvarConfig(true))
    },
    aplicarGroupMeta(groupKey, field) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g || !g.vendedores_detalhes) return
      const val = this.summaryGroupMeta(g, field)
      if (val === null || val === undefined) return
      g.vendedores_detalhes.forEach(v => {
        this.$set(v, field, val)
        const key = this.metaEditKey(v.cod_vendedor, field)
        this.$set(this.metaEditBuffer, key, this.formatNumber(val))
      })
      this.hasChanges = true
    },
    getGroupMetaInputValue(groupKey, field) {
      const key = this.groupMetaEditKey(groupKey, field)
      if (this.metaEditBuffer[key] !== undefined) return this.metaEditBuffer[key]
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      const val = g && (g[field] !== null && g[field] !== undefined && g[field] !== '') ? Number(g[field]) : null
      return val != null ? String(val) : ''
    },
    onGroupMetaFocus(groupKey, field) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      const val = g && (g[field] !== null && g[field] !== undefined && g[field] !== '') ? Number(g[field]) : null
      const cur = val != null ? String(val) : ''
      this.$set(this.metaEditBuffer, this.groupMetaEditKey(groupKey, field), cur)
    },
    onGroupMetaInputOnlyBuffer(groupKey, field, ev) {
      const raw = this.inputVal(ev)
      const key = this.groupMetaEditKey(groupKey, field)
      this.$set(this.metaEditBuffer, key, raw)
      const num = this.parseNumber(raw)
      if (num === null || isNaN(num)) return
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g) return
      const isAuto = this.metaAutoByGroup[groupKey] === true
      const pct1Below = (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100
      let meta1, meta2
      if (isAuto) {
        if (field === 'meta_2') {
          meta2 = Math.round(num * 100) / 100
          meta1 = Math.round(num * (1 - pct1Below) * 100) / 100
        } else {
          meta1 = Math.round(num * 100) / 100
          meta2 = (1 - pct1Below) <= 0 ? meta1 : Math.round(meta1 / (1 - pct1Below) * 100) / 100
        }
        this.$set(this.metaEditBuffer, this.groupMetaEditKey(groupKey, 'meta_1'), String(meta1))
        this.$set(this.metaEditBuffer, this.groupMetaEditKey(groupKey, 'meta_2'), String(meta2))
      }
      this.hasChanges = true
    },
    aplicarGroupMetas(groupKey) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g || !g.vendedores_detalhes) return
      const key1 = this.groupMetaEditKey(groupKey, 'meta_1')
      const key2 = this.groupMetaEditKey(groupKey, 'meta_2')
      const raw1 = this.metaEditBuffer[key1]
      const raw2 = this.metaEditBuffer[key2]
      const num1 = raw1 !== undefined && raw1 !== '' ? this.parseNumber(raw1) : null
      const num2 = raw2 !== undefined && raw2 !== '' ? this.parseNumber(raw2) : null
      if (num1 === null && num2 === null) return
      const isAuto = this.metaAutoByGroup[groupKey] === true
      const pct1Below = (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100
      let meta1, meta2
      if (isAuto) {
        if (num2 !== null && !isNaN(num2)) {
          meta2 = Math.round(num2 * 100) / 100
          meta1 = Math.round(meta2 * (1 - pct1Below) * 100) / 100
        } else if (num1 !== null && !isNaN(num1)) {
          meta1 = Math.round(num1 * 100) / 100
          meta2 = (1 - pct1Below) <= 0 ? meta1 : Math.round(meta1 / (1 - pct1Below) * 100) / 100
        } else return
      } else {
        meta1 = num1 !== null && !isNaN(num1) ? Math.round(num1 * 100) / 100 : (this.summaryGroupMeta(g, 'meta_1') != null ? Number(this.summaryGroupMeta(g, 'meta_1')) : null)
        meta2 = num2 !== null && !isNaN(num2) ? Math.round(num2 * 100) / 100 : (this.summaryGroupMeta(g, 'meta_2') != null ? Number(this.summaryGroupMeta(g, 'meta_2')) : null)
        if (meta1 == null && meta2 == null) return
        if (meta1 == null) meta1 = meta2 != null ? Math.round(meta2 * (1 - pct1Below) * 100) / 100 : null
        if (meta2 == null) meta2 = meta1 != null ? Math.round(meta1 / (1 - pct1Below) * 100) / 100 : null
      }
      this.applyGroupMetasToRows(groupKey, meta1, meta2)
      this.$set(this.metaEditBuffer, key1, meta1 != null ? String(meta1) : '')
      this.$set(this.metaEditBuffer, key2, meta2 != null ? String(meta2) : '')
      this.hasChanges = true
      this.syncMetasAtualFromCalculadas()
    },
    applyGroupMetasToRows(groupKey, meta1, meta2) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g || !g.vendedores_detalhes) return
      const m1 = meta1 != null ? Math.round(Number(meta1) * 100) / 100 : null
      const m2 = meta2 != null ? Math.round(Number(meta2) * 100) / 100 : null
      if (m1 != null) this.$set(g, 'meta_1', m1)
      if (m2 != null) this.$set(g, 'meta_2', m2)
      g.vendedores_detalhes.forEach(v => {
        if (m1 != null) this.$set(v, 'meta_1', m1)
        if (m2 != null) this.$set(v, 'meta_2', m2)
        if (m1 != null) this.$set(this.metaEditBuffer, this.metaEditKey(v.cod_vendedor, 'meta_1'), this.formatNumber(m1))
        if (m2 != null) this.$set(this.metaEditBuffer, this.metaEditKey(v.cod_vendedor, 'meta_2'), this.formatNumber(m2))
      })
      if (m1 != null) this.$set(this.metaEditBuffer, this.groupMetaEditKey(groupKey, 'meta_1'), String(m1))
      if (m2 != null) this.$set(this.metaEditBuffer, this.groupMetaEditKey(groupKey, 'meta_2'), String(m2))
    },
    aplicarMetaBase(groupKey) {
      const g = this.metasCalculadas && this.metasCalculadas[groupKey]
      if (!g || !g.vendedores_detalhes) return
      const keyBase = this.groupMetaEditKey(groupKey, 'meta_base')
      const raw = this.metaEditBuffer[keyBase]
      const baseVal = raw !== undefined ? this.parseNumber(raw) : (g.meta_base != null ? Number(g.meta_base) : this.summaryGroupMeta(g, 'meta_base'))
      if (baseVal === null || baseVal === undefined || isNaN(baseVal)) return
      const meta2 = Math.round(baseVal * 100) / 100
      const pct1Below = (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100
      const meta1 = Math.round(baseVal * (1 - pct1Below) * 100) / 100
      this.$set(g, 'meta_base', baseVal)
      this.$set(g, 'meta_2', meta2)
      this.$set(g, 'meta_1', meta1)
      this.applyGroupMetasToRows(groupKey, meta1, meta2)
      this.$set(this.metaEditBuffer, this.groupMetaEditKey(groupKey, 'meta_base'), this.formatNumber(baseVal))
      this.hasChanges = true
    },
    summaryTotalsExpected() {
      let t1 = 0, t2 = 0
      if (!this.metasCalculadas) return { total_expected_1: 0, total_expected_2: 0 }
      for (const k of ['calcado', 'roupa', 'loja']) {
        t1 += this.groupSumMeta(k, 'meta_1')
        t2 += this.groupSumMeta(k, 'meta_2')
      }
      return { total_expected_1: Math.round(t1 * 100) / 100, total_expected_2: Math.round(t2 * 100) / 100 }
    },
    displayMetaValue(item, field) {
      const val = item ? this.getEffectiveMeta(item, field) : null
      return (val !== null && val !== undefined) ? this.formatMoney(val) : ''
    },
    getMetaInputValue(item, field, groupKey) {
      const key = groupKey ? this.groupMetaEditKey(groupKey, field) : this.metaEditKey(item && item.cod_vendedor, field)
      if (this.metaEditBuffer[key] !== undefined) return this.metaEditBuffer[key]
      const obj = groupKey && this.metasCalculadas && this.metasCalculadas[groupKey] ? this.metasCalculadas[groupKey] : item
      return this.formatNumberDisplay(obj && obj[field])
    },
    onMetaFocus(item, field, groupKey) {
      const key = groupKey ? this.groupMetaEditKey(groupKey, field) : this.metaEditKey(item && item.cod_vendedor, field)
      const obj = groupKey && this.metasCalculadas && this.metasCalculadas[groupKey] ? this.metasCalculadas[groupKey] : item
      const cur = (obj && (obj[field] !== null && obj[field] !== undefined && obj[field] !== '')) ? this.formatNumber(obj[field]) : ''
      this.$set(this.metaEditBuffer, key, cur)
    },
    onMetaInput(item, field, ev, groupKey) {
      const key = groupKey ? this.groupMetaEditKey(groupKey, field) : this.metaEditKey(item && item.cod_vendedor, field)
      const raw = this.inputVal(ev)
      this.$set(this.metaEditBuffer, key, raw)
      const num = this.parseNumber(raw)
      if (groupKey && this.metasCalculadas && this.metasCalculadas[groupKey]) {
        const g = this.metasCalculadas[groupKey]
        this.$set(g, field, num)
        // Live preview: Meta Base = Meta 2; Meta 1 = Meta Base × (1 - margem %)
        if (field === 'meta_base') {
          if (num !== null && !isNaN(num)) {
            const meta2 = Math.round(num * 100) / 100
            const pct1Below = (this.margemCrescimentoMeta1 != null ? this.margemCrescimentoMeta1 : 5) / 100
            const meta1 = Math.round(num * (1 - pct1Below) * 100) / 100
            this.$set(g, 'meta_2', meta2)
            this.$set(g, 'meta_1', meta1)
          } else {
            this.$set(g, 'meta_1', null)
            this.$set(g, 'meta_2', null)
          }
        }
      } else if (item) {
        this.$set(item, field, num)
        // Ensure source array in metasCalculadas is updated (b-table row may be a copy)
        this.syncMetaEditToSource(item.cod_vendedor, field, num)
      }
      this.hasChanges = true
    },
    syncMetaEditToSource(cod_vendedor, field, num) {
      if (!this.metasCalculadas || cod_vendedor == null) return
      for (const g of ['calcado', 'roupa', 'loja']) {
        const detalhes = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
        const v = detalhes.find(d => d && Number(d.cod_vendedor) === Number(cod_vendedor))
        if (v) {
          this.$set(v, field, num)
          return
        }
      }
    },
    applyMetasPorVendedorToCalculadas(metas_por_vendedor) {
      if (!this.metasCalculadas || !metas_por_vendedor || typeof metas_por_vendedor !== 'object') return
      for (const g of ['calcado', 'roupa', 'loja']) {
        const detalhes = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
        detalhes.forEach(v => {
          if (!v || v.cod_vendedor == null) return
          const cod = Number(v.cod_vendedor)
          const entry = metas_por_vendedor[cod] || metas_por_vendedor[String(cod)]
          if (!entry) return
          if (entry.meta_1 !== undefined && entry.meta_1 !== null) this.$set(v, 'meta_1', entry.meta_1)
          if (entry.meta_2 !== undefined && entry.meta_2 !== null) this.$set(v, 'meta_2', entry.meta_2)
        })
      }
    },
    onMetaBlur(item, field, groupKey) {
      // Do NOT delete from buffer on blur: we need the value when building the save payload.
      // Buffer is cleared only after successful save. Commit display value to source on blur for per-vendedor fields.
      if (!groupKey && item && this.metasCalculadas) {
        const key = this.metaEditKey(item.cod_vendedor, field)
        const raw = this.metaEditBuffer[key]
        if (raw !== undefined && raw !== '') {
          const num = this.parseNumber(raw)
          if (num !== null) this.syncMetaEditToSource(item.cod_vendedor, field, num)
        }
      }
    },
    async saveTipo(item) {
      // Save tipo change to config
      try {
        const tipo = item.tipo || 'Calçado'  // Default to Calçado if not set
        const cod_vendedor = item.cod_vendedor
        
        // Update local arrays - IMPORTANT: For "Loja", we still need to save it in vendedores_tipo
        // but remove from calcado and roupa arrays
        if (tipo === 'Calçado') {
          if (!this.calcadoVendedores.includes(cod_vendedor)) {
            this.calcadoVendedores.push(cod_vendedor)
          }
          this.roupaVendedores = this.roupaVendedores.filter(v => v !== cod_vendedor)
        } else if (tipo === 'Roupa') {
          if (!this.roupaVendedores.includes(cod_vendedor)) {
            this.roupaVendedores.push(cod_vendedor)
          }
          this.calcadoVendedores = this.calcadoVendedores.filter(v => v !== cod_vendedor)
        } else if (tipo === 'Loja') {
          // Remove from both Calçado and Roupa arrays
          this.calcadoVendedores = this.calcadoVendedores.filter(v => v !== cod_vendedor)
          this.roupaVendedores = this.roupaVendedores.filter(v => v !== cod_vendedor)
        }
        
        this.editTipoMode = null
        this.hasChanges = true
        item.tipo = tipo
      } catch (error) {
        console.error('Error saving tipo:', error)
        this.error = 'Erro ao salvar tipo: ' + (error.response?.data?.detail || error.message)
      }
    },
    async saveTipoVerificacao(item) {
      // Save tipo change from verificacao table
      await this.saveTipo(item)
      // Reload verificacao
      await this.verificarVendas()
    },
    async saveTipoMetasCalculadas(item) {
      const tipo = item.tipo || 'Calçado'
      const cod_vendedor = item.cod_vendedor
      const targetKey = tipo === 'Roupa' ? 'roupa' : (tipo === 'Loja' ? 'loja' : 'calcado')

      if (this.metasCalculadas) {
        for (const g of ['calcado', 'roupa', 'loja']) {
          const det = (this.metasCalculadas[g] && this.metasCalculadas[g].vendedores_detalhes) || []
          const idx = det.findIndex(d => d && Number(d.cod_vendedor) === Number(cod_vendedor))
          if (idx >= 0) {
            const [moved] = det.splice(idx, 1)
            moved.tipo = tipo
            if (!this.metasCalculadas[targetKey]) {
              this.$set(this.metasCalculadas, targetKey, { count_atual: 0, sales_anterior: 0, media: 0, meta_1: null, meta_2: null, vendedores_detalhes: [] })
            }
            const targetDet = this.metasCalculadas[targetKey].vendedores_detalhes || []
            targetDet.push(moved)
            this.metasCalculadas[targetKey].vendedores_detalhes = targetDet
            this.$set(this.metasCalculadas[targetKey], 'count_atual', targetDet.length)
            if (this.metasCalculadas[g]) this.$set(this.metasCalculadas[g], 'count_atual', (this.metasCalculadas[g].vendedores_detalhes || []).length)
            this.$nextTick(() => this.recalcGroupAggregatesOnly())
            break
          }
        }
      }

      if (tipo === 'Calçado') {
        if (!this.calcadoVendedores.includes(cod_vendedor)) this.calcadoVendedores.push(cod_vendedor)
        this.roupaVendedores = this.roupaVendedores.filter(v => v !== cod_vendedor)
      } else if (tipo === 'Roupa') {
        if (!this.roupaVendedores.includes(cod_vendedor)) this.roupaVendedores.push(cod_vendedor)
        this.calcadoVendedores = this.calcadoVendedores.filter(v => v !== cod_vendedor)
      } else if (tipo === 'Loja') {
        this.calcadoVendedores = this.calcadoVendedores.filter(v => v !== cod_vendedor)
        this.roupaVendedores = this.roupaVendedores.filter(v => v !== cod_vendedor)
      }

      this.editTipoMode = null
      this.hasChanges = true
      this.$nextTick(() => this.salvarConfig(true))
    },
    async toggleAllCharts() {
      this.showAllCharts = !this.showAllCharts
      
      if (this.showAllCharts && this.metasAtual && this.metasAtual.vendedores) {
        // Load charts for all active sellers
        for (const vendedor of this.metasAtual.vendedores) {
          if (!this.sellerCharts[vendedor.cod_vendedor]) {
            await this.showSellerChart(vendedor.cod_vendedor, vendedor.nom_vendedor)
          }
        }
      }
    },
    async onAnoMesChange() {
      this.loading = true
      this.error = null
      try {
        await this.loadSaved()
        await this.loadMetasAtual()
      } catch (error) {
        console.warn('Error in onAnoMesChange:', error)
        if (error.response?.status !== 404) {
          this.error = 'Erro ao carregar dados: ' + (error.response?.data?.detail || error.message)
        }
      } finally {
        this.loading = false
      }
    }
  },
  watch: {
    calcadoVendedores() { this.hasChanges = true },
    roupaVendedores() { this.hasChanges = true },
    vendedoresAtivos() { this.hasChanges = true },
    margemCrescimentoMeta1() { this.hasChanges = true },
    margemCrescimentoMeta2() { this.hasChanges = true },
    meta1() { this.hasChanges = true },
    meta2() { this.hasChanges = true },
    metasAdicionais: {
      handler() { this.hasChanges = true },
      deep: true
    }
  }
}
</script>

<style scoped>
.metas-container {
  padding: 20px;
}
.metas-top-bar {
  gap: 0.25rem;
}
.metas-period-label {
  font-size: 0.9rem;
  margin-right: 0.5rem;
  color: #6c757d;
}
.metas-period-select {
  width: auto;
  min-width: 5rem;
  display: inline-block;
}
.metas-config-card .card-body {
  font-size: 0.85rem;
}
.config-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 1rem;
}
.config-row.config-two-rows {
  flex-direction: column;
  align-items: stretch;
}
.config-row-inner {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 0.25rem 0;
}
.config-row-inner .config-group-label {
  min-width: 4.5rem;
}
.config-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.config-group-label {
  font-weight: 600;
  color: var(--primary);
  min-width: 4rem;
  font-size: 0.9rem;
}
.config-fields {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.config-field {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.config-field label {
  margin-bottom: 0;
  white-space: nowrap;
}
.config-field .form-control {
  width: 5.5rem;
}
.config-extra {
  margin-left: auto;
}
/* Row color by seller type in Metas Calculadas tables */
.metas-row-calcado {
  background-color: rgba(0, 123, 255, 0.12) !important;
}
.metas-row-roupa {
  background-color: rgba(40, 167, 69, 0.12) !important;
}
.metas-row-loja {
  background-color: rgba(52, 58, 64, 0.2) !important;
}
</style>
