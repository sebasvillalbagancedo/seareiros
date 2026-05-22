<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-sm">
      <div class="modal-header">
        <h3>Resolver sorteo</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <p>
          ¿Confirma que desea resolver el sorteo <strong>"{{ sorteo.nombre }}"</strong>?
        </p>
        <p>
          Se seleccionarán <strong>{{ sorteo.numero_premios }}</strong>
          ganador(es) aleatoriamente entre los
          <strong>{{ sorteo.inscritos }}</strong> inscritos.
        </p>
        <p>Esta acción no se puede deshacer.</p>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Volver</button>
        <button class="btn-primario btn-baja-modal" :disabled="procesando" @click="confirmar">
          {{ procesando ? 'Resolviendo...' : 'Confirmar resolución' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
  import { useSorteosStore } from '@/stores/sorteos'

  export default {
    name: 'SorteoResolverModal',
    emits: ['cerrar', 'resuelto'],

    props: {
      sorteo: {
        type: Object,
        required: true,
      },
    },

    data() {
      return {
        procesando: false,
        error: null,
      }
    },
    methods: {
      async confirmar() {
        this.procesando = true
        this.error = null
        try {
          await useSorteosStore().resolver(this.sorteo.id)
          this.$emit('resuelto')
        } catch (err) {
          this.error = err.response?.data?.detail || 'Error al resolver el sorteo'
        } finally {
          this.procesando = false
        }
      },
    },
  }
</script>
