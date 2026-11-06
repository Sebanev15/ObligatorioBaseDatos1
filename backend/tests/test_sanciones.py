import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.main import app
from app.routers import sanciones_jugadores


class SanctionCandidateTests(unittest.TestCase):
    def test_candidate_route_is_registered_before_sanction_id_route(self):
        routes = [
            route.path
            for route in sanciones_jugadores.router.routes
            if "GET" in route.methods
        ]
        self.assertLess(routes.index("/sanciones/candidatos"), routes.index("/sanciones/{id_sancion}"))
        self.assertIn("/api/sanciones/candidatos", app.openapi()["paths"])

    def test_candidates_are_scoped_to_roster_members_of_tournament(self):
        user = SimpleNamespace(rol="administrador")
        connection = object()
        candidates = [{"ci": 1234567, "nombre": "Ana", "apellido": "Pérez"}]

        with patch.object(sanciones_jugadores, "get_connection") as get_connection, patch.object(
            sanciones_jugadores, "fetch_all", return_value=candidates
        ) as fetch_all:
            get_connection.return_value.__enter__.return_value = connection

            result = sanciones_jugadores.listar_candidatos(user, 7)

        self.assertEqual(result, candidates)
        _, sql, params = fetch_all.call_args.args
        self.assertIn("JOIN equipo_jugador_torneo", sql)
        self.assertIn("ejt.id_torneo = %s", sql)
        self.assertEqual(params, (7,))


if __name__ == "__main__":
    unittest.main()
