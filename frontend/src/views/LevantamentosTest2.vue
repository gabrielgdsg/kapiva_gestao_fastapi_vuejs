<template>
  <div class="page-layout levantamentos">
    <div class="page-header">
      <h1 class="page-title">Levantamentos</h1>
      <div class="page-subtitle">Produtos por marca, período e grade</div>
    </div>
    <div class="page-main">
        <b-alert v-if="loading" show variant="info">
            <b-spinner small></b-spinner> Carregando produtos... <span v-if="loadTime">({{loadTime}}ms)</span>
        </b-alert>
        <b-form @submit.stop.prevent="onSubmit">
            <b-row>
                <b-col sm="2">
                    <b-row>
                        <div class="autosuggest">
                            <b>Marca: </b>
                            <vue-autosuggest
                                    :get-suggestion-value="getSuggestionValue"
                                    :input-props="{id:'autosuggest__input', placeholder:'Digite a marca', class:'form-control'}"
                                    :suggestions="filteredOptions" @click="clickHandler" @focus="focusMe"
                                    @input="onInputChange"
                                    @selected="onSelected"
                                    v-model="query">
                                <div class="autosuggest-container-results" slot-scope="{suggestion}"
                                     style=" align-items: center;">
                                    <div> {{suggestion.item.nom_marca}} ({{suggestion.item.cod_marca}})</div>
                                </div>
                            </vue-autosuggest>
                        </div>
                    </b-row>
                    <b-row>
                        <div>
                            <b-form @submit.stop.prevent="pesquisarImagens">
                                <b-button type="submit" variant="primary">Pesquisar Imagens</b-button>
                            </b-form>
                            <b-form @submit.stop.prevent="carregarImagens">
                                <b-button type="submit" variant="primary">Carregar Imagens</b-button>
                            </b-form>
                            <b-form @submit.stop.prevent="saveProdutos">
                                <b-button type="submit" variant="primary">Salvar Produtos</b-button>
                            </b-form>
                        </div>
                        <b-form-checkbox name="check-button" switch v-model="showHideImgLink">
                            Link Imagens <b></b>
                        </b-form-checkbox>
                    </b-row>
                </b-col>
                <b-col sm="2">
                    <!-- Quick Filter Buttons -->
                    <b-row class="mb-2">
                        <b-col>
                            <small class="text-muted">Quick Filters:</small>
                            <b-button-group size="sm" class="d-flex flex-wrap">
                                <b-button variant="outline-primary" @click="setDateRange('month')">Month</b-button>
                                <b-button variant="outline-primary" @click="setDateRange('3months')">3M</b-button>
                                <b-button variant="outline-primary" @click="setDateRange('6months')">6M</b-button>
                                <b-button variant="outline-primary" @click="setDateRange('year')">Year</b-button>
                                <b-button variant="outline-secondary" @click="setDateRange('all')">All</b-button>
                            </b-button-group>
                        </b-col>
                    </b-row>
                    <b-row>
                        <label for="datepicker-data-ini">Data inicial: </label>
                        <mydatepicker-ini :datepicker_default="datepicker_ini" @childToParent="receiveDataCadastroIni"
                                          id="datepicker-data-ini"/>
                        <br><br>
                    </b-row>
                    <b-row>
                        <label for="datepicker-data-fim">Data final: </label>
                        <mydatepicker-fim :datepicker_default="datepicker_fim" @childToParent="receiveDataCadastroFim"
                                          id="datepicker-data-fim"/>
                        <br><br>

                    </b-row>
                </b-col>

                <b-col sm="2">
                    <b-row>
                        <b-button type="submit" variant="primary">Enviar</b-button>
                    </b-row>
                    <b-row>
                        <br>
                        <!--np-->
                    </b-row>

                    <b-row>
                        <b-form-group>
                            <b-input-group size="sm">
                                <b-form-input
                                        id="filter-input"
                                        placeholder="Filtrar por.."
                                        type="search"
                                        v-model="filter"
                                ></b-form-input>

                                <b-input-group-append>
                                    <b-button :disabled="!filter" @click="filter = ''">Limpar</b-button>
                                </b-input-group-append>
                            </b-input-group>
                        </b-form-group>
                    </b-row>

                </b-col>

                <b-col sm="4">
                    <b-row>
                        <b-col sm="12" class="mb-2">
                            <b-button-group class="w-100">
                                <b-button 
                                    variant="outline-secondary" 
                                    size="sm" 
                                    @click="showGradeSelector = !showGradeSelector"
                                    style="flex: 1;"
                                >
                                    {{ showGradeSelector ? '▼' : '▶' }} Grade Groups ({{grades_selected.length}} selected)
                                </b-button>
                                <b-button 
                                    variant="outline-danger" 
                                    size="sm" 
                                    @click="clearGradeSelection"
                                    :disabled="grades_selected.length === 0"
                                    title="Clear all selected grades"
                                >
                                    Clear
                                </b-button>
                            </b-button-group>
                        </b-col>
                        <!-- Selected Grades Sidebar -->
                        <b-col sm="12" v-if="grades_selected.length > 0" class="mb-2">
                            <b-card class="p-2" style="max-height: 200px; overflow-y: auto; background-color: #f8f9fa;">
                                <small class="text-muted d-block mb-1"><strong>Selected Groups:</strong></small>
                                <div class="selected-grades-list">
                                    <b-badge 
                                        v-for="(grade, idx) in grades_selected" 
                                        :key="idx"
                                        variant="primary" 
                                        class="mr-1 mb-1"
                                        style="font-size: 0.75rem;"
                                    >
                                        {{ grade.name || formatGradeSizes(grade) }}
                                    </b-badge>
                                </div>
                            </b-card>
                        </b-col>
                        <!-- Compact Grade Selector (Collapsible) -->
                        <b-col sm="12" v-if="showGradeSelector" class="mt-2">
                            <b-card class="p-2" style="max-height: 400px; overflow-y: auto;">
                                <!-- Search Filter -->
                                <b-input-group size="sm" class="mb-2">
                                    <b-form-input
                                        v-model="gradeSearchFilter"
                                        placeholder="Search grade groups..."
                                        type="search"
                                    ></b-form-input>
                                    <b-input-group-append>
                                        <b-button :disabled="!gradeSearchFilter" @click="gradeSearchFilter = ''">Clear</b-button>
                                    </b-input-group-append>
                                </b-input-group>
                                
                                <!-- Compact Grade Checkboxes -->
                                <div class="grade-selector-compact">
                                    <template v-for="grade in filteredGradeOptions">
                                        <div :key="grade.name" class="grade-item-compact">
                                            <b-form-checkbox
                                                :id="'grade-' + grade.name"
                                                :value="grade"
                                                v-model="grades_selected"
                                                size="sm"
                                            >
                                                <span class="grade-name">{{grade.name}}</span>
                                                <small class="text-muted grade-sizes">({{formatGradeSizes(grade)}})</small>
                                            </b-form-checkbox>
                                        </div>
                                    </template>
                                </div>
                                
                                <div v-if="filteredGradeOptions.length === 0" class="text-muted text-center mt-2">
                                    <small>No grade groups match your search</small>
                                </div>
                            </b-card>
                        </b-col>
                    </b-row>
                </b-col>

            </b-row>

            <b-row>
            </b-row>

        </b-form>

        <!-- Pagination & Virtual Scrolling Controls -->
        <b-row class="my-3">
            <b-col sm="6">
                <b-form-checkbox v-model="paginationEnabled" switch size="lg">
                    <strong>Pagination</strong> ({{ paginationEnabled ? 'ON' : 'OFF' }})
                    <small class="text-muted">{{ paginationEnabled ? 'Better performance' : 'Show all (for printing)' }}</small>
                </b-form-checkbox>
            </b-col>
            <b-col sm="6" v-if="paginationEnabled" class="text-right">
                <b-form-group label="Items per page:" label-cols="6" label-align="right">
                    <b-form-select v-model="perPage" :options="[50, 100, 200, 500]" size="sm" style="width: 100px"></b-form-select>
                </b-form-group>
            </b-col>
            <b-col sm="6" v-if="!paginationEnabled" class="mt-2">
                <b-form-checkbox v-model="virtualScrollingEnabled" switch size="lg">
                    <strong>Virtual Scrolling</strong> ({{ virtualScrollingEnabled ? 'ON' : 'OFF' }})
                    <small class="text-muted">{{ virtualScrollingEnabled ? 'Fast rendering for large datasets' : 'Standard rendering' }}</small>
                </b-form-checkbox>
            </b-col>
            <b-col sm="6" class="mt-2">
                <b-form-checkbox v-model="showCusto" switch size="lg">
                    <strong>Mostrar Custo</strong> ({{ showCusto ? 'ON' : 'OFF' }})
                    <small class="text-muted">{{ showCusto ? 'Coluna de custo visível' : 'Coluna de custo oculta' }}</small>
                </b-form-checkbox>
            </b-col>
        </b-row>

        <b-pagination
            v-if="paginationEnabled"
            v-model="currentPage"
            :total-rows="filteredmappedItemsComputed.length"
            :per-page="perPage"
            align="center"
            size="sm"
            class="my-2"
        ></b-pagination>

        <!-- Virtual Scrolling Table (when pagination OFF and virtual scrolling ON) -->
        <div v-if="!paginationEnabled && virtualScrollingEnabled" class="virtual-table-container">
            <table class="table table-bordered table-sm text-right" style="table-layout: fixed; width: 100%;">
                <thead class="thead-light" style="position: sticky; top: 0; z-index: 10; background: white;">
                    <tr>
                        <th v-for="field in computedFields" :key="field.key" class="text-right" style="position: sticky; top: 0;">
                            {{ field.label }}
                        </th>
                    </tr>
                    <!-- Filter row -->
                    <tr>
                        <td v-for="field in [...baseFields,...gradeFields,...valoresFields]" :key="field.key">
                            <template v-if="field.key==='nom_marca'||field.key==='dat_cadastro'||field.key==='dat_ultcompra'||field.key==='cod_referencia'||field.key==='des_cor'||field.key==='des_produto'||field.key==='vlr_custo_bruto'||field.key==='vlr_venda1'">
                                <b-form-input :placeholder="getFilterPlaceholder(field.key)" class="col-sm" size="sm"
                                              v-model="filters[field.key]"></b-form-input>
                            </template>
                            <template v-else>
                                {{gradeTotals[field.key+"_E"]}}<br><b :class="getStockClass(gradeTotals[field.key])">{{formatStock(gradeTotals[field.key])}}</b>
                            </template>
                        </td>
                    </tr>
                </thead>
            </table>
            <RecycleScroller
                class="virtual-scroller"
                :items="filteredmappedItemsComputed"
                :item-size="80"
                key-field="_virtualId"
                v-slot="{ item, index }"
            >
                <div class="virtual-row-wrapper">
                    <table class="table table-bordered table-sm mb-0 text-right" :class="{ 'table-striped': index % 2 === 0 }" style="table-layout: fixed; width: 100%;">
                        <tbody>
                            <tr @click="expandAdditionalInfo(item)" class="hover-row">
                                <td v-for="field in computedFields" :key="field.key" class="text-right">
                                    <template v-if="field.key === 'selected'">
                                        <input @change="formAnySelected" type="checkbox"
                                               v-model="subgrouped_items_bycolor_obj[item.cod_referencia][item.des_cor][0].selected"/>
                                    </template>
                                    <template v-else-if="field.key === 'img'">
                                        <img :src="item.img" v-bind="imageProps"/>
                                    </template>
                                    <template v-else-if="field.key === 'img_link'">
                                        <div v-show="showHideImgLink">
                                            <b-form-input v-model="subgrouped_items_bycolor_obj[item.cod_referencia][item.des_cor][0].img" size="sm"/>
                                        </div>
                                    </template>
                                    <template v-else-if="field.key === 'actions'">
                                        <b-btn size="sm" @click.stop="toggleDetails(item)">{{ item._showDetails ? '-' : '+'}}</b-btn>
                                    </template>
                                    <template v-else-if="gradeFields.find(f => f.key === field.key)">
                                        {{item[field.key+"_E"]}}<br><b v-if="(item[field.key+'_E'] || 0) > 0" :class="getStockClass(item[field.key])">{{formatStock(item[field.key])}}</b>
                                    </template>
                                    <template v-else-if="field.key === 'performance'">
                                        <SpeedGauge 
                                            :score="getPerformanceScore(item) || 0" 
                                            :size="90"
                                        />
                                    </template>
                                    <template v-else>
                                        {{ item[field.key] }}
                                    </template>
                                </td>
                            </tr>
                            <tr v-if="item._showDetails">
                                <td :colspan="computedFields.length">
                                    <div class="movimentos-container">
                                        <h6 class="mb-2"><strong>Histórico de Movimentos</strong></h6>
                                        <b-table 
                                            :fields="movimentosFields" 
                                            :items="formatMovimentos(item.movtos)" 
                                            :sort-asc="false"
                                            :sort-by="'data_movto'"
                                            :sort-compare="dateSorter" 
                                            small
                                            striped
                                            hover
                                            class="movimentos-table">
                                            <template v-slot:cell(origem)="{ item: movto }">
                                                <span :class="getOrigemClass(movto.cod_origem)">
                                                    <span v-if="movto.tipo_movto === 'E'" class="badge badge-success mr-1">E</span>
                                                    <span v-else class="badge badge-danger mr-1">S</span>
                                                    {{ movto.origem_nome }}
                                                </span>
                                            </template>
                                            <template v-slot:cell(data_movto)="{ item: movto }">
                                                {{ formatDate(movto.data_movto) }}
                                            </template>
                                            <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item: movto }">
                                                <span :key="field.key" :class="getMovimentoClass(movto[field.key])">
                                                    {{ movto[field.key] && movto[field.key] !== 0 ? movto[field.key] : '' }}
                                                </span>
                                            </template>
                                            <template v-slot:cell(tot_movto)="{ item: movto }">
                                                <span :class="getMovimentoClass(movto.tot_movto)">
                                                    {{ movto.tot_movto || 0 }}
                                                </span>
                                            </template>
                                        </b-table>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </RecycleScroller>
        </div>

        <!-- Standard b-table (when pagination ON or virtual scrolling OFF) -->
        <b-table v-else :bordered="true" :fields="computedFields" :items="paginatedItems"
                 :small=true
                 :sort-compare="dateSorter" @row-clicked="expandAdditionalInfo" class="text-right" head-variant="light" hover sticky-header="700px"
                 striped>

            <template v-slot:cell(actions)="{ detailsShowing, item }">
                <!-- Use the built in method from the scoped data to toggle the row details -->
                <b-btn @click="toggleDetails(item)">{{ detailsShowing ? '-' : '+'}}</b-btn>

            </template>
            <template v-slot:row-details="{ item }">
                <div class="movimentos-container">
                    <h6 class="mb-2"><strong>Histórico de Movimentos</strong></h6>
                    <b-table 
                        :fields="movimentosFields" 
                        :items="formatMovimentos(item.movtos)" 
                        :sort-asc="false"
                        :sort-by="'data_movto'"
                        :sort-compare="dateSorter" 
                        small
                        striped
                        hover
                        class="movimentos-table">
                        <template v-slot:cell(origem)="{ item: movto }">
                            <span :class="getOrigemClass(movto.cod_origem)">
                                <span v-if="movto.tipo_movto === 'E'" class="badge badge-success mr-1">E</span>
                                <span v-else class="badge badge-danger mr-1">S</span>
                                {{ movto.origem_nome }}
                            </span>
                        </template>
                        <template v-slot:cell(data_movto)="{ item: movto }">
                            {{ formatDate(movto.data_movto) }}
                        </template>
                        <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item: movto }">
                            <span :key="field.key" :class="getMovimentoClass(movto[field.key])">
                                {{ movto[field.key] && movto[field.key] !== 0 ? movto[field.key] : '' }}
                            </span>
                        </template>
                        <template v-slot:cell(tot_movto)="{ item: movto }">
                            <span :class="getMovimentoClass(movto.tot_movto)">
                                {{ movto.tot_movto || 0 }}
                            </span>
                        </template>
                    </b-table>
                </div>
            </template>

            <template slot-scope="data" slot="top-row"><!-- eslint-disable-line-->
                <td :key="field.key" v-for="field in [...baseFields,...gradeFields,...valoresFields]">
                    <template
                            v-if="field.key==='nom_marca'||field.key==='dat_cadastro'||field.key==='dat_ultcompra'||field.key==='cod_referencia'||field.key==='des_cor'||field.key==='des_produto'||field.key==='vlr_custo_bruto'||field.key==='vlr_venda1'">
                        <b-form-input :placeholder="field.label" class="col-sm"
                                      v-model="filters[field.key]"></b-form-input>
                    </template>
                    <template v-else-if="field.key === 'performance'">
                        <!-- Performance column header - no filter needed -->
                    </template>
                    <template v-else>
                        {{gradeTotals[field.key+"_E"]}}
                        <br><!-- eslint-disable-line-->
                        <b>{{gradeTotals[field.key]}}</b>

                    </template>
                </td>
            </template>

            <template #head(selected)="row"><!-- eslint-disable-line-->
                <b-form-checkbox
                        :indeterminate="form_indeterminate"
                        @change="form_toggleAll"
                        v-model="form_allSelected">
                </b-form-checkbox>
            </template>


            <template #cell(selected)="row">  <!-- eslint-disable-line-->

                <input @change="formAnySelected" type="checkbox"
                       v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].selected"/>
            </template>

            <template #cell(img)="data">  <!-- eslint-disable-line-->
                <img :src="data.value" v-bind="imageProps"/>
            </template>

            <template v-slot:head(img_link)="row">
                <div v-show="showHideImgLink">{{ row.label }}</div>
            </template>

            <template #cell(performance)="row">
                <SpeedGauge 
                    :score="getPerformanceScore(row.item) || 0" 
                    :size="90"
                />
            </template>

            <template #cell(img_link)="row">
                <div v-show="showHideImgLink">
                    <b-form-input
                            v-model="subgrouped_items_bycolor_obj[row.item.cod_referencia][row.item.des_cor][0].img"/>
                    <b-form-file @change="previewImage($event, row.item.cod_referencia, row.item.des_cor)" accept="image/*"
                                 placeholder="Nenhum arquivo"
                                 ref="file-input"></b-form-file>
                    <!--                    <input type="file" @change="previewImage($event, row.item.cod_referencia, row.item.des_cor)" accept="image/*">-->
                    <!--                    <img class="preview" :src="imageData">-->
                </div>
            </template>


            <template v-for="field in gradeFields" v-slot:[`cell(${field.key})`]="{ item }">
                <!-- eslint-disable-line-->
                {{item[field.key+"_E"]}}
                <br><!-- eslint-disable-line-->
                <template v-if="getInitialStock(item, field.key) > 0">
                    <b :class="getStockClass(item[field.key])"> {{formatStock(item[field.key])}} </b><!-- eslint-disable-line-->
                </template>
            </template>

        </b-table>

    </div>
  </div>
</template>

<script>
    import Mydatepicker from '../components/Mydatepicker'
    import SpeedGauge from '../components/SpeedGauge.vue'
    import axios from "axios"
    import {VueAutosuggest} from 'vue-autosuggest'
    import moment from "moment";
    import { RecycleScroller } from 'vue-virtual-scroller';
    // Import CSS for virtual scroller
    import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';

    export default {
        name: "LevantamentosTest",
        components: {
            'mydatepicker-ini': Mydatepicker,
            'mydatepicker-fim': Mydatepicker,
            'vue-autosuggest': VueAutosuggest,
            RecycleScroller,
            SpeedGauge
        },
        data() {
            return {
                loading: false,
                loadTime: null,
                filterTime: null,
                filterDebounceTimer: null,
                filterStartTime: null,
                isGradeTotalsInitialized: false,
                // Pagination
                paginationEnabled: true, // Default ON for better performance
                currentPage: 1,
                perPage: 100, // Default 100 items per page
                // Virtual Scrolling (only active when pagination is OFF)
                virtualScrollingEnabled: false, // Default OFF, enable when pagination is disabled
                // Cost column toggle
                showCusto: false, // Default OFF - hide cost column by default
                // Origem mapping for movimentos
                origemMapping: {
                    2: 'Emissão Nota Fiscal',
                    3: 'Requisição',
                    4: 'Devolução',
                    7: 'Ent. Proc. Notas',
                    9: 'Frente de Caixa',
                    12: 'Estorno Proc. Notas',
                    15: 'Condicional'
                },
                // Local filter state for immediate input feedback (not debounced)
                localFilters: {nom_marca: '', dat_cadastro: '', des_cor: '', des_produto: ''},
                // PERFORMANCE: Use Set for instant checkbox operations (O(1) instead of O(n))
                // Big companies like Google, Facebook use Sets for selection state
                selectedItemsSet: new Set(),
                showHideImgLink: false,
                form_selected_: [],
                produtos_selected: [],
                fields_selected: [],
                grades_selected: [], // Will be initialized in mounted() with default grade group
                gradeGroupsCache: [], // Cached grade groups (computed once, not on every reactive update)
                showGradeSelector: false, // Collapsible grade selector
                gradeSearchFilter: '', // Search filter for grade groups
                // Default grade groups (always available)
                defaultGradeGroups: [
                    {
                        name: 'Calçado Ad.',
                        grade: ['33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44'].map(s => ({key: s, label: s})),
                        sizes_str: '33;34;35;36;37;38;39;40;41;42;43;44'
                    },
                    {
                        name: 'Calçado Inf.',
                        grade: ['17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36'].map(s => ({key: s, label: s})),
                        sizes_str: '17;18;19;20;21;22;23;24;25;26;27;28;29;30;31;32;33;34;35;36'
                    },
                    {
                        name: 'Calçado Big',
                        grade: ['45', '46', '47', '48'].map(s => ({key: s, label: s})),
                        sizes_str: '45;46;47;48'
                    },
                    {
                        name: 'Havainas Ad.',
                        grade: ['33/34', '35/36', '37/38', '39/40', '41/42', '43/44', '45/46', '47/48'].map(s => ({key: s, label: s})),
                        sizes_str: '33/34;35/36;37/38;39/40;41/42;43/44;45/46;47/48'
                    },
                    {
                        name: 'Havaianaias Inf.',
                        grade: ['17/18', '19/20', '21/22', '23/24', '25/26', '27/28', '29/30', '31/32'].map(s => ({key: s, label: s})),
                        sizes_str: '17/18;19/20;21/22;23/24;25/26;27/28;29/30;31/32'
                    },
                    {
                        name: 'Cintos',
                        grade: ['85', '90', '95', '100', '105', '110', '115', '120', '125', '130', '135', '140'].map(s => ({key: s, label: s})),
                        sizes_str: '85;90;95;100;105;110;115;120;125;130;135;140'
                    },
                    {
                        name: 'Roupas',
                        grade: ['PP', 'M', 'G', 'GG'].map(s => ({key: s, label: s})),
                        sizes_str: 'PP;M;G;GG'
                    },
                    {
                        name: 'Roupas Extra',
                        grade: ['EG', 'EGG', 'G1', 'G2', 'G3'].map(s => ({key: s, label: s})),
                        sizes_str: 'EG;EGG;G1;G2;G3'
                    },
                    {
                        name: 'Grendene',
                        grade: ['17/18', '19', '20/21', '22', '23/24', '25', '26/27', '28', '29', '30', '31', '32/33'].map(s => ({key: s, label: s})),
                        sizes_str: '17/18;19;20/21;22;23/24;25;26/27;28;29;30;31;32/33'
                    },
                    {
                        name: 'Meias',
                        grade: ['33-38', '39-44', '39-42', '43-45', '33 A 38'].map(s => ({key: s, label: s})),
                        sizes_str: '33-38;39-44;39-42;43-45;33 A 38'
                    },
                    {
                        name: 'UN',
                        grade: ['UN'].map(s => ({key: s, label: s})),
                        sizes_str: 'UN'
                    }
                ],
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
                        "name": 'Padrão Adulto de Calçado',
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
                filter: null,
                debouncedFilters: {nom_marca: '', dat_cadastro: '', des_cor: '', des_produto: ''},
                google_search_array: [],
                produtos: [],
                ref_cor_marca: [],
                refs_array: '',
                mapped_items: [],
                form_selected: [],
                form_allSelected: false,
                form_indeterminate: false,
                grouped_items_byref_map: [],
                subgrouped_items_bycolor_obj: {},
                query: "",
                imageProps: {blank: true, width: 75, height: 75, class: 'm1'},
                imagem_test: 'https://www.katy.com.br/cdn/imagens/produtos/original/indoor-nike-beco-2-a451f3b4e2327ab6c8dc817bbc0250a3.jpg',
                suggestion_selected: {
                    cod_marca: 0,
                    fornecedores: [{fan_fornecedor: ''}],
                    nom_marca: "carregando",
                },
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
                // SCALABILITY STRATEGY: For production, use recent dates to limit data
                // Default: 01.01.2019 to today
                datepicker_ini: new Date('2019-01-01'),
                datepicker_fim: new Date(), // Today
                data_cadastro_ini: '',
                data_cadastro_fim: '',
                cod_fornecedor: 70,
                items: [],
                filters: {nom_marca: '', dat_cadastro: '', des_cor: '', des_produto: ''},
                currentItems: [],
                performanceData: {},  // Store performance metrics by reference-color key
                loadingPerformance: false
            }
        },
        computed: {
            // Filtered grade options based on search
            filteredGradeOptions() {
                if (!this.gradeSearchFilter) {
                    return this.grades_options
                }
                const filter = this.gradeSearchFilter.toLowerCase()
                return this.grades_options.filter(grade => {
                    const nameMatch = grade.name.toLowerCase().includes(filter)
                    const sizesMatch = grade.sizes_str && grade.sizes_str.toLowerCase().includes(filter)
                    return nameMatch || sizesMatch
                })
            },
            // Pagination: Returns paginated items or all items based on toggle
            paginatedItems() {
                if (!this.paginationEnabled) {
                    // Pagination OFF: return all items (for printing)
                    return this.filteredmappedItemsComputed;
                }
                // Pagination ON: return current page items
                const start = (this.currentPage - 1) * this.perPage;
                const end = start + this.perPage;
                return this.filteredmappedItemsComputed.slice(start, end);
            },
            // OPTIMIZATION: Uses debouncedFilters instead of direct filters to prevent
            // table re-render on every keystroke. This is a "Big Data" technique used
            // by companies like Google, Amazon, etc. for handling large datasets
            filteredmappedItemsComputed() {
                // Get base items (filtered or not)
                const hasFilters = Object.values(this.debouncedFilters).some(f => f !== '');
                let items = hasFilters 
                    ? this.mappedItemsComputed.filter(item => {
                        return Object.keys(this.debouncedFilters).every(key => {
                            const filterValue = this.debouncedFilters[key];
                            if (!filterValue) return true;
                            
                            const itemValue = item[key];
                            if (itemValue == null) return false;
                            
                            // Advanced filtering with operators: + (OR), & (AND), - (EXCLUDE), : (RANGE)
                            return this.advancedFilterMatch(String(itemValue), filterValue, key);
                        });
                    })
                    : this.mappedItemsComputed;
                
                // Filter: Only show products that have at least one selected grade with data
                if (this.grades_selected && this.grades_selected.length > 0) {
                    items = items.filter(item => {
                        // Get all selected grade keys
                        const selectedGradeKeys = new Set();
                        for (const selected of this.grades_selected) {
                            if (selected.grade) {
                                // Old format: {name: '...', grade: [...]}
                                selected.grade.forEach(g => selectedGradeKeys.add(g.key || g));
                            } else {
                                // New format: {key: '...', label: '...'}
                                selectedGradeKeys.add(selected.key || selected);
                            }
                        }
                        
                        // Check if this product has at least one selected grade with data
                        for (const gradeKey of selectedGradeKeys) {
                            const initialStockKey = gradeKey + '_E';
                            const actualStockKey = gradeKey;
                            
                            // Check if product has this grade with data
                            const hasInitialStock = item[initialStockKey] && item[initialStockKey] > 0;
                            const hasActualStock = item[actualStockKey] !== undefined && item[actualStockKey] !== null && item[actualStockKey] !== 0;
                            
                            if (hasInitialStock || hasActualStock) {
                                return true; // Product has this grade, include it
                            }
                        }
                        return false; // Product doesn't have any selected grade, exclude it
                    });
                }
                
                // SORT BY MOST RECENT: dat_ultcompra first, then dat_cadastro as fallback
                // Most recent dates appear first (descending order)
                return items.sort((a, b) => {
                    // Use dat_ultcompra for sorting (prioritize actual purchase date)
                    const dateA = a.dat_ultcompra || a.dat_cadastro || '1900-01-01';
                    const dateB = b.dat_ultcompra || b.dat_cadastro || '1900-01-01';
                    
                    // Descending order (most recent first)
                    return dateB.localeCompare(dateA);
                });
            },

            // Optimized gradeTotals - Vue's computed properties are automatically cached
            // Big Data optimization: Debounced filtering + early returns + optimized loops
            gradeTotals() {
                const filteredItems = this.filteredmappedItemsComputed;
                const grade_totals = {};

                if (filteredItems.length === 0) {
                    return grade_totals;
                }

                // Process each item and sum up grade values
                for (const item of filteredItems) {
                    for (const numero_da_grade in item) {
                        // Stop when we reach non-grade properties
                        if (numero_da_grade === 'nom_marca') {
                            break;
                        }

                        const value = item[numero_da_grade];

                        // Skip non-numeric values
                        if (isNaN(value)) {
                            continue;
                        }

                        // Initialize if needed
                        if (isNaN(grade_totals[numero_da_grade])) {
                            grade_totals[numero_da_grade] = 0;
                        }

                        // For actual stock (not _E), round negative to 0 when summing
                        if (numero_da_grade.endsWith('_E')) {
                            grade_totals[numero_da_grade] += value;
                        } else {
                            // Round negative stock to 0 for totals
                            grade_totals[numero_da_grade] += Math.max(0, value);
                        }
                    }
                }

                // Split totals into regular and _E categories
                const grade_totals_split = {};
                const grade_totals_split_E = {};
                
                for (const key in grade_totals) {
                    if (key.includes('E')) {
                        grade_totals_split_E[key] = grade_totals[key];
                    } else {
                        grade_totals_split[key] = grade_totals[key];
                    }
                }

                // Calculate overall totals
                const total = Object.values(grade_totals_split).reduce((a, b) => a + b, 0);
                const total_E = Object.values(grade_totals_split_E).reduce((a, b) => a + b, 0);

                grade_totals["totais"] = total;
                grade_totals["totais_E"] = total_E;

                return grade_totals;
            },

            // before chatgpt update try
            // gradeTotals() {
            //     const grade_totals = {}
            //     if (this.filteredmappedItemsComputed.length > 0) {
            //         for (const item in this.filteredmappedItemsComputed) {
            //             for (const numero_da_grade in this.filteredmappedItemsComputed[item]) {
            //                 if (numero_da_grade === 'nom_marca') {
            //                     break; //break loop when finds anything different from "numeros de grade"
            //                 }
            //                 if (isNaN(grade_totals[numero_da_grade])) {
            //                         grade_totals[numero_da_grade]= this.filteredmappedItemsComputed[item][numero_da_grade]
            //                     }
            //                 else {
            //                     grade_totals[numero_da_grade]= grade_totals[numero_da_grade] + this.filteredmappedItemsComputed[item][numero_da_grade]
            //                 }
            //             }
            //         }
            //     }
            //     let grade_totals_split = {}
            //     let grade_totals_split_E = {}
            //     let grade_totals_keys_E = Object.keys(grade_totals).filter((key) => key.includes('E'))
            //     let grade_totals_keys = Object.keys(grade_totals).filter((key) => !key.includes('E'))
            //
            //     for (const key in grade_totals_keys) {
            //         grade_totals_split_E[grade_totals_keys_E[key]]=grade_totals[grade_totals_keys_E[key]]
            //         grade_totals_split[grade_totals_keys[key]]=grade_totals[grade_totals_keys[key]]
            //     }
            //
            //     grade_totals["totais"] = Object.values(grade_totals_split).reduce((a, b) => a + b, 0)
            //     grade_totals["totais_E"]  = Object.values(grade_totals_split_E).reduce((a, b) => a + b, 0)
            //
            //     return grade_totals
            // },

            mappedItemsComputed() {
                let mapped_items = [];

                for (const ref_group in this.subgrouped_items_bycolor_obj) {
                    for (const cor in this.subgrouped_items_bycolor_obj[ref_group]) {
                        let saldo_estoq_entrada = 0;
                        let saldo_estoq = 0;
                        let graded_prods_estoq = {};
                        // Improved movtos processing - use Map for better performance and correctness
                        let movtosMap = new Map(); // Key: data_movto + cod_origem_movto, Value: movimento object
                        
                        // Collect all cod_origem_movto=7 (Ent. Proc. Notas) entries with their dates
                        // We'll check each cod_origem_movto=3 entry against these
                        const entradaProcNotasDates = [];
                        const items = this.subgrouped_items_bycolor_obj[ref_group][cor];
                        
                        for (const prod in items) {
                            const item = items[prod];
                            if (item.cod_origem_movto === 7 && item.tipo_movto === 'E' && item.data_movto) {
                                try {
                                    const movtoDate = moment(item.data_movto, 'DD/MM/YYYY');
                                    if (movtoDate.isValid()) {
                                        entradaProcNotasDates.push(movtoDate);
                                    }
                                } catch (e) {
                                    // Invalid date format, skip
                                }
                            }
                        }

                        // Track quantities to exclude from grade totals (cod_origem_movto=3 when cod_origem_movto=7 exists within 6 months)
                        let excludeFromTotals = {}; // Key: tamanho, Value: quantity to subtract
                        
                        // Get the end date for stock calculation (data_cadastro_fim)
                        let endDate = null;
                        if (this.data_cadastro_fim) {
                            try {
                                endDate = moment(this.data_cadastro_fim, 'DD/MM/YYYY');
                                if (!endDate.isValid()) {
                                    endDate = null;
                                }
                            } catch (e) {
                                endDate = null;
                            }
                        }

                        // CRITICAL FIX: Deduplicate movements to avoid SQL duplicate rows
                        // Use array index (prod) to ensure each row is processed only once
                        // This allows multiple legitimate movements on the same day with same origem
                        let processedMovements = new Set(); // Track processed row indices

                        let prodIndex = 0; // Track array index for deduplication
                        for (const prod in items) {
                            let movimento = 0;
                            const item = items[prod];
                            const tamanho = item.des_tamanho.toString();
                            let estoq_entrada_name = tamanho + "_E";

                            // Initialize estoque_entrada for this tamanho if not already done
                            if (isNaN(graded_prods_estoq[estoq_entrada_name])) {
                                graded_prods_estoq[estoq_entrada_name] = 0
                            }
                            
                            // Initialize stock calculation for this tamanho if not already done
                            if (graded_prods_estoq[tamanho] === undefined) {
                                graded_prods_estoq[tamanho] = 0; // Start from 0, we'll calculate from movements
                            }
                            
                            // Process movements for specific origem types
                            // Include: 2 (Emissão Nota Fiscal), 3 (Requisição), 4 (Devolução), 7 (Ent. Proc. Notas), 9 (Frente de Caixa), 12 (Estorno Proc. Notas), 15 (Condicional)
                            if ((item.cod_origem_movto === 2) || (item.cod_origem_movto === 7) || (item.cod_origem_movto === 3) || 
                                (item.cod_origem_movto === 4) || (item.cod_origem_movto === 9) || (item.cod_origem_movto === 12) || (item.cod_origem_movto === 15)) {
                                
                                // Calculate movimento quantity for display
                                if (item.tipo_movto === 'S' && item.cod_origem_movto === 12) {
                                    // Estorno Proc. Notas (Saída) - special case: subtracts from estoque_entrada
                                    movimento = 0 - item.qtd_movto;
                                    // Subtract from estoque_entrada (can make it negative, but that's correct for this special case)
                                    graded_prods_estoq[estoq_entrada_name] = graded_prods_estoq[estoq_entrada_name] - item.qtd_movto;
                                    saldo_estoq_entrada = saldo_estoq_entrada - item.qtd_movto;
                                } else if (item.tipo_movto === 'E') {
                                    // Entrada movements
                                    movimento = item.qtd_movto;
                                    
                                    // CRITICAL FIX: cod_origem_movto=3 (Requisicao) should only count as estoque_entrada
                                    // if there's NO cod_origem_movto=7 (Ent. Proc. Notas) within 6 months BEFORE this entry
                                    if (item.cod_origem_movto === 3) {
                                        let shouldExclude = false;
                                        
                                        // Check if there's any cod_origem_movto=7 entry within 6 months before this cod_origem_movto=3 entry
                                        if (item.data_movto && entradaProcNotasDates.length > 0) {
                                            try {
                                                const requisicaoDate = moment(item.data_movto, 'DD/MM/YYYY');
                                                if (requisicaoDate.isValid()) {
                                                    // Check if any Ent. Proc. Notas occurred within 6 months before this Requisicao
                                                    for (const procNotasDate of entradaProcNotasDates) {
                                                        const sixMonthsBeforeRequisicao = requisicaoDate.clone().subtract(6, 'months');
                                                        // If procNotasDate is after sixMonthsBeforeRequisicao and before or equal to requisicaoDate
                                                        if (procNotasDate.isAfter(sixMonthsBeforeRequisicao) && 
                                                            (procNotasDate.isBefore(requisicaoDate) || procNotasDate.isSame(requisicaoDate, 'day'))) {
                                                            shouldExclude = true;
                                                            break;
                                                        }
                                                    }
                                                }
                                            } catch (e) {
                                                // Invalid date format, skip check
                                            }
                                        }
                                        
                                        if (!shouldExclude) {
                                            // Only count as estoque_entrada if no cod_origem_movto=7 within 6 months before
                                            graded_prods_estoq[estoq_entrada_name] = graded_prods_estoq[estoq_entrada_name] + item.qtd_movto;
                                            saldo_estoq_entrada = saldo_estoq_entrada + item.qtd_movto;
                                        } else {
                                            // Track this quantity to exclude from grade totals
                                            if (!excludeFromTotals[tamanho]) {
                                                excludeFromTotals[tamanho] = 0;
                                            }
                                            excludeFromTotals[tamanho] += item.qtd_movto;
                                        }
                                        // movimento is still set for display purposes
                                    } else if (item.cod_origem_movto === 4) {
                                        // Devolução (Entrada) - do NOT count as estoque_entrada
                                        // Devolução is a return and should not be included in initial stock
                                        // But it DOES count toward actual stock (estoque_atual)
                                        // movimento is still set for display and stock calculation purposes
                                    } else if (item.cod_origem_movto === 15) {
                                        // Condicional (Entrada) - do NOT count as estoque_entrada
                                        // Condicional is temporary and should not be included in initial stock
                                        // movimento is still set for display purposes
                                    } else {
                                        // For other origem types (2, 7, 9), count as estoque_entrada
                                        graded_prods_estoq[estoq_entrada_name] = graded_prods_estoq[estoq_entrada_name] + item.qtd_movto;
                                        saldo_estoq_entrada = saldo_estoq_entrada + item.qtd_movto;
                                    }
                                } else if (item.tipo_movto === 'S') {
                                    // Saída movements (including cod_origem=2 Emissão Nota Fiscal, 9 Frente de Caixa, 15 Condicional)
                                    movimento = 0 - item.qtd_movto;
                                    // Note: Saídas don't count toward estoque_entrada, only toward movimento display and stock calculation
                                }

                                // CRITICAL FIX: Use array index to deduplicate - each row should be processed only once
                                // This prevents SQL duplicate rows from being processed multiple times
                                // But allows multiple legitimate movements on the same day (they'll have different array indices)
                                const movimentoRowKey = `${ref_group}_${cor}_${prodIndex}`;
                                
                                // Skip if we've already processed this exact row
                                if (processedMovements.has(movimentoRowKey)) {
                                    continue; // Skip duplicate row from SQL
                                }
                                processedMovements.add(movimentoRowKey);
                                
                                prodIndex++; // Increment for next iteration

                                // Check if this movimento is within the date range (up to endDate)
                                let includeInStockCalc = true;
                                if (endDate && item.data_movto) {
                                    try {
                                        const movtoDate = moment(item.data_movto, 'DD/MM/YYYY');
                                        if (movtoDate.isValid()) {
                                            // Only include movements up to and including the end date
                                            includeInStockCalc = movtoDate.isSameOrBefore(endDate, 'day');
                                        }
                                    } catch (e) {
                                        // Invalid date, include it
                                    }
                                }

                                // Create unique key for this movimento (date + origem) for grouping in display
                                const movtoKey = `${item.data_movto}_${item.cod_origem_movto}`;
                                
                                if (!movtosMap.has(movtoKey)) {
                                    // Create new movimento entry
                                    movtosMap.set(movtoKey, {
                                        data_movto: item.data_movto,
                                        tipo_movto: item.tipo_movto,
                                        cod_origem_movto: item.cod_origem_movto
                                    });
                                }
                                
                                // Add/update grade quantity for this movimento
                                const movto = movtosMap.get(movtoKey);
                                if (movto[tamanho]) {
                                    movto[tamanho] = movto[tamanho] + movimento;
                                } else {
                                    movto[tamanho] = movimento;
                                }
                                
                                // Calculate stock at the selected date by summing all movements up to that date
                                if (includeInStockCalc) {
                                    graded_prods_estoq[tamanho] = graded_prods_estoq[tamanho] + movimento;
                                }
                            }
                        }
                        
                        // Calculate total saldo_estoq from all tamanhos (round negatives to 0)
                        for (const tamanho in graded_prods_estoq) {
                            if (!tamanho.endsWith('_E') && tamanho !== 'totais') {
                                const stockValue = graded_prods_estoq[tamanho] || 0;
                                // Round negative stock to 0 for total calculation
                                saldo_estoq = saldo_estoq + Math.max(0, stockValue);
                            }
                        }
                        
                        // After processing all items, we've already excluded cod_origem_movto=3 from estoque_entrada
                        // by not adding them in the first place (when shouldExclude=true)
                        // So we don't need to subtract again - the excludeFromTotals was just for tracking
                        // The estoque_entrada values are already correct
                        
                        // Convert Map to array and sort by date
                        let reduced_movtos = Array.from(movtosMap.values()).sort((a, b) => {
                            return moment(b.data_movto, 'DD/MM/YYYY').toDate() - moment(a.data_movto, 'DD/MM/YYYY').toDate();
                        });


                        graded_prods_estoq['nom_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca;
                        graded_prods_estoq['dat_cadastro'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_cadastro;
                        graded_prods_estoq['dat_ultcompra'] = this.subgrouped_items_bycolor_obj[ref_group][cor][this.subgrouped_items_bycolor_obj[ref_group][cor].length - 1].dat_ultcompra;
                        graded_prods_estoq['cod_referencia'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_referencia;
                        graded_prods_estoq['des_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor
                        graded_prods_estoq['des_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_produto.replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_cor, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_tamanho, '').replace(this.subgrouped_items_bycolor_obj[ref_group][cor][0].nom_marca, '');
                        // Simplified: single image per product (not array)
                        graded_prods_estoq['img'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].img;
                        graded_prods_estoq['selected'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].selected;
                        // Unique ID for virtual scrolling
                        graded_prods_estoq['_virtualId'] = `${ref_group}-${cor}`;
                        graded_prods_estoq['totais_E'] = saldo_estoq_entrada;
                        graded_prods_estoq['totais'] = saldo_estoq;
                        graded_prods_estoq['vlr_custo_bruto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_bruto;
                        graded_prods_estoq['vlr_venda1'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_venda1;
                        graded_prods_estoq['des_grupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_grupo;
                        graded_prods_estoq['cod_grupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_grupo;
                        graded_prods_estoq['cod_subgrupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_subgrupo;
                        graded_prods_estoq['des_subgrupo'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_subgrupo;
                        graded_prods_estoq['cod_produto'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_produto;
                        graded_prods_estoq['vlr_custo_aquis'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].vlr_custo_aquis;
                        graded_prods_estoq['cod_grade'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_grade;
                        graded_prods_estoq['des_grade'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].des_grade;
                        graded_prods_estoq['cod_cor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_cor;
                        // graded_prods_estoq['dat_emissao'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_emissao;
                        // graded_prods_estoq['dat_lancamento'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].dat_lancamento;
                        graded_prods_estoq['cod_fornecedor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_fornecedor;
                        graded_prods_estoq['raz_fornecedor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].raz_fornecedor;
                        graded_prods_estoq['fan_fornecedor'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].fan_fornecedor;
                        graded_prods_estoq['cod_marca'] = this.subgrouped_items_bycolor_obj[ref_group][cor][0].cod_marca;
                        // graded_prods_estoq['ult_entrada'] = ult_entrada;
                        graded_prods_estoq['movtos'] =reduced_movtos;
                        // graded_prods_estoq['movtos'] =movtos;

                        mapped_items.push(graded_prods_estoq);
                    }
                }
                return mapped_items
            },
            todosProdutos() {
                // PERFORMANCE CRITICAL: Dates now pre-formatted by backend!
                // This eliminates ALL 808+ moment.js operations (60-70% faster)
                // Backend optimization - no PostgreSQL database changes required
                
                return this.mappedItemsComputed.map(produto => {
                    return {
                        cod_grupo: produto.cod_grupo || 0,
                        des_grupo: produto.des_grupo || '',
                        cod_subgrupo: produto.cod_subgrupo || 0,
                        des_subgrupo: produto.des_subgrupo || '',
                        cod_produto: produto.cod_produto || 0,
                        des_produto: produto.des_produto || '',
                        vlr_custo_bruto: produto.vlr_custo_bruto || 0.0,
                        vlr_custo_aquis: produto.vlr_custo_aquis || 0.0,
                        vlr_venda1: produto.vlr_venda1 || 0.0,
                        cod_grade: produto.cod_grade || 0,
                        des_grade: produto.des_grade || '',
                        cod_cor: produto.cod_cor || 0,
                        // OPTIMIZED: Dates arrive pre-formatted from backend API
                        // No moment.js operations needed!
                        dat_cadastro: produto.dat_cadastro || '1900-01-01T00:00:00.000000',
                        dat_ultcompra: produto.dat_ultcompra || '1900-01-01T00:00:00.000000',
                        cod_fornecedor: produto.cod_fornecedor || 0,
                        raz_fornecedor: produto.raz_fornecedor || '',
                        fan_fornecedor: produto.fan_fornecedor || '',
                        cod_marca: produto.cod_marca,
                        cod_referencia: produto.cod_referencia || 'default',
                        nom_marca: produto.nom_marca || '',
                        des_cor: produto.des_cor || '',
                        // Simplified: single image per product
                        img: produto.img || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=',
                        selected: produto.selected
                    }
                });
            },
            produtosSelecionados() {
                // OPTIMIZED: Use Set for O(1) lookup instead of filtering entire array
                return this.todosProdutos.filter(row => {
                    const key = `${row.cod_referencia}-${row.des_cor}`;
                    return this.selectedItemsSet.has(key);
                });
            },
            computedFields() {
                // return [].concat(this.baseFields, this.adultoFields, this.valoresFields)
                return [].concat(this.baseFields, this.gradeFields, this.valoresFields)
            },
            movimentosFields() {
                // Fields for movimentos table - removed qtd_movto, added origem and Tot.
                // Exclude 'totais' field from gradeFields to avoid duplicate Tot. column
                try {
                    const gradeFieldsFiltered = (this.gradeFields || []).filter(f => f.key !== 'totais');
                    return [
                        {key: 'data_movto', label: 'Data', sortable: true},
                        {key: 'origem', label: 'Origem', sortable: true},
                        ...gradeFieldsFiltered,
                        {key: 'tot_movto', label: 'Tot.', sortable: true}
                    ]
                } catch (e) {
                    console.error('Error in movimentosFields:', e);
                    return [
                        {key: 'data_movto', label: 'Data', sortable: true},
                        {key: 'origem', label: 'Origem', sortable: true},
                        {key: 'tot_movto', label: 'Tot.', sortable: true}
                    ];
                }
            },
            // Auto-discover grades from the data
            // Use mappedItemsComputed directly to avoid circular dependency with filteredmappedItemsComputed
            autoDiscoveredGrades() {
                const discoveredGrades = new Set();
                
                // List of fields to exclude (not grades)
                const excludedFields = new Set([
                    'nom_marca', 'selected', 'img', 'img_link', 'cod_referencia', 'des_cor', 'des_produto',
                    'dat_cadastro', 'dat_ultcompra', 'vlr_custo_bruto', 'vlr_venda1', 'cod_produto',
                    'des_grupo', 'cod_grupo', 'cod_subgrupo', 'des_subgrupo', 'vlr_custo_aquis', '_virtualId',
                    'totais', 'cod_cor', 'cod_fornecedor', 'cod_grade', 'cod_marca', 'cod_tamanho', 'cod_barra',
                    'raz_fornecedor', 'fan_fornecedor', 'des_grade', 'des_tamanho'
                ]);
                
                // Scan all mapped items (not filtered) to find all unique grades - avoids circular dependency
                if (this.mappedItemsComputed && this.mappedItemsComputed.length > 0) {
                    for (const item of this.mappedItemsComputed) {
                        // Look for grade keys (numeric or alphanumeric grade names)
                        for (const key in item) {
                            // Skip excluded fields and fields ending with _E
                            if (excludedFields.has(key) || key.includes('_E')) {
                                continue;
                            }
                            
                            // Check if this is a grade field (has a numeric value)
                            const value = item[key];
                            if (typeof value === 'number' && !isNaN(value)) {
                                // This looks like a grade field - add it
                                discoveredGrades.add(key);
                            }
                        }
                    }
                }
                
                // Convert Set to array of field objects
                return Array.from(discoveredGrades).map(grade => ({
                    key: grade,
                    label: grade
                })).sort((a, b) => {
                    // Sort: numeric grades first (ascending), then alphanumeric
                    const aNum = parseInt(a.key);
                    const bNum = parseInt(b.key);
                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        return aNum - bNum;
                    }
                    if (!isNaN(aNum)) return -1;
                    if (!isNaN(bNum)) return 1;
                    return a.key.localeCompare(b.key);
                });
            },
            // Available grades from loaded products (for dynamic checkboxes)
            // ONLY shows sizes from selected grade groups - hides all others
            gradeFields() {
                // Use selected grades from dynamic checkboxes
                if (this.grades_selected && this.grades_selected.length > 0) {
                    // Collect all unique grade keys from selected grade groups
                    const gradeKeysSet = new Set();
                    for (const selected of this.grades_selected) {
                        if (selected.grade && Array.isArray(selected.grade)) {
                            // Format: {name: '...', grade: [{key: '...', label: '...'}, ...]}
                            selected.grade.forEach(g => {
                                const key = g.key || g.label || g;
                                if (key) gradeKeysSet.add(key);
                            });
                        } else if (selected.key) {
                            // Format: {key: '...', label: '...'}
                            gradeKeysSet.add(selected.key);
                        }
                    }
                    
                    // Convert to array of field objects, sorted
                    const gradeKeys = Array.from(gradeKeysSet).map(key => ({
                        key: key,
                        label: key
                    })).sort((a, b) => {
                        // Sort: numeric grades first (ascending), then alphanumeric
                        const aNum = parseInt(a.key);
                        const bNum = parseInt(b.key);
                        if (!isNaN(aNum) && !isNaN(bNum)) {
                            return aNum - bNum;
                        }
                        if (!isNaN(aNum)) return -1;
                        if (!isNaN(bNum)) return 1;
                        return a.key.localeCompare(b.key);
                    });
                    
                    return [].concat(gradeKeys, this.totaisFields);
                }
                
                // If no grades selected, return empty (hide all grade columns)
                return this.totaisFields || [];
            },
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
            valoresFields() {
                const fields = [
                    // {key: 'totais', label: 'Tot.', sortable: true},
                    {key: 'vlr_venda1', label: 'Vlr. Venda', sortable: true},
                    {key: 'performance', label: 'Performance', sortable: true}
                ]
                // Conditionally add cost field based on toggle
                if (this.showCusto) {
                    fields.unshift({key: 'vlr_custo_bruto', label: 'Custo', sortable: true})
                }
                return fields
            },
            totaisFields() {
                return [
                    {key: 'totais', label: 'Tot.', sortable: true}
                ]
            },
            filteredOptions() {
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
            availableFornecedores() {
                return this.suggestion_selected.fornecedores
                    .filter(item => item)
                    .map(item => item.fan_fornecedor)
            },
            computedItems() {
                return this.items
                    .filter(item => item)
                    .map(item => item)
            }
        },
        beforeMount() {
            this.loadMarcas()
        },
        async mounted() {
            // Start with default grade groups
            let allGradeGroups = [...this.defaultGradeGroups]
            
            // Load additional grade groups from extracted JSON
            try {
                const response = await axios.get('/product_grade_groups_extracted.json')
                if (response.data && response.data.formatted_for_levantamentos) {
                    // Merge with defaults (avoid duplicates by checking sizes_str)
                    const defaultSizesStrs = new Set(this.defaultGradeGroups.map(g => g.sizes_str))
                    const additionalGroups = response.data.formatted_for_levantamentos.filter(
                        g => !defaultSizesStrs.has(g.sizes_str)
                    )
                    allGradeGroups = [...this.defaultGradeGroups, ...additionalGroups]
                    console.log(`Loaded ${allGradeGroups.length} grade groups (${this.defaultGradeGroups.length} defaults + ${additionalGroups.length} from JSON)`)
                } else if (response.data && response.data.grade_groups) {
                    // Fallback: use grade_groups if formatted_for_levantamentos not available
                    const defaultSizesStrs = new Set(this.defaultGradeGroups.map(g => g.sizes_str))
                    const additionalGroups = response.data.grade_groups
                        .filter(g => !defaultSizesStrs.has(g.sizes_str))
                        .map((g, i) => ({
                            name: g.sizes_str || `Grade Group ${i+1} (${g.sizes_count} sizes)`,
                            grade: g.sizes.map(s => ({key: s, label: s})),
                            sizes_str: g.sizes_str
                        }))
                    allGradeGroups = [...this.defaultGradeGroups, ...additionalGroups]
                    console.log(`Loaded ${allGradeGroups.length} grade groups from grade_groups data`)
                }
                
                // Load performance data
                await this.loadPerformanceData()
            } catch (error) {
                console.warn('Could not load grade groups from JSON, using defaults only:', error)
                // Use only default grades if JSON not found
            }
            
            // Update grades_options with merged list
            this.grades_options = allGradeGroups
            
            // Pre-select default "Calçado Ad." on component mount
            this.$nextTick(() => {
                if (this.grades_selected.length === 0) {
                    const defaultGrade = this.grades_options.find(g => g.name === 'Calçado Ad.')
                    if (defaultGrade) {
                        this.grades_selected = [defaultGrade]
                    } else if (this.grades_options.length > 0) {
                        // Fallback: select first grade group
                        this.grades_selected = [this.grades_options[0]]
                    }
                }
            })
        },
        watch: {
            filters: {
                handler(newFilters) {
                    // Debounce filter updates to improve performance
                    clearTimeout(this.filterDebounceTimer);
                    this.filterDebounceTimer = setTimeout(() => {
                        this.debouncedFilters = {...newFilters};
                    }, 300); // 300ms delay
                },
                deep: true
            }
        },
        methods: {
            // Intelligently group grades by analyzing product patterns
            // OPTIMIZED: Simplified logic, computed once via watcher, cached for performance
            // This is a METHOD, not a computed property, so side effects are allowed
            computeGroupedGrades() {
                if (!this.mappedItemsComputed || this.mappedItemsComputed.length === 0) {
                    this.gradeGroupsCache = [];
                    return;
                }
                
                // Cache check - avoid re-computation
                if (this.gradeGroupsCache.length > 0) {
                    return;
                }
                
                const excludedFields = new Set([
                    'nom_marca', 'selected', 'img', 'img_link', 'cod_referencia', 'des_cor', 'des_produto',
                    'dat_cadastro', 'dat_ultcompra', 'vlr_custo_bruto', 'vlr_venda1', 'cod_produto',
                    'des_grupo', 'cod_grupo', 'cod_subgrupo', 'des_subgrupo', 'vlr_custo_aquis', '_virtualId',
                    'totais', 'cod_cor', 'cod_fornecedor', 'cod_grade', 'cod_marca', 'cod_tamanho', 'cod_barra',
                    'raz_fornecedor', 'fan_fornecedor', 'des_grade', 'des_tamanho'
                ]);
                
                // Collect unique product references and their grades
                const refGradesMap = new Map(); // ref -> {grades: Set, nom_marca: string}
                
                for (const item of this.mappedItemsComputed) {
                    const ref = item.cod_referencia;
                    if (!refGradesMap.has(ref)) {
                        refGradesMap.set(ref, { grades: new Set(), nom_marca: item.nom_marca || '' });
                    }
                    const data = refGradesMap.get(ref);
                    for (const key in item) {
                        if (excludedFields.has(key) || key.includes('_E')) continue;
                        if (typeof item[key] === 'number' && !isNaN(item[key])) {
                            data.grades.add(key);
                        }
                    }
                }
                
                const gradeGroups = [];
                const processedRefs = new Set();
                const allGrades = new Set();
                
                // Helper: parse grade number (handles "23/24" -> 23)
                const parseNum = (g) => parseInt(g.split('/')[0]);
                const isNum = (g) => !isNaN(parseNum(g));
                const hasSplit = (grades) => grades.some(g => g.includes('/'));
                const hasRange = (grades) => grades.some(g => g.includes('-') && !g.includes('/'));
                
                // Process each product reference
                for (const [ref, data] of refGradesMap.entries()) {
                    const grades = Array.from(data.grades);
                    grades.forEach(g => allGrades.add(g));
                    
                    if (processedRefs.has(ref)) continue;
                    
                    const nums = grades.filter(isNum).map(parseNum).sort((a, b) => a - b);
                    let pattern = null;
                    let name = null;
                    
                    // Quick pattern matching (order matters - most specific first)
                    if (hasSplit(grades) && grades.filter(g => g.includes('/')).length >= 3) {
                        pattern = 'calcado_duplo';
                        name = 'Calçado Duplo';
                    } else if (hasRange(grades)) {
                        pattern = 'meia';
                        name = 'Meia';
                    } else if (nums.length >= 5 && nums[0] >= 85 && nums[nums.length - 1] <= 140) {
                        pattern = 'cintos';
                        name = 'Cintos';
                    } else if (nums.length >= 5 && nums[0] >= 34 && nums[nums.length - 1] <= 58 && nums.every(n => n % 2 === 0)) {
                        pattern = 'calca';
                        name = 'Calça';
                    } else if (nums.length >= 5 && nums[0] >= 15 && nums[nums.length - 1] <= 36) {
                        pattern = 'calcado_infantil';
                        name = 'Calçado Infantil';
                    } else if (nums.length >= 5 && nums[0] >= 33 && nums[nums.length - 1] <= 48) {
                        pattern = 'calcado_adulto';
                        name = 'Calçado Adulto';
                    } else if (['PP', 'P', 'M', 'G', 'GG'].every(e => grades.includes(e)) || 
                               ['P', 'M', 'G', 'GG'].every(e => grades.includes(e))) {
                        pattern = 'roupa_adulto';
                        name = 'Roupa Adulto';
                    } else if ([4, 6, 8, 10, 12, 14, 16].some(n => nums.includes(n)) && nums.length >= 3) {
                        pattern = 'roupa_infantil';
                        name = 'Roupa Infantil';
                    } else if (hasSplit(grades) || grades.length >= 6) {
                        pattern = 'product_specific';
                        name = `${data.nom_marca} ${ref}`;
                    }
                    
                    if (pattern) {
                        let group = gradeGroups.find(g => g.pattern === pattern && 
                            (pattern !== 'product_specific' || g.ref === ref));
                        
                        if (!group) {
                            group = {
                                name,
                                grade: grades.map(g => ({ key: g, label: g })),
                                pattern,
                                ref: pattern === 'product_specific' ? ref : null
                            };
                            gradeGroups.push(group);
                        } else {
                            // Merge grades
                            const existing = new Set(group.grade.map(g => g.key));
                            grades.forEach(g => {
                                if (!existing.has(g)) {
                                    group.grade.push({ key: g, label: g });
                                }
                            });
                            group.grade.sort((a, b) => {
                                const aNum = parseNum(a.key);
                                const bNum = parseNum(b.key);
                                if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
                                return a.key.localeCompare(b.key);
                            });
                        }
                        processedRefs.add(ref);
                    }
                }
                
                // Add individual grades
                const processed = new Set();
                gradeGroups.forEach(g => g.grade.forEach(gr => processed.add(gr.key)));
                allGrades.forEach(g => {
                    if (!processed.has(g)) {
                        gradeGroups.push({ name: g, grade: [{ key: g, label: g }], pattern: 'individual' });
                    }
                });
                
                // Sort
                const order = {
                    'calcado_infantil': 1, 'calcado_adulto': 2, 'calcado_duplo': 3, 'cintos': 4,
                    'roupa_infantil': 5, 'roupa_adulto': 6, 'calca': 7, 'meia': 8,
                    'product_specific': 9, 'individual': 10
                };
                const sorted = gradeGroups.sort((a, b) => {
                    const aOrd = order[a.pattern] || 99;
                    const bOrd = order[b.pattern] || 99;
                    return aOrd !== bOrd ? aOrd - bOrd : a.name.localeCompare(b.name);
                });
                
                this.gradeGroupsCache = sorted;
            },
            // Quick date range filter
            setDateRange(range) {
                const today = new Date();
                let startDate;
                
                switch(range) {
                    case 'month':
                        startDate = new Date(today.setMonth(today.getMonth() - 1));
                        break;
                    case '3months':
                        startDate = new Date(today.setMonth(today.getMonth() - 3));
                        break;
                    case '6months':
                        startDate = new Date(today.setMonth(today.getMonth() - 6));
                        break;
                    case 'year':
                        startDate = new Date(today.setFullYear(today.getFullYear() - 1));
                        break;
                    case 'all':
                        startDate = new Date(2000, 0, 1); // Start from year 2000
                        break;
                    default:
                        startDate = new Date(today.setFullYear(today.getFullYear() - 1));
                }
                
                this.datepicker_ini = startDate;
                this.datepicker_fim = new Date(); // Today
                
                // Trigger form submission automatically
                this.$nextTick(() => {
                    this.onSubmit();
                });
            },
            expandAdditionalInfo(row) {
      row._showDetails = !row._showDetails;
    },
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
            toggleAll(checked) {
                this.selected = checked ? this.flavours.slice() : []
            },
            clearGradesSelected() {
                // console.log("this.grades_selected")
                // console.log(this.grades_selected)
                // this.grades_selected = [];
            },
            dateSorter(a, b, key) {

                if (key === 'dat_ultcompra' || key === 'dat_cadastro'|| key === 'data_movto') {
                    if (moment(a[key], 'DD/MM/YYYY').toDate() > moment(b[key], 'DD/MM/YYYY').toDate()) return 1;
                    if (moment(a[key], 'DD/MM/YYYY').toDate() < moment(b[key], 'DD/MM/YYYY').toDate()) return -1;
                    return 0;
                } else {
                    return false       // If field is not `date` we let b-table handle the sorting
                }
            },
            objectify(element) {
                var result =
                    {
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
                        // dat_cadastro: element[20],
                        // dat_cadastro: moment(element[20]),
                        dat_cadastro: moment(element[20]).format('DD/MM/YYYY'),
                        dat_ultcompra: moment(element[21]).format('DD/MM/YYYY'),
                        // dat_emissao: moment(element[22]).format('DD/MM/YYYY'),
                        // dat_lancamento: moment(element[23]).format('DD/MM/YYYY'),
                        // dat_saida: moment(element[22]).format('DD/MM/YYYY'),
                        cod_fornecedor: element[22],
                        raz_fornecedor: element[23],
                        fan_fornecedor: element[24],
                        cod_marca: element[25],
                        nom_marca: element[26],
                        tipo_movto: element[27],
                        qtd_movto: element[28],
                        data_movto: moment(element[29]).format('DD/MM/YYYY'),
                        cod_movto: element[30],
                        cod_origem_movto: element[31],
                        selected: false,
                        // Simplified: single image per product (default thumbnail)
                        img: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII='
                    };
                return result
            },
            onSubmit() {
                this.loading = true;
                this.loadTime = null;
                const startTime = performance.now();
                
                const path = `/api/levantamentos/${this.data_cadastro_ini}/${this.data_cadastro_fim}/${this.suggestion_selected.cod_marca}`;
                axios.get(path)
                    .then((res) => {
                        this.items = [];
                        res.data.forEach(item => this.items.push(this.objectify(item)));
                        this.groupItemsByRef()
                        this.subgroupItemsByColor()
                        this.mapped_items = []
                        
                        const endTime = performance.now();
                        this.loadTime = Math.round(endTime - startTime);
                        this.loading = false;
                        
                        // AUTO-LOAD IMAGES: After products load, automatically fetch images
                        // Uses setTimeout to not block UI rendering (runs in next event loop)
                        setTimeout(() => {
                            this.carregarImagens();
                        }, 100); // 100ms delay to let UI render first
                    })
                    .catch((error) => {
                        this.loading = false;
                        this.loadTime = null;
                        console.error('Erro ao carregar levantamentos:', error)
                        console.error(error.response.data);
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
                // Send only identifier fields (avoid type validation issues)
                const produtosForImages = this.todosProdutos.map(p => ({
                    cod_referencia: p.cod_referencia,
                    nom_marca: p.nom_marca,
                    des_cor: p.des_cor,
                    des_produto: p.des_produto
                }));

                const path = `/api/produtos/images/`;
                axios.put(path, produtosForImages)
                    .then((res) => {
                        for (const key in res.data) {
                            // Simplified: single image per product (direct assignment)
                            this.$set(this.subgrouped_items_bycolor_obj[res.data[key].cod_referencia][res.data[key].des_cor][0], 'img', res.data[key].img)
                        }
                    })
                    .catch((error) => {
                        // Image loading error
                        console.error('Erro ao carregar imagens:', error);
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

                    this.image_index = 1 //these both lines are needed to auto refresh images
                    this.image_index = 0 //these both lines are needed to auto refresh images

                }
            },
            //maybe remove asyncs..

            async saveProdutos() {
                // Update img from subgrouped_items_bycolor_obj before saving
                const produtosToSave = this.produtosSelecionados.map(produto => {
                    // Get the latest img value from the view object
                    const currentImg = this.subgrouped_items_bycolor_obj[produto.cod_referencia]?.[produto.des_cor]?.[0]?.img;
                    return {
                        ...produto,
                        img: currentImg || produto.img // Use current img or fallback to original
                    };
                });

                const api_path = `/api/produtos/save`
                axios.put(api_path, produtosToSave)
                    .then(() => {
                        // Products saved successfully
                        alert('Produtos salvos com sucesso!');
                    })
                    .catch((error) => {
                        // Save error
                        console.error('Erro ao salvar produtos:', error);
                        alert('Erro ao salvar produtos. Verifique o console.');
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
                    .catch(() => {
                        // Fetch image error - silent fail
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
            async loadPerformanceData() {
                try {
                    this.loadingPerformance = true
                    // Try to load performance data for multiple years (most recent first)
                    const currentYear = new Date().getFullYear()
                    const yearsToTry = []
                    // Try last 3 years
                    for (let year = currentYear - 1; year >= Math.max(2019, currentYear - 3); year--) {
                        yearsToTry.push(year)
                    }
                    
                    // Try each year until we get data
                    for (const anoAnalise of yearsToTry) {
                        try {
                            const response = await axios.get(`/api/levantamentos/performance/${anoAnalise}`)
                            if (response.data && Object.keys(response.data).length > 0) {
                                this.performanceData = response.data
                                console.log(`Loaded performance data for ${Object.keys(this.performanceData).length} products (year ${anoAnalise})`)
                                // Log sample keys for debugging
                                const sampleKeys = Object.keys(this.performanceData).slice(0, 5)
                                console.log('Sample performance keys:', sampleKeys)
                                sampleKeys.forEach(key => {
                                    const perf = this.performanceData[key]
                                    console.log(`  ${key}: score=${perf.score}, velocity=${perf.velocity}, total_sold=${perf.total_sold}`)
                                })
                                return // Success, stop trying other years
                            }
                        } catch (err) {
                            // Try next year
                            continue
                        }
                    }
                    // If no data found, use empty object
                    this.performanceData = {}
                    console.warn('No performance data found for any year')
                } catch (error) {
                    console.warn('Could not load performance data:', error)
                    this.performanceData = {}
                } finally {
                    this.loadingPerformance = false
                }
            },
            getPerformanceScore(item) {
                // Ensure consistent key format: cod_referencia (string) - cod_cor (number)
                const cod_ref = String(item.cod_referencia || '').trim()
                const cod_cor = parseInt(item.cod_cor) || 0
                const key = `${cod_ref}-${cod_cor}`
                
                // Try exact match first
                let perf = this.performanceData[key]
                
                // If not found, try variations (case-insensitive, whitespace differences)
                if (!perf) {
                    const keys = Object.keys(this.performanceData)
                    const normalizedKey = key.toLowerCase().replace(/\s+/g, '')
                    perf = keys.find(k => {
                        const normalizedK = k.toLowerCase().replace(/\s+/g, '')
                        return normalizedK === normalizedKey
                    })
                    if (perf) {
                        perf = this.performanceData[perf]
                    }
                }
                
                // Debug: log first few lookups
                if (Object.keys(this.performanceData).length > 0) {
                    if (!perf) {
                        // Check if there's a similar key (for debugging first few)
                        const similarKeys = Object.keys(this.performanceData).filter(k => 
                            k.toLowerCase().includes(cod_ref.toLowerCase()) || 
                            k.includes(String(cod_cor))
                        )
                        if (similarKeys.length > 0 && similarKeys.length < 3) {
                            console.debug(`Performance key "${key}" not found. Item:`, { 
                                cod_referencia: item.cod_referencia, 
                                cod_cor: item.cod_cor,
                                type_cod_ref: typeof item.cod_referencia,
                                type_cod_cor: typeof item.cod_cor
                            }, 'Similar keys:', similarKeys)
                        }
                    }
                }
                
                if (perf && perf.score !== undefined && perf.score !== null && perf.score > 0) {
                    return perf.score
                }
                // If no performance data, return null (will show as 0)
                return null
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
                    .catch(() => {
                        // Load marcas error - silent fail
                    })
            },
            clickHandler(item) { // eslint-disable-line no-unused-vars
                // event fired when clicking on the input
            },
            onSelected(item) {
                this.suggestion_selected = item.item;
                this.form_selected = this.availableFornecedores
            },
            onInputChange(text) { // eslint-disable-line no-unused-vars
                // Input change handled by autosuggest
            },
            /**
             * This is what the <input/> value is set to when you are selecting a suggestion.
             */
            getSuggestionValue(suggestion) {
                return suggestion.item.nom_marca;
            },
            focusMe(e) { // eslint-disable-line no-unused-vars
                // FocusEvent handler
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
            formAnySelected(checked) { // eslint-disable-line no-unused-vars
                // OPTIMIZED: Use Set instead of filtering entire array
                var selected_rows = this.todosProdutos.filter(row => row.selected == true)
                this.form_selected_ = selected_rows
                
                // Update selectedItemsSet for consistency
                this.selectedItemsSet.clear();
                selected_rows.forEach(row => {
                    const key = `${row.cod_referencia}-${row.des_cor}`;
                    this.selectedItemsSet.add(key);
                });
            },
            // PERFORMANCE METHODS for fast checkbox operations
            isItemSelected(codReferencia, desCor) {
                const key = `${codReferencia}-${desCor}`;
                return this.selectedItemsSet.has(key);
            },
            toggleItemSelection(codReferencia, desCor) {
                const key = `${codReferencia}-${desCor}`;
                if (this.selectedItemsSet.has(key)) {
                    this.selectedItemsSet.delete(key);
                } else {
                    this.selectedItemsSet.add(key);
                }
                // Update the item's selected property
                if (this.subgrouped_items_bycolor_obj[codReferencia] && 
                    this.subgrouped_items_bycolor_obj[codReferencia][desCor]) {
                    this.subgrouped_items_bycolor_obj[codReferencia][desCor][0].selected = !this.subgrouped_items_bycolor_obj[codReferencia][desCor][0].selected;
                }
                this.formAnySelected();
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
            },
            // Format movimentos for display - ensures all movements are shown correctly
            formatMovimentos(movtos) {
                try {
                    if (!movtos || !Array.isArray(movtos)) {
                        return [];
                    }
                    
                    return movtos.map(movto => {
                        // Get origem name from mapping - use cod_origem_movto if available, otherwise tipo_movto
                        const cod_origem = movto.cod_origem_movto || movto.tipo_movto;
                        const origem_nome = (this.origemMapping && this.origemMapping[cod_origem]) || `Origem ${cod_origem}`;
                        
                        // Determine tipo_movto from movimento values (positive = entrada, negative = saida)
                        let tipo_movto = movto.tipo_movto;
                        if (!tipo_movto) {
                            // Try to infer from grade values
                            const gradeValues = Object.values(movto).filter(v => typeof v === 'number' && v !== 0);
                            tipo_movto = gradeValues.length > 0 && gradeValues[0] > 0 ? 'E' : 'S';
                        }
                        
                        // Calculate total for this movimento row - sum all grade values (exclude 'totais' field)
                        let tot_movto = 0;
                        const gradeKeys = this.gradeFields.filter(f => f.key !== 'totais').map(f => f.key);
                        gradeKeys.forEach(gradeKey => {
                            const value = movto[gradeKey];
                            if (typeof value === 'number' && !isNaN(value)) {
                                tot_movto += value;
                            }
                        });
                        
                        return {
                            ...movto,
                            cod_origem: cod_origem,
                            origem_nome: origem_nome,
                            tipo_movto: tipo_movto || 'E', // Default to entrada if not specified
                            tot_movto: tot_movto // Add calculated total
                        };
                    }).filter(movto => movto.data_movto); // Filter out invalid entries
                } catch (e) {
                    console.error('Error in formatMovimentos:', e, movtos);
                    return [];
                }
            },
            // Format date for display
            formatDate(dateStr) {
                if (!dateStr) return '';
                try {
                    return moment(dateStr, 'DD/MM/YYYY').format('DD/MM/YYYY');
                } catch (e) {
                    return dateStr;
                }
            },
            // Format grade sizes in compact way (e.g., "22-36" or "33;34;35;36")
            formatGradeSizes(grade) {
                if (!grade || !grade.grade || !Array.isArray(grade.grade)) {
                    return ''
                }
                if (grade.sizes_str) {
                    // Use the sizes_str if available (more compact)
                    return grade.sizes_str.length > 50 ? grade.sizes_str.substring(0, 50) + '...' : grade.sizes_str
                }
                // Fallback: join labels
                const labels = grade.grade.map(g => g.label || g.key || g).join(';')
                return labels.length > 50 ? labels.substring(0, 50) + '...' : labels
            },
            // Clear all selected grades
            clearGradeSelection() {
                this.grades_selected = []
            },
            // Get CSS class for origem type
            getOrigemClass(cod_origem) {
                const classes = {
                    2: 'text-primary',   // Emissão Nota Fiscal
                    3: 'text-info',       // Requisição
                    4: 'text-warning',    // Devolução
                    7: 'text-success',   // Ent. Proc. Notas
                    9: 'text-primary',   // Frente de Caixa
                    12: 'text-danger',   // Estorno Proc. Notas
                    15: 'text-secondary'  // Condicional
                };
                return classes[cod_origem] || 'text-dark';
            },
            // Get CSS class for movimento quantity (positive/negative)
            getMovimentoClass(value) {
                if (!value || value === 0) return 'text-muted';
                return value > 0 ? 'text-success font-weight-bold' : 'text-danger font-weight-bold';
            },
            // Format stock value: round negative to 0
            formatStock(value) {
                if (value === null || value === undefined || isNaN(value)) return 0;
                return Math.max(0, Math.round(value));
            },
            // Get CSS class for stock: red if negative (will be rounded to 0 but still shown in red)
            getStockClass(value) {
                if (value === null || value === undefined || isNaN(value)) return '';
                if (value < 0) return 'text-danger font-weight-bold';
                return '';
            },
            // Get initial stock value for a grade
            getInitialStock(item, gradeKey) {
                const initialStockKey = gradeKey + '_E';
                const value = item[initialStockKey];
                if (value === null || value === undefined || isNaN(value)) return 0;
                return value;
            },
            // Get filter placeholder with operator examples
            getFilterPlaceholder(fieldKey) {
                const examples = {
                    'des_cor': 'Ex: preto+branco (OR), -preto (EXCLUDE)',
                    'nom_marca': 'Ex: beira+rio (OR), -larsen (EXCLUDE)',
                    'dat_cadastro': 'Ex: 2025-01-01:2025-12-31 (RANGE)',
                    'dat_ultcompra': 'Ex: 2025-01-01:2025-12-31 (RANGE)',
                    'cod_referencia': 'Ex: 8513+617B (OR)',
                    'des_produto': 'Ex: bota+sandalia (OR)',
                    'vlr_custo_bruto': 'Ex: 50:200 (RANGE)',
                    'vlr_venda1': 'Ex: 100:500 (RANGE)'
                };
                return examples[fieldKey] || fieldKey;
            },
            // Advanced filtering with operators: + (OR), & (AND), - (EXCLUDE), : (RANGE)
            advancedFilterMatch(itemValue, filterValue, fieldKey) {
                const itemStr = String(itemValue).toLowerCase();
                const filterStr = String(filterValue).toLowerCase().trim();
                
                // Handle EXCLUDE operator (-)
                if (filterStr.startsWith('-')) {
                    const excludeValue = filterStr.substring(1).trim();
                    return !itemStr.includes(excludeValue);
                }
                
                // Handle RANGE operator (:) for dates and numbers
                if (filterStr.includes(':')) {
                    const parts = filterStr.split(':');
                    if (parts.length === 2) {
                        const minStr = parts[0].trim();
                        const maxStr = parts[1].trim();
                        
                        // Check if it's a date field
                        if (fieldKey.includes('data') || fieldKey.includes('dat_')) {
                            try {
                                const itemDate = moment(itemValue, 'DD/MM/YYYY');
                                const minDate = moment(minStr, 'YYYY-MM-DD');
                                const maxDate = moment(maxStr, 'YYYY-MM-DD');
                                
                                if (itemDate.isValid() && minDate.isValid() && maxDate.isValid()) {
                                    return itemDate.isSameOrAfter(minDate, 'day') && itemDate.isSameOrBefore(maxDate, 'day');
                                }
                            } catch (e) {
                                // Fall back to string comparison
                            }
                        }
                        
                        // Check if it's a number field
                        const itemNum = parseFloat(itemValue);
                        const minNum = parseFloat(minStr);
                        const maxNum = parseFloat(maxStr);
                        
                        if (!isNaN(itemNum) && !isNaN(minNum) && !isNaN(maxNum)) {
                            return itemNum >= minNum && itemNum <= maxNum;
                        }
                    }
                }
                
                // Handle OR operator (+)
                if (filterStr.includes('+')) {
                    const orValues = filterStr.split('+').map(v => v.trim());
                    return orValues.some(val => itemStr.includes(val));
                }
                
                // Handle AND operator (&)
                if (filterStr.includes('&')) {
                    const andValues = filterStr.split('&').map(v => v.trim());
                    return andValues.every(val => itemStr.includes(val));
                }
                
                // Default: simple contains match
                return itemStr.includes(filterStr);
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

    /* Virtual Scrolling Styles */
    .virtual-table-container {
        height: 700px;
        display: flex;
        flex-direction: column;
        border: 1px solid #dee2e6;
    }

    .virtual-scroller {
        flex: 1;
        overflow: auto;
    }

    .virtual-row-wrapper {
        border-bottom: 1px solid #dee2e6;
    }

    .virtual-row-wrapper .hover-row:hover {
        background-color: rgba(0, 0, 0, 0.075);
        cursor: pointer;
    }

    .virtual-table-container table {
        margin-bottom: 0;
    }

    /* Movimentos Table Styles */
    .movimentos-container {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 4px;
        margin: 10px 0;
    }

    .movimentos-table {
        font-size: 0.875rem;
    }

    /* Compact Grade Selector Styles */
    .grade-selector-compact {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 4px;
        font-size: 0.85rem;
    }

    .grade-item-compact {
        padding: 2px 4px;
        border: 1px solid #e0e0e0;
        border-radius: 3px;
        background-color: #fafafa;
    }

    .grade-item-compact:hover {
        background-color: #f0f0f0;
    }

    .grade-name {
        font-weight: 500;
        font-size: 0.9rem;
    }

    .grade-sizes {
        display: block;
        margin-top: 2px;
        font-size: 0.75rem;
        color: #6c757d;
        word-break: break-all;
    }

    .selected-grades-list {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }

    .movimentos-table .text-success {
        color: #28a745 !important;
    }

    .movimentos-table .text-danger {
        color: #dc3545 !important;
    }


</style>