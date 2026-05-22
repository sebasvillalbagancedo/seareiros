<template>
  <div class="modal-overlay" @click.self="$emit('cerrar')">
    <div class="modal modal-sm">
      <div class="modal-header">
        <h3>Nueva Conversación</h3>
        <button class="btn-cerrar" @click="$emit('cerrar')">✕</button>
      </div>

      <div class="modal-body">
        <div class="campo">
          <label>Destinatario *</label>
          <select v-model="usuarioSeleccionado" class="select-full">
            <option value="">— Selecciona un usuario —</option>
            <option v-for="u in usuariosDisponibles" :key="u.id" :value="u.id">
              {{ u.nombre }} {{ u.apellidos }} ({{ u.codigo_usuario }})
            </option>
          </select>
        </div>
        <p v-if="!usuariosDisponibles.length && !cargando" class="mensaje">
          No hay usuarios disponibles para iniciar una nueva conversación.
        </p>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-secundario" @click="$emit('cerrar')">Cancelar</button>
        <button
          class="btn-primario"
          :disabled="!usuarioSeleccionado || cargando"
          @click="confirmar"
        >
          {{ cargando ? '...' : 'Iniciar conversación' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
  import { useUsuariosStore } from '@/stores/usuarios'
  import { useChatStore } from '@/stores/chat'

  export default {
    name: 'NuevaConversacionModal',
    emits: ['cerrar', 'seleccionada'],

    data() {
      return {
        usuarioSeleccionado: '',
        cargando: false,
        error: null,
      }
    },

    computed: {
      usuariosDisponibles() {
        const miId = useUsuariosStore().usuario?.id
        const idsConConversacion = useChatStore().idsConversacionDirecta
        return useUsuariosStore().usuarios.filter(
          (u) =>
            // Excluir al propio usuario
            u.id !== miId &&
            // Excluir usuarios con los que ya hay conversación directa
            !idsConConversacion.includes(u.id),
        )
      },
    },

    async created() {
      this.cargando = true
      try {
        await useUsuariosStore().cargarUsuarios()
      } finally {
        this.cargando = false
      }
    },

    methods: {
      async confirmar() {
        if (!this.usuarioSeleccionado) return
        const usuario = this.usuariosDisponibles.find((u) => u.id === this.usuarioSeleccionado)
        this.$emit('seleccionada', usuario)
      },
    },
  }
</script>
