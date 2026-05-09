import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token   = ref(localStorage.getItem('token') || null)
  const usuario = ref(null)

  const estaAutenticado = () => !!token.value

  async function login(identificador, contrasena) {
    const { data } = await api.post('/auth/login', {
      identificador,
      contrasena,
    })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await cargarUsuario()
  }

  async function cargarUsuario() {
    const { data } = await api.get('/auth/me')
    usuario.value = data
  }

  function logout() {
    token.value   = null
    usuario.value = null
    localStorage.removeItem('token')
  }

  return { token, usuario, estaAutenticado, login, cargarUsuario, logout }
})