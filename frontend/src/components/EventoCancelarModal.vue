<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-sm">
      <div class="modal-header">
        <h3>Cancelar Evento</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <p>
          ¿Estás seguro de que quieres cancelar el evento
          <strong>{{ evento.nombre }}</strong
          >?
        </p>
        <div class="campo">
          <label>Motivo de cancelación *</label>
          <input
            v-model="motivo"
            type="text"
            placeholder="Indica el motivo de la cancelación"
            :class="{ 'input-error': errorMotivo }"
          />
          <p v-if="errorMotivo" class="error">{{ errorMotivo }}</p>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Volver</button>
        <button class="btn-primario btn-baja-modal" :disabled="procesando" @click="confirmar">
          {{ procesando ? 'Cancelando...' : 'Confirmar cancelación' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
  import { useEventosStore } from '@/stores/eventos'

  export default {
    name: 'EventoCancelarModal',
    emits: ['cerrar', 'cancelado'],

    props: {
      evento: { type: Object, required: true },
    },

    data() {
      return {
        motivo: '',
        procesando: false,
        error: null,
        errorMotivo: null,
      }
    },

    methods: {
      async confirmar() {
        this.error = null
        this.errorMotivo = null

        if (!this.motivo.trim()) {
          this.errorMotivo = 'El motivo de cancelación es obligatorio.'
          return
        }

        this.procesando = true
        try {
          await useEventosStore().cancelar(this.evento.id, this.motivo.trim())
          this.$emit('cancelado')
        } catch (e) {
          this.error = e.response?.data?.detail || 'Error al cancelar el evento'
        } finally {
          this.procesando = false
        }
      },
    },
  }
</script>
