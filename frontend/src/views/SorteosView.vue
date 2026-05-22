<template>
  <div class="modulo-view">
    <div class="modulo-header">
      <h2>Sorteos</h2>
      <button v-if="esAdmin" class="btn-primario" @click="abrirModalCrear">+ Nuevo sorteo</button>
    </div>

    <!-- Filtros -->
    <div class="barra-filtros">
      <input
        v-model="textoBusqueda"
        type="text"
        placeholder="Buscar por nombre..."
        class="input-busqueda"
      />
      <select v-model="filtroEstado" class="select-filtro">
        <option value="abierto">Abiertos</option>
        <option value="pendiente">Pendientes</option>
        <option value="resuelto">Resueltos</option>
        <option value="cancelado">Cancelados</option>
        <option value="">Todos</option>
      </select>
    </div>

    <p v-if="store.cargando" class="mensaje">Cargando sorteos...</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <div v-if="!store.cargando && sorteosFiltrados.length" class="tabla-wrapper">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Celebración</th>
            <th>Inscritos</th>
            <th>Premios</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sorteosFiltrados" :key="s.id">
            <td>{{ s.nombre }}</td>
            <td>{{ formatFecha(s.fecha_celebracion) }}</td>
            <td>
              {{ s.inscritos }}
              <span v-if="s.maximo_inscritos !== null" class="texto-limite">
                / {{ s.maximo_inscritos }}
              </span>
            </td>
            <td>{{ s.numero_premios }}</td>
            <td>
              <span class="badge" :class="claseBadge(s.estado)">
                {{ etiquetaEstado(s.estado) }}
              </span>
            </td>
            <td class="acciones">
              <button class="btn-accion" @click="abrirInscripciones(s)">
                {{ s.estado === 'resuelto' ? 'Resultados' : 'Inscripciones' }}
              </button>
              <button
                v-if="esAdmin && s.estado === 'abierto'"
                class="btn-accion"
                @click="abrirModalEditar(s)"
              >
                Editar
              </button>
              <button
                v-if="esAdmin && ['abierto', 'pendiente'].includes(s.estado)"
                class="btn-accion"
                @click="abrirModalResolver(s)"
              >
                Resolver
              </button>
              <button
                v-if="esAdmin && !['resuelto', 'cancelado'].includes(s.estado)"
                class="btn-accion btn-baja"
                @click="abrirModalCancelar(s)"
              >
                Cancelar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="!store.cargando && !sorteosFiltrados.length && !store.error" class="mensaje">
      No hay sorteos que coincidan con los filtros aplicados.
    </p>

    <p v-if="mensajeExito" class="exito">{{ mensajeExito }}</p>

    <!-- Modal alta / edición -->
    <SorteoFormModal
      v-if="modalVisible"
      :modo="modalModo"
      :sorteo="sorteoSeleccionado"
      @cerrar="cerrarModal"
      @guardado="handleGuardado"
    />

    <!-- Modal inscripciones -->
    <InscripcionesModal
      v-if="inscripcionesVisible"
      :sorteo="sorteoSeleccionado"
      @cerrar="inscripcionesVisible = false"
    />

    <!-- Modal cancelar -->
    <SorteoCancelarModal
      v-if="cancelarVisible"
      :sorteo="sorteoSeleccionado"
      @cerrar="cancelarVisible = false"
      @cancelado="onCancelado"
    />

    <!-- Modal resolver -->
    <SorteoResolverModal
      v-if="resolverVisible"
      :sorteo="sorteoSeleccionado"
      @cerrar="resolverVisible = false"
      @resuelto="onResuelto"
    />
  </div>
</template>

<script>
  import { useSorteosStore } from '@/stores/sorteos'
  import { useUsuariosStore } from '@/stores/usuarios'
  import { formatFecha } from '@/utils/fecha'
  import SorteoFormModal from '@/components/SorteoFormModal.vue'
  import InscripcionesModal from '@/components/InscripcionesModal.vue'
  import SorteoCancelarModal from '@/components/SorteoCancelarModal.vue'
  import SorteoResolverModal from '@/components/SorteoResolverModal.vue'

  export default {
    name: 'SorteosView',
    components: {
      SorteoFormModal,
      InscripcionesModal,
      SorteoCancelarModal,
      SorteoResolverModal,
    },

    data() {
      return {
        textoBusqueda: '',
        filtroEstado: 'abierto', // por defecto muestra solo abiertos
        modalVisible: false,
        modalModo: 'crear',
        sorteoSeleccionado: null,
        inscripcionesVisible: false,
        cancelarVisible: false,
        resolverVisible: false,
        mensajeExito: null,
      }
    },

    computed: {
      store() {
        return useSorteosStore()
      },
      esAdmin() {
        return useUsuariosStore().usuario?.rol === 'administrador'
      },

      sorteosFiltrados() {
        return this.store.sorteos.filter((s) => {
          const texto = this.textoBusqueda.toLowerCase()
          const coincideTexto = !texto || s.nombre.toLowerCase().includes(texto)
          const coincideEstado = !this.filtroEstado || s.estado === this.filtroEstado
          return coincideTexto && coincideEstado
        })
      },
    },

    async created() {
      await useSorteosStore().cargar()
    },

    methods: {
      formatFecha,

      claseBadge(estado) {
        const mapa = {
          abierto: 'badge-activo',
          pendiente: 'badge-pendiente',
          resuelto: 'badge-resuelto',
          cancelado: 'badge-baja',
        }
        return mapa[estado] || ''
      },

      etiquetaEstado(estado) {
        const mapa = {
          abierto: 'Abierto',
          pendiente: 'Pendiente',
          resuelto: 'Resuelto',
          cancelado: 'Cancelado',
        }
        return mapa[estado] || estado
      },

      abrirModalCrear() {
        this.sorteoSeleccionado = null
        this.modalModo = 'crear'
        this.modalVisible = true
      },

      abrirModalEditar(sorteo) {
        this.sorteoSeleccionado = sorteo
        this.modalModo = 'editar'
        this.modalVisible = true
      },

      cerrarModal() {
        this.modalVisible = false
        this.sorteoSeleccionado = null
      },

      abrirInscripciones(sorteo) {
        this.sorteoSeleccionado = sorteo
        this.inscripcionesVisible = true
      },

      abrirModalCancelar(sorteo) {
        this.sorteoSeleccionado = sorteo
        this.cancelarVisible = true
      },

      abrirModalResolver(sorteo) {
        this.sorteoSeleccionado = sorteo
        this.resolverVisible = true
      },

      // Helper para extraer el mensaje de error de la respuesta de FastAPI
      getMensajeError(e) {
        const detail = e.response?.data?.detail
        if (!detail) return 'Error inesperado. Inténtalo de nuevo.'
        if (typeof detail === 'string') return detail
        if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
        return 'Error inesperado. Inténtalo de nuevo.'
      },

      async handleGuardado(datos) {
        try {
          if (this.modalModo === 'crear') {
            await this.store.crear(datos)
            this.mostrarExito('Sorteo creado correctamente.')
          } else {
            await this.store.editar(this.sorteoSeleccionado.id, datos)
            this.mostrarExito('Sorteo actualizado correctamente.')
          }
          this.cerrarModal()
        } catch (e) {
          alert(this.getMensajeError(e))
        }
      },

      onCancelado() {
        this.cancelarVisible = false
        this.mostrarExito('Sorteo cancelado correctamente.')
      },

      onResuelto() {
        this.resolverVisible = false
        this.mostrarExito('Sorteo resuelto correctamente.')
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
