

-- Usuarios (contraseñas guardadas como hash SHA-256)
INSERT INTO login (correo, contrasena, rol) VALUES
('admin@torneo.edu.uy',       SHA2('admin123', 256),  'administrador'),
('planillero1@torneo.edu.uy', SHA2('planilla1', 256), 'planillero'),
('planillero2@torneo.edu.uy', SHA2('planilla2', 256), 'planillero');

INSERT INTO facultad (id_facultad, nombre) VALUES

(1, 'Facultad de Ingeniería'),
(2, 'Facultad de Ciencias Económicas'),
(3, 'Facultad de Derecho'),
(4, 'Facultad de Medicina'),
(5, 'Facultad de Arquitectura'),
(6, 'Facultad de Humanidades');


INSERT INTO complejo (id_complejo, nombre, direccion, departamento) VALUES
(1, 'Complejo Deportivo Norte', 'Av. de las Instrucciones 1850', 'Montevideo'),
(2, 'Fútbol 7 Costa',           'Rambla Costanera 4520',         'Canelones'),
(3, 'Complejo Sur',             'Bulevar Artigas 2210',          'Montevideo');

INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
('Cancha 1', 1, 'sintetico', FALSE),
('Cancha 2', 1, 'sintetico', TRUE),
('Cancha A', 2, 'parquet',   TRUE),
('Cancha B', 2, 'sintetico', FALSE),
('Cancha 1', 3, 'sintetico', FALSE);

INSERT INTO turno (id_turno, hora_inicio, hora_fin) VALUES
(1, '18:00:00', '19:00:00'),
(2, '19:00:00', '20:00:00'),
(3, '20:00:00', '21:00:00'),
(4, '21:00:00', '22:00:00');

INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
(1, 'Copa Interfacultades', 2026, 2, '2026-09-26', '2026-12-05', 'en curso');

-- Jugadores (8 por equipo; el id_facultad coincide con el de su equipo)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES

(3599625, 'Martín', 'González', 'martin.gonzalez@correo.edu.uy', '2005-07-27', 1, 'grado'),
(4440015, 'Lucía', 'López', 'lucia.lopez@correo.edu.uy', '2005-03-21', 1, 'grado'),
(5207703, 'Santiago', 'Medina', 'santiago.medina@correo.edu.uy', '2004-08-03', 1, 'grado'),
(5246740, 'Valentina', 'Moreira', 'valentina.moreira@correo.edu.uy', '2000-04-21', 1, 'grado'),
(3530490, 'Mateo', 'Machado', 'mateo.machado@correo.edu.uy', '2003-10-09', 1, 'grado'),
(4036523, 'Camila', 'Martínez', 'camila.martinez@correo.edu.uy', '1995-09-06', 1, 'posgrado'),
(5434377, 'Joaquín', 'Cabrera', 'joaquin.cabrera@correo.edu.uy', '2007-05-31', 1, 'grado'),
(4864186, 'Sofía', 'Sosa', 'sofia.sosa@correo.edu.uy', '1988-06-17', 1, 'funcionario'),
(5501527, 'Nicolás', 'Píriz', 'nicolas.piriz@correo.edu.uy', '2004-07-04', 2, 'grado'),
(5397687, 'Agustina', 'Pérez', 'agustina.perez@correo.edu.uy', '2003-06-19', 2, 'grado'),
(5159002, 'Federico', 'Núñez', 'federico.nunez@correo.edu.uy', '2004-11-18', 2, 'grado'),
(5560046, 'Florencia', 'Rivero', 'florencia.rivero@correo.edu.uy', '2001-11-25', 2, 'grado'),
(4950086, 'Gonzalo', 'Olivera', 'gonzalo.olivera@correo.edu.uy', '2003-09-17', 2, 'grado'),
(4106356, 'Micaela', 'Rodríguez', 'micaela.rodriguez@correo.edu.uy', '1996-04-29', 2, 'posgrado'),
(3110631, 'Sebastián', 'Díaz', 'sebastian.diaz@correo.edu.uy', '2004-05-16', 2, 'grado'),
(3438579, 'Carolina', 'Ferreira', 'carolina.ferreira@correo.edu.uy', '1986-07-04', 2, 'docente'),
(3564462, 'Diego', 'Vázquez', 'diego.vazquez@correo.edu.uy', '2004-10-22', 3, 'grado'),
(4304772, 'Natalia', 'Ramos', 'natalia.ramos@correo.edu.uy', '1999-04-14', 3, 'grado'),
(3511258, 'Matías', 'Silva', 'matias.silva@correo.edu.uy', '2005-06-15', 3, 'grado'),
(4985989, 'Romina', 'Acosta', 'romina.acosta@correo.edu.uy', '2001-07-08', 3, 'grado'),
(3148187, 'Facundo', 'Correa', 'facundo.correa@correo.edu.uy', '2007-08-03', 3, 'grado'),
(5156411, 'Paula', 'Britos', 'paula.britos@correo.edu.uy', '1991-06-13', 3, 'posgrado'),
(4417989, 'Andrés', 'García', 'andres.garcia@correo.edu.uy', '1999-07-20', 3, 'grado'),
(3981746, 'Victoria', 'Techera', 'victoria.techera@correo.edu.uy', '1986-09-26', 3, 'funcionario'),
(4766050, 'Martín', 'Moreira', 'martin.moreira@correo.edu.uy', '2006-07-09', 4, 'grado'),
(4154922, 'Lucía', 'Machado', 'lucia.machado@correo.edu.uy', '2000-02-25', 4, 'grado'),
(4558182, 'Santiago', 'Martínez', 'santiago.martinez@correo.edu.uy', '2007-01-17', 4, 'grado'),
(4595840, 'Valentina', 'Cabrera', 'valentina.cabrera@correo.edu.uy', '2005-12-23', 4, 'grado'),
(4678503, 'Mateo', 'Sosa', 'mateo.sosa@correo.edu.uy', '2003-10-25', 4, 'grado'),
(5254142, 'Camila', 'Píriz', 'camila.piriz@correo.edu.uy', '1995-04-10', 4, 'posgrado'),
(3420108, 'Joaquín', 'Pérez', 'joaquin.perez@correo.edu.uy', '2000-08-06', 4, 'grado'),
(4527718, 'Sofía', 'Núñez', 'sofia.nunez@correo.edu.uy', '1985-10-24', 4, 'docente'),
(3476082, 'Nicolás', 'Rivero', 'nicolas.rivero@correo.edu.uy', '2001-07-26', 5, 'grado'),
(5438117, 'Agustina', 'Olivera', 'agustina.olivera@correo.edu.uy', '2000-05-14', 5, 'grado'),
(5356807, 'Federico', 'Rodríguez', 'federico.rodriguez@correo.edu.uy', '2006-01-10', 5, 'grado'),
(4325247, 'Florencia', 'Díaz', 'florencia.diaz@correo.edu.uy', '2006-11-10', 5, 'grado'),
(4306289, 'Gonzalo', 'Ferreira', 'gonzalo.ferreira@correo.edu.uy', '2004-02-15', 5, 'grado'),
(5018675, 'Micaela', 'Vázquez', 'micaela.vazquez@correo.edu.uy', '1997-07-24', 5, 'posgrado'),
(3690928, 'Sebastián', 'Ramos', 'sebastian.ramos@correo.edu.uy', '2004-04-06', 5, 'grado'),
(5521889, 'Carolina', 'Silva', 'carolina.silva@correo.edu.uy', '1987-03-28', 5, 'funcionario'),
(4396034, 'Diego', 'Acosta', 'diego.acosta@correo.edu.uy', '2001-10-25', 6, 'grado'),
(3203764, 'Natalia', 'Correa', 'natalia.correa@correo.edu.uy', '2005-04-11', 6, 'grado'),
(4647046, 'Matías', 'Britos', 'matias.britos@correo.edu.uy', '2003-07-05', 6, 'grado'),
(4624806, 'Romina', 'García', 'romina.garcia@correo.edu.uy', '2006-07-06', 6, 'grado'),
(5033878, 'Facundo', 'Techera', 'facundo.techera@correo.edu.uy', '2002-06-14', 6, 'grado'),
(4870908, 'Paula', 'Castro', 'paula.castro@correo.edu.uy', '1996-02-24', 6, 'posgrado'),
(3480357, 'Andrés', 'Cardozo', 'andres.cardozo@correo.edu.uy', '2007-12-20', 6, 'grado'),
(4772576, 'Victoria', 'Fernández', 'victoria.fernandez@correo.edu.uy', '1986-04-04', 6, 'docente');


-- Equipos (el capitán se asigna después de inscribir a los jugadores)
INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES

(1, 'Ingeniería FC', 1, 1, NULL),
(2, 'Económicas United', 1, 2, NULL),
(3, 'Derecho Atlético', 1, 3, NULL),
(4, 'Medicina Sporting', 1, 4, NULL),
(5, 'Arquitectura Rovers', 1, 5, NULL),
(6, 'Humanidades City', 1, 6, NULL);


-- Inscripción de jugadores por equipo: (equipo, jugador, torneo, camiseta)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES

(1, 3599625, 1, 1),
(1, 4440015, 1, 2),
(1, 5207703, 1, 3),
(1, 5246740, 1, 4),
(1, 3530490, 1, 5),
(1, 4036523, 1, 7),
(1, 5434377, 1, 9),
(1, 4864186, 1, 10),
(2, 5501527, 1, 1),
(2, 5397687, 1, 2),
(2, 5159002, 1, 3),
(2, 5560046, 1, 4),
(2, 4950086, 1, 5),
(2, 4106356, 1, 7),
(2, 3110631, 1, 9),
(2, 3438579, 1, 10),
(3, 3564462, 1, 1),
(3, 4304772, 1, 2),
(3, 3511258, 1, 3),
(3, 4985989, 1, 4),
(3, 3148187, 1, 5),
(3, 5156411, 1, 7),
(3, 4417989, 1, 9),
(3, 3981746, 1, 10),
(4, 4766050, 1, 1),
(4, 4154922, 1, 2),
(4, 4558182, 1, 3),
(4, 4595840, 1, 4),
(4, 4678503, 1, 5),
(4, 5254142, 1, 7),
(4, 3420108, 1, 9),
(4, 4527718, 1, 10),
(5, 3476082, 1, 1),
(5, 5438117, 1, 2),
(5, 5356807, 1, 3),
(5, 4325247, 1, 4),
(5, 4306289, 1, 5),
(5, 5018675, 1, 7),
(5, 3690928, 1, 9),
(5, 5521889, 1, 10),
(6, 4396034, 1, 1),
(6, 3203764, 1, 2),
(6, 4647046, 1, 3),
(6, 4624806, 1, 4),
(6, 5033878, 1, 5),
(6, 4870908, 1, 7),
(6, 3480357, 1, 9),
(6, 4772576, 1, 10);


-- Capitanes (jugador con camiseta 5 de cada equipo)

UPDATE equipo SET ci_capitan = 3530490 WHERE id_equipo = 1;
UPDATE equipo SET ci_capitan = 4950086 WHERE id_equipo = 2;
UPDATE equipo SET ci_capitan = 3148187 WHERE id_equipo = 3;
UPDATE equipo SET ci_capitan = 4678503 WHERE id_equipo = 4;
UPDATE equipo SET ci_capitan = 4306289 WHERE id_equipo = 5;
UPDATE equipo SET ci_capitan = 5033878 WHERE id_equipo = 6;

-- ---------------------------------------------------------------------
-- 3) PARTIDOS
-- (id, torneo, fecha, local, visitante, día, turno, cancha, complejo, estado)
-- ---------------------------------------------------------------------
INSERT INTO partido (id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES

(1, 1, 1, 1, 6, '2026-09-26', 1, 'Cancha 1', 1, 'jugado'),
(2, 1, 1, 2, 5, '2026-09-26', 1, 'Cancha 2', 1, 'jugado'),
(3, 1, 1, 3, 4, '2026-09-26', 2, 'Cancha 1', 1, 'jugado'),
(4, 1, 2, 1, 5, '2026-10-03', 2, 'Cancha A', 2, 'jugado'),
(5, 1, 2, 6, 4, '2026-10-03', 3, 'Cancha B', 2, 'jugado'),
(6, 1, 2, 2, 3, '2026-10-03', 3, 'Cancha 1', 1, 'jugado'),
(7, 1, 3, 1, 4, '2026-10-10', 1, 'Cancha 1', 1, 'jugado'),
(8, 1, 3, 3, 5, '2026-10-10', 2, 'Cancha 2', 1, 'jugado'),
(9, 1, 3, 2, 6, '2026-10-10', 1, 'Cancha 1', 3, 'jugado'),
(10, 1, 4, 1, 3, '2026-10-24', 1, 'Cancha 1', 1, 'programado'),
(11, 1, 4, 4, 2, '2026-10-24', 2, 'Cancha 2', 1, 'programado'),
(12, 1, 4, 5, 6, '2026-10-24', 3, 'Cancha 1', 3, 'postergado'),
(13, 1, 5, 1, 2, '2026-10-31', 1, 'Cancha A', 2, 'programado'),
(14, 1, 5, 3, 6, '2026-10-31', 2, 'Cancha A', 2, 'programado'),
(15, 1, 5, 4, 5, '2026-10-31', 3, 'Cancha B', 2, 'cancelado');


-- Planilla de los partidos JUGADOS: se anota todo el plantel (8 jugadores)
-- de los dos equipos de cada partido.
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo)
SELECT p.id_partido, ejt.ci_jugador, ejt.id_equipo
FROM partido p
JOIN equipo_jugador_torneo ejt
  ON ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
WHERE p.estado = 'jugado';


-- ---------------------------------------------------------------------
-- 4) GOLES  (partido, jugador, minuto, autogol)
-- Un autogol suma al equipo rival del jugador que lo convierte.
-- ---------------------------------------------------------------------
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES

(1, 5434377, 12, FALSE),  -- Ingeniería FC #9
(1, 5434377, 30, FALSE),  -- Ingeniería FC #9
(1, 4864186, 45, FALSE),  -- Ingeniería FC #10
(1, 3480357, 22, FALSE),  -- Humanidades City #9
(2, 3110631, 8, FALSE),  -- Económicas United #9
(2, 5521889, 15, FALSE),  -- Arquitectura Rovers #10
(2, 5521889, 33, FALSE),  -- Arquitectura Rovers #10
(2, 3438579, 41, FALSE),  -- Económicas United #10
(3, 3420108, 38, FALSE),  -- Medicina Sporting #9
(4, 4864186, 5, FALSE),  -- Ingeniería FC #10
(4, 3690928, 20, FALSE),  -- Arquitectura Rovers #9
(4, 5434377, 44, FALSE),  -- Ingeniería FC #9
(6, 3110631, 10, FALSE),  -- Económicas United #9
(6, 4417989, 30, FALSE),  -- Derecho Atlético #9
(6, 4106356, 25, FALSE),  -- Económicas United #7
(6, 3981746, 48, FALSE),  -- Derecho Atlético #10
(6, 4985989, 49, TRUE),  -- Derecho Atlético #4 (autogol)
(7, 4527718, 27, FALSE),  -- Medicina Sporting #10
(8, 4417989, 14, FALSE),  -- Derecho Atlético #9
(8, 3690928, 40, FALSE),  -- Arquitectura Rovers #9
(9, 3110631, 6, FALSE),  -- Económicas United #9
(9, 3110631, 33, FALSE);  -- Económicas United #9


-- ---------------------------------------------------------------------
-- 5) TARJETAS  (partido, jugador, minuto, color)
-- ---------------------------------------------------------------------
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES

(1, 4647046, 18, 'amarilla'),  -- Humanidades City #3
(1, 3530490, 40, 'amarilla'),  -- Ingeniería FC #5
(2, 4306289, 30, 'amarilla'),  -- Arquitectura Rovers #5
(2, 5159002, 44, 'amarilla'),  -- Económicas United #3
(3, 4985989, 20, 'amarilla'),  -- Derecho Atlético #4
(4, 4306289, 12, 'amarilla'),  -- Arquitectura Rovers #5
(4, 5207703, 33, 'amarilla'),  -- Ingeniería FC #3
(5, 3203764, 15, 'amarilla'),  -- Humanidades City #2
(5, 4595840, 36, 'amarilla'),  -- Medicina Sporting #4
(6, 4985989, 35, 'amarilla'),  -- Derecho Atlético #4
(6, 4950086, 20, 'amarilla'),  -- Económicas United #5
(7, 4558182, 45, 'roja'),  -- Medicina Sporting #3
(7, 5434377, 30, 'amarilla'),  -- Ingeniería FC #9
(8, 4985989, 22, 'amarilla'),  -- Derecho Atlético #4
(8, 5356807, 47, 'amarilla'),  -- Arquitectura Rovers #3
(9, 5033878, 40, 'roja'),  -- Humanidades City #5
(9, 4624806, 15, 'amarilla');  -- Humanidades City #4


-- ---------------------------------------------------------------------
-- 6) SANCIONES  (jugador, torneo, motivo, fecha de inicio, cantidad de fechas)
-- ---------------------------------------------------------------------
INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES

(4985989, 1, 'acumulacion de amarillas', 4, 1),  -- Derecho Atlético #4
(4558182, 1, 'roja', 4, 1),  -- Medicina Sporting #3
(5033878, 1, 'roja', 4, 2),  -- Humanidades City #5
(4440015, 1, 'disciplinaria', 4, 3);  -- Ingeniería FC #2
