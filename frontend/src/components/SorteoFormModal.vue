<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal">

      <div class="modal-header">
        <h3>{{ modo === 'crear' ? 'Nuevo sorteo' : 'Editar sorteo' }}</h3>
        <p v-if="errorForm" class="error-header">{{ errorForm }}</p>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="modal-body">

          <div class="campo">
            <label>Nombre *</label>
            <input v-model="form.nombre" type="text" required placeholder="Nombre del sorteo" />
          </div>

          <div class="campo">
            <label>Descripción</label>
            <input v-model="form.descripcion" type="text" placeholder="Descripción opcional" />
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
          </div>

          <div class="fila-campos">
            <div class="campo">
              <label>Fecha celebración *</label>
              <input v-model="form.fecha_celebracion" type="datetime-local" required />
            </div>
          </div>

          <div class="fila-campos">
            <div class="campo campo-cp">
              <label>Número de Premios *</label>
              <input v-model.number="form.numero_premios" type="number" min="1" required placeholder="1" />
            </div>
            <div class="campo campo-cp">
              <label>Máximo de inscritos</label>
              <input v-model.number="form.maximo_inscritos" type="number" min="1" placeholder="Sin límite" />
            </div>
          </div>

          <div class="fila-campos">
            <div class="campo">
              <label>Fecha nacimiento máxima</label>
              <input v-model="form.fecha_nacimiento_maxima" type="date"
                     placeholder="Edad mínima" />
            </div>
            <div class="campo">
              <label>Fecha nacimiento mínima</label>
              <input v-model="form.fecha_nacimiento_minima" type="date"
                     placeholder="Edad máxima" />
            </div>
          </div>

          <div class="campo">
            <label>Fecha alta máxima</label>
            <input v-model="form.fecha_alta_maxima" type="date"
                   placeholder="Antigüedad mínima" />
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
  name: 'SorteoFormModal',
  emits: ['cerrar', 'guardado'],

  props: {
    modo:   { type: String, default: 'crear' },
    sorteo: { type: Object, default: null },
  },

  data() {
    return {
      form: {
        nombre:                   '',
        descripcion:              '',
        fecha_inicio_inscripcion: '',
        fecha_fin_inscripcion:    '',
        fecha_celebracion:        '',
        numero_premios:           1,
        maximo_inscritos:         null,
        fecha_nacimiento_maxima:  '',
        fecha_nacimiento_minima:  '',
        fecha_alta_maxima:        '',
        ultimoFinInscripcion:     '', // Para sincronizar celebración con fin de inscripción
      },
      guardando: false,
      errorForm: null,
    }
  },

  created() {
    if (this.modo === 'editar' && this.sorteo) {
      this.form = {
        nombre:                   this.sorteo.nombre                   || '',
        descripcion:              this.sorteo.descripcion              || '',
        fecha_inicio_inscripcion: this.toDatetimeLocal(this.sorteo.fecha_inicio_inscripcion),
        fecha_fin_inscripcion:    this.toDatetimeLocal(this.sorteo.fecha_fin_inscripcion),
        fecha_celebracion:        this.toDatetimeLocal(this.sorteo.fecha_celebracion),
        maximo_inscritos:         this.sorteo.maximo_inscritos         || null,
        numero_premios:           this.sorteo.numero_premios           || 1,
        fecha_nacimiento_maxima:  this.sorteo.fecha_nacimiento_maxima  || '',
        fecha_nacimiento_minima:  this.sorteo.fecha_nacimiento_minima  || '',
        fecha_alta_maxima:        this.sorteo.fecha_alta_maxima        || '',
      } 
    } else {
          // Modo crear: rellenar fechas por defecto
          const hoy = new Date()

          // Inicio inscripción: hoy a las 00:00
          const inicio = new Date(hoy)
          inicio.setHours(0, 0, 0, 0)
          this.form.fecha_inicio_inscripcion = this.toDatetimeLocal(inicio)
        
          // Fin inscripción: hoy + 3 días a las 23:59
          const fin = new Date(hoy)
          fin.setDate(fin.getDate() + 3)
          fin.setHours(23, 59, 0, 0)
          this.form.fecha_fin_inscripcion = this.toDatetimeLocal(fin)

          // Celebración: igual que fin de inscripción por defecto
          this.form.fecha_celebracion = this.toDatetimeLocal(fin)
          this.ultimoFinInscripcion   = this.toDatetimeLocal(fin)
    }
  },

  watch: {
    'form.fecha_fin_inscripcion'(nuevaFecha) {
      // Solo actualiza celebración si coincidía con el valor anterior de fin
      // (es decir, si el usuario no la ha modificado manualmente)
      if (this.form.fecha_celebracion === '' ||
          this.form.fecha_celebracion === this.form.fecha_fin_inscripcion ||
          this.ultimoFinInscripcion === this.form.fecha_celebracion) {
        this.form.fecha_celebracion = nuevaFecha
      }
      this.ultimoFinInscripcion = nuevaFecha
    }
  },

  methods: {
    toDatetimeLocal(date) {
      if (!date) return ''
        // Si es string ISO lo convertimos a Date primero
        const d = typeof date === 'string' ? new Date(date) : date
        const pad = n => String(n).padStart(2, '0')
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    },

    async handleSubmit() {
      this.errorForm = null

      // Validación de fechas
      if (this.form.fecha_fin_inscripcion <= this.form.fecha_inicio_inscripcion) {
        this.errorForm = 'La fecha de fin de inscripción debe ser posterior a la de inicio.'
        return
      }
      if (this.form.fecha_celebracion < this.form.fecha_fin_inscripcion) {
        this.errorForm = 'La fecha de celebración debe ser posterior al cierre de inscripción.'
        return
      }

      // Validación de premios vs máximo inscritos
      if (
        this.form.maximo_inscritos !== null &&
        this.form.numero_premios > this.form.maximo_inscritos
      ) {
        this.errorForm = 'El número de premios no puede superar el máximo de inscritos.'
        return
      }

      this.guardando = true
      
      // Limpiar campos opcionales vacíos
      const datos = Object.fromEntries(
        Object.entries(this.form).filter(([, v]) => v !== '' && v !== null)
      )
      try {
        this.$emit('guardado', datos)
      } catch {
        this.errorForm = 'Error al guardar. Inténtalo de nuevo.'
      } finally {
        this.guardando = false
      }
    }
  }
}
</script>