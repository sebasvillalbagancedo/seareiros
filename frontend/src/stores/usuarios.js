import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useUsuariosStore = defineStore('usuario', () => {
  const usuario   = ref(null)
  const usuarios  = ref([])

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

  return { usuario, usuarios, cargarUsuario, cargarUsuarios, limpiar }
})