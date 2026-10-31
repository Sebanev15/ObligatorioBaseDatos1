
CREATE TABLE login (
    correo     VARCHAR(255) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    rol        VARCHAR(20)  NOT NULL CHECK (rol IN ('administrador', 'planillero'))
);

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT       PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL UNIQUE
);

-- Listo en backend
CREATE TABLE jugador (
    ci               INTEGER      PRIMARY KEY,
    nombre           VARCHAR(100) NOT NULL,
    apellido         VARCHAR(100) NOT NULL,
    email            VARCHAR(255) NOT NULL UNIQUE,
    fecha_nacimiento DATE         NOT NULL,
    id_facultad      INTEGER      NOT NULL,
    tipo             VARCHAR(20)  NOT NULL
                    
    CHECK (tipo IN ('grado', 'posgrado', 'docente', 'funcionario')),
    FOREIGN KEY (id_facultad) REFERENCES facultad (id_facultad)
);

CREATE TABLE torneo (
    id_torneo    INT AUTO_INCREMENT       PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL,
    anio         INTEGER      NOT NULL,
    semestre     INTEGER      NOT NULL CHECK (semestre IN (1, 2)),
    fecha_inicio DATE         NOT NULL,
    fecha_fin    DATE         NOT NULL,
    estado       VARCHAR(20)  NOT NULL DEFAULT 'inscripcion'
    CHECK (estado IN ('inscripcion', 'en curso', 'finalizado')),
    CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE equipo (
    id_equipo   INT AUTO_INCREMENT       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    id_torneo   INTEGER      NOT NULL,
    id_facultad INTEGER      NOT NULL,
    ci_capitan  INTEGER,     -- puede ser NULL al crear el equipo; se asigna después
    FOREIGN KEY (id_torneo)   REFERENCES torneo (id_torneo),
    FOREIGN KEY (id_facultad) REFERENCES facultad (id_facultad),
    UNIQUE (nombre, id_torneo),
    UNIQUE (id_equipo, id_torneo)        -- para poder referenciarla desde otras tablas
);

CREATE TABLE equipo_jugador_torneo (
    id_equipo       INTEGER  NOT NULL,
    ci_jugador      INTEGER  NOT NULL,
    id_torneo       INTEGER  NOT NULL,
    numero_camiseta INTEGER  NOT NULL CHECK (numero_camiseta BETWEEN 1 AND 99),
    PRIMARY KEY (id_equipo, ci_jugador, id_torneo),
    FOREIGN KEY (ci_jugador) REFERENCES jugador (ci),
    FOREIGN KEY (id_equipo, id_torneo) REFERENCES equipo (id_equipo, id_torneo),
    UNIQUE (ci_jugador, id_torneo),      -- un jugador, un solo equipo por torneo
    UNIQUE (id_equipo, numero_camiseta), -- camiseta no repetida en el equipo
    UNIQUE (id_equipo, ci_jugador)       -- para referenciarla desde equipo (capitán)
);

-- El capitán debe ser jugador del mismo equipo
ALTER TABLE equipo
    ADD FOREIGN KEY (id_equipo, ci_capitan)
    REFERENCES equipo_jugador_torneo (id_equipo, ci_jugador);

-- Listo en backend
CREATE TABLE complejo (
    id_complejo  INT AUTO_INCREMENT       PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL,
    direccion    VARCHAR(255) NOT NULL,
    departamento VARCHAR(100) NOT NULL
);

-- Listo en backend
CREATE TABLE cancha (
    nombre_cancha VARCHAR(100) NOT NULL,
    id_complejo   INTEGER      NOT NULL,
    superficie    VARCHAR(20)  NOT NULL CHECK (superficie IN ('sintetico', 'parquet')),
    techada       BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (nombre_cancha, id_complejo),
    FOREIGN KEY (id_complejo) REFERENCES complejo (id_complejo)
);

CREATE TABLE turno (
    id_turno    INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME   NOT NULL,
    hora_fin    TIME   NOT NULL,
    CHECK (hora_fin > hora_inicio)
);

CREATE TABLE partido (
    id_partido          INT AUTO_INCREMENT       PRIMARY KEY,
    id_torneo           INTEGER      NOT NULL,
    numero_fecha        INTEGER      NOT NULL CHECK (numero_fecha > 0),
    id_equipo_local     INTEGER      NOT NULL,
    id_equipo_visitante INTEGER      NOT NULL,
    dia                 DATE         NOT NULL,
    id_turno            INTEGER      NOT NULL,
    nombre_cancha       VARCHAR(100) NOT NULL,
    id_complejo         INTEGER      NOT NULL,
    estado              VARCHAR(20)  NOT NULL DEFAULT 'programado'
    CHECK (estado IN ('programado', 'jugado', 'postergado', 'cancelado')),
    FOREIGN KEY (id_torneo) REFERENCES torneo (id_torneo),
    FOREIGN KEY (id_turno)  REFERENCES turno (id_turno),
    FOREIGN KEY (nombre_cancha, id_complejo) REFERENCES cancha (nombre_cancha, id_complejo),
    -- ambos equipos deben ser del torneo del partido
    FOREIGN KEY (id_equipo_local,     id_torneo) REFERENCES equipo (id_equipo, id_torneo),
    FOREIGN KEY (id_equipo_visitante, id_torneo) REFERENCES equipo (id_equipo, id_torneo),
    CHECK (id_equipo_local <> id_equipo_visitante),
    -- una cancha no puede tener dos partidos el mismo día y turno
    UNIQUE (dia, id_turno, nombre_cancha, id_complejo)
);

CREATE TABLE planilla_partido (
    id_partido INTEGER NOT NULL,
    ci_jugador INTEGER NOT NULL,
    id_equipo  INTEGER NOT NULL,
    PRIMARY KEY (id_partido, ci_jugador),
    FOREIGN KEY (id_partido) REFERENCES partido (id_partido),
    -- el jugador debe estar inscripto en ese equipo
    FOREIGN KEY (id_equipo, ci_jugador) REFERENCES equipo_jugador_torneo (id_equipo, ci_jugador)
);

CREATE TABLE gol (
    id_gol     INT AUTO_INCREMENT   PRIMARY KEY,
    id_partido INTEGER  NOT NULL,
    ci_jugador INTEGER  NOT NULL,
    minuto     INTEGER  NOT NULL CHECK (minuto BETWEEN 0 AND 130),
    autogol    BOOLEAN  NOT NULL DEFAULT FALSE,
    -- el jugador debe figurar en la planilla de ese partido
    FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido (id_partido, ci_jugador)
);

CREATE TABLE tarjeta (
    id_tarjeta INT AUTO_INCREMENT      PRIMARY KEY,
    id_partido INTEGER     NOT NULL,
    ci_jugador INTEGER     NOT NULL,
    minuto     INTEGER     NOT NULL CHECK (minuto BETWEEN 0 AND 130),
    color      VARCHAR(10) NOT NULL CHECK (color IN ('amarilla', 'roja')),
    FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido (id_partido, ci_jugador)
);

CREATE TABLE sancion_jugador (
    id_sancion          INT AUTO_INCREMENT      PRIMARY KEY,
    ci_jugador          INTEGER     NOT NULL,
    id_torneo           INTEGER     NOT NULL,
    motivo              VARCHAR(30) NOT NULL
    CHECK (motivo IN ('roja', 'acumulacion de amarillas', 'disciplinaria')),
    numero_fecha_inicio INTEGER     NOT NULL CHECK (numero_fecha_inicio > 0),
    cantidad_fechas     INTEGER     NOT NULL CHECK (cantidad_fechas > 0),
    FOREIGN KEY (ci_jugador) REFERENCES jugador (ci),
    FOREIGN KEY (id_torneo)  REFERENCES torneo (id_torneo)
);

-- Orden recomendado para cargar un equipo:
--   1) INSERT en equipo (ci_capitan NULL)
--   2) INSERT en equipo_jugador_torneo
--   3) UPDATE equipo SET ci_capitan = ... WHERE id_equipo = ...