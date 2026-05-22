-- Crear la secuencia
CREATE SEQUENCE socios_numero_socio_seq START 1;

-- ── Tabla socios ─────────────────────────────────────────────────
CREATE TABLE socios (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_socio    INTEGER         NOT NULL UNIQUE DEFAULT nextval('socios_numero_socio_seq'),
    nombre          VARCHAR(255)    NOT NULL,
    apellidos       VARCHAR(255)    NOT NULL,
    fecha_nacimiento DATE,
    direccion       VARCHAR(1000),
	codigo_postal	VARCHAR(10),
	localidad		VARCHAR(100),
	provincia		VARCHAR(100),
	pais			VARCHAR(100),
    telefono_fijo   VARCHAR(20),
	telefono_movil  VARCHAR(20),
    email           VARCHAR(255),
    fecha_alta      DATE            NOT NULL DEFAULT CURRENT_DATE,
    estado          VARCHAR(20)     NOT NULL DEFAULT 'activo'
                                    CHECK (estado IN ('activo', 'baja')),
    fecha_creacion  TIMESTAMP       NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── Tabla usuarios_socios ───────────────────────────────────────────
-- Relación muchos a muchos entre usuarios y socios con histórico
CREATE TABLE usuarios_socios (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id          UUID        NOT NULL REFERENCES usuarios(id),
    socio_id            UUID        NOT NULL REFERENCES socios(id),
    fecha_asignacion    TIMESTAMP   NOT NULL DEFAULT NOW(),
    usuario_asignacion  UUID        NOT NULL REFERENCES usuarios(id),
    fecha_revocacion    TIMESTAMP,
    usuario_revocacion  UUID        REFERENCES usuarios(id)
);