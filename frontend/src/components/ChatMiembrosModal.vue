<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-wide">
      <div class="modal-header">
        <h3>Miembros — {{ chat.nombre }}</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <!-- Solicitudes pendientes (solo admin) -->
        <div v-if="esAdminChat && solicitudesPendientes.length" class="seccion-chat">
          <h4>Solicitudes pendientes ({{ solicitudesPendientes.length }})</h4>
          <ChatSolicitudesTable
            :solicitudes="solicitudesPendientes"
            :procesando="procesando"
            @resolver="resolver"
          />
        </div>

        <!-- Miembros activos -->
        <div class="seccion-chat">
          <h4>Miembros activos</h4>
          <p v-if="cargando" class="mensaje">Cargando...</p>
          <ChatMiembrosTable
            v-if="!cargando"
            :miembros="store.miembros"
            :es-admin-chat="esAdminChat"
            :procesando="procesando"
            @promover="promover"
            @degradar="degradar"
            @dar-baja="darBaja"
          />
        </div>

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
  import { useUsuariosStore } from '@/stores/usuarios'
  import ChatSolicitudesTable from '@/components/ChatSolicitudesTable.vue'
  import ChatMiembrosTable from '@/components/ChatMiembrosTable.vue'

  export default {
    name: 'ChatMiembrosModal',
    components: { ChatSolicitudesTable, ChatMiembrosTable },
    emits: ['cerrar'],

    props: {
      chat: { type: Object, required: true },
      esAdminChat: { type: Boolean, default: false },
    },

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
      usuarioActualId() {
        return useUsuariosStore().usuario?.id
      },
      solicitudesPendientes() {
        return this.store.solicitudes.filter((s) => s.estado === 'pendiente')
      },
    },

    async created() {
      this.cargando = true
      try {
        const chatId = this.chat.chat_id || this.chat.id
        await this.store.cargarMiembros(chatId)
        if (this.esAdminChat) {
          await this.store.cargarSolicitudes(chatId)
        }
      } finally {
        this.cargando = false
      }
    },

    methods: {
      chatId() {
        return this.chat.chat_id || this.chat.id
      },

      async resolver(solicitud, aceptar) {
        this.procesando = solicitud.id
        this.error = null
        try {
          await this.store.resolverSolicitud(this.chatId(), solicitud.id, aceptar)
          if (aceptar) await this.store.cargarMiembros(this.chatId())
          this.mostrarExito(aceptar ? 'Solicitud aceptada.' : 'Solicitud rechazada.')
        } catch {
          this.error = 'Error al resolver la solicitud.'
        } finally {
          this.procesando = null
        }
      },

      async promover(miembro) {
        this.procesando = miembro.id
        this.error = null
        try {
          await this.store.cambiarRol(this.chatId(), miembro.id, 'administrador')
          this.mostrarExito(`${miembro.nombre_usuario} es ahora administrador.`)
        } catch {
          this.error = 'Error al cambiar el rol.'
        } finally {
          this.procesando = null
        }
      },

      async degradar(miembro) {
        this.procesando = miembro.id
        this.error = null
        try {
          await this.store.cambiarRol(this.chatId(), miembro.id, 'miembro')
          this.mostrarExito(`${miembro.nombre_usuario} es ahora miembro.`)
        } catch {
          this.error = 'Error al cambiar el rol.'
        } finally {
          this.procesando = null
        }
      },

      async darBaja(miembro) {
        this.error = null
        if (!confirm(`¿Dar de baja a ${miembro.nombre_usuario}?`)) return
        this.procesando = miembro.id
        try {
          await this.store.darBajaMiembro(this.chatId(), miembro.id)
          this.mostrarExito(`${miembro.nombre_usuario} ha causado baja del chat.`)
        } catch {
          this.error = 'Error al dar de baja al miembro.'
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
