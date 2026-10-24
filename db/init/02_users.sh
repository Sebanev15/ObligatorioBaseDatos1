#!/bin/bash
set -eo pipefail

DB="\`${MYSQL_DATABASE}\`"
# Todo el torneo menos login: el planillero no debe ver los hashes
TABLAS="facultad jugador torneo equipo equipo_jugador_torneo complejo cancha turno partido planilla_partido gol tarjeta sancion_jugador"

GRANTS=""
for t in $TABLAS; do
  GRANTS="${GRANTS}GRANT SELECT ON ${DB}.\`${t}\` TO 'usuario_planillero'@'%';"$'\n'
done

mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" <<EOSQL
CREATE USER IF NOT EXISTS 'usuario_admin'@'%'      IDENTIFIED BY '${DB_ADMIN_PASSWORD}';
CREATE USER IF NOT EXISTS 'usuario_planillero'@'%' IDENTIFIED BY '${DB_PLANILLERO_PASSWORD}';
CREATE USER IF NOT EXISTS 'usuario_auth'@'%'       IDENTIFIED BY '${DB_AUTH_PASSWORD}';

-- Admin: gestiona toda la información (sin permisos de DDL)
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON ${DB}.* TO 'usuario_admin'@'%';

-- Auth: solo lee la tabla login
GRANT SELECT ON ${DB}.\`login\` TO 'usuario_auth'@'%';

-- Planillero: lee el torneo; escribe solo planilla, goles y tarjetas
${GRANTS}
GRANT INSERT, UPDATE, DELETE ON ${DB}.\`planilla_partido\` TO 'usuario_planillero'@'%';
GRANT INSERT, UPDATE, DELETE ON ${DB}.\`gol\`              TO 'usuario_planillero'@'%';
GRANT INSERT, UPDATE, DELETE ON ${DB}.\`tarjeta\`          TO 'usuario_planillero'@'%';
-- puede marcar un partido como jugado, pero no crearlo ni tocar otra columna
GRANT UPDATE (estado) ON ${DB}.\`partido\` TO 'usuario_planillero'@'%';

FLUSH PRIVILEGES;
EOSQL