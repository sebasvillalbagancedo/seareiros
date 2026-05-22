<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-wide">
      <div class="modal-header">
        <h3>
          {{ sorteo.estado === 'resuelto' ? 'Resultados' : 'Inscripciones' }} —
          {{ sorteo.nombre }}
        </h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <!-- Inscribir socio (solo si el sorteo está abierto) -->
        <div v-if="sorteoAbierto" class="seccion-inscribir">
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
        <div v-if="!cargando && inscripcionesActivas.length" class="tabla-wrapper">
          <table>
            <thead>
              <tr>
                <th>N.º</th>
                <th>Nombre</th>
                <th>Apellidos</th>
                <th>Fecha inscripción</th>
                <th>Ganador</th>
                <th v-if="sorteoAbierto">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="i in inscripcionesActivas" :key="i.id">
                <td>{{ i.socio_numero }}</td>
                <td>{{ i.socio_nombre }}</td>
                <td>{{ i.socio_apellidos }}</td>
                <td>{{ formatFecha(i.fecha_inscripcion) }}</td>
                <td>
                  <span
                    v-if="sorteo.estado === 'resuelto'"
                    class="badge"
                    :class="i.es_ganador ? 'badge-activo' : 'badge-baja'"
                  >
                    {{ i.es_ganador ? 'Sí' : 'No' }}
                  </span>
                  <span v-else>—</span>
                </td>
                <td v-if="sorteoAbierto">
                  <button
                    class="btn-accion btn-baja"
                    :disabled="cancelando === i.id"
                    @click="cancelarInscripcion(i)"
                  >
                    {{ cancelando === i.id ? '...' : 'Cancelar' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="!cargando && !inscripcionesActivas.length" class="mensaje">
          No hay inscripciones activas en este sorteo.
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
  import { useSorteosStore } from '@/stores/sorteos'
  import { useSociosStore } from '@/stores/socios'
  import { formatFecha } from '@/utils/fecha'

  export default {
    name: 'InscripcionesModal',
    emits: ['cerrar'],

    props: {
      sorteo: { type: Object, required: true },
    },

    data() {
      return {
        socioSeleccionado: '',
        inscribiendo: false,
        cancelando: null,
        cargando: false,
        errorInscripcion: null,
        mensajeExito: null,
      }
    },

    computed: {
      sorteoAbierto() {
        return this.sorteo.estado === 'abierto'
      },

      inscripcionesActivas() {
        return useSorteosStore().inscripcionesActivas
      },

      // Socios disponibles: activos y no ya inscritos
      sociosDisponibles() {
        const idsInscritos = useSorteosStore().idsSociosInscritos
        return useSociosStore().socios.filter(
          (s) => s.estado === 'activo' && !idsInscritos.includes(s.id),
        )
      },
    },

    async created() {
      this.cargando = true
      await useSorteosStore().cargarInscripciones(this.sorteo.id)
      this.cargando = false
    },

    methods: {
      formatFecha,

      async inscribir() {
        this.errorInscripcion = null
        this.inscribiendo = true
        try {
          await useSorteosStore().inscribir(this.sorteo.id, this.socioSeleccionado)
          this.socioSeleccionado = ''
          this.mostrarExito('Socio inscrito correctamente.')
        } catch (e) {
          this.errorInscripcion = e.response?.data?.detail || 'Error al inscribir el socio.'
        } finally {
          this.inscribiendo = false
        }
      },

      async cancelarInscripcion(inscripcion) {
        this.cancelando = inscripcion.id
        try {
          await useSorteosStore().cancelarInscripcion(this.sorteo.id, inscripcion.id)
          this.mostrarExito('Inscripción cancelada correctamente.')
        } catch {
          this.errorInscripcion = 'Error al cancelar la inscripción.'
        } finally {
          this.cancelando = null
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
