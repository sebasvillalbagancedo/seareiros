-- ── Tabla sorteos ─────────────────────────────────────────────
CREATE TABLE sorteos (
    id                         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre                     VARCHAR(255) NOT NULL,
    descripcion                TEXT,
    fecha_inicio_inscripcion   TIMESTAMP    NOT NULL,
    fecha_fin_inscripcion      TIMESTAMP    NOT NULL,
    fecha_celebracion          TIMESTAMP    NOT NULL,
    numero_premios             INTEGER      NOT NULL CHECK (numero_premios > 0),
    maximo_inscritos           INTEGER,  
    fecha_nacimiento_maxima    DATE,
    fecha_nacimiento_minima    DATE,
    fecha_alta_maxima          DATE,
    estado                     VARCHAR(20)  NOT NULL DEFAULT 'abierto'
                                            CHECK (estado IN (
                                                'abierto',
                                                'pendiente',
                                                'resuelto',
                                                'cancelado'
                                            )),
    fecha_creacion             TIMESTAMP    NOT NULL DEFAULT NOW(),
    usuario_creacion           UUID         NOT NULL REFERENCES usuarios(id),
    motivo_cancelacion         TEXT,
    fecha_cancelacion          TIMESTAMP ,
    usuario_cancelacion        UUID         REFERENCES usuarios(id)
);

-- ── Tabla inscripciones_sorteos ────────────────────────────────
CREATE TABLE inscripciones_sorteos (
    id                      UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    sorteo_id               UUID      NOT NULL REFERENCES sorteos(id),
    socio_id                UUID      NOT NULL REFERENCES socios(id),
    usuario_inscripcion     UUID      NOT NULL REFERENCES usuarios(id),
    fecha_inscripcion       TIMESTAMP NOT NULL DEFAULT NOW(),
    es_ganador              BOOLEAN   NOT NULL DEFAULT FALSE,
    estado                  VARCHAR(20) NOT NULL DEFAULT 'activa'
                                  CHECK (estado IN (
                                      'activa',
                                      'cancelada'
                                  )),
    fecha_cancelacion       TIMESTAMP,
    usuario_cancelacion     UUID      REFERENCES usuarios(id),
    UNIQUE (sorteo_id, socio_id)
);

-- Garantizar que los premios no superan las plazas
ALTER TABLE sorteos ADD CONSTRAINT chk_premios_inscritos
    CHECK (numero_premios <= maximo_inscritos OR maximo_inscritos IS NULL);