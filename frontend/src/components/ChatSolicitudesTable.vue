<template>
  <table v-if="solicitudes.length">
    <thead>
      <tr>
        <th>Usuario</th>
        <th>Fecha solicitud</th>
        <th>Acción</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="s in solicitudes" :key="s.id">
        <td>{{ s.nombre_usuario }} {{ s.apellidos_usuario }}</td>
        <td>{{ formatFecha(s.fecha_solicitud) }}</td>
        <td class="acciones">
          <button
            class="btn-accion"
            :disabled="procesando === s.id"
            @click="$emit('resolver', s, true)"
          >
            Aceptar
          </button>
          <button
            class="btn-accion btn-baja"
            :disabled="procesando === s.id"
            @click="$emit('resolver', s, false)"
          >
            Rechazar
          </button>
        </td>
      </tr>
    </tbody>
  </table>
  <p v-else class="mensaje">No hay solicitudes pendientes.</p>
</template>

<script>
  import { formatFecha } from '@/utils/fecha'

  export default {
    name: 'ChatSolicitudesTable',
    emits: ['resolver'],

    props: {
      solicitudes: { type: Array, required: true },
      procesando: { type: String, default: null },
    },

    methods: {
      formatFecha,
    },
  }
</script>
