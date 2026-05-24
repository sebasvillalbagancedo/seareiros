import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/services/api'

export const useUsuariosStore = defineStore('usuario', () => {
  const usuario = ref(null)
  const usuarios = ref([])

  const usuariosNormales = computed(() => usuarios.value.filter((u) => u.rol === 'normal'))

  const idUsuarioActual = computed(() => usuario.value?.id)

  async function cargarUsuario() {
    const { data } = await api.get('/usuarios/me')
    usuario.value = data
  }

  async function cargarUsuarios() {
    const { data } = await api.get('/usuarios')
    usuarios.value = data
  }

  function limpiar() {
    usuario.value = null
    usuarios.value = []
  }

  return {
    usuario,
    usuarios,
    usuariosNormales,
    idUsuarioActual,
    cargarUsuario,
    cargarUsuarios,
    limpiar,
  }
})
