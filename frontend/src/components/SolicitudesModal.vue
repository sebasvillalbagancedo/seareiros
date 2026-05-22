<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-wide">
      <div class="modal-header">
        <h3>Solicitudes pendientes</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <p v-if="cargando" class="mensaje">Cargando...</p>

        <template v-else-if="chatsConSolicitudes.length">
          <div v-for="grupo in chatsConSolicitudes" :key="grupo.chat_id" class="seccion-chat">
            <h4>{{ grupo.nombre }}</h4>
            <ChatSolicitudesTable
              :solicitudes="grupo.solicitudes"
              :procesando="procesando"
              @resolver="(s, aceptar) => resolver(grupo.chat_id, s, aceptar)"
            />
          </div>
        </template>

        <p v-else class="mensaje">No hay solicitudes pendientes.</p>

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
  import api from '@/services/api'
  import ChatSolicitudesTable from '@/components/ChatSolicitudesTable.vue'

  export default {
    name: 'SolicitudesModal',
    components: { ChatSolicitudesTable },
    emits: ['cerrar', 'resuelta'],

    data() {
      return {
        cargando: true,
        procesando: null,
        error: null,
        mensajeExito: null,
        chatsConSolicitudes: [],
      }
    },

    async created() {
      await this.cargarTodas()
    },

    methods: {
      async cargarTodas() {
        this.cargando = true
        try {
          // Obtener los chats del historial que tienen solicitudes pendientes
          const chats = useChatStore().historialChats.filter((c) => c.solicitudes_pendientes > 0)

          const resultados = await Promise.all(
            chats.map(async (c) => {
              const { data } = await api.get(`/chat/chats/${c.chat_id}/solicitudes`)
              return { chat_id: c.chat_id, nombre: c.nombre, solicitudes: data }
            }),
          )
          this.chatsConSolicitudes = resultados.filter((g) => g.solicitudes.length > 0)
        } catch {
          this.error = 'Error al cargar las solicitudes.'
        } finally {
          this.cargando = false
        }
      },

      async resolver(chatId, solicitud, aceptar) {
        this.procesando = solicitud.id
        this.error = null
        try {
          await useChatStore().resolverSolicitud(chatId, solicitud.id, aceptar)
          this.mostrarExito(aceptar ? 'Solicitud aceptada.' : 'Solicitud rechazada.')
          this.$emit('resuelta')
          // Retirar la solicitud resuelta de la vista
          for (const grupo of this.chatsConSolicitudes) {
            if (grupo.chat_id === chatId) {
              grupo.solicitudes = grupo.solicitudes.filter((s) => s.id !== solicitud.id)
            }
          }
          this.chatsConSolicitudes = this.chatsConSolicitudes.filter(
            (g) => g.solicitudes.length > 0,
          )
        } catch {
          this.error = 'Error al resolver la solicitud.'
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
