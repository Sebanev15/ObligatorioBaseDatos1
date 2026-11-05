import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.main import app
from app.routers import reportes


class ReportsTests(unittest.TestCase):
    def test_report_endpoints_are_registered(self):
        expected = {
            "/api/reportes/{id_torneo}/posiciones",
            "/api/reportes/{id_torneo}/goleadores",
            "/api/reportes/{id_torneo}/fair-play",
            "/api/reportes/{id_torneo}/goles-por-fecha",
            "/api/reportes/{id_torneo}/uso-canchas-turnos",
            "/api/reportes/jugadores-por-facultad-tipo",
            "/api/reportes/{id_torneo}/jugadores-sin-planilla",
            "/api/reportes/{id_torneo}/sanciones-por-equipo-motivo",
            "/api/reportes/{id_torneo}/estado-partidos",
            "/api/reportes/{id_torneo}/resultados-localia",
            "/api/reportes/{id_torneo}/promedio-tarjetas-por-fecha",
            "/api/reportes/{id_torneo}/goles-por-facultad",
        }

        self.assertTrue(expected.issubset(app.openapi()["paths"]))

    def test_positions_report_scopes_matches_to_tournament(self):
        user = SimpleNamespace(rol="administrador")
        connection = object()

        with patch.object(reportes, "get_connection") as get_connection, patch.object(
            reportes, "fetch_all", return_value=[]
        ) as fetch_all:
            get_connection.return_value.__enter__.return_value = connection

            result = reportes.tabla_posiciones(17, user)

        self.assertEqual(result, [])
        _, sql, params = fetch_all.call_args.args
        self.assertEqual(params, (17, 17))
        self.assertIn("p.id_torneo = %s AND p.estado = 'jugado'", sql)
        self.assertIn("WHEN g.autogol = 1", sql)


if __name__ == "__main__":
    unittest.main()
