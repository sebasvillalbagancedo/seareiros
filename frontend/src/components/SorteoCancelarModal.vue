<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-sm">
      <div class="modal-header">
        <h3>Cancelar Sorteo</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <div class="campo">
          <label>Motivo de cancelación *</label>
          <input v-model="motivo" type="text" required placeholder="Motivo de cancelación" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Volver</button>
        <button
          class="btn-primario btn-baja-modal"
          :disabled="!motivo || procesando"
          @click="confirmar"
        >
          {{ procesando ? 'Cancelando...' : 'Confirmar cancelación' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
  import { useSorteosStore } from '@/stores/sorteos'

  export default {
    name: 'SorteoCancelarModal',
    emits: ['cerrar', 'cancelado'],

    props: {
      sorteo: {
        type: Object,
        required: true,
      },
    },

    data() {
      return {
        motivo: '',
        procesando: false,
        error: null,
      }
    },

    methods: {
      async confirmar() {
        this.procesando = true
        this.error = null
        try {
          await useSorteosStore().cancelar(this.sorteo.id, this.motivo)
          this.$emit('cancelado')
        } catch (e) {
          this.error = e.response?.data?.detail || 'Error al cancelar el sorteo'
        } finally {
          this.procesando = false
        }
      },
    },
  }
</script>
