import unittest
from datetime import time
from types import SimpleNamespace
from unittest.mock import patch

from app.routers import turnos
from app.schemas.turno import TurnoOut


class TurnosTests(unittest.TestCase):
    def test_select_formats_mysql_time_values_as_schema_compatible_strings(self):
        self.assertIn("TIME_FORMAT(hora_inicio, '%%H:%%i:%%s')", turnos._SELECT)
        self.assertIn("TIME_FORMAT(hora_fin, '%%H:%%i:%%s')", turnos._SELECT)

        user = SimpleNamespace(rol="administrador")
        connection = object()
        rows = [{"id_turno": 1, "hora_inicio": "18:00:00", "hora_fin": "19:00:00"}]
        with patch.object(turnos, "get_connection") as get_connection, patch.object(
            turnos, "fetch_all", return_value=rows
        ) as fetch_all:
            get_connection.return_value.__enter__.return_value = connection

            result = turnos.listar(user)

        self.assertEqual(fetch_all.call_args.args[1], turnos._SELECT + " ORDER BY hora_inicio")
        parsed = TurnoOut.model_validate(result[0])
        self.assertEqual(parsed.hora_inicio, time(18, 0))
        self.assertEqual(parsed.hora_fin, time(19, 0))


if __name__ == "__main__":
    unittest.main()
