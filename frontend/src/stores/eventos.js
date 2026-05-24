import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/services/api'

export const useEventosStore = defineStore('eventos', () => {
  const eventos = ref([])
  const historico = ref([])
  const inscripciones = ref([])
  const cargando = ref(false)
  const error = ref(null)

  const inscripcionesTodas = computed(() => inscripciones.value)

  const inscripcionesActivas = computed(() =>
    inscripciones.value.filter((i) => i.estado === 'pendiente' || i.estado === 'confirmada'),
  )

  const idsSociosInscritos = computed(() => inscripcionesActivas.value.map((i) => i.socio_id))

  async function cargar() {
    cargando.value = true
    error.value = null
    try {
      const { data } = await api.get('/eventos')
      eventos.value = data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Error al cargar eventos'
    } finally {
      cargando.value = false
    }
  }

  async function cargarHistorico() {
    cargando.value = true
    error.value = null
    try {
      const { data } = await api.get('/eventos/historico')
      historico.value = data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Error al cargar histórico de eventos'
    } finally {
      cargando.value = false
    }
  }

  async function crear(datos) {
    const { data } = await api.post('/eventos', datos)
    eventos.value.push(data)
    return data
  }

  async function editar(id, datos) {
    const { data } = await api.put(`/eventos/${id}`, datos)
    const idx = eventos.value.findIndex((e) => e.id === id)
    if (idx !== -1) eventos.value[idx] = data
    return data
  }

  async function cancelar(id, motivo_cancelacion) {
    const { data } = await api.patch(`/eventos/${id}/cancelar`, { motivo_cancelacion })
    const idx = eventos.value.findIndex((e) => e.id === id)
    if (idx !== -1) eventos.value[idx] = data
    return data
  }

  async function cargarInscripciones(eventoId) {
    const { data } = await api.get(`/eventos/${eventoId}/inscripciones`)
    inscripciones.value = data
  }

  async function inscribir(eventoId, socioId) {
    const { data } = await api.post(`/eventos/${eventoId}/inscripciones`, { socio_id: socioId })
    inscripciones.value.push(data)
    const idx = eventos.value.findIndex((e) => e.id === eventoId)
    if (idx !== -1) eventos.value[idx].inscritos++
    return data
  }

  async function gestionarInscripcion(eventoId, inscripcionId, estado) {
    const { data } = await api.patch(`/eventos/${eventoId}/inscripciones/${inscripcionId}`, {
      estado,
    })
    const idx = inscripciones.value.findIndex((i) => i.id === inscripcionId)
    if (idx !== -1) inscripciones.value[idx] = data
    return data
  }

  function limpiar() {
    eventos.value = []
    historico.value = []
    inscripciones.value = []
    error.value = null
  }

  return {
    eventos,
    historico,
    inscripciones,
    cargando,
    error,
    inscripcionesTodas,
    inscripcionesActivas,
    idsSociosInscritos,
    cargar,
    cargarHistorico,
    crear,
    editar,
    cancelar,
    cargarInscripciones,
    inscribir,
    gestionarInscripcion,
    limpiar,
  }
})
