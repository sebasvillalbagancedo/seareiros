<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-wide">
      <div class="modal-header">
        <h3>Inscripciones — {{ evento.nombre }}</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <!-- Inscribir socio (solo si el evento está abierto) -->
        <div v-if="eventoAbierto" class="seccion-inscribir">
          <h4>Inscribir socio</h4>
          <div class="fila-campos">
            <div class="campo">
              <select v-model="socioSeleccionado" class="select-full">
                <option value="">— Selecciona un socio —</option>
                <option v-for="s in sociosDisponibles" :key="s.id" :value="s.id">
                  {{ s.numero_socio }} — {{ s.nombre }} {{ s.apellidos }}
                </option>
              </select>
            </div>
            <button
              class="btn-primario"
              :disabled="!socioSeleccionado || inscribiendo"
              @click="inscribir"
            >
              {{ inscribiendo ? '...' : 'Inscribir' }}
            </button>
          </div>
          <p v-if="errorInscripcion" class="error">{{ errorInscripcion }}</p>
        </div>

        <p v-if="cargando" class="mensaje">Cargando inscripciones...</p>

        <!-- Tabla de inscripciones -->
        <div v-if="!cargando && inscripcionesTodas.length" class="tabla-wrapper">
          <table>
            <thead>
              <tr>
                <th>N.º</th>
                <th>Nombre</th>
                <th>Apellidos</th>
                <th>Fecha inscripción</th>
                <th>Estado</th>
                <th v-if="esAdmin && !soloConsulta">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="i in inscripcionesTodas" :key="i.id">
                <td>{{ i.socio_numero }}</td>
                <td>{{ i.socio_nombre }}</td>
                <td>{{ i.socio_apellidos }}</td>
                <td>{{ formatFecha(i.fecha_inscripcion) }}</td>
                <td>
                  <span class="badge" :class="claseBadgeInscripcion(i.estado)">
                    {{ etiquetaEstadoInscripcion(i.estado) }}
                  </span>
                </td>
                <td v-if="esAdmin && !soloConsulta">
                  <button
                    v-if="i.estado === 'pendiente'"
                    class="btn-accion"
                    :disabled="gestionando === i.id"
                    @click="gestionar(i, 'confirmada')"
                  >
                    {{ gestionando === i.id ? '...' : 'Confirmar' }}
                  </button>
                  <button
                    v-if="i.estado === 'pendiente'"
                    class="btn-accion btn-baja"
                    :disabled="gestionando === i.id"
                    @click="gestionar(i, 'rechazada')"
                  >
                    {{ gestionando === i.id ? '...' : 'Rechazar' }}
                  </button>
                  <button
                    v-if="i.estado === 'confirmada'"
                    class="btn-accion btn-baja"
                    :disabled="gestionando === i.id"
                    @click="gestionar(i, 'cancelada')"
                  >
                    {{ gestionando === i.id ? '...' : 'Cancelar' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="!cargando && !inscripcionesTodas.length" class="mensaje">
          No hay inscripciones activas en este evento.
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
  import { useEventosStore } from '@/stores/eventos'
  import { useSociosStore } from '@/stores/socios'
  import { useUsuariosStore } from '@/stores/usuarios'
  import { formatFecha } from '@/utils/fecha'

  export default {
    name: 'EventoInscripcionesModal',
    emits: ['cerrar'],

    props: {
      evento: { type: Object, required: true },
      soloConsulta: { type: Boolean, default: false },
    },

    data() {
      return {
        socioSeleccionado: '',
        inscribiendo: false,
        gestionando: null,
        cargando: false,
        errorInscripcion: null,
        mensajeExito: null,
      }
    },

    computed: {
      esAdmin() {
        return useUsuariosStore().usuario?.rol === 'administrador'
      },

      eventoAbierto() {
        return !this.soloConsulta && this.evento.estado === 'abierto'
      },

      inscripcionesTodas() {
        return useEventosStore().inscripcionesTodas
      },

      sociosDisponibles() {
        const idsInscritos = useEventosStore().idsSociosInscritos
        return useSociosStore().socios.filter(
          (s) => s.estado === 'activo' && !idsInscritos.includes(s.id),
        )
      },
    },

    async created() {
      this.cargando = true
      await Promise.all([
        useEventosStore().cargarInscripciones(this.evento.id),
        useSociosStore().socios.length === 0 ? useSociosStore().cargar() : Promise.resolve(),
      ])
      this.cargando = false
    },

    methods: {
      formatFecha,

      claseBadgeInscripcion(estado) {
        const mapa = {
          pendiente: 'badge-pendiente',
          confirmada: 'badge-activo',
          rechazada: 'badge-baja',
          cancelada: 'badge-baja',
        }
        return mapa[estado] || ''
      },

      etiquetaEstadoInscripcion(estado) {
        const mapa = {
          pendiente: 'Pendiente',
          confirmada: 'Confirmada',
          rechazada: 'Rechazada',
          cancelada: 'Cancelada',
        }
        return mapa[estado] || estado
      },

      async inscribir() {
        this.errorInscripcion = null
        this.inscribiendo = true
        try {
          await useEventosStore().inscribir(this.evento.id, this.socioSeleccionado)
          this.socioSeleccionado = ''
          this.mostrarExito('Socio inscrito correctamente.')
        } catch (e) {
          this.errorInscripcion = e.response?.data?.detail || 'Error al inscribir el socio.'
        } finally {
          this.inscribiendo = false
        }
      },

      async gestionar(inscripcion, nuevoEstado) {
        this.gestionando = inscripcion.id
        try {
          await useEventosStore().gestionarInscripcion(this.evento.id, inscripcion.id, nuevoEstado)
          this.mostrarExito('Inscripción actualizada correctamente.')
        } catch (e) {
          this.errorInscripcion = e.response?.data?.detail || 'Error al gestionar la inscripción.'
        } finally {
          this.gestionando = null
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
