<template>
  <table v-if="miembros.length">
    <thead>
      <tr>
        <th>Usuario</th>
        <th>Rol</th>
        <th v-if="esAdminChat">Acciones</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="m in miembros" :key="m.id">
        <td>{{ m.nombre_usuario }} {{ m.apellidos_usuario }}</td>
        <td>
          <span
            class="badge"
            :class="m.rol === 'administrador' ? 'badge-activo' : 'badge-pendiente'"
            >{{ m.rol }}</span
          >
        </td>
        <td v-if="esAdminChat" class="acciones">
          <button
            v-if="m.rol === 'miembro'"
            class="btn-accion"
            :disabled="procesando === m.id"
            @click="$emit('promover', m)"
          >
            Hacer admin
          </button>
          <button
            v-else-if="m.rol_sistema !== 'administrador'"
            class="btn-accion"
            :disabled="procesando === m.id"
            @click="$emit('degradar', m)"
          >
            Quitar admin
          </button>
          <button
            class="btn-accion btn-baja"
            :disabled="procesando === m.id"
            @click="$emit('dar-baja', m)"
          >
            Dar de baja
          </button>
        </td>
      </tr>
    </tbody>
  </table>
  <p v-else class="mensaje">No hay miembros activos.</p>
</template>

<script>
  export default {
    name: 'ChatMiembrosTable',
    emits: ['promover', 'degradar', 'dar-baja'],

    props: {
      miembros: { type: Array, required: true },
      esAdminChat: { type: Boolean, default: false },
      procesando: { type: String, default: null },
    },
  }
</script>
