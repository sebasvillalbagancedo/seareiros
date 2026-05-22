import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/services/api'

export const useChatStore = defineStore('chat', () => {
  const historialDirectos = ref([])
  const historialChats    = ref([])
  const mensajes          = ref([])
  const miembros          = ref([])
  const solicitudes       = ref([])
  const invitaciones      = ref([])
  const cargando          = ref(false)
  const error             = ref(null)
  
  // Conversación activa
  const conversacionActiva = ref(null)
 
  // tipo: 'directo' | 'chat'
  const tipoActivo         = ref(null)
  
  // Total de mensajes no leídos en el historial
  const totalNoLeidos     = computed(() =>
    historialDirectos.value.reduce((sum, d) => sum + d.no_leidos, 0)
    + historialChats.value.reduce((sum, g) => sum + g.no_leidos, 0))
 
  // Total de invitaciones pendientes  
  const totalInvitacionesPendientes = computed(() => invitaciones.value.length)

  // Total de solicitudes pendientes en todos los chats donde el usuario es admin
  const totalSolicitudesPendientes = computed(() =>
    historialChats.value.reduce((sum, g) => sum + (g.solicitudes_pendientes || 0), 0)
  )

  // Historial unificado ordenado por fecha_ultimo descendente
  const historialUnificado = computed(() => {
    const directos = historialDirectos.value.map(d => ({
      ...d,
      _tipo:      'directo',
      _clave:     d.usuario_id,
      _nombre:    `${d.nombre} ${d.apellidos}`,
      _subtitulo: null,
    }))
    const chats = historialChats.value.map(g => ({
      ...g,
      _tipo:      'chat',
      _clave:     g.chat_id,
      _nombre:    g.nombre,
      _subtitulo: g.modalidad,
    }))
    return [...directos, ...chats].sort((a, b) => {
      const fa = a.fecha_ultimo ? new Date(a.fecha_ultimo) : new Date(0)
      const fb = b.fecha_ultimo ? new Date(b.fecha_ultimo) : new Date(0)
      return fb - fa
    })
  })
 
  // IDs de usuarios con los que ya hay conversación directa
  const idsConversacionDirecta = computed(() =>
    historialDirectos.value.map(d => d.usuario_id)
  )

  // ── Historial ─────────────────────────────────────────────────
  async function cargarHistorial() {
    cargando.value = true
    error.value    = null
    try {
      const [directos, chatsRes] = await Promise.all([
        api.get('/chat/historial/directos'),
        api.get('/chat/historial/chats'),
      ])
      historialDirectos.value = directos.data
      historialChats.value   = chatsRes.data
    } catch {
      error.value = 'No se pudo cargar el historial.'
    } finally {
      cargando.value = false
    }
  }

  // ── Chats ────────────────────────────────────────────────────
  async function crearChat(datos) {
    const { data } = await api.post('/chat/chats', datos)
    historialChats.value.unshift({
      chat_id:        data.id,
      nombre:         data.nombre,
      modalidad:      data.modalidad,
      ultimo_mensaje: null,
      fecha_ultimo:   null,
      no_leidos:      0,
    })
    return data
  }

  async function editarChat(chatId, datos) {
    const { data } = await api.put(`/chat/chats/${chatId}`, datos)
    const idx = historialChats.value.findIndex(g => g.chat_id === chatId)
    if (idx !== -1) historialChats.value[idx].nombre = data.nombre
    return data
  }
  
  // ── Miembros ─────────────────────────────────────────────────  
  async function cargarMiembros(chatId) {
    const { data } = await api.get(`/chat/chats/${chatId}/miembros`)
    miembros.value = data
  }
 
  async function cambiarRol(chatId, miembroId, rol) {
    const { data } = await api.patch(
      `/chat/chats/${chatId}/miembros/${miembroId}/rol`,
      { rol }
    )
    const idx = miembros.value.findIndex(m => m.id === miembroId)
    if (idx !== -1) miembros.value[idx] = data
    return data
  }
 
  async function darBajaMiembro(chatId, miembroId) {
    const { data } = await api.patch(
      `/chat/chats/${chatId}/miembros/${miembroId}/baja`
    )
    miembros.value = miembros.value.filter(m => m.id !== miembroId)
    return data
  }

  // ── Solicitudes ───────────────────────────────────────────────
  async function cargarSolicitudes(chatId) {
    const { data } = await api.get(`/chat/chats/${chatId}/solicitudes`)
    solicitudes.value = data
  }
 
  async function enviarSolicitud(chatId) {
    const { data } = await api.post(`/chat/chats/${chatId}/solicitudes`)
    return data
  }
 
  async function resolverSolicitud(chatId, solicitudId, aceptar) {
    const { data } = await api.patch(
      `/chat/chats/${chatId}/solicitudes/${solicitudId}?aceptar=${aceptar}`
    )
    const idx = solicitudes.value.findIndex(s => s.id === solicitudId)
    if (idx !== -1) solicitudes.value[idx] = data
    return data
  }

   // ── Invitaciones ──────────────────────────────────────────────
  async function cargarInvitaciones() {
    const { data } = await api.get('/chat/invitaciones')
    invitaciones.value = data
  }
 
  async function enviarInvitacion(chatId, usuarioDestinatarioId) {
    const { data } = await api.post(`/chat/chats/${chatId}/invitaciones`, {
      usuario_destinatario: usuarioDestinatarioId,
    })
    return data
  }
 
  async function resolverInvitacion(invitacionId, aceptar) {
    const { data } = await api.patch(
      `/chat/invitaciones/${invitacionId}?aceptar=${aceptar}`
    )
    // Si se acepta, añadir al historial de chats
    if (aceptar) {
      await cargarHistorial()
    }
    // Eliminar de la lista de pendientes
    invitaciones.value = invitaciones.value.filter(i => i.id !== invitacionId)
    return data
  }

  // ── Mensajes ──────────────────────────────────────────────────
  async function cargarMensajesChat(chatId) {
    const { data } = await api.get(`/chat/chats/${chatId}/mensajes`)
    mensajes.value = data
    // Marcar como leídos en el historial
    const idx = historialChats.value.findIndex(g => g.chat_id === chatId)
    if (idx !== -1) historialChats.value[idx].no_leidos = 0
  }

  async function cargarMensajesDirectos(usuarioId) {
    const { data } = await api.get(`/chat/directos/${usuarioId}`)
    mensajes.value = data
    // Marcar como leídos en el historial
    const idx = historialDirectos.value.findIndex(d => d.usuario_id === usuarioId)
    if (idx !== -1) historialDirectos.value[idx].no_leidos = 0
  }

  async function enviarMensajeChat(chatId, contenido)  {
    const { data } = await api.post(`/chat/chats/${chatId}/mensajes`, { contenido })
    mensajes.value.push(data)
    // Actualizar último mensaje en el historial
    const idx = historialChats.value.findIndex(g => g.chat_id === chatId)
    if (idx !== -1) {
      historialChats.value[idx].ultimo_mensaje = contenido
      historialChats.value[idx].fecha_ultimo   = data.fecha_envio
    }
    return data
  }

  async function enviarMensajeDirecto(usuarioDestinatarioId, contenido) {
    const { data } = await api.post('/chat/directos', {
      contenido,
      usuario_destinatario: usuarioDestinatarioId,
    })
    mensajes.value.push(data)
    // Actualizar o crear entrada en el historial
    const idx = historialDirectos.value.findIndex(
      d => d.usuario_id === usuarioDestinatarioId
    )
    if (idx !== -1) {
      historialDirectos.value[idx].ultimo_mensaje = contenido
      historialDirectos.value[idx].fecha_ultimo   = data.fecha_envio
    }
    return data
  }

  // ── Abrir conversación ────────────────────────────────────────
  async function abrirDirecto(entradaHistorial) {
    conversacionActiva.value = entradaHistorial
    tipoActivo.value         = 'directo'
    await cargarMensajesDirectos(entradaHistorial.usuario_id)
  }

  async function abrirChat(entradaHistorial) {
    conversacionActiva.value = entradaHistorial
    tipoActivo.value         = 'chat'
    // Cargar detalle completo del chat para tener mi_rol, es_miembro, modalidad...
    const { data } = await api.get(`/chat/chats/${entradaHistorial.chat_id}`)
    conversacionActiva.value = { ...entradaHistorial, ...data }
    // Solo cargar mensajes si el usuario es miembro activo del chat
    if (data.es_miembro) {
      await cargarMensajesChat(entradaHistorial.chat_id)
    } else {
      mensajes.value = []
    }
  }

  function limpiar() {
    historialDirectos.value  = []
    historialChats.value     = []
    mensajes.value           = []
    miembros.value           = []
    solicitudes.value        = []
    invitaciones.value       = []
    conversacionActiva.value = null
    tipoActivo.value         = null
    error.value              = null
  }

  return {
    historialDirectos, historialChats, mensajes,
    miembros, solicitudes, invitaciones,
    cargando, error, conversacionActiva, tipoActivo,
    totalNoLeidos, totalInvitacionesPendientes, totalSolicitudesPendientes,
    historialUnificado, idsConversacionDirecta,
    cargarHistorial, crearChat, editarChat,
    cargarMiembros, cambiarRol, darBajaMiembro,
    cargarSolicitudes, enviarSolicitud, resolverSolicitud,
    cargarInvitaciones, enviarInvitacion, resolverInvitacion,
    cargarMensajesChat, cargarMensajesDirectos,
    enviarMensajeChat, enviarMensajeDirecto,
    abrirDirecto, abrirChat, limpiar,
  }
})