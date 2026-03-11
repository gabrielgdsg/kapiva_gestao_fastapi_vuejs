<template>
  <div class="lev2-marca-wrap">
    <label class="lev2-label">Marca</label>
    <div class="lev2-marca-combo">
      <b-form-input
        v-model="localQuery"
        size="sm"
        class="lev2-input lev2-marca-input"
        placeholder="Digite para buscar..."
        autocomplete="off"
        @focus="dropdownOpen = true"
        @input="dropdownOpen = true"
        @blur="onBlur"
      />
      <div v-if="dropdownOpen" class="lev2-marca-dropdown" @mousedown.prevent>
        <div
          v-for="(m, idx) in filteredSlice"
          :key="m && m.cod_marca != null ? m.cod_marca : 'm-' + idx"
          class="lev2-marca-option"
          :class="{ active: m && m.cod_marca === value }"
          @mousedown="select(m)"
        >
          {{ m && m.nom_marca }} <span v-if="m" class="lev2-marca-cod">({{ m.cod_marca }})</span>
        </div>
        <div v-if="filteredSlice.length === 0" class="lev2-marca-empty">Nenhuma marca encontrada</div>
      </div>
    </div>
    <div v-if="value && selectedNom" class="lev2-marca-hint">Selecionada: {{ selectedNom }}</div>
  </div>
</template>

<script>
export default {
  name: 'Levantamentos2MarcaSelect',
  props: {
    marcas: { type: Array, default: () => [] },
    value: { type: [Number, String], default: null }
  },
  data() {
    return {
      localQuery: '',
      dropdownOpen: false
    }
  },
  computed: {
    filteredSlice() {
      const q = (this.localQuery || '').trim().toLowerCase()
      const list = (this.marcas || []).filter(m => m && (m.nom_marca != null || m.cod_marca != null))
      if (!q) return list.slice(0, 80)
      return list
        .filter(m => (String(m.nom_marca || '').toLowerCase().includes(q) || String(m.cod_marca || '').toLowerCase().includes(q)))
        .slice(0, 80)
    },
    selectedNom() {
      if (!this.value || !this.marcas.length) return ''
      const m = this.marcas.find(x => String(x.cod_marca) === String(this.value))
      return m ? m.nom_marca : ''
    }
  },
  watch: {
    value: {
      handler(v) {
        if (v && this.marcas.length) {
          const m = this.marcas.find(x => String(x.cod_marca) === String(v))
          if (m) this.localQuery = m.nom_marca || ''
        }
      },
      immediate: true
    }
  },
  methods: {
    onBlur() {
      setTimeout(() => { this.dropdownOpen = false }, 200)
    },
    select(m) {
      if (!m) return
      this.$emit('input', m.cod_marca)
      this.localQuery = m.nom_marca || ''
      this.dropdownOpen = false
    }
  }
}
</script>

<style scoped>
.lev2-marca-wrap { display: flex; flex-direction: column; gap: 4px; min-width: 200px; }
.lev2-label { font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.lev2-marca-combo { position: relative; }
.lev2-marca-input { min-width: 200px; }
.lev2-marca-dropdown { position: absolute; left: 0; right: 0; top: 100%; margin-top: 2px; max-height: 220px; overflow-y: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); z-index: 100; }
.lev2-marca-option { padding: 6px 10px; cursor: pointer; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
.lev2-marca-option:hover, .lev2-marca-option.active { background: #eff6ff; color: #1d4ed8; }
.lev2-marca-cod { font-size: 11px; color: #64748b; margin-left: 4px; }
.lev2-marca-empty { padding: 8px 10px; font-size: 12px; color: #94a3b8; }
.lev2-marca-hint { font-size: 10px; color: #64748b; margin-top: 2px; }
</style>
