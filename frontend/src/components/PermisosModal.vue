<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal">

      <div class="modal-header">
        <h3>Permisos — {{ socio.nombre }} {{ socio.apellidos }}</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">

        <p v-if="cargando" class="mensaje">Cargando usuarios...</p>
        <p v-if="error" class="error">{{ error }}</p>

        <table v-if="!cargando && usuariosNormales.length">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Permiso</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in usuariosNormales" :key="u.id">
              <td>{{ u.codigo_usuario }}</td>
              <td>{{ u.nombre }} {{ u.apellidos }}</td>
              <td>
                <span class="badge" :class="u.estado === 'activa' ? 'badge-activo' : 'badge-baja'">
                  {{ u.estado }}
                </span>
              </td>
              <td>
                <span class="badge" :class="tienePermiso(u.id) ? 'badge-activo' : 'badge-baja'">
                  {{ tienePermiso(u.id) ? 'Asignado' : 'Sin permiso' }}
                </span>
              </td>
              <td>
                <button
                  v-if="!tienePermiso(u.id)"
                  class="btn-accion"
                  :disabled="procesando === u.id"
                  @click="asignar(u)"
                >
                  {{ procesando === u.id ? '...' : 'Asignar' }}
                </button>
                <button
                  v-else
                  class="btn-accion btn-baja"
                  :disabled="procesando === u.id"
                  @click="revocar(u)"
                >
                  {{ procesando === u.id ? '...' : 'Revocar' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <p v-if="!cargando && !usuariosNormales.length && !error" class="mensaje">
          No hay usuarios normales registrados.
        </p>

        <p v-if="mensajeExito" class="exito">{{ mensajeExito }}</p>

      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Cerrar</button>
      </div>

    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { useSociosStore } from '@/stores/socios'

export default {
  name: 'PermisosModal',
  emits: ['cerrar'],

  props: {
    socio:            { type: Object, required: true },
    sociosConPermiso: { type: Array,  default: () => [] },
  },

  data() {
    return {
      usuarios:      [],
      permisos:      [],   // ids de usuarios con permiso vigente sobre este socio
      cargando:      false,
      procesando:    null,
      error:         null,
      mensajeExito:  null,
    }
  },

  computed: {
    usuariosNormales() {
      return this.usuarios.filter(u => u.rol === 'normal')
    },
  },

  async created() {
    await this.cargarDatos()
  },

  methods: {
    async cargarDatos() {
      this.cargando = true
      this.error    = null
      try {
        const { data } = await api.get('/auth/usuarios')
        this.usuarios = data
        await this.cargarPermisos()
      } catch {
        this.error = 'No se pudo cargar la lista de usuarios.'
      } finally {
        this.cargando = false
      }
    },

    async cargarPermisos() {
      // Obtenemos los permisos vigentes consultando los socios asignados
      // a cada usuario, comparando con el socio actual
      const { data } = await api.get(`/socios/${this.socio.id}/permisos`)
      this.permisos = data.map(p => p.usuario_id)
    },

    tienePermiso(usuarioId) {
      return this.permisos.includes(usuarioId)
    },

    async asignar(usuario) {
      this.procesando   = usuario.id
      this.mensajeExito = null
      try {
        await useSociosStore().asignarPermiso(this.socio.id, usuario.id)
        this.permisos.push(usuario.id)
        this.mostrarExito(`Permiso asignado a ${usuario.nombre}.`)
      } catch {
        this.error = 'Error al asignar el permiso.'
      } finally {
        this.procesando = null
      }
    },

    async revocar(usuario) {
      this.procesando   = usuario.id
      this.mensajeExito = null
      try {
        await useSociosStore().revocarPermiso(this.socio.id, usuario.id)
        this.permisos = this.permisos.filter(id => id !== usuario.id)
        this.mostrarExito(`Permiso revocado a ${usuario.nombre}.`)
      } catch {
        this.error = 'Error al revocar el permiso.'
      } finally {
        this.procesando = null
      }
    },

    mostrarExito(msg) {
      this.mensajeExito = msg
      setTimeout(() => { this.mensajeExito = null }, 3000)
    }
  }
}
</script>