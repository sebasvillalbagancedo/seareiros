CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE usuarios (
    id              		UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_usuario  		VARCHAR(50)     NOT NULL UNIQUE,
    email           		VARCHAR(255)    NOT NULL UNIQUE,
    contrasena_cifrada   	VARCHAR(255)    NOT NULL,
	nombre          		VARCHAR(255)    NOT NULL,
    apellidos       		VARCHAR(255)    NOT NULL,
    rol             		VARCHAR(20)     NOT NULL DEFAULT 'normal'
                                    			CHECK (rol IN ('administrador', 'normal')),
    estado          		VARCHAR(20)     NOT NULL DEFAULT 'activa'
                                    			CHECK (estado IN ('activa', 'bloqueada', 'inactiva')),
    fecha_creacion      	TIMESTAMP       NOT NULL DEFAULT NOW(),
    fecha_ult_conexion 		TIMESTAMP
);