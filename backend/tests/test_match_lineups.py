import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.routers import partidos_equipos, planillas_partidos
from app.schemas.planilla_partido import PlanillaPartidoCreate


class MatchTeamsTests(unittest.TestCase):
    def test_match_teams_are_read_from_match_columns(self):
        user = SimpleNamespace(rol="administrador")
        connection = object()
        rows = [
            {"id_partido": 1, "id_equipo": 1, "id_torneo": 1, "equipo": "Local"},
            {"id_partido": 1, "id_equipo": 2, "id_torneo": 1, "equipo": "Visitante"},
        ]
        with patch.object(partidos_equipos, "get_connection") as get_connection, patch.object(
            partidos_equipos, "fetch_one", return_value={"id_partido": 1}
        ), patch.object(partidos_equipos, "fetch_all", return_value=rows) as fetch_all:
            get_connection.return_value.__enter__.return_value = connection

            result = partidos_equipos.listar(1, user)

        self.assertEqual(result, rows)
        query = fetch_all.call_args.args[1]
        self.assertIn("p.id_equipo_local", query)
        self.assertIn("p.id_equipo_visitante", query)
        self.assertNotIn("partido_equipo", query)

    def test_lineup_assignment_validates_team_from_match_without_join_table(self):
        user = SimpleNamespace(rol="administrador")
        connection = object()
        expected = {
            "id_partido": 1,
            "ci_jugador": 1234567,
            "id_equipo": 2,
            "jugador": "Jugador Ejemplo",
            "equipo": "Visitante",
        }
        with patch.object(planillas_partidos, "get_connection") as get_connection, patch.object(
            planillas_partidos,
            "exigir_partido_editable",
            return_value={"id_torneo": 3, "numero_fecha": 2, "id_equipo_local": 1, "id_equipo_visitante": 2},
        ), patch.object(
            planillas_partidos, "fetch_one", side_effect=[{"ok": 1}, None, expected]
        ) as fetch_one, patch.object(planillas_partidos, "execute") as execute:
            get_connection.return_value.__enter__.return_value = connection

            result = planillas_partidos.agregar(
                1, PlanillaPartidoCreate(ci_jugador=1234567, id_equipo=2), user
            )

        self.assertEqual(result, expected)
        self.assertTrue(all("partido_equipo" not in call.args[1] for call in fetch_one.call_args_list))
        execute.assert_called_once()

    def test_lineup_rejects_team_not_in_match(self):
        user = SimpleNamespace(rol="administrador")
        connection = object()
        with patch.object(planillas_partidos, "get_connection") as get_connection, patch.object(
            planillas_partidos,
            "exigir_partido_editable",
            return_value={"id_torneo": 3, "numero_fecha": 2, "id_equipo_local": 1, "id_equipo_visitante": 2},
        ), patch.object(planillas_partidos, "execute") as execute:
            get_connection.return_value.__enter__.return_value = connection

            with self.assertRaises(HTTPException) as error:
                planillas_partidos.agregar(
                    1, PlanillaPartidoCreate(ci_jugador=1234567, id_equipo=4), user
                )

        self.assertEqual(error.exception.status_code, 422)
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
