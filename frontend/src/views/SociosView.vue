<template>
  <div class="modulo-view">
    <div class="modulo-header">
      <h2>Socios</h2>
      <button v-if="esAdmin" class="btn-primario" @click="abrirModalCrear">+ Nuevo socio</button>
    </div>

    <!-- Búsqueda y filtrado — RF.0204 -->
    <div class="barra-filtros">
      <input
        v-model="textoBusqueda"
        type="text"
        placeholder="Buscar por nombre o apellidos..."
        class="input-busqueda"
      />
      <select v-model="filtroEstado" class="select-filtro">
        <option value="">Todos</option>
        <option value="activo">Activos</option>
        <option value="baja">Baja</option>
      </select>
    </div>

    <p v-if="store.cargando" class="mensaje">Cargando socios...</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <div v-if="!store.cargando && sociosFiltrados.length" class="tabla-wrapper">
      <table>
        <thead>
          <tr>
            <th>N.º</th>
            <th>Nombre</th>
            <th>Apellidos</th>
            <th>Email</th>
            <th>Teléfono</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="socio in sociosFiltrados"
            :key="socio.id"
            :class="{ 'fila-baja': socio.estado === 'baja' }"
          >
            <td>{{ socio.numero_socio }}</td>
            <td>{{ socio.nombre }}</td>
            <td>{{ socio.apellidos }}</td>
            <td>{{ socio.email || '—' }}</td>
            <td>{{ socio.telefono_movil || socio.telefono_fijo || '—' }}</td>
            <td>
              <span
                class="badge"
                :class="socio.estado === 'activo' ? 'badge-activo' : 'badge-baja'"
              >
                {{ socio.estado }}
              </span>
            </td>
            <td class="acciones">
              <button class="btn-accion" @click="abrirModalEditar(socio)">Editar</button>
              <button
                v-if="esAdmin && socio.estado === 'activo'"
                class="btn-accion btn-baja"
                @click="confirmarBaja(socio)"
              >
                Baja
              </button>
              <button v-if="esAdmin" class="btn-accion" @click="abrirModalPermisos(socio)">
                Permisos
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Sin socios -->
    <p v-if="!store.cargando && !sociosFiltrados.length && !store.error" class="mensaje">
      No hay socios que coincidan con los filtros aplicados.
    </p>

    <!-- Mensaje de éxito -->
    <p v-if="mensajeExito" class="exito">{{ mensajeExito }}</p>

    <!-- Modal de alta / edición -->
    <SocioFormModal
      v-if="modalVisible"
      :modo="modalModo"
      :socio="socioSeleccionado"
      @cerrar="cerrarModal"
      @guardado="handleGuardado"
    />

    <!-- Permisos de Socio -->
    <PermisosModal
      v-if="permisosModalVisible"
      :socio="socioSeleccionado"
      @cerrar="cerrarModalPermisos"
    />
  </div>
</template>

<script>
  import { useSociosStore } from '@/stores/socios'
  import { useUsuariosStore } from '@/stores/usuarios'
  import SocioFormModal from '@/components/SocioFormModal.vue'
  import PermisosModal from '@/components/PermisosModal.vue'
  export default {
    name: 'SociosView',
    components: { SocioFormModal, PermisosModal },

    data() {
      return {
        modalVisible: false,
        modalModo: 'crear',
        socioSeleccionado: null,
        mensajeExito: null,
        permisosModalVisible: false,
        textoBusqueda: '',
        filtroEstado: 'activo',
      }
    },

    computed: {
      store() {
        return useSociosStore()
      },
      esAdmin() {
        return useUsuariosStore().usuario?.rol === 'administrador'
      },
      sociosFiltrados() {
        return this.store.socios.filter((s) => {
          const texto = this.textoBusqueda.toLowerCase()
          const coincideTexto =
            !texto ||
            s.nombre.toLowerCase().includes(texto) ||
            s.apellidos.toLowerCase().includes(texto)
          const coincideEstado = !this.filtroEstado || s.estado === this.filtroEstado
          return coincideTexto && coincideEstado
        })
      },
    },

    async created() {
      await useSociosStore().cargar()
    },

    methods: {
      abrirModalCrear() {
        this.socioSeleccionado = null
        this.modalModo = 'crear'
        this.modalVisible = true
      },

      abrirModalEditar(socio) {
        this.socioSeleccionado = socio
        this.modalModo = 'editar'
        this.modalVisible = true
      },

      cerrarModal() {
        this.modalVisible = false
        this.socioSeleccionado = null
      },

      abrirModalPermisos(socio) {
        this.socioSeleccionado = socio
        this.permisosModalVisible = true
      },

      cerrarModalPermisos() {
        this.permisosModalVisible = false
        this.socioSeleccionado = null
      },

      async handleGuardado(datos) {
        try {
          if (this.modalModo === 'crear') {
            await this.store.crear(datos)
            this.mostrarExito('Socio creado correctamente.')
          } else {
            await this.store.editar(this.socioSeleccionado.id, datos)
            this.mostrarExito('Socio actualizado correctamente.')
          }
          this.cerrarModal()
        } catch {
          // el error lo gestiona el modal
        }
      },

      async confirmarBaja(socio) {
        if (!confirm(`¿Dar de baja a ${socio.nombre} ${socio.apellidos}?`)) return
        try {
          await this.store.darBaja(socio.id)
          this.mostrarExito('Socio dado de baja correctamente.')
        } catch {
          alert('Error al dar de baja al socio.')
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
