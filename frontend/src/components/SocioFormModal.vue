<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal">
      <div class="modal-header">
        <h3>{{ modo === 'crear' ? 'Nuevo socio' : 'Editar socio' }}</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="modal-body">
          <div class="fila-campos">
            <div class="campo">
              <label>Nombre *</label>
              <input v-model="form.nombre" type="text" required placeholder="Nombre" />
            </div>
            <div class="campo">
              <label>Apellidos *</label>
              <input v-model="form.apellidos" type="text" required placeholder="Apellidos" />
            </div>
          </div>

          <div class="fila-campos">
            <div class="campo">
              <label>Fecha de nacimiento</label>
              <input v-model="form.fecha_nacimiento" type="date" />
            </div>
            <div class="campo">
              <label>Email</label>
              <input v-model="form.email" type="email" placeholder="email@ejemplo.com" />
            </div>
          </div>

          <div class="fila-campos">
            <div class="campo">
              <label>Teléfono móvil</label>
              <input v-model="form.telefono_movil" type="tel" placeholder="600000000" />
            </div>
            <div class="campo">
              <label>Teléfono fijo</label>
              <input v-model="form.telefono_fijo" type="tel" placeholder="986000000" />
            </div>
          </div>

          <div class="campo">
            <label>Dirección</label>
            <input v-model="form.direccion" type="text" placeholder="Calle, número, piso..." />
          </div>

          <div class="fila-campos">
            <div class="campo campo-cp">
              <label>Código postal</label>
              <input v-model="form.codigo_postal" type="text" placeholder="36001" />
            </div>
            <div class="campo">
              <label>Localidad</label>
              <input v-model="form.localidad" type="text" placeholder="Localidad" />
            </div>
            <div class="campo">
              <label>Provincia</label>
              <input v-model="form.provincia" type="text" placeholder="Provincia" />
            </div>
          </div>

          <div class="campo">
            <label>País</label>
            <input v-model="form.pais" type="text" placeholder="España" />
          </div>

          <p v-if="errorForm" class="error">{{ errorForm }}</p>
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
    name: 'SocioFormModal',
    emits: ['cerrar', 'guardado'],

    props: {
      modo: { type: String, default: 'crear' },
      socio: { type: Object, default: null },
    },

    data() {
      return {
        form: {
          nombre: '',
          apellidos: '',
          fecha_nacimiento: null,
          email: '',
          telefono_movil: '',
          telefono_fijo: '',
          direccion: '',
          codigo_postal: '',
          localidad: '',
          provincia: '',
          pais: '',
        },
        guardando: false,
        errorForm: null,
      }
    },

    created() {
      if (this.modo === 'editar' && this.socio) {
        this.form = {
          nombre: this.socio.nombre || '',
          apellidos: this.socio.apellidos || '',
          fecha_nacimiento: this.socio.fecha_nacimiento || null,
          email: this.socio.email || '',
          telefono_movil: this.socio.telefono_movil || '',
          telefono_fijo: this.socio.telefono_fijo || '',
          direccion: this.socio.direccion || '',
          codigo_postal: this.socio.codigo_postal || '',
          localidad: this.socio.localidad || '',
          provincia: this.socio.provincia || '',
          pais: this.socio.pais || '',
        }
      }
    },

    methods: {
      async handleSubmit() {
        this.errorForm = null
        this.guardando = true
        const datos = Object.fromEntries(
          Object.entries(this.form).filter(([, v]) => v !== '' && v !== null),
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
