"""
Planificador de tareas automáticas — Seareiros
Gestiona dos tareas periódicas relacionadas con el ciclo de vida de los sorteos:
  1. Cerrar inscripciones de sorteos cuyo plazo ha vencido (abierto → pendiente)
  2. Resolver sorteos cuya fecha de celebración ha llegado (pendiente → resuelto/cancelado)
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


def cerrar_inscripciones():
    """
    Tarea 1 — Se ejecuta cada minuto.
    Busca sorteos en estado 'abierto' cuya fecha_fin_inscripcion ya ha pasado
    y los pasa a estado 'pendiente', indicando que están listos para resolverse.
    """
    ahora = datetime.now()
    with Session(engine) as session:
        sorteos = session.exec(
            select(Sorteo).where(
                Sorteo.estado == "abierto", Sorteo.fecha_fin_inscripcion <= ahora
            )
        ).all()

        if not sorteos:
            return

        for sorteo in sorteos:
            sorteo.estado = "pendiente"
            session.add(sorteo)
            logger.info(f"Sorteo '{sorteo.nombre}' ({sorteo.id}) → pendiente")

        session.commit()


def resolver_sorteos_pendientes():
    """
    Tarea 2 — Se ejecuta cada minuto.
    Busca sorteos en estado 'pendiente' cuya fecha_celebracion ya ha llegado
    y los resuelve automáticamente seleccionando ganadores al azar.
    Si no hay inscritos activos, el sorteo pasa a cancelado.
    """
    ahora = datetime.now()
    with Session(engine) as session:
        sorteos = session.exec(
            select(Sorteo).where(
                Sorteo.estado == "pendiente", Sorteo.fecha_celebracion <= ahora
            )
        ).all()

        if not sorteos:
            return

        for sorteo in sorteos:
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
        cerrar_inscripciones,
        trigger="interval",
        minutes=1,
        id="cerrar_inscripciones",
        replace_existing=True,
    )
    scheduler.add_job(
        resolver_sorteos_pendientes,
        trigger="interval",
        minutes=1,
        id="resolver_sorteos_pendientes",
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
