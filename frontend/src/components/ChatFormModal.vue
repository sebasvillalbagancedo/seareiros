<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal">
      <div class="modal-header">
        <h3>{{ modo === 'crear' ? 'Nuevo chat' : 'Editar chat' }}</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="modal-body">
          <div class="campo">
            <label>Nombre *</label>
            <input v-model="form.nombre" type="text" required placeholder="Nombre del Chat" />
          </div>

          <div class="campo">
            <label>Descripción</label>
            <input v-model="form.descripcion" type="text" placeholder="Descripción opcional" />
          </div>

          <div class="fila-campos">
            <div class="campo">
              <label>Tipo de acceso *</label>
              <select v-model="form.tipo_acceso" class="select-full">
                <option value="libre">Libre</option>
                <option value="restringido">Restringido</option>
              </select>
            </div>
            <div class="campo">
              <label>Modalidad *</label>
              <select v-model="form.modalidad" class="select-full">
                <option value="bidireccional">Bidireccional</option>
                <option value="canal">Canal de difusión</option>
              </select>
            </div>
            <div class="campo">
              <label>Visibilidad *</label>
              <select v-model="form.visibilidad" class="select-full">
                <option value="visible">Visible</option>
                <option value="oculta">Oculta</option>
              </select>
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
  import { useChatStore } from '@/stores/chat'

  export default {
    name: 'ChatFormModal',
    emits: ['cerrar', 'guardado'],

    props: {
      modo: { type: String, default: 'crear' },
      chat: { type: Object, default: null },
    },

    data() {
      return {
        form: {
          nombre: '',
          descripcion: '',
          tipo_acceso: 'libre',
          modalidad: 'bidireccional',
          visibilidad: 'visible',
        },
        guardando: false,
        errorForm: null,
      }
    },

    created() {
      if (this.modo === 'editar' && this.chat) {
        this.form = {
          nombre: this.chat.nombre || '',
          descripcion: this.chat.descripcion || '',
          tipo_acceso: this.chat.tipo_acceso,
          modalidad: this.chat.modalidad,
          visibilidad: this.chat.visibilidad,
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
          if (this.modo === 'crear') {
            await useChatStore().crearChat(datos)
          } else {
            await useChatStore().editarChat(this.chat.chat_id || this.chat.id, datos)
          }
          this.$emit('guardado')
        } catch (e) {
          const detail = e.response?.data?.detail
          this.errorForm = typeof detail === 'string' ? detail : 'Error al guardar el chat.'
        } finally {
          this.guardando = false
        }
      },
    },
  }
</script>
