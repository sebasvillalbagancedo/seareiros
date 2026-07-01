"""
Planificador de tareas automáticas — Seareiros
Gestiona el ciclo de vida automático de sorteos y eventos:
  - Sorteos: encadena en una única tarea el cierre de inscripciones vencidas
    (abierto → pendiente) y la resolución de sorteos cuya fecha de celebración
    ya ha llegado (pendiente → resuelto/cancelado)
  - Eventos: marca como celebrados los eventos cuya fecha de celebración ya ha llegado
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select
from app.database import engine
from app.models.sorteo import Sorteo
from app.models.evento import Evento
from app.services.sorteos import resolver_sorteo_automatico
from app.services.eventos import celebrar_evento

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


# ── Tareas de sorteos ─────────────────────────────────────────────


def procesar_sorteos():
    """
    Tarea única — Se ejecuta cada minuto.
    Encadena, en la misma ejecución y la misma sesión de BD, los dos pasos
    del ciclo de vida del sorteo:
      1. abierto → pendiente  (cuando fecha_fin_inscripcion ya ha pasado)
      2. pendiente → resuelto/cancelado (cuando fecha_celebracion ya ha llegado)

    Encadenar ambos pasos en un único job evita que un sorteo cuya
    fecha_fin_inscripcion coincide con su fecha_celebracion (o la fecha_celebracion
    es anterior/igual al momento de cierre) tenga que esperar al siguiente
    ciclo del planificador para resolverse.
    """
    ahora = datetime.now()
    with Session(engine) as session:
        # Paso 1: cerrar inscripciones vencidas
        sorteos_a_cerrar = session.exec(
            select(Sorteo).where(
                Sorteo.estado == "abierto", Sorteo.fecha_fin_inscripcion <= ahora
            )
        ).all()

        for sorteo in sorteos_a_cerrar:
            sorteo.estado = "pendiente"
            session.add(sorteo)
            logger.info(f"Sorteo '{sorteo.nombre}' ({sorteo.id}) → pendiente")

        if sorteos_a_cerrar:
            session.commit()
            for sorteo in sorteos_a_cerrar:
                session.refresh(sorteo)

        # Paso 2: resolver pendientes cuya fecha de celebración ya ha llegado
        sorteos_a_resolver = session.exec(
            select(Sorteo).where(
                Sorteo.estado == "pendiente", Sorteo.fecha_celebracion <= ahora
            )
        ).all()

        for sorteo in sorteos_a_resolver:
            try:
                sorteo_actualizado, ganadores = resolver_sorteo_automatico(sorteo, session)
                if ganadores:
                    logger.info(
                        f"Sorteo '{sorteo.nombre}' resuelto — "
                        f"{len(ganadores)} ganador(es) seleccionado(s)"
                    )
                else:
                    logger.info(
                        f"Sorteo '{sorteo.nombre}' cancelado — "
                        f"sin inscritos en el momento de la resolución"
                    )
            except Exception as e:
                logger.error(
                    f"Error al resolver sorteo '{sorteo.nombre}' ({sorteo.id}): {e}"
                )


# ── Tareas de eventos ─────────────────────────────────────────────
def celebrar_eventos_pendientes():
    """
    Tarea 3 — Se ejecuta cada minuto.
    Busca eventos en estado 'abierto' o 'completo' cuya fecha_celebracion
    ya ha llegado y los marca automáticamente como 'celebrado'.
    Las inscripciones pendientes se mantienen en su estado actual.
    """
    ahora = datetime.now()
    with Session(engine) as session:
        eventos = session.exec(
            select(Evento).where(
                Evento.estado.in_(["abierto", "completo"]),
                Evento.fecha_celebracion <= ahora,
            )
        ).all()

        if not eventos:
            return

        for evento in eventos:
            try:
                celebrar_evento(evento, session)
                logger.info(f"Evento '{evento.nombre}' ({evento.id}) → celebrado")
            except Exception as e:
                logger.error(
                    f"Error al celebrar evento '{evento.nombre}' ({evento.id}): {e}"
                )


# ── Arranque ──────────────────────────────────────────────────────


def iniciar_scheduler():
    """
    Registra las tareas y arranca el planificador en segundo plano.
    Se llama una única vez al arrancar la aplicación FastAPI.
    """
    # Ejecutar cada minuto
    scheduler.add_job(
        procesar_sorteos,
        trigger="interval",
        minutes=1,
        id="procesar_sorteos",
        replace_existing=True,
    )
    scheduler.add_job(
        celebrar_eventos_pendientes,
        trigger="interval",
        minutes=1,
        id="celebrar_eventos_pendientes",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Planificador del sistema iniciado")
