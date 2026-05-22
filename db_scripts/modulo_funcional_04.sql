-- ── Tabla chat ─────────────────────────────────────────
CREATE TABLE chats (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre              VARCHAR(255) NOT NULL,
    descripcion         TEXT,
    tipo_acceso         VARCHAR(20)  NOT NULL
                                     CHECK (tipo_acceso IN ('libre', 'restringido')),
    modalidad           VARCHAR(20)  NOT NULL
                                     CHECK (modalidad IN ('bidireccional', 'canal')),
    visibilidad         VARCHAR(20)  NOT NULL
                                     CHECK (visibilidad IN ('visible', 'oculta')),
    fecha_creacion      TIMESTAMP    NOT NULL DEFAULT NOW(),
    usuario_creacion    UUID         NOT NULL REFERENCES usuarios(id)
);

-- ── Tabla miembros_chats ────────────────────────────────
CREATE TABLE miembros_chats (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id             UUID            NOT NULL REFERENCES chats(id),
    usuario_id          UUID            NOT NULL REFERENCES usuarios(id),
    rol                 VARCHAR(20)     NOT NULL DEFAULT 'miembro'
                                        CHECK (rol IN ('miembro', 'administrador')),
    estado              VARCHAR(10)     NOT NULL DEFAULT 'activo'
                                        CHECK (estado IN ('activo', 'baja')),
    fecha_incorporacion TIMESTAMP       NOT NULL DEFAULT NOW(),
    usuario_baja        UUID            REFERENCES usuarios(id),
    fecha_baja          TIMESTAMP
);

-- ── Tabla solicitudes_chats ────────────────────────────────
CREATE TABLE solicitudes_chats (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id             UUID        NOT NULL REFERENCES chats(id),
    usuario_id          UUID        NOT NULL REFERENCES usuarios(id),
    estado              VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                                    CHECK (estado IN ('pendiente', 'aceptada', 'rechazada')),
    fecha_solicitud     TIMESTAMP   NOT NULL DEFAULT NOW(),
    fecha_resolucion    TIMESTAMP,
    usuario_resolucion  UUID        REFERENCES usuarios(id)
);

-- ── Tabla solicitudes_chats ────────────────────────────────
CREATE TABLE invitaciones_chats (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id              UUID        NOT NULL REFERENCES chats(id),
    usuario_destinatario UUID        NOT NULL REFERENCES usuarios(id),
    usuario_invitacion   UUID        NOT NULL REFERENCES usuarios(id),
    fecha_invitacion     TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado               VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                                     CHECK (estado IN ('pendiente', 'aceptada', 'rechazada')),
    fecha_resolucion     TIMESTAMP
);

-- ── Tabla mensajes ────────────────────────────────────────────
CREATE TABLE mensajes (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    contenido           TEXT            NOT NULL,
    usuario_envio       UUID            NOT NULL REFERENCES usuarios(id),
    fecha_envio         TIMESTAMP       NOT NULL DEFAULT NOW(),
    chat_id             UUID            REFERENCES chats(id) -- NULL = mensaje directo, NOT NULL = mensaje de chat
);

-- ── Tabla mensajes_destinatarios ─────────────────────────────
CREATE TABLE mensajes_destinatarios (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    mensaje_id              UUID            NOT NULL REFERENCES mensajes(id),
    usuario_destinatario    UUID            NOT NULL REFERENCES usuarios(id),
    fecha_recepcion         TIMESTAMP,
    fecha_lectura           TIMESTAMP,
    estado                  VARCHAR(20)     NOT NULL DEFAULT 'enviado'
                                            CHECK (estado IN ('enviado', 'recibido', 'leido')),
    UNIQUE (mensaje_id, usuario_destinatario)
);