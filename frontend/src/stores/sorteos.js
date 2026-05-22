import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/services/api'

export const useSorteosStore  = defineStore('sorteos', () => {
  const sorteos         = ref([])
  const inscripciones   = ref([])
  const cargando        = ref(false)
  const error           = ref(null)

  const inscripcionesActivas = computed(() =>
    inscripciones.value.filter(i => i.estado === 'activa')
  )

  const idsSociosInscritos = computed(() =>
    inscripcionesActivas.value.map(i => i.socio_id)
  )

  async function cargar() {
    cargando.value = true
    error.value = null 
    try {
      const { data } = await api.get('/sorteos')
      sorteos.value = data
    } catch (err) {
      error.value = err.response?.data?.message || 'Error al cargar sorteos'
    } finally {
      cargando.value = false
    }
  }

  async function crear(datos) {
    const { data } = await api.post('/sorteos', datos)
    sorteos.value.push(data)
    return data
  }

  async function editar(id, datos) {
    const { data } = await api.put(`/sorteos/${id}`, datos)
    const idx = sorteos.value.findIndex(s => s.id === id)
    if (idx !== -1) sorteos.value[idx] = data
    return data
  }

  async function cancelar(id, motivo_cancelacion) {
    const { data } = await api.patch(`/sorteos/${id}/cancelar`, { motivo_cancelacion })
    const idx = sorteos.value.findIndex(s => s.id === id)
    if (idx !== -1) sorteos.value[idx] = data
    return data
  }

  async function resolver(id) {
    const { data } = await api.patch(`/sorteos/${id}/resolver`)
    const idx = sorteos.value.findIndex(s => s.id === id)
    if (idx !== -1) sorteos.value[idx] = data
    return data
  }

  async function cargarInscripciones(sorteoId) {
    const { data } = await api.get(`/sorteos/${sorteoId}/inscripciones`)
    inscripciones.value = data
  }

  async function inscribir(sorteoId, socioId) {
    const { data } = await api.post(`/sorteos/${sorteoId}/inscripciones`, { socio_id: socioId })
    inscripciones.value.push(data)
    // Actualizar contador de inscritos en el sorteo
    const idx = sorteos.value.findIndex(s => s.id === sorteoId)
    if (idx !== -1) sorteos.value[idx].inscritos++
    return data
  }

  async function cancelarInscripcion(sorteoId, inscripcionId) {
    const { data } = await api.patch(`/sorteos/${sorteoId}/inscripciones/${inscripcionId}`)
    const idx = inscripciones.value.findIndex(i => i.id === inscripcionId)
    if (idx !== -1) inscripciones.value[idx] = data
    // Actualizar contador de inscritos en el sorteo
    const idxSorteo = sorteos.value.findIndex(s => s.id === sorteoId)
    if (idxSorteo !== -1) sorteos.value[idxSorteo].inscritos--
    return data
  }

  function limpiar() {
    sorteos.value       = []
    inscripciones.value = []
    error.value         = null
  }

  return { sorteos, inscripciones, cargando, error, inscripcionesActivas, idsSociosInscritos, 
            cargar, crear, editar, cancelar , resolver, cargarInscripciones, inscribir, cancelarInscripcion, limpiar }
})