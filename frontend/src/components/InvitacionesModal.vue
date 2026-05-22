<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-wide">
      <div class="modal-header">
        <h3>Invitaciones pendientes</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <p v-if="cargando" class="mensaje">Cargando invitaciones...</p>

        <table v-if="!cargando && store.invitaciones.length">
          <thead>
            <tr>
              <th>Chat</th>
              <th>Invitado por</th>
              <th>Fecha</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in store.invitaciones" :key="inv.id">
              <td>{{ inv.nombre_chat }}</td>
              <td>{{ inv.nombre_invitador }} {{ inv.apellidos_invitador }}</td>
              <td>{{ formatFecha(inv.fecha_invitacion) }}</td>
              <td class="acciones">
                <button
                  class="btn-accion"
                  :disabled="procesando === inv.id"
                  @click="resolver(inv, true)"
                >
                  {{ procesando === inv.id ? '...' : 'Aceptar' }}
                </button>
                <button
                  class="btn-accion btn-baja"
                  :disabled="procesando === inv.id"
                  @click="resolver(inv, false)"
                >
                  {{ procesando === inv.id ? '...' : 'Rechazar' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <p v-if="!cargando && !store.invitaciones.length" class="mensaje">
          No tienes invitaciones pendientes.
        </p>

        <p v-if="mensajeExito" class="exito">{{ mensajeExito }}</p>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Cerrar</button>
      </div>
    </div>
  </div>
</template>

<script>
  import { useChatStore } from '@/stores/chat'
  import { formatFecha } from '@/utils/fecha'

  export default {
    name: 'InvitacionesModal',
    emits: ['cerrar'],

    data() {
      return {
        cargando: false,
        procesando: null,
        error: null,
        mensajeExito: null,
      }
    },

    computed: {
      store() {
        return useChatStore()
      },
    },

    async created() {
      this.cargando = true
      try {
        await useChatStore().cargarInvitaciones()
      } finally {
        this.cargando = false
      }
    },

    methods: {
      formatFecha,

      async resolver(invitacion, aceptar) {
        this.procesando = invitacion.id
        this.error = null
        try {
          await this.store.resolverInvitacion(invitacion.id, aceptar)
          this.mostrarExito(
            aceptar
              ? `Te has unido al chat "${invitacion.nombre_chat}".`
              : `Invitación al chat "${invitacion.nombre_chat}" rechazada.`,
          )
          // Cerrar si ya no quedan invitaciones
          if (!this.store.invitaciones.length) {
            setTimeout(() => this.$emit('cerrar'), 1500)
          }
        } catch (e) {
          this.error = e.response?.data?.detail || 'Error al procesar la invitación.'
        } finally {
          this.procesando = null
        }
      },

      mostrarExito(msg) {
        this.mensajeExito = msg
        setTimeout(() => {
          this.mensajeExito = null
        }, 3000)
      },
    },
  }
</script>
