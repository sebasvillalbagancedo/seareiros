/**
 * Formatea una fecha ISO mostrando día, mes, año, hora y minutos.
 * Devuelve '—' si el valor es nulo o indefinido.
 */

export function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

/**
 * Formatea una fecha ISO mostrando solo hora y minutos.
 * Devuelve '' si el valor es nulo o indefinido.
 */
export function formatHora(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('es-ES', {
    hour: '2-digit', minute: '2-digit'
  })
}