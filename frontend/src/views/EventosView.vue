<template>
  <div class="modulo-view">
    <div class="modulo-header">
      <h2>Eventos</h2>
      <button v-if="esAdmin" class="btn-primario" @click="abrirModalCrear">+ Nuevo evento</button>
    </div>

    <!-- Tabs disponibles / histórico -->
    <div class="tabs-vista">
      <button
        class="tab"
        :class="{ 'tab-activo': vistaActiva === 'disponibles' }"
        @click="cambiarVista('disponibles')"
      >
        Disponibles
      </button>
      <button
        class="tab"
        :class="{ 'tab-activo': vistaActiva === 'historico' }"
        @click="cambiarVista('historico')"
      >
        Histórico
      </button>
    </div>

    <!-- Filtros — disponibles -->
    <div v-if="vistaActiva === 'disponibles'" class="barra-filtros">
      <input
        v-model="textoBusquedaDisp"
        type="text"
        placeholder="Buscar por nombre..."
        class="input-busqueda"
      />
      <select v-model="filtroEstadoDisp" class="select-filtro">
        <option value="">Todos los estados</option>
        <option value="abierto">Abierto</option>
        <option value="completo">Completo</option>
        <option value="cancelado">Cancelado</option>
      </select>
    </div>

    <!-- Filtros — histórico -->
    <div v-if="vistaActiva === 'historico'" class="barra-filtros">
      <input
        v-model="textoBusquedaHist"
        type="text"
        placeholder="Buscar por nombre..."
        class="input-busqueda"
      />
      <select v-model="filtroEstadoHist" class="select-filtro">
        <option value="">Todos los estados</option>
        <option value="celebrado">Celebrado</option>
        <option value="cancelado">Cancelado</option>
      </select>
      <input v-model="filtroDesde" type="date" class="input-fecha" />
      <input v-model="filtroHasta" type="date" class="input-fecha" />
      <button class="btn-secundario" @click="limpiarFiltrosHistorico">Limpiar filtros</button>
    </div>

    <p v-if="store.cargando" class="mensaje">Cargando eventos...</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <div v-if="!store.cargando && eventosMostrados.length" class="tabla-wrapper">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Lugar</th>
            <th>Celebración</th>
            <th>Plazas</th>
            <th>Inscritos</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in eventosMostrados" :key="e.id">
            <td>{{ e.nombre }}</td>
            <td>{{ e.lugar || '—' }}</td>
            <td>{{ formatFecha(e.fecha_celebracion) }}</td>
            <td>{{ e.plazas_disponibles }}</td>
            <td>{{ e.inscritos }}</td>
            <td>
              <span class="badge" :class="claseBadge(e.estado)">
                {{ etiquetaEstado(e.estado) }}
              </span>
            </td>
            <td class="acciones">
              <button class="btn-accion" @click="abrirInscripciones(e)">Inscripciones</button>
              <template v-if="vistaActiva === 'disponibles' && esAdmin">
                <button
                  v-if="e.estado === 'abierto'"
                  class="btn-accion"
                  @click="abrirModalEditar(e)"
                >
                  Editar
                </button>
                <button
                  v-if="!['cancelado', 'celebrado'].includes(e.estado)"
                  class="btn-accion btn-baja"
                  @click="abrirModalCancelar(e)"
                >
                  Cancelar
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="!store.cargando && !eventosMostrados.length && !store.error" class="mensaje">
      No hay eventos que coincidan con los filtros aplicados.
    </p>

    <p v-if="mensajeExito" class="exito">{{ mensajeExito }}</p>

    <!-- Modal alta / edición -->
    <EventoFormModal
      v-if="modalVisible"
      :modo="modalModo"
      :evento="eventoSeleccionado"
      @cerrar="cerrarModal"
      @guardado="handleGuardado"
    />

    <!-- Modal inscripciones -->
    <EventoInscripcionesModal
      v-if="inscripcionesVisible"
      :evento="eventoSeleccionado"
      :solo-consulta="vistaActiva === 'historico'"
      @cerrar="inscripcionesVisible = false"
    />

    <!-- Modal cancelar -->
    <EventoCancelarModal
      v-if="cancelarVisible"
      :evento="eventoSeleccionado"
      @cerrar="cancelarVisible = false"
      @cancelado="onCancelado"
    />
  </div>
</template>

<script>
  import { useEventosStore } from '@/stores/eventos'
  import { useUsuariosStore } from '@/stores/usuarios'
  import { formatFecha } from '@/utils/fecha'
  import EventoFormModal from '@/components/EventoFormModal.vue'
  import EventoInscripcionesModal from '@/components/EventoInscripcionesModal.vue'
  import EventoCancelarModal from '@/components/EventoCancelarModal.vue'

  export default {
    name: 'EventosView',
    components: {
      EventoFormModal,
      EventoInscripcionesModal,
      EventoCancelarModal,
    },

    data() {
      return {
        vistaActiva: 'disponibles',
        // Filtros disponibles
        textoBusquedaDisp: '',
        filtroEstadoDisp: '',
        // Filtros histórico
        textoBusquedaHist: '',
        filtroEstadoHist: '',
        filtroDesde: '',
        filtroHasta: '',
        // Modales
        modalVisible: false,
        modalModo: 'crear',
        eventoSeleccionado: null,
        inscripcionesVisible: false,
        cancelarVisible: false,
        mensajeExito: null,
      }
    },

    computed: {
      store() {
        return useEventosStore()
      },
      esAdmin() {
        return useUsuariosStore().usuario?.rol === 'administrador'
      },
      eventosMostrados() {
        const lista = this.vistaActiva === 'disponibles' ? this.store.eventos : this.store.historico

        return lista.filter((e) => {
          const busqueda =
            this.vistaActiva === 'disponibles'
              ? this.textoBusquedaDisp.toLowerCase()
              : this.textoBusquedaHist.toLowerCase()
          const estado =
            this.vistaActiva === 'disponibles' ? this.filtroEstadoDisp : this.filtroEstadoHist

          const coincideTexto = !busqueda || e.nombre.toLowerCase().includes(busqueda)
          const coincideEstado = !estado || e.estado === estado
          const coincideFecha =
            this.vistaActiva === 'disponibles'
              ? true
              : (!this.filtroDesde || e.fecha_celebracion >= this.filtroDesde) &&
                (!this.filtroHasta || e.fecha_celebracion <= this.filtroHasta + 'T23:59:59')

          return coincideTexto && coincideEstado && coincideFecha
        })
      },
    },

    async created() {
      await useEventosStore().cargar()
    },

    methods: {
      formatFecha,

      async cambiarVista(vista) {
        this.vistaActiva = vista
        if (vista === 'disponibles') {
          await this.store.cargar()
        } else {
          await this.store.cargarHistorico()
        }
      },

      limpiarFiltrosHistorico() {
        this.textoBusquedaHist = ''
        this.filtroEstadoHist = ''
        this.filtroDesde = ''
        this.filtroHasta = ''
      },

      claseBadge(estado) {
        const mapa = {
          abierto: 'badge-activo',
          completo: 'badge-pendiente',
          celebrado: 'badge-resuelto',
          cancelado: 'badge-baja',
        }
        return mapa[estado] || ''
      },

      etiquetaEstado(estado) {
        const mapa = {
          abierto: 'Abierto',
          completo: 'Completo',
          celebrado: 'Celebrado',
          cancelado: 'Cancelado',
        }
        return mapa[estado] || estado
      },

      abrirModalCrear() {
        this.eventoSeleccionado = null
        this.modalModo = 'crear'
        this.modalVisible = true
      },

      abrirModalEditar(evento) {
        this.eventoSeleccionado = evento
        this.modalModo = 'editar'
        this.modalVisible = true
      },

      cerrarModal() {
        this.modalVisible = false
        this.eventoSeleccionado = null
      },

      abrirInscripciones(evento) {
        this.eventoSeleccionado = evento
        this.inscripcionesVisible = true
      },

      abrirModalCancelar(evento) {
        this.eventoSeleccionado = evento
        this.cancelarVisible = true
      },

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
            this.mostrarExito('Evento creado correctamente.')
          } else {
            await this.store.editar(this.eventoSeleccionado.id, datos)
            this.mostrarExito('Evento actualizado correctamente.')
          }
          this.cerrarModal()
        } catch (e) {
          alert(this.getMensajeError(e))
        }
      },

      onCancelado() {
        this.cancelarVisible = false
        this.mostrarExito('Evento cancelado correctamente.')
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
