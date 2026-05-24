-- ── Tabla eventos ─────────────────────────────────────────────
CREATE TABLE eventos (
    id                         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre                     VARCHAR(255) NOT NULL,
    descripcion                TEXT,
    lugar                      VARCHAR(255),
    fecha_celebracion          TIMESTAMP    NOT NULL,
    fecha_inicio_inscripcion   TIMESTAMP    NOT NULL,
    fecha_fin_inscripcion      TIMESTAMP    NOT NULL,
    plazas_disponibles         INTEGER      NOT NULL CHECK (plazas_disponibles > 0),
    fecha_nacimiento_maxima    DATE,
    fecha_nacimiento_minima    DATE,
    fecha_alta_maxima          DATE,
    estado                     VARCHAR(20)  NOT NULL DEFAULT 'abierto'
                                            CHECK (estado IN (
                                                'abierto',
                                                'completo',
                                                'celebrado',
                                                'cancelado'
                                            )),
    fecha_creacion             TIMESTAMP    NOT NULL DEFAULT NOW(),
    usuario_creacion           UUID         NOT NULL REFERENCES usuarios(id),
    motivo_cancelacion         TEXT,
    fecha_cancelacion          TIMESTAMP ,
    usuario_cancelacion        UUID         REFERENCES usuarios(id)
);

-- ── Tabla inscripciones_eventos ────────────────────────────────
CREATE TABLE inscripciones_eventos (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id               UUID        NOT NULL REFERENCES eventos(id),
    socio_id                UUID        NOT NULL REFERENCES socios(id),
    usuario_inscripcion     UUID        NOT NULL REFERENCES usuarios(id),
    fecha_inscripcion       TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado                  VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                                        CHECK (estado IN ('pendiente', 'confirmada', 'rechazada', 'cancelada')),
    usuario_gestion     UUID            REFERENCES usuarios(id),
    fecha_gestion       TIMESTAMP,
    UNIQUE (evento_id, socio_id)
);