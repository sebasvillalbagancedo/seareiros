import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useSociosStore = defineStore('socios', () => {
  const socios   = ref([])
  const cargando = ref(false)
  const error    = ref(null)

  async function cargar() {
    cargando.value = true
    error.value    = null
    try {
      const { data } = await api.get('/socios')
      socios.value = data
    } catch {
      error.value = 'No se pudieron cargar los socios.'
    } finally {
      cargando.value = false
    }
  }

  async function crear(datos) {
    const { data } = await api.post('/socios', datos)
    socios.value.push(data)
    return data
  }

  async function editar(id, datos) {
    const { data } = await api.put(`/socios/${id}`, datos)
    const idx = socios.value.findIndex(s => s.id === id)
    if (idx !== -1) socios.value[idx] = data
    return data
  }

  async function darBaja(id) {
    const { data } = await api.patch(`/socios/${id}/baja`)
    const idx = socios.value.findIndex(s => s.id === id)
    if (idx !== -1) socios.value[idx] = data
    return data
  }

  async function asignarPermiso(socioId, usuarioId) {
    await api.post(`/socios/${socioId}/asignar/${usuarioId}`)
  }

  async function revocarPermiso(socioId, usuarioId) {
    await api.patch(`/socios/${socioId}/revocar/${usuarioId}`)
  }

  return { socios, cargando, error, cargar, crear, editar, darBaja, asignarPermiso, revocarPermiso }
})