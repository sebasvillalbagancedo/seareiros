<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-sm">
      <div class="modal-header">
        <div>
          <h3>Invitar usuario — {{ chat.nombre }}</h3>
          <p v-if="errorForm" class="error-header">{{ errorForm }}</p>
        </div>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <div class="campo">
          <label>Usuario a invitar *</label>
          <select v-model="usuarioSeleccionado" class="select-full">
            <option value="">— Selecciona un usuario —</option>
            <option v-for="u in usuariosDisponibles" :key="u.id" :value="u.id">
              {{ u.nombre }} {{ u.apellidos }} ({{ u.codigo_usuario }})
            </option>
          </select>
        </div>
        <p v-if="!usuariosDisponibles.length && !cargando" class="mensaje">
          No hay usuarios disponibles para invitar.
        </p>
      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Cancelar</button>
        <button class="btn-primario" :disabled="!usuarioSeleccionado || enviando" @click="enviar">
          {{ enviando ? 'Enviando...' : 'Enviar invitación' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
  import { useChatStore } from '@/stores/chat'
  import { useUsuariosStore } from '@/stores/usuarios'

  export default {
    name: 'ChatInvitarModal',
    emits: ['cerrar'],

    props: {
      chat: { type: Object, required: true },
    },

    data() {
      return {
        usuarioSeleccionado: '',
        cargando: false,
        enviando: false,
        errorForm: null,
      }
    },

    computed: {
      // Excluye a los miembros activos del chat del listado de invitables
      usuariosDisponibles() {
        const idsMiembros = useChatStore().miembros.map((m) => m.usuario_id)
        const miId = useUsuariosStore().usuario?.id
        return useUsuariosStore().usuarios.filter(
          (u) => u.id !== miId && !idsMiembros.includes(u.id),
        )
      },
    },

    async created() {
      this.cargando = true
      try {
        await Promise.all([
          useUsuariosStore().cargarUsuarios(),
          useChatStore().cargarMiembros(this.chat.chat_id || this.chat.id),
        ])
      } finally {
        this.cargando = false
      }
    },

    methods: {
      async enviar() {
        this.errorForm = null
        this.enviando = true
        try {
          await useChatStore().enviarInvitacion(
            this.chat.chat_id || this.chat.id,
            this.usuarioSeleccionado,
          )
          this.$emit('cerrar')
        } catch (e) {
          const detail = e.response?.data?.detail
          this.errorForm = typeof detail === 'string' ? detail : 'Error al enviar la invitación.'
        } finally {
          this.enviando = false
        }
      },
    },
  }
</script>
