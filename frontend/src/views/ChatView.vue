<template>
  <div class="chat-layout">
    <!-- Panel izquierdo — historial -->
    <div class="chat-sidebar">
      <!-- Acciones -->
      <div class="chat-sidebar-header">
        <button v-if="esAdmin" class="chat-nav-btn" @click="modalChatVisible = true">
          <Plus :size="16" />
          <span>Nuevo chat</span>
        </button>
        <button class="chat-nav-btn" @click="modalConversacionVisible = true">
          <MessageSquare :size="16" />
          <span>Nueva conversación</span>
        </button>
        <button
          v-if="store.totalInvitacionesPendientes"
          class="chat-nav-btn"
          @click="modalInvitacionesVisible = true"
        >
          <Bell :size="16" />
          <span>Invitaciones</span>
          <span class="badge-noLeidos">{{ store.totalInvitacionesPendientes }}</span>
        </button>
        <button
          v-if="store.totalSolicitudesPendientes"
          class="chat-nav-btn"
          @click="modalSolicitudesVisible = true"
        >
          <Bell :size="16" />
          <span>Solicitudes</span>
          <span class="badge-noLeidos">{{ store.totalSolicitudesPendientes }}</span>
        </button>
      </div>

      <!-- Pestañas -->
      <div class="chat-tabs">
        <button
          class="chat-tab"
          :class="{ 'chat-tab-activa': tabActiva === 'historial' }"
          @click="tabActiva = 'historial'"
        >
          Mis conversaciones
        </button>
        <button
          class="chat-tab"
          :class="{ 'chat-tab-activa': tabActiva === 'explorar' }"
          @click="((tabActiva = 'explorar'), cargarChatsVisibles())"
        >
          Explorar chats
        </button>
      </div>

      <!-- TAB: Mis conversaciones -->
      <template v-if="tabActiva === 'historial'">
        <div class="chat-sidebar-filtro">
          <input
            v-model="filtroTexto"
            type="text"
            placeholder="Buscar conversación..."
            class="input-busqueda"
          />
        </div>
        <div class="chat-lista">
          <div
            v-for="entrada in historialFiltrado"
            :key="`${entrada._tipo}-${entrada._clave}`"
            class="chat-entrada"
            :class="{ activa: esEntradaActiva(entrada) }"
            @click="abrirEntrada(entrada)"
          >
            <div class="chat-entrada-nombre">
              {{ entrada._nombre }}
              <span v-if="entrada._subtitulo" class="badge-modalidad">
                {{ etiquetaModalidad(entrada._subtitulo) }}
              </span>
              <span v-else class="badge-modalidad badge-directo">Directo</span>
            </div>
            <div class="chat-entrada-preview">
              {{ entrada.ultimo_mensaje || 'Sin mensajes' }}
            </div>
            <span v-if="entrada.no_leidos" class="badge-noLeidos">
              {{ entrada.no_leidos }}
            </span>
          </div>
          <p v-if="store.cargando" class="chat-vacio">Cargando...</p>
          <p v-else-if="!historialFiltrado.length && filtroTexto" class="chat-vacio">
            Sin resultados para "{{ filtroTexto }}".
          </p>
          <p v-else-if="!historialFiltrado.length" class="chat-vacio">
            No tienes conversaciones aún.
          </p>
        </div>
      </template>

      <!-- TAB: Explorar chats -->
      <template v-else>
        <div class="chat-sidebar-filtro">
          <input
            v-model="filtroExplorar"
            type="text"
            placeholder="Buscar chat..."
            class="input-busqueda"
          />
        </div>
        <div class="chat-lista">
          <div
            v-for="chat in chatsVisiblesFiltrados"
            :key="chat.chat_id || chat.id"
            class="chat-entrada"
            :class="{ activa: esEntradaActivaExplorar(chat) }"
            @click="abrirChatVisible(chat)"
          >
            <div class="chat-entrada-nombre">
              {{ chat.nombre }}
              <span class="badge-modalidad">{{ etiquetaModalidad(chat.modalidad) }}</span>
              <span
                v-if="chat.tipo_acceso === 'restringido'"
                class="badge-modalidad badge-restringido"
                >🔒</span
              >
            </div>
            <div class="chat-entrada-preview">{{ chat.num_miembros }} miembro(s)</div>
          </div>
          <p v-if="cargandoVisibles" class="chat-vacio">Cargando...</p>
          <p v-else-if="!chatsVisiblesFiltrados.length && filtroExplorar" class="chat-vacio">
            Sin resultados para "{{ filtroExplorar }}".
          </p>
          <p v-else-if="!chatsVisiblesFiltrados.length" class="chat-vacio">
            No hay chats disponibles.
          </p>
        </div>
      </template>
    </div>

    <!-- Panel derecho — conversación activa -->
    <div class="chat-contenido">
      <!-- Sin conversación activa -->
      <div v-if="!store.conversacionActiva" class="chat-bienvenida">
        <p>Selecciona una conversación o inicia una nueva.</p>
      </div>

      <!-- Conversación activa -->
      <template v-else>
        <!-- Cabecera -->
        <div class="chat-cabecera">
          <div class="chat-cabecera-info">
            <strong>{{ nombreConversacion }}</strong>
            <span v-if="store.tipoActivo === 'chat'" class="chat-modalidad">
              {{ etiquetaModalidad(store.conversacionActiva.modalidad) }}
            </span>
          </div>
          <div class="chat-cabecera-acciones">
            <!-- Unirse / Solicitar acceso -->
            <button
              v-if="store.tipoActivo === 'chat' && puedeUnirse"
              class="btn-accion"
              :disabled="procesando"
              @click="enviarSolicitud"
            >
              {{ chatEsLibre ? 'Unirse' : 'Solicitar acceso' }}
            </button>
            <!-- Solicitud pendiente -->
            <span
              v-if="store.tipoActivo === 'chat' && tieneSolicitudPendiente"
              class="badge badge-pendiente"
            >
              Solicitud pendiente
            </span>
            <!-- Invitar usuario (admin del chat) -->
            <button
              v-if="store.tipoActivo === 'chat' && soyAdminChat"
              class="btn-accion"
              @click="modalInvitarVisible = true"
            >
              Invitar
            </button>
            <!-- Gestión de miembros (admin del chat) -->
            <button
              v-if="store.tipoActivo === 'chat' && soyAdminChat"
              class="btn-accion"
              @click="modalMiembrosVisible = true"
            >
              Miembros
            </button>
            <!-- Editar chat (admin del chat) -->
            <button
              v-if="store.tipoActivo === 'chat' && soyAdminChat"
              class="btn-accion"
              @click="modalEditarChatVisible = true"
            >
              Editar
            </button>
          </div>
        </div>

        <!-- Lista de mensajes -->
        <div class="chat-mensajes" ref="listaMensajes">
          <div
            v-for="m in store.mensajes"
            :key="m.id"
            class="chat-mensaje"
            :class="{ propio: m.usuario_envio === usuarioActualId }"
          >
            <div class="chat-mensaje-autor">
              {{ m.nombre_remitente }} {{ m.apellidos_remitente }}
            </div>
            <div class="chat-mensaje-burbuja">{{ m.contenido }}</div>
            <div class="chat-mensaje-hora">{{ formatHora(m.fecha_envio) }}</div>
          </div>
          <p
            v-if="!store.mensajes.length && store.conversacionActiva.es_miembro"
            class="chat-vacio"
          >
            No hay mensajes aún. ¡Sé el primero en escribir!
          </p>
        </div>

        <!-- Campo de entrada -->
        <div v-if="puedeEscribir" class="chat-entrada-mensaje">
          <input
            v-model="mensajeRedactado"
            type="text"
            placeholder="Escribe un mensaje..."
            @keyup.enter="enviarMensaje"
          />
          <button
            class="btn-primario"
            :disabled="!mensajeRedactado.trim() || enviando"
            @click="enviarMensaje"
          >
            {{ enviando ? '...' : 'Enviar' }}
          </button>
        </div>
        <p
          v-else-if="store.tipoActivo === 'chat' && !store.conversacionActiva.es_miembro"
          class="chat-sin-permiso"
        >
          Solo los miembros del chat tienen acceso a los mensajes.
        </p>
        <p
          v-else-if="store.tipoActivo === 'chat' && store.conversacionActiva.es_miembro"
          class="chat-sin-permiso"
        >
          Solo los administradores pueden publicar en este canal.
        </p>
      </template>
    </div>

    <!-- Modal crear chat -->
    <ChatFormModal
      v-if="modalChatVisible"
      modo="crear"
      @cerrar="modalChatVisible = false"
      @guardado="onChatCreado"
    />

    <!-- Modal editar chat -->
    <ChatFormModal
      v-if="modalEditarChatVisible"
      modo="editar"
      :chat="store.conversacionActiva"
      @cerrar="modalEditarChatVisible = false"
      @guardado="modalEditarChatVisible = false"
    />

    <!-- Modal nueva conversación directa -->
    <NuevaConversacionModal
      v-if="modalConversacionVisible"
      @cerrar="modalConversacionVisible = false"
      @seleccionada="onConversacionSeleccionada"
    />

    <!-- Modal miembros -->
    <ChatMiembrosModal
      v-if="modalMiembrosVisible"
      :chat="store.conversacionActiva"
      :es-admin-chat="soyAdminChat"
      @cerrar="modalMiembrosVisible = false"
    />

    <!-- Modal invitar usuario -->
    <ChatInvitarModal
      v-if="modalInvitarVisible"
      :chat="store.conversacionActiva"
      @cerrar="modalInvitarVisible = false"
    />

    <!-- Modal invitaciones recibidas -->
    <InvitacionesModal v-if="modalInvitacionesVisible" @cerrar="modalInvitacionesVisible = false" />

    <!-- Modal solicitudes pendientes (admin) -->
    <SolicitudesModal
      v-if="modalSolicitudesVisible"
      @cerrar="modalSolicitudesVisible = false"
      @resuelta="onSolicitudResuelta"
    />

    <p v-if="errorEnvio" class="error chat-error-envio">{{ errorEnvio }}</p>
  </div>
</template>

<script>
  import { useChatStore } from '@/stores/chat'
  import { useUsuariosStore } from '@/stores/usuarios'
  import { Plus, MessageSquare, Bell } from 'lucide-vue-next'
  import { formatHora } from '@/utils/fecha'
  import api from '@/services/api'
  import ChatFormModal from '@/components/ChatFormModal.vue'
  import ChatMiembrosModal from '@/components/ChatMiembrosModal.vue'
  import ChatInvitarModal from '@/components/ChatInvitarModal.vue'
  import InvitacionesModal from '@/components/InvitacionesModal.vue'
  import SolicitudesModal from '@/components/SolicitudesModal.vue'
  import NuevaConversacionModal from '@/components/NuevaConversacionModal.vue'

  export default {
    name: 'ChatView',
    components: {
      ChatFormModal,
      ChatMiembrosModal,
      ChatInvitarModal,
      InvitacionesModal,
      SolicitudesModal,
      NuevaConversacionModal,
      Plus,
      MessageSquare,
      Bell,
    },

    data() {
      return {
        tabActiva: 'historial',
        filtroTexto: '',
        filtroExplorar: '',
        chatsVisibles: [],
        cargandoVisibles: false,
        mensajeRedactado: '',
        enviando: false,
        procesando: false,
        errorEnvio: null,
        modalChatVisible: false,
        modalEditarChatVisible: false,
        modalConversacionVisible: false,
        modalMiembrosVisible: false,
        modalInvitarVisible: false,
        modalInvitacionesVisible: false,
        modalSolicitudesVisible: false,
      }
    },

    computed: {
      store() {
        return useChatStore()
      },
      esAdmin() {
        return useUsuariosStore().usuario?.rol === 'administrador'
      },
      usuarioActualId() {
        return useUsuariosStore().usuario?.id
      },

      historialFiltrado() {
        const texto = this.filtroTexto.toLowerCase().trim()
        if (!texto) return this.store.historialUnificado
        return this.store.historialUnificado.filter((e) => e._nombre.toLowerCase().includes(texto))
      },

      chatsVisiblesFiltrados() {
        const texto = this.filtroExplorar.toLowerCase().trim()
        if (!texto) return this.chatsVisibles
        return this.chatsVisibles.filter((c) => c.nombre.toLowerCase().includes(texto))
      },

      nombreConversacion() {
        if (!this.store.conversacionActiva) return ''
        if (this.store.tipoActivo === 'chat') return this.store.conversacionActiva.nombre
        const c = this.store.conversacionActiva
        return `${c.nombre} ${c.apellidos}`
      },

      soyAdminChat() {
        if (this.store.tipoActivo !== 'chat') return false
        return this.store.conversacionActiva?.mi_rol === 'administrador'
      },

      tieneSolicitudPendiente() {
        if (this.store.tipoActivo !== 'chat') return false
        return this.store.conversacionActiva?.solicitud_estado === 'pendiente'
      },

      puedeUnirse() {
        if (this.store.tipoActivo !== 'chat') return false
        const c = this.store.conversacionActiva
        return !c?.es_miembro && c?.solicitud_estado !== 'pendiente'
      },

      chatEsLibre() {
        return this.store.conversacionActiva?.tipo_acceso === 'libre'
      },

      puedeEscribir() {
        if (!this.store.conversacionActiva) return false
        if (this.store.tipoActivo === 'directo') return true
        const c = this.store.conversacionActiva
        if (!c.es_miembro) return false
        if (c.modalidad === 'canal') return c.mi_rol === 'administrador'
        return true
      },
    },

    async created() {
      await Promise.all([useChatStore().cargarHistorial(), useChatStore().cargarInvitaciones()])
    },

    updated() {
      this.scrollAlFinal()
    },

    methods: {
      formatHora,

      etiquetaModalidad(modalidad) {
        return modalidad === 'canal' ? 'Canal' : 'Chat'
      },

      esEntradaActiva(entrada) {
        if (entrada._tipo === 'chat') {
          return (
            this.store.tipoActivo === 'chat' &&
            this.store.conversacionActiva?.chat_id === entrada.chat_id
          )
        }
        return (
          this.store.tipoActivo === 'directo' &&
          this.store.conversacionActiva?.usuario_id === entrada.usuario_id
        )
      },

      async abrirEntrada(entrada) {
        if (entrada._tipo === 'chat') {
          await this.store.abrirChat(entrada)
        } else {
          await this.store.abrirDirecto(entrada)
        }
      },

      esEntradaActivaExplorar(chat) {
        return (
          this.store.tipoActivo === 'chat' &&
          (this.store.conversacionActiva?.chat_id === chat.chat_id ||
            this.store.conversacionActiva?.id === chat.id)
        )
      },

      async cargarChatsVisibles() {
        if (this.cargandoVisibles) return
        this.cargandoVisibles = true
        try {
          const { data } = await api.get('/chat/chats')
          this.chatsVisibles = data
        } catch {
          this.chatsVisibles = []
        } finally {
          this.cargandoVisibles = false
        }
      },

      async abrirChatVisible(chat) {
        const entrada = { ...chat, chat_id: chat.chat_id || chat.id }
        await this.store.abrirChat(entrada)
      },

      scrollAlFinal() {
        const lista = this.$refs.listaMensajes
        if (lista) lista.scrollTop = lista.scrollHeight
      },

      async enviarMensaje() {
        const contenido = this.mensajeRedactado.trim()
        if (!contenido) return
        this.enviando = true
        this.errorEnvio = null
        try {
          if (this.store.tipoActivo === 'chat') {
            await this.store.enviarMensajeChat(this.store.conversacionActiva.chat_id, contenido)
          } else {
            await this.store.enviarMensajeDirecto(
              this.store.conversacionActiva.usuario_id,
              contenido,
            )
          }
          this.mensajeRedactado = ''
        } catch (e) {
          this.errorEnvio = e.response?.data?.detail || 'Error al enviar el mensaje.'
        } finally {
          this.enviando = false
        }
      },

      async enviarSolicitud() {
        this.procesando = true
        try {
          await this.store.enviarSolicitud(this.store.conversacionActiva.chat_id)
          // Recargar detalle del chat para actualizar solicitud_estado y es_miembro
          await this.store.abrirChat(this.store.conversacionActiva)
        } catch (e) {
          this.errorEnvio = e.response?.data?.detail || 'Error al procesar la solicitud.'
        } finally {
          this.procesando = false
        }
      },

      onChatCreado() {
        this.modalChatVisible = false
      },

      async onSolicitudResuelta() {
        await useChatStore().cargarHistorial()
      },

      async onConversacionSeleccionada(usuario) {
        this.modalConversacionVisible = false
        const existente = this.store.historialDirectos.find((d) => d.usuario_id === usuario.id)
        if (existente) {
          await this.store.abrirDirecto(existente)
        } else {
          const nueva = {
            usuario_id: usuario.id,
            nombre: usuario.nombre,
            apellidos: usuario.apellidos,
            codigo_usuario: usuario.codigo_usuario,
            ultimo_mensaje: null,
            fecha_ultimo: null,
            no_leidos: 0,
          }
          this.store.historialDirectos.unshift(nueva)
          await this.store.abrirDirecto(nueva)
        }
      },
    },
  }
</script>
