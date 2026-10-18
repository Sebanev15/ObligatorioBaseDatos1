#!/bin/bash
set -e

mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<EOSQL
CREATE USER IF NOT EXISTS 'usuario_admin'@'%' IDENTIFIED BY '${DB_ADMIN_PASSWORD}';
CREATE USER IF NOT EXISTS 'usuario_planillero'@'%' IDENTIFIED BY '${DB_PLANILLERO_PASSWORD}';
CREATE USER IF NOT EXISTS 'usuario_auth'@'%' IDENTIFIED BY '${DB_AUTH_PASSWORD}';


GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO 'usuario_admin'@'%';

-- Planillero: solo lo necesario para cargar partidos (ajustar a tus tablas)
GRANT SELECT ON \`${MYSQL_DATABASE}\`.* TO 'usuario_planillero'@'%';
GRANT INSERT, UPDATE ON \`${MYSQL_DATABASE}\`.partido TO 'usuario_planillero'@'%';
GRANT INSERT, UPDATE ON \`${MYSQL_DATABASE}\`.gol TO 'usuario_planillero'@'%';
GRANT INSERT, UPDATE ON \`${MYSQL_DATABASE}\`.tarjeta TO 'usuario_planillero'@'%';


GRANT SELECT ON \`${MYSQL_DATABASE}\`.usuario TO 'usuario_auth'@'%';

FLUSH PRIVILEGES;
EOSQL