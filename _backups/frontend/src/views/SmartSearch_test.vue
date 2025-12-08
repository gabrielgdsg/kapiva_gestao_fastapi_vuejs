<template>
  <div class="search-table h-100 justify-content-center align-items-center"
       v-bind:class="{row: data.length === 0}" v-if="isMounted">


    <div v-if="data.length > 0">

      <div class="d-flex justify-content-between">

        <!-- main search -->
        <b-input-group size="xs">
          <b-form-input v-model="searchInput"></b-form-input>
          <b-input-group-append is-text>
            <b-icon icon="search"></b-icon>
          </b-input-group-append>
        </b-input-group>

      </div>

      <div class="d-flex justify-content-between mt-2 mb-0">
        <b-button-group>
          <!-- dropdown -->
          <b-dropdown id="col-dropdown" class="col-dropdown" no-flip text="Visibilité">
            <b-dropdown-item :key="field.key" class="p-0" style="padding: 0" v-for="field in fields"
                             v-if="field.key !== 'action'">
              <div @click.stop="onDropdownClick(field.key)"
                   class="checkbox-wrapper">
                <b-form-checkbox
                        :checked="isColumnDisplayed(field.key)"
                        disabled
                >
                  {{ field.label || field.key }}
                </b-form-checkbox>
              </div>
            </b-dropdown-item>
          </b-dropdown>
          <b-button :variant="noneOfSearchMethodIsUsed ? '' : 'danger'" @click="cancelFilters">Enlever filtre</b-button>

          <!-- dropdown action groupées -->
          <slot name="groupped-actions"></slot>

        </b-button-group>
        <div align="right" style="display: inline-flex">
          <span style="margin: 4px;">Afficher</span>
          <b-form-select
                  v-model="perPage"
                  :options="perPageOptions"
                  size="sm"
          ></b-form-select>
          <span style="margin: 4px;">éléments</span>
        </div>
      </div>
      <div class="d-flex justify-content-between mt-0 mb-2">
        <span style="margin-top: 5px;">{{ buildInformationLine }}</span>
        <!-- pagination -->
        <b-pagination
                :per-page="perPage"
                :total-rows="formattedData.length"
                align="right"
                class="my-0 mt-1"
                size="sm"
                v-model="currentPage"
        ></b-pagination>
      </div>
      <!-- TABLE -->
      <b-table
              :current-page="currentPage"
              :fields="fieldsToShow"
              :items="formattedData"
              :per-page="perPage"
              foot-clone
              no-footer-sorting
              primary-key="id"
              :sticky-header="true"
              responsive
              striped
      >
        <!-- action col template -->
        <template
                v-if="!!$scopedSlots.action"
                v-slot:cell(action)="row">
          <slot name="action" v-bind="row.item"></slot>
        </template>

        <!-- html escape template -->
        <template v-slot:cell()="data">
          <span v-html="data.value"></span>
        </template>

        <!-- footer -->
        <template v-slot:foot()="data">
          <input :value="getFieldFromKey(data.column).searchVal"
                 @input="setFieldSearchValue(data.column, $event.target.value)"
                 v-if="getFieldFromKey(data.column).key !== 'action'"
                 class="w-100"
                 placeholder="Recherche">
        </template>

      </b-table>

      <div class="d-flex justify-content-between mt-0">
        <span style="margin-top: 5px;">{{ buildInformationLine }}</span>
        <!-- pagination -->
        <b-pagination
                :per-page="perPage"
                :total-rows="formattedData.length"
                align="right"
                class="my-0 mt-1"
                size="sm"
                v-model="currentPage"
        ></b-pagination>
      </div>
    </div>

    <div v-else>
      <p>Aucun résultat</p>
    </div>
  </div>
</template>


<script lang="ts">
  import { Component, Prop, Vue } from 'vue-property-decorator'
  import BvTableField from '../../interfaces/BvTableField'

  enum SearchFusionMethod {
    Union = 'union',
    Intersection = 'intersection',
  }

  interface FieldsInteractiveInterface extends BvTableField {
    searchVal: string
    stickyColumn: boolean
  }

  @Component
  export default class SearchTable extends Vue {
    // The array containing the data objects
    @Prop(Array) readonly data!: any[]
    // The array containing the info of each column. key must be equal to key in object data
    @Prop(Array) readonly fields!: BvTableField[]
    @Prop({default: SearchFusionMethod.Intersection}) readonly searchFusionMethod!: SearchFusionMethod
    @Prop({default: 'highlight'}) readonly highlighterClass!: string
    mainHighlighterClass: string = this.highlighterClass
    @Prop({default: 'field-highlight'}) readonly fieldHighlighterClass!: string
    currentPage = 1
    perPage = 10
    perPageOptions = [10, 25, 50, 100]
    searchInput = ''
    isMounted = false
    // Contains the value of each column search field
    fieldsInteractive: FieldsInteractiveInterface[] = []

    // ---
    mainHilightColor: string = 'yellow'
    fieldHilightColor: string = 'orange'

    get fieldsToShow(): BvTableField[] {
      return this.fieldsInteractive.filter(field => {
        return field.display
      })
    }

    get noneColumnSearchFieldIsUsed(): boolean {
      return this.numberOfSearchFieldsUsed === 0
    }

    get numberOfSearchFieldsUsed(): number {
      return this.fieldsInteractive.reduce((count: number, field) => {
        return count + (field.searchVal !== '' ? 1 : 0)
      }, 0)
    }

    // (01), (10)
    get exactlyOneSearchMethodIsUsed(): boolean {
      return (this.searchInput !== '' && this.noneColumnSearchFieldIsUsed) || (this.searchInput === '' && !this.noneColumnSearchFieldIsUsed)
    }

    // (00)
    get noneOfSearchMethodIsUsed(): boolean {
      return (this.searchInput === '' && this.noneColumnSearchFieldIsUsed)
    }

    // (11)
    get bothSearchMethodsAreUsed(): boolean {
      return (this.searchInput !== '' && !this.noneColumnSearchFieldIsUsed)
    }

    get onlyMainSearchIsUsed(): boolean {
      return (this.searchInput !== '' && this.noneColumnSearchFieldIsUsed)
    }

    get onlyFieldSearchIsUsed(): boolean {
      return (this.searchInput === '' && !this.noneColumnSearchFieldIsUsed)
    }

    get buildInformationLine(): string {
      const txt: String[] = []
      txt.push("Affichage de l'élément")
      txt.push(this.formattedData.length === 0 ? '0' : (((this.currentPage-1) *  this.perPage)+1).toString())
      txt.push('à')
      txt.push((this.currentPage * this.perPage < this.formattedData.length ? this.currentPage * this.perPage : this.formattedData.length).toString())
      txt.push('sur')
      txt.push((this.formattedData.length).toString())
      txt.push('éléments')
      if (this.formattedData.length < this.data.length) {
        txt.push('(filtré de')
        txt.push((this.data.length).toString())
        txt.push('éléments au total)')
      }
      return txt.join(' ')
    }

    // Data with
    get formattedData() {
      const mapped = this.data
              .map((item: any) => {
                const itemWithHighlight: any = {}
                this.fields.forEach(field => {
                  itemWithHighlight[field.key] = this.replaceBySearch(field.key, item[field.key])
                })
                return itemWithHighlight
              })

      return mapped
              .filter((item: any) => {
                //                                                                                                      (searchInput,columnSearchField)
                // If there is no filter at all, return the row                                                         (00)
                if (this.noneOfSearchMethodIsUsed) return true

                let countFromMainHighlight = 0
                let countFromFieldHighlight = 0

                // loop through each field
                for (const [key, col] of Object.entries(item)) {
                  if (!this.fieldsInteractive[this.fieldsInteractive.findIndex(x => x.key === key)].display) continue // Only search in displayed column
                  if (typeof col !== 'string') continue // only check in string values

                  if (this.onlyMainSearchIsUsed) {
                    // if only one of the search method has been used, return anything having a 'highlight' class       (01), (10)
                    if (col.includes('fromMainSearch') || col.includes(this.fieldHighlighterClass)) {
                      return true
                    }
                  } else {

                    // if both of the search method have been used, filter according to the searchFusionMethod          (11)
                    if (this.searchFusionMethod === SearchFusionMethod.Intersection) {

                      // TODO: search only in class attribute of markup (faster)
                      if (col.includes('fromMainSearch')) {
                        countFromMainHighlight++
                      }
                      if (col.includes('fromFieldSearch')) {
                        countFromFieldHighlight++
                      }
                    } else if (this.searchFusionMethod === SearchFusionMethod.Union) {
                      if (col.includes(`<span class="${this.highlighterClass}`)) {
                        // TODO
                        return true
                      }
                    }
                  }
                }

                // determine whether we keep the row
                if (this.bothSearchMethodsAreUsed) {
                  return countFromMainHighlight > 0 && countFromFieldHighlight === this.numberOfSearchFieldsUsed
                } else {
                  if (this.onlyMainSearchIsUsed) {
                    return countFromFieldHighlight > 0
                  } else if (this.onlyFieldSearchIsUsed) {

                    return countFromFieldHighlight === this.numberOfSearchFieldsUsed
                  }
                }
              })
    }

    isColumnDisplayed(key: string) {
      const field = this.getFieldFromKey(key)
      return field.display
    }

    setFieldSearchValue(key: string, searchVal: string) {
      const index = this.fieldsInteractive.findIndex(field => field.key === key)
      if (index === -1) throw new DOMException('Key not found')
      Vue.set(this.fieldsInteractive, index, {
        ...this.fieldsInteractive[index],
        searchVal: searchVal
      })
      // this.fieldsInteractive[index].searchVal = searchVal
    }

    mounted() {
      // programatically add action column if slot given
      if (!!this.$scopedSlots.action) {
        const fieldAction = {key: 'action'}
        this.fields.push(fieldAction)
      }

      // init column search values
      this.fields.forEach(field => {
        if (field.key === 'action') {
          this.fieldsInteractive.unshift({
            ...field,
            searchVal: '',
            sortable: false,
            display: field.display ?? true,
            stickyColumn: true
          })
        } else {
          this.fieldsInteractive.push({
            ...field,
            searchVal: '',
            sortable: field.sortable ?? true,
            display: field.display ?? true,
            stickyColumn: false
          })
        }
      })
      this.isMounted = true
    }

    onDropdownClick(key: string) {
      for (const index in this.fieldsInteractive) {
        if (this.fieldsInteractive[index].key === key) {
          this.fieldsInteractive[index].display = !this.fieldsInteractive[index].display // toggle
          return
        }
      }
    }

    private cancelFilters(): void {
      this.fieldsInteractive = this.fieldsInteractive.map((field) => {
        field.searchVal = ''
        return field
      })
      this.searchInput = ''
    }

    private getFieldFromKey(key: string): FieldsInteractiveInterface {
      const f = this.fieldsInteractive.find(field => field.key === key)
      if (f === undefined) {
        throw new DOMException('Key not found')
      }
      return f
    }

    private replaceBySearch(key: string, str: string | any) {
      if ((this.searchInput === '' && this.noneColumnSearchFieldIsUsed)
              || str === undefined || str === null) return str

      str = String(str)

      // main search bar
      if (this.exactlyOneSearchMethodIsUsed || this.bothSearchMethodsAreUsed) {
        const regexMain: RegExp | undefined = this.searchInput !== '' ? new RegExp(`${this.searchInput}`, 'i') : undefined
        const regexField: RegExp | undefined = this.getFieldFromKey(key).searchVal !== '' ? new RegExp(`${this.getFieldFromKey(key).searchVal}`, 'i') : undefined
        const matchMain: string[] | null = regexMain ? (str).match(regexMain) : null
        const matchField: string[] | null = regexField ? (str).match(regexField) : null

        if (matchMain || matchField) {
          str = this.surroundWithHilightClass(str, matchMain, matchField)
        }
      }

      return str
    }

    // https://stackoverflow.com/questions/1144783/how-can-i-replace-all-occurrences-of-a-string
    // replace only if not already contains a highlight class

    /**
     * @param str string to be surrounded
     * @param findMain what is matching with main search
     * @param findField what is matching with field search
     */
    private surroundWithHilightClass(str: string, findMain: string[] | null, findField: string[] | null) {
      const main: string | null = findMain && findMain.length > 0 ? findMain[0] : null
      const field: string | null = findField && findField.length > 0 ? findField[0] : null

      str = String(str)

      // if a search is in another search, put two classes
      if (field && main?.includes(field)) {
        str = str.replace(new RegExp(main, 'g'), `<span class="${this.mainHighlighterClass} fromFieldSearch fromMainSearch">${main}</span>`)
      } else if (main && field?.includes(main)) {
        str = str.replace(new RegExp(field, 'g'), `<span class="${this.mainHighlighterClass} fromMainSearch fromFieldSearch">${field}</span>`)
      } else {
        // here we are sur the highlightning will be separated (this prevents having span in span)
        if (main) {
          str = str.replace(new RegExp(main, 'g'), `<span class="${this.mainHighlighterClass} fromMainSearch">${main}</span>`)
        }
        if (field) {
          str = str.replace(new RegExp(field, 'g'), `<span class="${this.fieldHighlighterClass} fromFieldSearch">${field}</span>`)
        }
      }
      return str
    }

  }
</script>


<style lang="scss">
  .search-table {
    div {
      p {
        color: gray;
        text-align: center;
      }
    }

    span.fromFieldSearch {
      background-color: orange; // not defined : var(--main-highlighter-class);
    }

    /* Why this overrides fromFielSearch even if fromFieldSearch appear after in class order ? */
    span.fromMainSearch {
      background-color: yellow; // not defined : var(--field-highlighter-class);
    }

    span.field-highlight {
      background-color: orange;
    }

    .col-dropdown {
      .dropdown-item {
        padding: 0 !important;
      }
    }

    .checkbox-wrapper {
      padding: 4px 24px;
      width: 100%;
    }

    .custom-control-input[disabled] ~ .custom-control-label, .custom-control-input:disabled ~ .custom-control-label {
      color: #000 !important;
    }

    .b-table-sticky-header > .table.b-table > thead > tr > th {
      top: -2px !important;
    }

    .b-table-sticky-header {
      max-height: calc(125vh - 400px) !important;
    }

    .b-table-sticky-header > .table.b-table > tfoot > tr > th {
      position: sticky;
      bottom: 0;
      background-color: white;
      z-index: 0;
    }

    th.b-table-sticky-column {
      z-index: 4 !important;
    }
  }
</style>