<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-wide">
      <div class="modal-header">
        <h3>{{ modo === 'crear' ? 'Nuevo evento' : 'Editar evento' }}</h3>
        <p v-if="errorForm" class="error-header">{{ errorForm }}</p>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="modal-body">
          <div class="campo">
            <label>Nombre *</label>
            <input v-model="form.nombre" type="text" required placeholder="Nombre del evento" />
          </div>

          <div class="campo">
            <label>Descripción</label>
            <input v-model="form.descripcion" type="text" placeholder="Descripción opcional" />
          </div>

          <div class="campo">
            <label>Lugar</label>
            <input v-model="form.lugar" type="text" placeholder="Lugar de celebración" />
          </div>

          <div class="fila-campos">
            <div class="campo">
              <label>Inicio inscripción *</label>
              <input v-model="form.fecha_inicio_inscripcion" type="datetime-local" required />
            </div>
            <div class="campo">
              <label>Fin inscripción *</label>
              <input v-model="form.fecha_fin_inscripcion" type="datetime-local" required />
            </div>
            <div class="campo">
              <label>Fecha celebración *</label>
              <input v-model="form.fecha_celebracion" type="datetime-local" required />
            </div>
            <div class="campo campo-cp">
              <label>Plazas *</label>
              <input
                v-model.number="form.plazas_disponibles"
                type="number"
                min="1"
                required
                placeholder="1"
              />
            </div>
          </div>

          <!-- Requisitos de participación -->
          <div class="seccion-requisitos">
            <h4>Requisitos de participación</h4>
            <div class="fila-campos">
              <div class="campo">
                <label>Fecha nacimiento máxima</label>
                <input v-model="form.fecha_nacimiento_maxima" type="date" />
              </div>
              <div class="campo">
                <label>Fecha nacimiento mínima</label>
                <input v-model="form.fecha_nacimiento_minima" type="date" />
              </div>
              <div class="campo">
                <label>Fecha alta máxima</label>
                <input v-model="form.fecha_alta_maxima" type="date" />
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn-secundario" @click="$emit('cerrar')">Cancelar</button>
          <button type="submit" class="btn-primario" :disabled="guardando">
            {{ guardando ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'EventoFormModal',
    emits: ['cerrar', 'guardado'],

    props: {
      modo: { type: String, default: 'crear' },
      evento: { type: Object, default: null },
    },

    data() {
      return {
        form: {
          nombre: '',
          descripcion: '',
          lugar: '',
          fecha_inicio_inscripcion: '',
          fecha_fin_inscripcion: '',
          fecha_celebracion: '',
          plazas_disponibles: 1,
          fecha_nacimiento_maxima: '',
          fecha_nacimiento_minima: '',
          fecha_alta_maxima: '',
          ultimoFinInscripcion: '',
        },
        guardando: false,
        errorForm: null,
      }
    },

    created() {
      if (this.modo === 'editar' && this.evento) {
        this.form = {
          nombre: this.evento.nombre || '',
          descripcion: this.evento.descripcion || '',
          lugar: this.evento.lugar || '',
          fecha_inicio_inscripcion: this.toDatetimeLocal(this.evento.fecha_inicio_inscripcion),
          fecha_fin_inscripcion: this.toDatetimeLocal(this.evento.fecha_fin_inscripcion),
          fecha_celebracion: this.toDatetimeLocal(this.evento.fecha_celebracion),
          plazas_disponibles: this.evento.plazas_disponibles || 1,
          fecha_nacimiento_maxima: this.evento.fecha_nacimiento_maxima || '',
          fecha_nacimiento_minima: this.evento.fecha_nacimiento_minima || '',
          fecha_alta_maxima: this.evento.fecha_alta_maxima || '',
        }
      } else {
        const hoy = new Date()

        const inicio = new Date(hoy)
        inicio.setHours(0, 0, 0, 0)
        this.form.fecha_inicio_inscripcion = this.toDatetimeLocal(inicio)

        const fin = new Date(hoy)
        fin.setDate(fin.getDate() + 3)
        fin.setHours(23, 59, 0, 0)
        this.form.fecha_fin_inscripcion = this.toDatetimeLocal(fin)

        this.form.fecha_celebracion = this.toDatetimeLocal(fin)
        this.form.ultimoFinInscripcion = this.toDatetimeLocal(fin)
      }
    },

    watch: {
      'form.fecha_fin_inscripcion'(nuevaFecha) {
        if (
          this.form.fecha_celebracion === '' ||
          this.form.fecha_celebracion === this.form.ultimoFinInscripcion
        ) {
          this.form.fecha_celebracion = nuevaFecha
        }
        this.form.ultimoFinInscripcion = nuevaFecha
      },
    },

    methods: {
      toDatetimeLocal(date) {
        if (!date) return ''
        const d = typeof date === 'string' ? new Date(date) : date
        const pad = (n) => String(n).padStart(2, '0')
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
      },

      async handleSubmit() {
        this.errorForm = null

        if (this.form.fecha_fin_inscripcion <= this.form.fecha_inicio_inscripcion) {
          this.errorForm = 'La fecha de fin de inscripción debe ser posterior a la de inicio.'
          return
        }
        if (this.form.fecha_celebracion < this.form.fecha_fin_inscripcion) {
          this.errorForm = 'La fecha de celebración debe ser posterior al cierre de inscripción.'
          return
        }
        if (this.form.plazas_disponibles < 1) {
          this.errorForm = 'El número de plazas debe ser mayor que cero.'
          return
        }

        this.guardando = true
        const datos = Object.fromEntries(
          Object.entries(this.form).filter(
            ([k, v]) => k !== 'ultimoFinInscripcion' && v !== '' && v !== null,
          ),
        )
        try {
          this.$emit('guardado', datos)
        } catch {
          this.errorForm = 'Error al guardar. Inténtalo de nuevo.'
        } finally {
          this.guardando = false
        }
      },
    },
  }
</script>
